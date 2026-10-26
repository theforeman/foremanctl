import os
import re
from pathlib import Path


def test_post_install_message_format(pytestconfig, obsah_params):
    """Check initial and subsequent post-install messages in the deployment log."""
    state_dir = Path(os.environ.get('OBSAH_STATE', '.var/lib/foremanctl'))
    log_paths = sorted(state_dir.glob('foremanctl.*.log'))
    log_paths.append(state_dir / 'foremanctl.log')
    log = '\n'.join(
        path.read_text(encoding='utf-8')
        for path in log_paths if path.is_file()
    )
    blocks = re.findall(
        r'^[ \t]+msg: \|[-+]?\n'
        r'([ \t]+You can log in at [^\n]+\n(?:[ \t]+[^\n]+\n)*)',
        log,
        re.MULTILINE,
    )
    messages = [[line.lstrip() for line in block.splitlines()] for block in blocks]
    assert messages, 'Expected a multiline post-install message in foremanctl.log'

    featureset = pytestconfig.getoption('featureset')
    if featureset != 'upgrade':
        # Upgrade jobs log the initial credentials using the old version.
        username = obsah_params.get('foreman_initial_admin_username', 'admin')
        password = obsah_params.get('foreman_initial_admin_password')
        if password is None:
            password = (state_dir / 'foreman-admin-init-passwd').read_text(
                encoding='utf-8',
            ).rstrip('\n')
        expected_credentials = f'Admin credentials: {username}:{password}'
        credentials_found = any(
            message[1:] == [expected_credentials] for message in messages
        )
        assert credentials_found, 'Expected initial credentials in the multiline message'

    if featureset != 'migration':
        # Migration CI deploys once; other jobs also exercise a subsequent run.
        url_only = len(messages[-1]) == 1
        assert url_only, 'Expected only the login URL after the subsequent deployment'
