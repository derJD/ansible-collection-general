# Copyright (c) 2021 Jean-Denis Gebhardt <projects@der-jd.de>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from os import getenv
from lxml import html
import requests

__metaclass__ = type

DOCUMENTATION = '''
    name: http
    plugin_type: inventory
    author:
      - Jean-Denis Gebhardt <projects@der-jd.de> (@derjd)
    short_description: HTTP(s) inventory source.
    requirements:
      - python >= 3
      - python-lxml
      - python-requests
    extends_documentation_fragment:
      - constructed
    description:
      - Reads inventories from Webservers (i.e. GitLab Pages, GitLab Artifacts, S3, etc.).
      - The webserver must return inventory as json with `_meta`. see:
      - https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html#tuning-the-external-inventory-script
      - Uses a YAML configuration file http_inventory.[yml|yaml].
    options:
        plugin:
            description: >-
              The name of this plugin,
              it should always be set to 'http' for
              this plugin to recognize it as it's own.
            type: str
            required: true
            choices:
              - http
              - derjd.general.http
        url:
            description: The URL with protocol (i.e. http or https).
            env:
              - name: HTTP_URL
            type: str
            required: yes
        auth_method:
            description: >-
              How to authenticate. Since protected GitLab Pages do not use
              Basic auth nor Tokens, use `gitlab` with your personal
              credentials.
            env:
              - name: HTTP_AUTH_METHOD
            type: str
            default: None
            choices:
              - basic
              - gitlab
            required: no
        username:
            description: Username to access website.
            env:
              - name: HTTP_USERNAME
            type: str
            required: no
        password:
            description: Password to access website.
            env:
              - name: HTTP_PASSWORD
            type: str
            required: no
'''  # noqa[E501]

EXAMPLES = '''
# http_inventory.yml
plugin: derjd.geleral.http
url: https://example.gitlab.io/example_page/inventory.json
'''


class InventoryModule(BaseInventoryPlugin, Constructable):
    ''' Host inventory parser for ansible using HTTP(s) as source. '''

    NAME = 'derjd.general.http'

    def __init__(self):
        super(InventoryModule, self).__init__()

        self.url = getenv('HTTP_URL')
        self.auth_method = getenv('HTTP_AUTH_METHOD')
        self.username = getenv('HTTP_USERNAME')
        self.password = getenv('HTTP_PASSWORD')
        self.data = None

    def get_generic_page(self):
        if self.username is None or self.password is None:
            r = requests.get(self.url)
        else:
            r = requests.get(self.url, auth=(self.username, self.password))

        if self.is_valid_content(r):
            return r.json()

    def get_gitlab_page(self):
        xmeta = '//meta[@property="og:url"]'
        xinput = '//input[@name="authenticity_token"]'

        with requests.Session() as session:
            oauth = session.get(self.url)
            tree = html.fromstring(oauth.text)
            login_url = tree.xpath(xmeta)[0].attrib['content']
            token = tree.xpath(xinput)[0].attrib['value']
            auth = {
                'authenticity_token': token,
                'user[login]': self.username,
                'user[password]': self.password
            }

            session.post(login_url, data=auth)
            r = session.get(self.url, data=auth)

        if self.is_valid_content(r):
            return r.json()

    def is_valid_content(self, data):
        self.display.vvv(
            f"Header Content-Type: {data.headers['Content-Type']}")
        self.display.vvv(f"Header Status-Code: {data.status_code}")

        if data.status_code >= 300:
            raise AnsibleError(f'''
                Server returned status code {data.status_code}.
                Maybe server is in Maintenance or unreachable...
            ''')

        if "json" in data.headers['Content-Type']:
            return True
        else:
            raise AnsibleParserError(f'''
                {self.url} did not return json.
                The page must return the same content as the
                `ansible-inventory --list` command.
            ''')

    def add_hostvars(self, data):
        hostvars = data['_meta']['hostvars']
        for host in hostvars:
            self.display.vvv(f'Add hostvars: {host} with vars{hostvars[host]}')
            self._populate_host_vars([host], hostvars[host])

    def add_groups(self, groups, mode):
        for group in groups:
            if group == "_meta":
                continue

            self.display.vvv(f'Add group: {group}')
            self.inventory.add_group(group)

            if mode == "hosts" and mode in groups[group].keys():
                for host in groups[group]['hosts']:
                    self.display.vvv(f'Add host: {host} to group {group}')
                    self.inventory.add_host(host, group)

            if mode == "children" and mode in groups[group].keys():
                for child in groups[group]['children']:
                    self.display.vvv(f'Add child: {child} to group {group}')
                    self.inventory.add_child(group, child)

    def verify_file(self, path):
        ''' Return the possibility of a file being consumed by this plugin.'''
        return (
            super(InventoryModule, self).verify_file(path) and
            path.endswith(("http_inventory.yaml", "http_inventory.yml")))

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._read_config_data(path)

        if self.url is None:
            self.url = self.get_option('url')
        if self.auth_method is None:
            self.auth_method = self.get_option('auth_method')
        if self.username is None:
            self.username = self.get_option('username')
        if self.password is None:
            self.password = self.get_option('password')

        if self.url is None:
            raise AnsibleError('''
                url is missing.
                Please set it either as parameter
                or environment variable (HTTP_URL)
            ''')

        # Undefined get_option() values seem to be converted
        # into a "None" string and not NoneType
        if self.auth_method in [None, "None", "basic"]:
            self.display.vvv(
                f"Auth Method is {self.auth_method}. Using generic page parser"
            )
            self.data = self.get_generic_page()

        if self.auth_method == "gitlab":
            self.display.vvv(
                f"Auth Method is {self.auth_method}. Using gitlab page parser"
            )
            self.data = self.get_gitlab_page()

        if self.data is None:
            raise AnsibleParserError(
                'Did not received any data. Can not parse inventory.')
        else:
            self.add_hostvars(self.data)
            self.add_groups(self.data, "hosts")
            self.add_groups(self.data, "children")
