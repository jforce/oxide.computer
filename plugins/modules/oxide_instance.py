#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oxide_utils import (
    validate_name,
    create_instance,
    delete_instance,
    get_instance
)

DOCUMENTATION = r'''
---
module: oxide_instance
short_description: Manage instances in Oxide Cloud
description:
  - This module allows you to create, delete, or modify instances in the Oxide Cloud environment.
  - You can specify details such as the instance name, description, hostname, memory, CPU count, disks, SSH keys, and user data.
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
  hostname:
    description:
      - The hostname of the instance.
    required: false
    type: str
  memory:
    description:
      - The amount of memory (in GB) to allocate to the instance.
    required: true
    type: int
  ncpus:
    description:
      - The number of CPUs to allocate to the instance.
    required: true
    type: int
  disks:
    description:
      - A list of disks to create or attach to the instance.
      - Each disk can have a type of C(create) or C(attach).
      - For C(create), provide the disk description, size (in GB), and disk source.
      - For C(attach), provide the disk ID.
    required: false
    type: list
    elements: dict
    suboptions:
      type:
        description:
          - The type of operation for the disk: C(create) or C(attach).
        required: true
        type: str
        choices: ['create', 'attach']
      description:
        description:
          - A description of the disk. Required for C(create).
        type: str
      size:
        description:
          - The size of the disk in GB. Required for C(create).
        type: int
      disk_source:
        description:
          - The source information for the disk. Required for C(create).
        type: dict
        suboptions:
          type:
            description:
              - The type of the disk source, such as C(image).
            type: str
          image_id:
            description:
              - The ID of the image to use as the disk source. Required if C(type=image).
            type: str
      id:
        description:
          - The ID of the disk to attach. Required for C(attach).
        type: str
  ssh_public_keys:
    description:
      - A list of SSH public keys to add to the instance.
    required: false
    type: list
    elements: str
  user_data:
    description:
      - User data to provide when creating the instance.
    required: false
    type: str
  start_on_create:
    description:
      - Whether to start the instance immediately after creation.
    required: false
    type: bool
    default: true
  state:
    description:
      - The desired state of the instance.
    required: true
    type: str
    choices: ['present', 'absent']
author:
  - James Force (@jforce)
'''

EXAMPLES = r'''
# Create an instance with a new disk
- name: Create an instance
  oxide_instance:
    name: "albert"
    description: "an instance named albert"
    hostname: "albert"
    memory: 4
    ncpus: 1
    disks:
      - name: "croissant"
        description: "disk description"
        type: create
        size: 10
        disk_source:
          type: "image"
          image_id: "5c2bfb2c-6e7b-4542-940e-7231161a2f80"
    ssh_public_keys:
      - "mykey"
    user_data: I2Nsb3VkLWNvbmZpZwpncm91cHM6CiAgLSBhZG1pbmdyb3VwOiBbcm9vdCxzeXNdCiAgLSBjbG91ZC11c2Vycwp1c2VyczoKICAtIG5hbWU6IGFsYmVydAogICAgZ2Vjb3M6IEFsYmVydCBUaGUgR3JleWhvdW5kCiAgICBwcmltYXJ5X2dyb3VwOiBjbG91ZC11c2VycwogICAgc2VsaW51eF91c2VyOiBzdGFmZl91CiAgICBleHBpcmVkYXRlOiAnMjAzMi0wOS0wMScKICAgIGxvY2tfcGFzc3dkOiBmYWxzZQogICAgcGFzc3dkOiAkNiRyb3VuZHM9NDA5NiQvdHV2MUpBZ3NFeDR3aEdSJHMyRTJ2VWRINlBhekx2WENrcUlCQWJqdGNKVldNTHMwZmZvRXJzSEVKSEFpdEVyT1RMdUg4SWpjTEV4LmNRNXVxdzJvem1VVUdQNVBEQWozYm9BTUsvCg==
    state: present

# Attach an existing disk to an instance
- name: Attach a disk to an instance
  oxide_instance:
    name: "albert"
    hostname: "albert"
    memory: 4
    ncpus: 1
    disks:
      - id: "existing_disk_id"
        type: attach
    state: present

# Delete an instance
- name: Delete an instance
  oxide_instance:
    name: "albert"
    state: absent
'''

RETURN = r'''
instance:
  description: Information about the instance created or modified.
  returned: when state is 'present'
  type: dict
  sample: {
    "id": "instance_id",
    "name": "albert",
    "description": "The Italian Greyhound",
    "hostname": "albert"
  }
msg:
  description: Message indicating the result of the operation.
  returned: always
  type: str
response:
  description: The full API response in case of failure.
  returned: on failure
  type: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            oxide_host=dict(required=True, type='str'),
            oxide_token=dict(required=True, type='str', no_log=True),
            project=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            description=dict(required=False, type='str', default=''),
            hostname=dict(required=True, type='str'),
            memory=dict(required=True, type='int'),
            ncpus=dict(required=True, type='int'),
            disks=dict(required=False, type='list', elements='dict', default=[]),
            ssh_public_keys=dict(required=False, type='list', elements='str', default=[]),
            user_data=dict(required=False, type='str', default=''),
            start_on_create=dict(required=False, type='bool', default=True),
            state=dict(default='present', choices=['present', 'absent'])
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
    disks = module.params['disks']
    ssh_public_keys = module.params['ssh_public_keys']
    user_data = module.params['user_data']
    start_on_create = module.params['start_on_create']
    state = module.params['state']

    is_valid, error_message = validate_name(name)
    if not is_valid:
        module.fail_json(msg=error_message)

    headers = {
        "Authorization": f"Bearer {oxide_token}",
        "Content-Type": "application/json"
    }

    if state == 'present':
        status_code, instance = get_instance(name, project, oxide_host, headers)
        if status_code == 404:
            disk_payload = []
            for disk in disks:
                if disk['type'] == 'create':
                    disk_payload.append({
                        "description": disk['description'],
                        "disk_source": disk['disk_source'],
                        "name": disk['name'],
                        "size": disk['size'] * 1024 * 1024 * 1024,
                        "type": "create"
                    })
                elif disk['type'] == 'attach':
                    disk_payload.append({
                        "id": disk['id'],
                        "type": "attach"
                    })

            data = {
                'name': name,
                'description': description,
                'hostname': hostname,
                'memory': memory,
                'ncpus': ncpus,
                'disks': disk_payload,
                'ssh_public_keys': ssh_public_keys,
                'user_data': user_data,
                'start_on_create': start_on_create
            }
            status_code, response = create_instance(data, project, oxide_host, headers)
            if status_code != 201:
                module.fail_json(msg="Failed to create instance", response=response)
            module.exit_json(changed=True, instance=response)
        elif status_code == 200:
            module.exit_json(changed=False, instance=instance)
        else:
            module.fail_json(msg="Failed to retrieve instance details", response=instance)

    elif state == 'absent':
        status_code, instance = get_instance(name, project, oxide_host, headers)
        if status_code == 404:
            module.exit_json(changed=False, msg="Instance does not exist")
        elif status_code == 200:
            status_code, response = delete_instance(name, project, oxide_host, headers)
            if status_code != 204:
                module.fail_json(msg="Failed to delete instance", response=response)
            module.exit_json(changed=True, msg="Instance deleted")
        else:
            module.fail_json(msg="Failed to retrieve instance details", response=instance)

if __name__ == '__main__':
    main()
