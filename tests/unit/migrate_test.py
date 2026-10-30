import os
import sys
import tempfile

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/plugins/modules'))

import migrate_answers


class TestParameterMapping:
    """Test the parameter mapping logic"""

    def test_simple_parameter_mapping(self):
        """Test basic parameter translation"""
        old_config = {
            'foreman': {
                'db_host': 'localhost',
                'db_port': 5432
            }
        }

        result = migrate_answers.apply_mappings(old_config)

        assert 'database_host' not in result['mapped']
        assert result['mapped']['database_port'] == 5432
        assert result['unmappable'] == []

    def test_parameter_transformation(self):
        """Test parameters that need value transformation"""
        old_config = {
            'foreman': {
                'db_manage': True
            }
        }

        result = migrate_answers.apply_mappings(old_config)

        assert result['mapped']['database_mode'] == 'internal'

        old_config['foreman']['db_manage'] = False
        result = migrate_answers.apply_mappings(old_config)
        assert result['mapped']['database_mode'] == 'external'

    def test_ignore_parameters(self):
        """Test parameters marked as IGNORE"""
        old_config = {
            'foreman': {
                'db_manage_rake': True,
                'db_host': 'localhost'
            }
        }

        result = migrate_answers.apply_mappings(old_config)

        assert 'db_manage_rake' not in result['mapped']
        assert 'db_manage_rake' not in str(result['unmappable'])
        assert 'database_host' not in result['mapped']

    def test_certificate_parameters_ignored(self):
        """Test that certificate path parameters are ignored (handled by migration role)"""
        old_config = {
            'foreman': {
                'server_ssl_cert': '/etc/pki/katello/certs/server.crt',
                'server_ssl_key': '/etc/pki/katello/private/server.key',
                'server_ssl_ca': '/etc/pki/katello/certs/ca.crt',
                'db_host': 'localhost'
            }
        }

        result = migrate_answers.apply_mappings(old_config)

        assert 'server_certificate' not in result['mapped']
        assert 'server_key' not in result['mapped']
        assert 'ca_certificate' not in result['mapped']
        assert not any('ssl' in p for p in result['unmappable'])
        assert 'database_host' not in result['mapped']

    def test_unmappable_parameters(self):
        """Test that unmappable parameters are reported"""
        old_config = {
            'foreman': {
                'unknown_param': 'value'
            },
            'katello': {
                'enable_ostree': True
            }
        }

        result = migrate_answers.apply_mappings(old_config)

        assert 'foreman::unknown_param' in result['unmappable']
        assert 'katello::enable_ostree' in result['unmappable']
        assert len(result['unmappable']) == 2

    def test_empty_config(self):
        """Test with empty configuration"""
        old_config = {}

        result = migrate_answers.apply_mappings(old_config)

        assert result['mapped'] == {}
        assert result['unmappable'] == []

    def test_mixed_config(self):
        """Test with mix of mappable and unmappable parameters"""
        old_config = {
            'foreman': {
                'db_host': 'database.example.com',
                'db_port': 5432,
                'unknown_param': 'test',
                'initial_admin_username': 'admin'
            }
        }

        result = migrate_answers.apply_mappings(old_config)

        assert result['mapped']['database_host'] == 'database.example.com'
        assert result['mapped']['database_port'] == 5432
        assert result['mapped']['foreman_initial_admin_username'] == 'admin'

        assert 'foreman::unknown_param' in result['unmappable']
        assert len(result['unmappable']) == 1

    def test_skip_none_values_in_unmappable(self):
        """Test that None values are not added to unmappable list"""
        old_config = {
            'foreman': {
                'db_host': 'localhost',
                'unknown_param': None,
                'another_unknown': 'value'
            }
        }

        result = migrate_answers.apply_mappings(old_config)

        assert 'database_host' not in result['mapped']
        assert 'foreman::unknown_param' not in result['unmappable']
        assert 'foreman::another_unknown' in result['unmappable']
        assert len(result['unmappable']) == 1

    def test_skip_none_values_in_mapped(self):
        """Test that None values are not added to mapped list"""
        old_config = {
            'katello': {
                'candlepin_db_password': None
            }
        }

        result = migrate_answers.apply_mappings(old_config)

        assert 'candlepin_database_password' not in result['mapped']
        assert 'katello::candlepin_db_password' not in result['unmappable']
        assert len(result['unmappable']) == 0

    def test_database_config(self):
        """Test that all relevant database parameters are correctly mapped"""
        old_config = {
            'foreman': {'db_manage': True, 'db_host': 'db.example.com', 'db_port': 5432, 'db_database': 'foreman', 'db_username': 'foreman', 'db_password': 'foreman123', 'db_sslmode': 'verify-full', 'db_root_cert': '/etc/pki/tls/certs/ca-bundle.crt', 'db_pool': None, 'db_extra_options': {}, 'db_manage_rake': True},
            'foreman_proxy_content': {'pulpcore_manage_postgresql': True, 'pulpcore_postgresql_host': 'db.example.com', 'pulpcore_postgresql_port': 5432, 'pulpcore_postgresql_user': 'pulp', 'pulpcore_postgresql_password': 'pulp123', 'pulpcore_postgresql_db_name': 'pulpcore', 'pulpcore_postgresql_ssl': False, 'pulpcore_postgresql_ssl_require': True, 'pulpcore_postgresql_ssl_cert': '/etc/pki/katello/certs/pulpcore-database.crt', 'pulpcore_postgresql_ssl_key': '/etc/pki/katello/private/pulpcore-database.key', 'pulpcore_postgresql_ssl_root_ca': '/etc/pki/tls/certs/ca-bundle.crt'},
            'katello': {'candlepin_db_host': 'db.example.com', 'candlepin_db_port': 5432, 'candlepin_db_name': 'candlepin', 'candlepin_db_user': 'candlepin', 'candlepin_db_password': 'candlepin123', 'candlepin_db_ssl': False, 'candlepin_db_ssl_verify': True, 'candlepin_db_ssl_ca': '/etc/pki/tls/certs/ca-bundle.crt', 'candlepin_manage_db': True}
        }
        result = migrate_answers.apply_mappings(old_config)

        assert 'database_host' in result['mapped']
        assert result['mapped']['database_host'] == 'db.example.com'
        assert 'database_ssl_mode' in result['mapped']
        assert result['mapped']['database_ssl_mode'] == 'verify-full'
        assert 'database_ssl_ca' in result['mapped']
        assert result['mapped']['database_ssl_ca'] == '/etc/pki/tls/certs/ca-bundle.crt'

        assert 'candlepin_database_user' in result['mapped']
        assert result['mapped']['candlepin_database_user'] == 'candlepin'
        assert 'candlepin_database_password' in result['mapped']
        assert result['mapped']['candlepin_database_password'] == 'candlepin123'
        assert 'candlepin_database_name' in result['mapped']
        assert result['mapped']['candlepin_database_name'] == 'candlepin'
        assert 'foreman_database_user' in result['mapped']
        assert result['mapped']['foreman_database_user'] == 'foreman'
        assert 'foreman_database_password' in result['mapped']
        assert result['mapped']['foreman_database_password'] == 'foreman123'
        assert 'foreman_database_name' in result['mapped']
        assert result['mapped']['foreman_database_name'] == 'foreman'
        assert 'pulp_database_user' in result['mapped']
        assert result['mapped']['pulp_database_user'] == 'pulp'
        assert 'pulp_database_password' in result['mapped']
        assert result['mapped']['pulp_database_password'] == 'pulp123'
        assert 'pulp_database_name' in result['mapped']
        assert result['mapped']['pulp_database_name'] == 'pulpcore'
        assert len(result['unmappable']) == 0


