#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oxide_utils import validate_name
import requests
import json

DOCUMENTATION = r'''
---
module: oxide_snapshot
short_description: Manage snapshots in Oxide cloud computer
description:
  - This module allows you to create and delete snapshots in the Oxide cloud computer.
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
      - The ID of the project in which to manage the snapshot.
    required: true
    type: str
  name:
    description:
      - The name of the snapshot.
    required: true
    type: str
  description:
    description:
      - A description of the snapshot.
    required: false
    type: str
    default: ''
  disk:
    description:
      - The ID of the disk to create the snapshot from.
    required: true
    type: str
  state:
    description:
      - The desired state of the snapshot.
    required: true
    type: str
    choices: ['present', 'absent']
    default: 'present'
author:
  - James Force (@jforce)
'''

EXAMPLES = r'''
# Create a snapshot
- name: Create a snapshot
  oxide_snapshot:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "your_project_id"
    name: "snap"
    description: "A snapshot of a disk"
    disk: "disk"
    state: present

# Delete a snapshot
- name: Delete a snapshot
  oxide_snapshot:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "your_project_id"
    name: "snap"
    state: absent
'''

RETURN = r'''
snapshot:
  description: Information about the snapshot created.
  returned: when state is 'present'
  type: dict
  sample: {
    "id": "snapshot_id",
    "name": "snap",
    "description": "A snapshot of a disk"
  }
msg:
  description: Message indicating the result of the operation.
  returned: when state is 'absent'
  type: str
  sample: "Snapshot deleted"
response:
  description: The full API response in case of failure.
  returned: on failure
  type: dict
'''

def create_snapshot(data, project, oxide_host, headers):
    payload = {
        "name": data['name'],
        "description": data['description'],
        "disk": data['disk']
    }
    response = requests.post(f"{oxide_host}/v1/snapshots?project={project}", headers=headers, json=payload)
    return response.status_code, response.json()

def delete_snapshot(name, project, oxide_host, headers):
    response = requests.delete(f"{oxide_host}/v1/snapshots/{name}?project={project}", headers=headers)
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
            disk=dict(required=False, type='str'),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    oxide_host = module.params['oxide_host']
    oxide_token = module.params['oxide_token']
    project = module.params['project']
    name = module.params['name']
    description = module.params['description']
    disk = module.params['disk']
    state = module.params['state']

    is_valid, error_message = validate_name(name)
    if not is_valid:
        module.fail_json(msg=error_message)

    headers = {
        "Authorization": f"Bearer {oxide_token}",
        "Content-Type": "application/json"
    }

    if state == 'present':

        if not disk:
            module.fail_json(msg="Parameter 'disk' is required when state is 'present'")

        status_code, response = create_snapshot({
            "name": name,
            "description": description,
            "disk": disk
        }, project, oxide_host, headers)

        if status_code == 201:
            module.exit_json(changed=True, snapshot=response, msg="Snapshot created")
        elif status_code == 400:
            if 'error_code' in response and response['error_code'] == 'ObjectAlreadyExists':
                module.exit_json(changed=False, msg="Snapshot already present")
            else:
                module.fail_json(msg="Failed to create snapshot", response=response)
        else:
            module.fail_json(msg="Failed to create snapshot", response=response)

    elif state == 'absent':
        status_code, response = delete_snapshot(name, project, oxide_host, headers)

        if status_code == 204:
            module.exit_json(changed=True, msg="Snapshot deleted")
        elif status_code == 404:
            if 'error_code' in response and response['error_code'] == 'ObjectNotFound':
                module.exit_json(changed=False, msg="Snapshot not present")
            else:
                module.fail_json(msg="Failed to delete snapshot", response=response)
        else:
            module.fail_json(msg="Failed to delete snapshot", response=response)

if __name__ == '__main__':
    main()
