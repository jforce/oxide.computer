#!/usr/bin/python

DOCUMENTATION = r'''
---
module: oxide_disk_info
short_description: Retrieve information about disks in Oxide
description:
    - This module allows the user to retrieve information about all disks in a specified project or specific disks by their IDs using the Oxide API.
version_added: "1.0"
author:
    - James Force (@jforce)
options:
    oxide_host:
        description:
            - The base URL for the Oxide API.
        required: true
        type: str
    oxide_token:
        description:
            - The API key for authenticating with the Oxide API.
        required: true
        type: str
        no_log: true
    project:
        description:
            - Name or ID of the project. This is required when retrieving all disks.
        required: false
        type: str
    disk_ids:
        description:
            - A list of disk IDs to retrieve. If not provided, information about all disks in the project will be retrieved.
        required: false
        type: list
        elements: str
'''

EXAMPLES = r'''
# Retrieve information about all disks in a project
- name: Retrieve all disks
  oxide_disk_info:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    project: "project_id_or_name"

# Retrieve information about specific disks by IDs
- name: Retrieve specific disks
  oxide_disk_info:
    oxide_host: "https://api.oxide.computer"
    oxide_token: "your_oxide_token"
    disk_ids:
      - "disk_id_1"
      - "disk_id_2"
'''

RETURN = r'''
disks:
    description: List of disks or details of specific disks
    returned: success
    type: list
    sample: [
        {
            "id": "disk_id_1",
            "name": "disk_name_1",
            "size": 100,
            "description": "Disk description 1",
            "source": "source_disk_id_or_snapshot_id_1"
        },
        {
            "id": "disk_id_2",
            "name": "disk_name_2",
            "size": 200,
            "description": "Disk description 2",
            "source": "source_disk_id_or_snapshot_id_2"
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
import requests

class OxideAPI:
    def __init__(self, oxide_host, oxide_token):
        self.oxide_host = oxide_host
        self.oxide_token = oxide_token
        self.headers = {
            'Authorization': f'Bearer {self.oxide_token}',
            'Content-Type': 'application/json'
        }

    def request(self, method, endpoint, params=None):
        url = f'{self.oxide_host}{endpoint}'
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            return {'error': str(http_err), 'response': response.json() if response.content else {}}
        except Exception as err:
            return {'error': str(err)}

    def get_disk(self, disk_id):
        endpoint = f'/v1/disks/{disk_id}'
        return self.request('GET', endpoint)

    def list_disks(self, project):
        endpoint = f'/v1/disks?project={project}'
        return self.request('GET', endpoint)

def main():
    module_args = dict(
        oxide_host=dict(type='str', required=True),
        oxide_token=dict(type='str', required=True, no_log=True),
        project=dict(type='str', required=False),
        disk_ids=dict(type='list', required=False, elements='str')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    oxide_host = module.params['oxide_host']
    oxide_token = module.params['oxide_token']
    project = module.params['project']
    disk_ids = module.params['disk_ids']

    api = OxideAPI(oxide_host, oxide_token)

    if module.check_mode:
        module.exit_json(changed=False)

    try:
        if disk_ids:
            disks = [api.get_disk(disk_id) for disk_id in disk_ids]
        else:
            if not project:
                module.fail_json(msg="Project is required when disk_ids are not provided")
            disks = api.list_disks(project)
        module.exit_json(changed=False, disks=disks)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