class TestFileOperations:
    """Test file loading and writing"""

    def test_load_valid_yaml(self):
        """Test loading a valid YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({'foreman': {'db_host': 'localhost'}}, f)
            temp_file = f.name

        try:
            result = migrate_answers.load_answer_file(temp_file)
            assert result == {'foreman': {'db_host': 'localhost'}}
        finally:
            os.unlink(temp_file)

    def test_load_empty_yaml(self):
        """Test loading an empty YAML file raises ValueError"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('---\n')
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="is empty"):
                migrate_answers.load_answer_file(temp_file)
        finally:
            os.unlink(temp_file)

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist"""
        with pytest.raises(FileNotFoundError):
            migrate_answers.load_answer_file('/nonexistent/file.yaml')

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: content: [')
            temp_file = f.name

        try:
            with pytest.raises(ValueError):
                migrate_answers.load_answer_file(temp_file)
        finally:
            os.unlink(temp_file)


class TestTransformations:
    """Test individual transformation functions"""

    def test_cast_database_mode_true(self):
        """Test database mode transformation with True"""
        assert migrate_answers.cast_database_mode(True) == 'internal'

    def test_cast_database_mode_false(self):
        """Test database mode transformation with False"""
        assert migrate_answers.cast_database_mode(False) == 'external'

    def test_cast_database_mode_passthrough(self):
        """Test database mode transformation with non-boolean"""
        assert migrate_answers.cast_database_mode('already_a_string') == 'already_a_string'
