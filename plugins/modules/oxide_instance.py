#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Oxide Computer Company
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oxide_utils import validate_name
import requests

DOCUMENTATION = r'''
---
module: oxide_instance
short_description: Manage instances in Oxide cloud computer
description:
  - This module allows you to create and delete instances in the Oxide cloud computer.
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
      - The ID of the project in which to manage the instance.
    required: true
    type: str
  name:
    description:
      - The name of the instance.
    required: true
    type: str
  description:
    description:
      - A description of the instance.
    required: true
    type: str
  hostname:
    description:
      - Hostname of the instance.
    required: true
    type: str
  memory:
    description:
      - Instance memory in bytes.
    required: true
    type: int
  ncpus:
    description:
      - Number of CPUs allocated for this instance.
    required: true
    type: int
  disks:
    description:
      - The disks to be created or attached for this instance.
    required: false
    type: dict
    options=dict(
      create=dict(
        description="Disks to be created",
        required=False,
        type='list',
        elements='dict',
        options=dict(
          description=dict(required=True, type='str'),
          disk_source=dict(required=True, type='dict', options=dict(
            type=dict(type='str', required=True, choices=['blank', 'snapshot', 'image', 'importing_blocks']),
            block_size=dict(type='int', required=False, choices=[512, 2048, 4096]),
            snapshot_id=dict(type='str', required=False),
            image_id=dict(type='str', required=False),
          )),
          name=dict(required=True, type='str'),
          size=dict(required=True, type='int')
        )
      ),
      attach=dict(
        description="IDs of the disks to be attached",
        required=False,
        type='list',
        elements='str'
      )
    )
  ssh_public_keys:
    description:
      - An allowlist of IDs of the saved SSH public keys to be transferred to the instance via cloud-init during instance creation.
    required: false
    type: list
    elements: str
  start_on_create:
    description:
      - Starts the instance on creation when set to true.
    required: false
    type: bool
    default: true
  user_data:
    description:
      - User data for instance initialization systems (such as cloud-init). Must be a Base64-encoded string.
    required: false
    type: str
  state:
    description:
      - The desired state of the instance.
    required: true
    type: str
    choices: ['present', 'absent']
    default: 'present'
author:
  - James Force (@jforce)
'''

EXAMPLES = r'''
# Create an instance
- name: Create an instance
  oxide_instance:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "3f8e4c7a-9a3d-4e2f-b1c7-839f6d34f7e2"
    name: "myinstance"
    description: "My instance"
    hostname: "hostname"
    memory: 4
    ncpus: 1
    disks:
      create:
        - description: "disk description"
          disk_source:
            type: "blank"
            block_size: 512
          name: "mydisk"
          size: 10
      attach:
        - "611bb17d-6883-45be-b3aa-8a186fdeafe8"
    state: present

# Delete an instance
- name: Delete an instance
  oxide_instance:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "3f8e4c7a-9a3d-4e2f-b1c7-839f6d34f7e2"
    name: "myinstance"
    state: absent
'''

RETURN = r'''
instance:
  description: Information about the instance created.
  returned: when state is 'present'
  type: dict
  sample: {
    "id": "instance_id",
    "name": "myinstance",
    "description": "My instance",
    "hostname": "hostname",
    "memory": 4,
    "ncpus": 1,
    "disks": {
      "create": [{
        "description": "disk description",
        "disk_source": {
          "type": "blank",
          "block_size": 512
        },
        "name": "mydisk",
        "size": 10
      }],
      "attach": ["611bb17d-6883-45be-b3aa-8a186fdeafe8"]
    }
  }
msg:
  description: Message indicating the result of the operation.
  returned: when state is 'absent'
  type: str
  sample: "Instance deleted"
response:
  description: The full API response in case of failure.
  returned: on failure
  type: dict
'''

