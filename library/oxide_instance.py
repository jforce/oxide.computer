#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Oxide Computer Company
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
import requests
import json
import re

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
    required: false
    type: str
    default: ''
  type:
    description:
      - The type of the instance.
    required: true
    type: str
  memory:
    description:
      - The amount of memory (in bytes) for the instance.
    required: true
    type: int
  vcpu:
    description:
      - The number of virtual CPUs for the instance.
    required: true
    type: int
  disk:
    description:
      - The disk configuration for the instance.
    required: true
    type: dict
    options:
      id:
        description:
          - The ID of the disk to attach to the instance.
        required: true
        type: str
      size:
        description:
          - The size of the disk (in bytes).
        required: true
        type: int
  network:
    description:
      - The network configuration for the instance.
    required: true
    type: dict
    options:
      id:
        description:
          - The ID of the network to attach to the instance.
        required: true
        type: str
      ip_address:
        description:
          - The IP address for the instance.
        required: true
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
    name: "mynewinstance"
    description: "A new instance"
    type: "t2.micro"
    memory: 2147483648  # 2 GB in bytes
    vcpu: 2
    disk:
      id: "disk_id"
      size: 10737418240  # 10 GB in bytes
    network:
      id: "network_id"
      ip_address: "192.168.1.10"
    state: present

# Delete an instance
- name: Delete an instance
  oxide_instance:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "3f8e4c7a-9a3d-4e2f-b1c7-839f6d34f7e2"
    name: "mynewinstance"
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
    "description": "A new instance"
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

def validate_name(name):
    pattern = r"^[a-z0-9][a-z0-9-]*$"
    if len(name) > 63:
        return False, "Name exceeds the maximum length of 63 characters"
    if not re.match(pattern, name):
        return False, "Name does not match the required pattern"
    return True, ""

def create_instance(data, project, oxide_host, headers):
    payload = {
        "description": data['description'],
        "name": data['name'],
        "type": data['type'],
        "memory": data['memory'],
        "vcpu": data['vcpu'],
        "disk": {
            "id": data['disk']['id'],
            "size": data['disk']['size']
        },
        "network": {
            "id": data['network']['id'],
            "ip_address": data['network']['ip_address']
        }
    }
    response = requests.post(f"{oxide_host}/v1/instances?project={project}", headers=headers, json=payload)
    return response.status_code, response.json()

def delete_instance(name, project, oxide_host, headers):
    response = requests.delete(f"{oxide_host}/v1/instances/{name}?project={project}", headers=headers)
    return response.status_code, response.json()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            oxide_host=dict(required=True, type='str'),
            oxide_token=dict(required=True, type='str', no_log=True),
            project=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            description=dict(required=False, type='str', default=''),
            type=dict(required=True, type='str'),
            memory=dict(required=True, type='int'),
            vcpu=dict(required=True, type='int'),
            disk=dict(
                required=True,
                type='dict',
                options=dict(
                    id=dict(type='str', required=True),
                    size=dict(type='int', required=True)
                )
            ),
            network=dict(
                required=True,
                type='dict',
                options=dict(
                    id=dict(type='str', required=True),
                    ip_address=dict(type='str', required=True)
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
    instance_type = module.params['type']
    memory = module.params['memory']
    vcpu = module.params['vcpu']
    disk = module.params['disk']
    network = module.params['network']
    state = module.params['state']

    # Validate name
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
            "type": instance_type,
            "memory": memory,
            "vcpu": vcpu,
            "disk": disk,
            "network": network
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
