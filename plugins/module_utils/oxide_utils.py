import re
import requests

def validate_name(name):
    """
    Validate a name according to specific rules.
    Names must begin with a lower case ASCII letter, be composed exclusively of lowercase ASCII, uppercase ASCII, numbers, and '-', and may not end with a '-'.
    Names cannot be a UUID though they may contain a UUID.
    Minimum length is 1 character.
    Maximim length is 63 characters.

    :param name: The name to validate
    :return: (is_valid, error_message)
    """
    pattern = r"^[a-z0-9][a-z0-9-]*$"
    if len(name) > 63:
        return False, "Name exceeds the maximum length of 63 characters"
    if len(name) < 1:
        return False, "Name does not meet the minimum length of 1 character"
    if not re.match(pattern, name):
        return False, "Name does not match the required pattern. Names must begin with a lower case ASCII letter, be composed exclusively of lowercase ASCII, uppercase ASCII, numbers, and '-', and may not end with a '-'. Names cannot be a UUID though they may contain a UUID."
    return True, ""

def create_instance(data, project, oxide_host, headers):
    payload = {
        "name": data['name'],
        "description": data['description'],
        "hostname": data['hostname'],
        "memory": data['memory'] * 1024 * 1024 * 1024,
        "ncpus": data['ncpus'],
        "start_on_create": data.get('start_on_create', True)
    }

    disks_payload = []
    if 'disks' in data and data['disks']:
        for disk in data['disks']:
            if disk['type'] == 'create':
                disks_payload.append({
                    "description": disk['description'],
                    "disk_source": disk['disk_source'],
                    "name": disk['name'],
                    "size": disk['size'],
                    "type": "create"
                })
            elif disk['type'] == 'attach':
                disks_payload.append({
                    "name": disk['name'],
                    "type": "attach"
                })

    if disks_payload:
        payload['disks'] = disks_payload

    if 'ssh_public_keys' in data and data['ssh_public_keys']:
        payload['ssh_public_keys'] = data['ssh_public_keys']

    if 'user_data' in data and data['user_data']:
        payload['user_data'] = data['user_data']

    response = requests.post(f"{oxide_host}/v1/instances?project={project}", headers=headers, json=payload)
    return response.status_code, response.json()

def get_instance(name, project, oxide_host, headers):
    response = requests.get(f"{oxide_host}/v1/instances/{name}?project={project}", headers=headers)
    return response.status_code, response.json()

def delete_instance(name, project, oxide_host, headers):
    response = requests.delete(f"{oxide_host}/v1/instances/{name}?project={project}", headers=headers)
    return response.status_code, response.json()
