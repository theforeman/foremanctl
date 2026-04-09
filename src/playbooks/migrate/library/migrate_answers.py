#!/usr/bin/python3

import os
import sys
import yaml
from ansible.module_utils.basic import AnsibleModule


def cast_database_mode(value):
    """Convert db_manage boolean to database_mode string."""
    if isinstance(value, bool):
        return 'internal' if value else 'external'
    return value


def cast_certificate_source(value):
    """Map certificate management boolean to certificate source."""
    if isinstance(value, bool):
        return 'default' if value else 'installer'
    return value


PARAMETER_MAP = {
    # Database configuration
    ('foreman', 'db_host'): 'database_host',
    ('foreman', 'db_port'): 'database_port',
    ('foreman', 'db_database'): 'foreman_database_name',
    ('foreman', 'db_username'): 'foreman_database_user',
    ('foreman', 'db_password'): 'foreman_database_password',
    ('foreman', 'db_manage'): ('database_mode', cast_database_mode),
    ('foreman', 'db_manage_rake'): 'IGNORE',  # Not needed in new format

    # Foreman configuration
    ('foreman', 'initial_admin_username'): 'foreman_initial_admin_username',
    ('foreman', 'initial_admin_password'): 'foreman_initial_admin_password',

    # Certificate configuration
    ('foreman', 'server_ssl_cert'): 'server_certificate',
    ('foreman', 'server_ssl_key'): 'server_key',
    ('foreman', 'server_ssl_ca'): 'ca_certificate',

    # TODO: Add more mappings as discovered
}

IGNORE_PARAMS = {'IGNORE'}


def load_answer_file(file_path):
    """Load and parse YAML answer file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Answer file not found: {file_path}")

    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Cannot read answer file: {file_path}")

    with open(file_path, 'r') as f:
        try:
            data = yaml.safe_load(f)
            if data is None:
                return {}
            return data
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in answer file: {e}")


def flatten_nested_dict(nested_dict, parent_key=''):
    """
    Flatten nested dictionary structure from foreman-installer format.

    Example:
        {'foreman': {'db_host': 'localhost'}}
    becomes:
        {('foreman', 'db_host'): 'localhost'}
    """
    items = []
    for key, value in nested_dict.items():
        if isinstance(value, dict):
            items.extend(flatten_nested_dict(value, key).items())
        else:
            if parent_key:
                items.append(((parent_key, key), value))
            else:
                items.append((key, value))
    return dict(items)


def apply_mappings(old_config):
    """
    Transform old config to new format using mapping table.

    Returns:
        dict: {
            'mapped': {new_param: value},
            'unmappable': [old_param_name, ...]
        }
    """
    flat_config = flatten_nested_dict(old_config)

    result = {}
    unmappable = []

    for old_key, old_value in flat_config.items():
        if old_key in PARAMETER_MAP:
            mapping = PARAMETER_MAP[old_key]

            if mapping == 'IGNORE':
                continue

            if isinstance(mapping, tuple):
                new_key, transform_func = mapping
                new_value = transform_func(old_value)
            else:
                new_key = mapping
                new_value = old_value

            if new_value is not None:
                result[new_key] = new_value
        else:
            if isinstance(old_key, tuple):
                param_name = '::'.join(old_key)
            else:
                param_name = str(old_key)
            unmappable.append(param_name)

    return {
        'mapped': result,
        'unmappable': unmappable
    }


def write_output(data, output_path=None):
    """Write migrated configuration to file or stdout."""
    yaml_content = yaml.dump(data, default_flow_style=False, sort_keys=True)

    if output_path:
        with open(output_path, 'w') as f:
            f.write(yaml_content)
    else:
        print(yaml_content)


def run_module():
    module_args = dict(
        answer_file=dict(type='str', required=True),
        output=dict(type='str', required=False, default=None),
    )

    result = dict(
        changed=False,
        mapped_count=0,
        unmappable_count=0,
        unmappable=[],
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        old_config = load_answer_file(module.params['answer_file'])

        migration_result = apply_mappings(old_config)

        result['mapped_count'] = len(migration_result['mapped'])
        result['unmappable_count'] = len(migration_result['unmappable'])
        result['unmappable'] = migration_result['unmappable']

        if not module.check_mode:
            output_path = module.params.get('output')
            write_output(migration_result['mapped'], output_path)

            if output_path:
                result['output_file'] = output_path
                result['changed'] = True  # File was written

        module.exit_json(**result)

    except FileNotFoundError as e:
        module.fail_json(msg=str(e), **result)
    except PermissionError as e:
        module.fail_json(msg=str(e), **result)
    except ValueError as e:
        module.fail_json(msg=str(e), **result)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {e}", **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
