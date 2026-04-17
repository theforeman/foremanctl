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


def resolve_answer_file_from_scenario(scenario_file='/etc/foreman-installer/scenarios.d/last_scenario.yaml'):
    """Read scenario file and extract answer file path from :answer_file: key."""
    with open(scenario_file, 'r') as f:
        try:
            scenario_data = yaml.safe_load(f)
            if scenario_data is None:
                raise ValueError(f"Scenario file {scenario_file} is empty")

            answer_file = scenario_data.get(':answer_file')
            if not answer_file:
                raise ValueError(f"Scenario file does not contain :answer_file: key")

            return answer_file
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in scenario file: {e}")


def load_answer_file(file_path):
    """Load and parse YAML answer file."""
    with open(file_path, 'r') as f:
        try:
            data = yaml.safe_load(f)
            if data is None:
                raise ValueError(f"Answer file {file_path} is empty")
            return data
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in answer file: {e}")


def validate_answer_file(data, file_path):
    """
    Validate that the loaded YAML has the expected structure of a foreman-installer answer file.

    Expected structure: Top-level keys should be module names (strings) with nested dictionaries.
    Example: {'foreman': {'db_host': 'localhost'}, 'katello': {...}}
    """
    if not isinstance(data, dict):
        raise ValueError(
            f"Answer file {file_path} has invalid structure. "
            f"Expected a dictionary but got {type(data).__name__}"
        )

    if len(data) == 0:
        raise ValueError(f"Answer file {file_path} is empty (contains no configuration)")

    dict_values = sum(1 for v in data.values() if isinstance(v, dict))

    if dict_values == 0:
        raise ValueError(
            f"Answer file {file_path} does not appear to be a valid foreman-installer answer file. "
            f"Expected nested module configurations (e.g., 'foreman:', 'katello:') but found flat structure"
        )


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


def write_output(data, output_path=None, working_directory=None):
    """Write migrated configuration to file or return as string."""
    yaml_content = yaml.dump(data, default_flow_style=False, sort_keys=True)

    if output_path:
        if working_directory and not os.path.isabs(output_path):
            absolute_path = os.path.join(working_directory, output_path)
        else:
            absolute_path = os.path.abspath(output_path)
        with open(absolute_path, 'w') as f:
            f.write(yaml_content)
        return absolute_path
    else:
        return yaml_content


def run_module():
    module_args = dict(
        answer_file=dict(type='str', required=False, default=None),
        output=dict(type='str', required=False, default=None),
        working_directory=dict(type='str', required=False, default=None),
    )

    result = dict(
        changed=False,
        mapped_count=0,
        unmappable_count=0,
        unmappable=[],
        output_content='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        answer_file = module.params.get('answer_file')
        if not answer_file:
            answer_file = resolve_answer_file_from_scenario()

        old_config = load_answer_file(answer_file)
        validate_answer_file(old_config, answer_file)

        migration_result = apply_mappings(old_config)

        result['mapped_count'] = len(migration_result['mapped'])
        result['unmappable_count'] = len(migration_result['unmappable'])
        result['unmappable'] = migration_result['unmappable']

        # Issue warnings for unmappable parameters
        if migration_result['unmappable']:
            for param in migration_result['unmappable']:
                module.warn(f"Parameter '{param}' could not be mapped and will need manual review")

        if not module.check_mode:
            output_path = module.params.get('output')
            working_directory = module.params.get('working_directory')

            if output_path:
                absolute_path = write_output(migration_result['mapped'], output_path, working_directory)
                result['output_file'] = absolute_path
                result['changed'] = True
            else:
                # Output to stdout - store in result so Ansible displays it
                yaml_content = write_output(migration_result['mapped'], output_path, working_directory)
                result['output_content'] = yaml_content

        module.exit_json(**result)

    except (FileNotFoundError, PermissionError, ValueError) as e:
        module.fail_json(msg=str(e), **result)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {e}", **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
