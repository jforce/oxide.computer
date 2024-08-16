#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oxide_utils import validate_name
import requests

DOCUMENTATION = r'''
---
module: oxide_ssh_key
short_description: Manage SSH keys in Oxide cloud computer
description:
  - This module allows you to create and delete SSH keys in the Oxide cloud computer.
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
      - The name of the SSH key.
    required: true
    type: str
  public_key:
    description:
      - The public SSH key.
    required: true
    type: str
  description:
    description:
      - A description of the SSH key.
    required: false
    type: str
  state:
    description:
      - The desired state of the SSH key.
    required: true
    type: str
    choices: ['present', 'absent']
    default: 'present'
author:
  - James Force (@jforce)
'''

EXAMPLES = r'''
# Create an SSH key
- name: Create an SSH key
  oxide_ssh_key:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    name: "mysshkey"
    public_key: "ssh-rsa AAAAB3Nz..."
    description: "My SSH key"
    state: present

# Delete an SSH key
- name: Delete an SSH key
  oxide_ssh_key:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    name: "mysshkey"
    state: absent
'''

RETURN = r'''
ssh_key:
  description: Information about the SSH key created.
  returned: when state is 'present'
  type: dict
  sample: {
    "id": "ssh_key_id",
    "name": "mysshkey",
    "public_key": "ssh-rsa AAAAB3Nz..."
  }
msg:
  description: Message indicating the result of the operation.
  returned: when state is 'absent'
  type: str
  sample: "SSH key deleted"
response:
  description: The full API response in case of failure.
  returned: on failure
  type: dict
'''

def create_ssh_key(data, oxide_host, headers):
    payload = {
        "name": data['name'],
        "public_key": data['public_key'],
        "description": data['description']
    }
    response = requests.post(f"{oxide_host}/v1/me/ssh-keys", headers=headers, json=payload)
    return response.status_code, response.json()

def delete_ssh_key(name, oxide_host, headers):
    response = requests.delete(f"{oxide_host}/v1/me/ssh-keys/{name}", headers=headers)
    if response.status_code == 204:
        return response.status_code, {}
    return response.status_code, response.json()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            oxide_host=dict(required=True, type='str'),
            oxide_token=dict(required=True, type='str', no_log=True),
            name=dict(required=True, type='str'),
            public_key=dict(required=False, type='str'),
            description=dict(default='', required=False, type='str'),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    oxide_host = module.params['oxide_host']
    oxide_token = module.params['oxide_token']
    name = module.params['name']
    public_key = module.params['public_key']
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
        if not public_key:
            module.fail_json(msg="Parameter 'public_key' is required when state is 'present'")

        status_code, response = create_ssh_key({
            "name": name,
            "public_key": public_key,
            "description": description
        }, oxide_host, headers)

        if status_code == 201:
            module.exit_json(changed=True, ssh_key=response, msg="SSH key created")
        elif status_code == 400:
            if 'error_code' in response and response['error_code'] == 'ObjectAlreadyExists':
                module.exit_json(changed=False, msg="SSH key already present")
            else:
                module.fail_json(msg="Failed to create SSH key", response=response)
        else:
            module.fail_json(msg="Failed to create SSH key", response=response)

    elif state == 'absent':
        status_code, response = delete_ssh_key(name, oxide_host, headers)

        if status_code == 204:
            module.exit_json(changed=True, msg="SSH key deleted")
        elif status_code == 404:
            if 'error_code' in response and response['error_code'] == 'ObjectNotFound':
                module.exit_json(changed=False, msg="SSH key not present")
            else:
                module.fail_json(msg="Failed to delete SSH key", response=response)
        else:
            module.fail_json(msg="Failed to delete SSH key", response=response)

if __name__ == '__main__':
    main()
