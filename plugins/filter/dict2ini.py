# Copyright (c) 2021 Jean-Denis Gebhardt <projects@der-jd.de>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

def dict2ini(data, quote=True):
    '''
    Convert a nested dict into a list, easily parsable by loops

    Arguments:
        quote   optional    (bool: True) Some ini/Toml files needs to have
                            their string values to be in quotes.

    Example:
        ini_vars:
            ima_1_section:
                ima_1_option: ima_1_value
                ima_2_option: ima_2_value
            ima_2_section:
                ima_3_option: ima_3_value
                ima_4_option: ima_4_value

        "{{ ini_vars | derJD.general.dict2ini }}"
        Would be converted into this structure:

        - section: ima_1_section
          option: ima_1_option
          value: ima_1_value
        - section: ima_1_section
          option: ima_2_option
          value: ima_2_value
        - section: ima_2_section
          option: ima_3_option
          value: ima_3_value
        - section: ima_2_section
          option: ima_4_option
          value: ima_4_value

        Passing to a loop:

        tasks:
            - name: edit /tmp/test.ini file
              ini_file:
                path: /tmp/test.ini
                section: "{{ item.section }}"
                option: "{{ item.option }}"
                value: "{{ item.value }}"
              loop: "{{ ini_vars | derJD.general.dict2ini }}"
    '''

    ret = []
    for section, elements in data.items():
        for option, value in elements.items():
            if isinstance(value, str) and quote:
                value = f'"{value}"'
            ret.append(dict(section=section, option=option, value=value))
    return ret


class FilterModule(object):
    ''' dict2ini filter '''

    def filters(self):
        return {
            'dict2ini': dict2ini
        }
