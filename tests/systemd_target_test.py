def test_foreman_tail_installed(server):
    helper = server.file('/usr/local/bin/foreman-tail')

    assert helper.exists
    assert helper.is_file
    assert helper.mode == 0o755
