import pytest
import sys
import os
import tempfile
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

        assert result['mapped']['database_host'] == 'localhost'
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
        assert result['mapped']['database_host'] == 'localhost'

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

    def test_write_output_to_file(self):
        """Test writing output to a file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name

        try:
            test_data = {'database_host': 'localhost', 'database_port': 5432}
            migrate_answers.write_output(test_data, temp_file)

            with open(temp_file, 'r') as f:
                result = yaml.safe_load(f)
            assert result == test_data
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
