#!/usr/bin/python
# TO DO:
# - Check/add response codes and handling
# - Add defaults for type and block size

from ansible.module_utils.basic import AnsibleModule
import requests
import json
import re


DOCUMENTATION = r'''
---
module: oxide_disk
short_description: Manage disks in Oxide cloud computer
description:
  - This module allows you to create and delete disks in the Oxide cloud computer.
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
      - The ID of the project in which to manage the disk.
    required: true
    type: str
  name:
    description:
      - The name of the disk.
    required: true
    type: str
  description:
    description:
      - A description of the disk.
    required: false
    type: str
    default: ''
  size:
    description:
      - The size of the disk in GB. Required for 'blank', 'snapshot', 'image', and 'importing_blocks'.
    required: true
    type: int
  disk_source:
    description:
      - The source information for the disk.
    required: true
    type: dict
    options:
      type:
        description:
          - The type of the disk source.
        required: true
        type: str
        choices: ['blank', 'snapshot', 'image', 'importing_blocks']
      block_size:
        description:
          - The block size of the disk. Required when type is 'blank' or 'importing_blocks'.
        required: false
        type: int
        choices: [512, 2048, 4096]
      snapshot_id:
        description:
          - The ID of the snapshot from which to create the disk. Required when type is 'snapshot'.
        required: false
        type: str
      image_id:
        description:
          - The ID of the image from which to create the disk. Required when type is 'image'.
        required: false
        type: str
  state:
    description:
      - The desired state of the disk.
    required: true
    type: str
    choices: ['present', 'absent']
    default: 'present'
author:
  - James Force (@jforce)
'''

EXAMPLES = r'''
# Create a blank disk
- name: Create a blank disk
  oxide_disk:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "3f8e4c7a-9a3d-4e2f-b1c7-839f6d34f7e2"
    name: "blanketyblank"
    description: "A new blank disk"
    size: 50
    disk_source:
      type: "blank"
      block_size: 512
    state: present

# Create a disk from a snapshot
- name: Create a disk from a snapshot
  oxide_disk:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "3f8e4c7a-9a3d-4e2f-b1c7-839f6d34f7e2"
    name: "thisisnotaphotograph"
    description: "A disk from a snapshot"
    size: 50
    disk_source:
      type: "snapshot"
      snapshot_id: "snapshot_id"
    state: present

# Create a disk from an image
- name: Create a disk from an image
  oxide_disk:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "3f8e4c7a-9a3d-4e2f-b1c7-839f6d34f7e2"
    name: "thisisapicture"
    description: "A disk from an image"
    size: 50
    disk_source:
      type: "image"
      image_id: "image_id"
    state: present

# Create an importing blocks disk
- name: Create an importing blocks disk
  oxide_disk:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "3f8e4c7a-9a3d-4e2f-b1c7-839f6d34f7e2"
    name: "importo"
    description: "A disk ready for importing blocks"
    size: 100
    disk_source:
      type: "importing_blocks"
      block_size: 4096
    state: present

# Delete a disk
- name: Delete a disk
  oxide_disk:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "3f8e4c7a-9a3d-4e2f-b1c7-839f6d34f7e2"
    name: "blanketyblank"
    state: absent
'''

RETURN = r'''
disk:
  description: Information about the disk created.
  returned: when state is 'present'
  type: dict
  sample: {
    "id": "disk_id",
    "name": "mydisk",
    "size": 50,
    "block_size": 512,
    "description": "A new disk"
  }
msg:
  description: Message indicating the result of the operation.
  returned: when state is 'absent'
  type: str
  sample: "Disk deleted"
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

def create_disk(data, project, oxide_host, headers):
    payload = {
        "description": data['description'],
        "disk_source": {
            "type": data['disk_source']['type']
        },
        "name": data['name'],
        "size": data['size'] * 1024 * 1024 * 1024  # convert GB to bytes
    }

    disk_type = data['disk_source']['type']

    if disk_type in ['blank', 'importing_blocks']:
        payload['disk_source']['block_size'] = data['disk_source']['block_size']
    elif disk_type == 'snapshot':
        payload['disk_source']['snapshot_id'] = data['disk_source']['snapshot_id']
    elif disk_type == 'image':
        payload['disk_source']['image_id'] = data['disk_source']['image_id']

    response = requests.post(f"{oxide_host}/v1/disks?project={project}", headers=headers, json=payload)
    return response.status_code, response.json()

def delete_disk(name, project, oxide_host, headers):
    response = requests.delete(f"{oxide_host}/v1/disks/{name}?project={project}", headers=headers)
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
            size=dict(required=False, type='int'),
            disk_source=dict(
                required=False,
                type='dict',
                options=dict(
                    type=dict(type='str', required=True, choices=['blank', 'snapshot', 'image', 'importing_blocks']),
                    block_size=dict(type='int', required=False, choices=[512, 2048, 4096], default=512),
                    snapshot_id=dict(type='str', required=False),
                    image_id=dict(type='str', required=False),
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
    size = module.params['size']
    disk_source = module.params['disk_source']
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
        if disk_source['type'] in ['blank', 'importing_blocks'] and 'block_size' not in disk_source:
            module.fail_json(msg="Parameter 'block_size' is required when disk_source type is 'blank' or 'importing_blocks'")
        if disk_source['type'] == 'snapshot' and 'snapshot_id' not in disk_source:
            module.fail_json(msg="Parameter 'snapshot_id' is required when disk_source type is 'snapshot'")
        if disk_source['type'] == 'image' and 'image_id' not in disk_source:
            module.fail_json(msg="Parameter 'image_id' is required when disk_source type is 'image'")
        if not size:
            module.fail_json(msg="Parameter 'size' is required when state is 'present'")

        status_code, response = create_disk({
            "name": name,
            "description": description,
            "size": size,
            "disk_source": disk_source
        }, project, oxide_host, headers)

        if status_code == 201:
            module.exit_json(changed=True, disk=response)
        elif status_code == 400:
            module.exit_json(changed=False, disk=response)
        else:
            module.fail_json(msg="Failed to create disk", response=response)

    elif state == 'absent':
        status_code, response = delete_disk(name, project, oxide_host, headers)
        if status_code == 204:
            module.exit_json(changed=True, msg="Disk deleted")
        elif status_code == 404:
            if 'error_code' in response and response['error_code'] == 'ObjectNotFound':
              module.exit_json(changed=False, msg="Disk not present")
            else:
                module.fail_json(msg="Failed to delete disk", response=response)
        else:
            module.fail_json(msg="Failed to delete disk", response=response)


if __name__ == '__main__':
    main()