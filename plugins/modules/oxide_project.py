#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oxide_utils import validate_name
import requests
import json

DOCUMENTATION = r'''
---
module: oxide_project
short_description: Manage projects in Oxide cloud computer
description:
  - This module allows you to create and delete projects in the Oxide cloud computer.
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
  name:
    description:
      - The name of the project.
    required: true
    type: str
  description:
    description:
      - A description of the project.
    required: false
    type: str
    default: ''
  state:
    description:
      - The desired state of the project.
    required: true
    type: str
    choices: ['present', 'absent']
    default: 'present'
author:
  - James Force (@jforce)
'''

EXAMPLES = r'''
# Create a project
- name: Create a project
  oxide_project:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    name: "mynewproject"
    description: "A new project"
    state: present

# Delete a project
- name: Delete a project
  oxide_project:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    name: "mynewproject"
    state: absent
'''

RETURN = r'''
project:
  description: Information about the project created.
  returned: when state is 'present'
  type: dict
  sample: {
    "id": "project_id",
    "name": "myproject",
    "description": "A new project"
  }
msg:
  description: Message indicating the result of the operation.
  returned: when state is 'absent'
  type: str
  sample: "Project deleted"
response:
  description: The full API response in case of failure.
  returned: on failure
  type: dict
'''

def create_project(data, oxide_host, headers):
    payload = {
        "name": data['name'],
        "description": data['description']
    }
    response = requests.post(f"{oxide_host}/v1/projects", headers=headers, json=payload)
    return response.status_code, response.json()

def delete_project(name, oxide_host, headers):
    response = requests.delete(f"{oxide_host}/v1/projects/{name}", headers=headers)
    if response.status_code == 204:
        return response.status_code, {}
    return response.status_code, response.json()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            oxide_host=dict(required=True, type='str'),
            oxide_token=dict(required=True, type='str', no_log=True),
            name=dict(required=True, type='str'),
            description=dict(required=False, type='str', default=''),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    oxide_host = module.params['oxide_host']
    oxide_token = module.params['oxide_token']
    name = module.params['name']
    description = module.params['description']
    state = module.params['state']

    is_valid, error_message = validate_name(name)
    if not is_valid:
        module.fail_json(msg=error_message)

    headers = {
        "Authorization": f"Bearer {oxide_token}",
        "Content-Type": "application/json"
    }

    if state == 'present':
        status_code, response = create_project({
            "name": name,
            "description": description
        }, oxide_host, headers)

        if status_code == 201:
            module.exit_json(changed=True, project=response, msg="Project created")
        elif status_code == 400:
            if 'error_code' in response and response['error_code'] == 'ObjectAlreadyExists':
                module.exit_json(changed=False, msg="Project already present")
            else:
                module.fail_json(msg="Failed to create project", response=response)
        else:
            module.fail_json(msg="Failed to create project", response=response)

    elif state == 'absent':
        status_code, response = delete_project(name, oxide_host, headers)

        if status_code == 204:
            module.exit_json(changed=True, msg="Project deleted")
        elif status_code == 404:
            if 'error_code' in response and response['error_code'] == 'ObjectNotFound':
                module.exit_json(changed=False, msg="Project not present")
            else:
                module.fail_json(msg="Failed to delete project", response=response)
        else:
            module.fail_json(msg="Failed to delete project", response=response)

if __name__ == '__main__':
    main()
