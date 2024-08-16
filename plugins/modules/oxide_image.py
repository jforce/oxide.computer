#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oxide_utils import validate_name
import requests
import json

DOCUMENTATION = r'''
---
module: oxide_image
short_description: Manage images in Oxide cloud computer
description:
  - This module allows you to create and delete images in the Oxide cloud computer.
options:
  oxide_host:
    description:
      - The URL of the Oxide API.
    required: true
    type: str
  oxide_token:
    description:
      - The API token for authenticating with the Oxide API.
    required: true
    type: str
    no_log: true
  project:
    description:
      - The ID of the project in which to manage the image.
    required: true
    type: str
  name:
    description:
      - The name of the image.
    required: true
    type: str
  description:
    description:
      - A description of the image.
    required: false
    type: str
    default: ''
  os:
    description:
      - The operating system of the image.
    required: true
    type: str
  version:
    description:
      - The version of the operating system.
    required: true
    type: str
  source:
    description:
      - The source information for the image.
    required: true
    type: dict
    options:
      snapshot:
        description:
          - The snapshot information for the image source.
        required: true
        type: dict
        options:
          id:
            description:
              - The ID of the snapshot to create the image from.
            required: true
            type: str
  state:
    description:
      - The desired state of the image.
    required: true
    type: str
    choices: ['present', 'absent']
    default: 'present'
author:
  - James Force (@jforce)
'''

EXAMPLES = r'''
# Create an image
- name: Create an image
  oxide_image:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "3f8e4c7a-9a3d-4e2f-b1c7-839f6d34f7e2"
    name: "mynewimage"
    description: "A new image"
    os: "linux"
    version: "1.0"
    source:
      snapshot:
        id: "snapshot_id"
    state: present

# Delete an image
- name: Delete an image
  oxide_image:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "3f8e4c7a-9a3d-4e2f-b1c7-839f6d34f7e2"
    name: "mynewimage"
    state: absent
'''

RETURN = r'''
image:
  description: Information about the image created.
  returned: when state is 'present'
  type: dict
  sample: {
    "id": "image_id",
    "name": "myimage",
    "description": "A new image"
  }
msg:
  description: Message indicating the result of the operation.
  returned: when state is 'absent'
  type: str
  sample: "Image deleted"
response:
  description: The full API response in case of failure.
  returned: on failure
  type: dict
'''

def create_image(data, project, oxide_host, headers):
    if 'snapshot' not in data['source'] or 'id' not in data['source']['snapshot']:
        return 400, {'error_code': 'InvalidSource', 'message': 'The source must include a snapshot id'}

    payload = {
        "description": data['description'],
        "name": data['name'],
        "os": data['os'],
        "version": data['version'],
        "source": {
            "type": "snapshot",
            "id": data['source']['snapshot']['id']
        }
    }
    response = requests.post(f"{oxide_host}/v1/images?project={project}", headers=headers, json=payload)
    return response.status_code, response.json()

def delete_image(name, project, oxide_host, headers):
    response = requests.delete(f"{oxide_host}/v1/images/{name}?project={project}", headers=headers)
    if response.status_code == 204:
        return response.status_code, {}
    return response.status_code, response.json()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            oxide_host=dict(required=True, type='str'),


            oxide_token=dict(required=True, type='str', no_log=True),
            project=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            description=dict(required=False, type='str', default=''),
            os=dict(required=False, type='str'),
            version=dict(required=False, type='str'),
            source=dict(
                required=False,
                type='dict',
                options=dict(
                    snapshot=dict(
                        required=True,
                        type='dict',
                        options=dict(
                            id=dict(type='str', required=True)
                        )
                    )
                )
            ),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    oxide_host = module.params['oxide_host']
    oxide_token = module.params['oxide_token']
    project = module.params['project']
    name = module.params['name']
    description = module.params['description']
    os = module.params['os']
    version = module.params['version']
    source = module.params['source']
    state = module.params['state']

    is_valid, error_message = validate_name(name)
    if not is_valid:
        module.fail_json(msg=error_message)

    headers = {
        "Authorization": f"Bearer {oxide_token}",
        "Content-Type": "application/json"
    }

    if state == 'present':

        if not os:
            module.fail_json(msg="Parameter 'os' is required when state is 'present'")
        if not version:
            module.fail_json(msg="Parameter 'version' is required when state is 'present'")


        status_code, response = create_image({
            "name": name,
            "description": description,
            "os": os,
            "version": version,
            "source": source
        }, project, oxide_host, headers)

        if status_code == 201:
            module.exit_json(changed=True, image=response, msg="Image created")
        elif status_code == 400:
            if 'error_code' in response and response['error_code'] == 'ObjectAlreadyExists':
                module.exit_json(changed=False, msg="Image already present")
            else:
                module.fail_json(msg="Failed to create image", response=response)
        else:
            module.fail_json(msg="Failed to create image", response=response)

    elif state == 'absent':
        status_code, response = delete_image(name, project, oxide_host, headers)

        if status_code == 204:
            module.exit_json(changed=True, msg="Image deleted")
        elif status_code == 404:
            if 'error_code' in response and response['error_code'] == 'ObjectNotFound':
                module.exit_json(changed=False, msg="Image not present")
            else:
                module.fail_json(msg="Failed to delete image", response=image)
        else:
            module.fail_json(msg="Failed to delete image", response=image)


if __name__ == '__main__':
    main()
