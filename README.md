# Ansible Collection - derjd.general

[![Galaxy](https://img.shields.io/static/v1??style=flat&logo=ansible&label=galaxy&message=derJD.general&color=blue)](https://galaxy.ansible.com/derJD/general)

This repo contains the `derjd.general` collection. You'll find several plugins in this collection
that aren't part of the [community.general collection](https://github.com/ansible-collections/community.general)
and aren't part of more specialized collections as well.

## Requirements

* python >= 3
* python-requests
* python-lxml
* ansible >= 2.9

## Installation

You can use this collection simply by installing it with `ansible-galaxy`:

```bash
ansible-galaxy collection install derjd.general
```

If you are using requirement.yml files for downloading collections and roles, add these lines:

```yaml
collections:
  - derjd.general
```

## Usage

### Filter

#### dict2ini

Converts nested, human readable, dicts into list of dicts,
that are easily parsable by ansible loops.

```yaml
---

- hosts: localhost
  gather_facts: false
  vars:
    ini_vars:
      ima_1_section:
        ima_1_option: ima_1_value
        ima_2_option: ima_2_value
      ima_2_section:
        ima_3_option: ima_3_value
        ima_4_option: ima_4_value

  tasks:
    - name: edit /tmp/test.ini file
      ini_file:
        path: /tmp/test.ini
        section: "{{ item.section }}"
        option: "{{ item.option }}"
        value: "{{ item.value }}"
      loop: "{{ ini_vars | derjd.general.dict2ini }}"
```

### Inventory

#### html

Reads json inventories from any HTTP(s) source. The hosted inventory json file must comply with the [new inventory script convention](https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html#tuning-the-external-inventory-script), containing the top level `_meta` element with `hostvars` inside and all `groups` with `children` and `hosts`.
This inventory plugin should be detected by ansible's `auto inventory plugin` as soon as an inventory is specified that ends on `html_inventory.yml` or `html_inventory.yaml`.

**Example**:

Inventory hosted on a plain webserver without authentication.

`web.html_inventory.yml`:

```yaml
plugin: derjd.general.http
url: https://example.io/example_inventories/dev/inventory.json
```

```bash
ansible-inventory -i web.html_inventory.yml --graph
@all:
  |--@devstack:
  |  |--@api:
  |  |  |--api01ve.devstack
  [...]
```

Inventory hosted on gitlab pages and authentication enabled.

`gitlab_pages.html_inventory.yml`:

```yaml
plugin: derjd.general.http
url: https://example.gitlab.io/example_inventories/dev/inventory.json
auth_method: gitlab
```

```bash
export HTTP_USERNAME=example_USERNAME
export HTTP_PASSWORD=example_PASSWORD

ansible-inventory -i gitlab_pages.html_inventory.yml --graph
@all:
  |--@devstack:
  |  |--@api:
  |  |  |--api01ve.devstack
  [...]
```

## License

* Code released under [GNU General Public License v3.0 or later](https://www.gnu.org/licenses/gpl-3.0.txt)

## Author

* [derJD](https://github.com/derJD/)
