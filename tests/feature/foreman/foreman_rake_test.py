def test_foreman_rake_wrapper_exists(server):
    wrapper = server.file('/usr/sbin/foreman-rake')
    assert wrapper.exists
    assert wrapper.mode == 0o755


def test_foreman_rake_list_tasks(server):
    result = server.run('ALLOW_UNSUPPORTED=true foreman-rake -T')
    assert result.succeeded
    assert 'WARNING: Unsupported action detected' in result.stderr
    assert 'rake cron:daily' in result.stdout


def test_foreman_rake_rejects_unsupported_action(server):
    result = server.run_expect([1], 'foreman-rake unsupported:task')
    assert 'ERROR: Unsupported action detected' in result.stderr


def test_foreman_rake_supported_action(server):
    result = server.run('foreman-rake facts:clean')
    assert result.succeeded
