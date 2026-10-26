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
        r'^[ \t]+msg:([^\n]*)\n((?:[ \t]+[^\n]*\n)*)',
        log,
        re.MULTILINE,
    )
    messages = [
        (style.strip(), [line.lstrip() for line in block.splitlines() if line.strip()])
        for style, block in blocks if 'You can log in at ' in style + block
    ]
    assert messages, 'Expected a post-install message in the deployment logs'

    multiline_styles = ('|', '|-', '|+')
    latest_style, latest_message = messages[-1]
    latest_is_multiline = latest_style in multiline_styles
    assert latest_is_multiline, 'Expected the latest post-install message to use multiline format'

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
            style in multiline_styles and message[1:] == [expected_credentials]
            for style, message in messages
        )
        assert credentials_found, 'Expected initial credentials in the multiline message'

    if featureset != 'migration':
        # Migration CI deploys once; other jobs also exercise a subsequent run.
        url_only = len(latest_message) == 1 and latest_message[0].startswith('You can log in at ')
        assert url_only, 'Expected only the login URL after the subsequent deployment'
