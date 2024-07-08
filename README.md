# Oxide Computer Collection

This repository contains the `oxide.computer` Ansible Collection.

Please note this collection is in a **very early development stage**. 

> Here be dragons!

## Modules

The following modules have been created so far:

| Module         | Description                                |
|----------------|--------------------------------------------|
| oxide_disk     | Create and delete different types of disks |
| oxide_image    | Create images from snapshots               |
| oxide_project  | Manage projects                            |
| oxide_snapshot | Manage snapshots                           |
| oxide_ssh_key  | Manage user SSH keys                       |

As you can see, there is no '_info' type modules yet and key modules that would manage instances and networking are missing too. These will be picked up next. The initial goal is to have a similar parity with the [existing Terraform](https://registry.terraform.io/providers/oxidecomputer/oxide/latest/docs).

## Using this collection

See [installing collections](https://docs.ansible.com/ansible/latest/collections_guide/collections_installing.html) and [using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

Authentication requires a token which can be obtained using the Oxide CLI:
```bash
oxide auth status --show-token
```

## More information

<!-- List out where the user can find additional information, such as working group meeting times, slack/IRC channels, or documentation for the product this collection automates. At a minimum, link to: -->

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/devel/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/devel/dev_guide/index.html)
- [Ansible Collections Checklist](https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html)
- [The Bullhorn (the Ansible Contributor newsletter)](https://us19.campaign-archive.com/home/?u=56d874e027110e35dea0e03c1&id=d6635f5420)
- [News for Maintainers](https://github.com/ansible-collections/news-for-maintainers)

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
