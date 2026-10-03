from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
TEST_METADATA = ROOT / 'development/playbooks/test/metadata.obsah.yaml'
TEST_PLAYBOOK = ROOT / 'development/playbooks/test/test.yaml'


def test_fast_test_option_excludes_slow_tests():
    metadata = yaml.safe_load(TEST_METADATA.read_text())

    assert metadata['variables']['fast'] == {
        'help': 'Skip tests marked as slow.',
        'parameter': '--fast',
        'action': 'store_true',
    }
    assert "'-m \"not slow\"' if fast | default(false) else ''" in TEST_PLAYBOOK.read_text()