def create_instance(data, project, oxide_host, headers):
    payload = {
        "name": data['name'],
        "description": data['description'],
        "hostname": data['hostname'],
        "memory": data['memory'] * 1024 * 1024 * 1024,
        "ncpus": data['ncpus'],
        "start_on_create": data.get('start_on_create', True)
    }

    if 'disks' in data and data['disks']:
        disks = []
        if 'create' in data['disks'] and data['disks']['create']:
            for disk in data['disks']['create']:
                disks.append({
                    "description": disk['description'],
                    "disk_source": disk['disk_source'],
                    "name": disk['name'],
                    "size": disk['size'] * 1024 * 1024 * 1024,
                    "type": "create"
                })
        if 'attach' in data['disks'] and data['disks']['attach']:
            for disk_id in data['disks']['attach']:
                disks.append({
                    "id": disk_id,
                    "type": "attach"
                })
        payload['disks'] = disks

    if 'ssh_public_keys' in data and data['ssh_public_keys']:
        payload['ssh_public_keys'] = data['ssh_public_keys']

    if 'user_data' in data and data['user_data']:
        payload['user_data'] = data['user_data']

    response = requests.post(f"{oxide_host}/v1/instances?project={project}", headers=headers, json=payload)
    return response.status_code, response.json()

def delete_instance(name, project, oxide_host, headers):
    response = requests.delete(f"{oxide_host}/v1/instances/{name}?project={project}", headers=headers)
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
            description=dict(required=True, type='str'),
            hostname=dict(required=True, type='str'),
            memory=dict(required=True, type='int'),
            ncpus=dict(required=True, type='int'),
            disks=dict(required=False, type='dict', options=dict(
                create=dict(
                    type='list',
                    elements='dict',
                    options=dict(
                        description=dict(required=True, type='str'),
                        disk_source=dict(required=True, type='dict', options=dict(
                            type=dict(type='str', required=True, choices=['blank', 'snapshot', 'image', 'importing_blocks']),
                            block_size=dict(type='int', required=False, choices=[512, 2048, 4096]),
                            snapshot_id=dict(type='str', required=False),
                            image_id=dict(type='str', required=False),
                        )),
                        name=dict(required=True, type='str'),
                        size=dict(required=True, type='int')
                    )
                ),
                attach=dict(
                    type='list',
                    elements='str'
                )
            )),
            ssh_public_keys=dict(required=False, type='list', elements='str'),
            start_on_create=dict(required=False, type='bool', default=True),
            user_data=dict(required=False, type='str'),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    oxide_host = module.params['oxide_host']
    oxide_token = module.params['oxide_token']
    project = module.params['project']
    name = module.params['name']
    description = module.params['description']
    hostname = module.params['hostname']
    memory = module.params['memory']
    ncpus = module.params['ncpus']
    disks = module.params.get('disks', {})
    ssh_public_keys = module.params.get('ssh_public_keys', [])
    start_on_create = module.params['start_on_create']
    user_data = module.params.get('user_data', '')
    state = module.params['state']

    is_valid, error_message = validate_name(name)
    if not is_valid:
        module.fail_json(msg=error_message)

    headers = {
        "Authorization": f"Bearer {oxide_token}",
        "Content-Type": "application/json"
    }

    if state == 'present':
        status_code, response = create_instance({
            "name": name,
            "description": description,
            "hostname": hostname,
            "memory": memory,
            "ncpus": ncpus,
            "disks": disks,
            "ssh_public_keys": ssh_public_keys,
            "start_on_create": start_on_create,
            "user_data": user_data
        }, project, oxide_host, headers)

        if status_code == 201:
            module.exit_json(changed=True, instance=response, msg="Instance created")
        elif status_code == 400:
            if 'error_code' in response and response['error_code'] == 'ObjectAlreadyExists':
                module.exit_json(changed=False, msg="Instance already present")
            else:
                module.fail_json(msg="Failed to create instance", response=response)
        else:
            module.fail_json(msg="Failed to create instance", response=response)

    elif state == 'absent':
        status_code, response = delete_instance(name, project, oxide_host, headers)

        if status_code == 204:
            module.exit_json(changed=True, msg="Instance deleted")
        elif status_code == 404:
            if 'error_code' in response and response['error_code'] == 'ObjectNotFound':
                module.exit_json(changed=False, msg="Instance not present")
            else:
                module.fail_json(msg="Failed to delete instance", response=response)
        else:
            module.fail_json(msg="Failed to delete instance", response=response)

if __name__ == '__main__':
    main()
