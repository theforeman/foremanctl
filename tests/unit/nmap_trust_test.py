import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


def test_nmap_trust_is_prepared_only_when_needed(tmp_path):
    root = Path(__file__).resolve().parents[2]
    setup = yaml.safe_load((root / 'development/playbooks/test/test.yaml').read_text())[0]
    trust_file = tmp_path / 'trust'
    log_file = tmp_path / 'calls.jsonl'
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    cli = fake_bin / 'fapolicyd-cli'
    cli.write_text(f'#!{sys.executable}\n' + '''
import json
import os
from pathlib import Path
import sys

root = Path(os.environ['FAKE_TRUST_ROOT'])
args = sys.argv[1:]
with (root / 'calls.jsonl').open('a') as log:
    log.write(json.dumps([os.environ['FAKE_TRUST_CASE'], args]) + '\\n')
if args[:1] == ['--file']:
    expected = 'update' if (root / 'trust').exists() else 'add'
    assert args == ['--file', expected, '/usr/share/nmap/', '--trust-file', 'foremanctl-nmap']
    (root / 'trust').write_text('prepared')
elif args == ['--update']:
    assert (root / 'trust').exists()
    (root / 'database').write_text('loaded')
elif args == ['--dump-db']:
    if (root / 'database').exists():
        print('file /usr/share/nmap/nselib/outlib.lua 1 checksum')
else:
    raise AssertionError(args)
''')
    cli.chmod(0o755)

    plays = []
    cases = [('created', False, 'fapolicyd'), ('unchanged', False, 'fapolicyd'),
             ('updated', True, 'fapolicyd'), ('disabled', True, 'none')]
    for name, changed, security in cases:
        play = copy.deepcopy(setup)
        play.update({
            'name': name, 'hosts': 'localhost', 'connection': 'local',
            'become': False, 'gather_facts': False,
            'vars': {'security_mode': security, 'ansible_python_interpreter': sys.executable,
                     'ansible_remote_tmp': str(tmp_path / 'remote')},
            'environment': {'PATH': str(fake_bin) + os.pathsep + os.environ['PATH'],
                            'FAKE_TRUST_ROOT': str(tmp_path), 'FAKE_TRUST_CASE': name},
        })
        # Package installation is external to this test. Exercise the actual
        # following tasks and handlers with its two possible changed results.
        play['tasks'][0] = {'ansible.builtin.set_fact': {'testing_dependencies': {'changed': changed}}}
        play['tasks'][1]['block'][0]['ansible.builtin.stat']['path'] = str(trust_file)
        plays.append(play)

    playbook = tmp_path / 'play.json'
    playbook.write_text(json.dumps(plays))
    env = os.environ.copy()
    env.update({'ANSIBLE_HOME': str(tmp_path / 'ansible'),
                'ANSIBLE_LOCAL_TEMP': str(tmp_path / 'ansible/tmp'), 'TMPDIR': str(tmp_path)})
    result = subprocess.run(
        [shutil.which('ansible-playbook') or 'ansible-playbook', '-i', 'localhost,', str(playbook)],
        env=env, capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    calls = {}
    for line in log_file.read_text().splitlines():
        name, args = json.loads(line)
        calls.setdefault(name, []).append(args)
    assert [args[:2] for args in calls['created']] == [['--file', 'add'], ['--update'], ['--dump-db']]
    assert calls['unchanged'] == [['--dump-db']]
    assert [args[:2] for args in calls['updated']] == [['--file', 'update'], ['--update'], ['--dump-db']]
    assert 'disabled' not in calls
