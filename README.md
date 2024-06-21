# Oxide Ansible POC

## Dev notes:

Oxide resources:
* [Oxide API docs](https://docs.oxide.computer/api/guides/introduction) 
* [OpenAPI spec](https://github.com/oxidecomputer/oxide.rs/blob/main/oxide.json)

Ansible resources:
* [Ansible developer guide](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#creating-a-module)

## User notes:

Get oxide token:
```bash
oxide auth status --show-token
```

User vars defined in a vault:
```yaml
oxide_api: "https://******.oxide-preview.com"
oxide_project: "*************"
oxide_token: "oxide-token-******************"
```

View docs:
```bash
ANSIBLE_LIBRARY=./library ansible-doc oxide_disk
```

Run testing playbook:
```bash
ansible-playbook disk_test.yaml --vault-pass-file .vault_pass.txt
```

