def test_collect_report(host):
    host.run('mkdir -p logs')
    for container, filename in [('foreman', '/var/log/foreman/production.log')]:
        localfile = filename.replace('/', '_')
        host.run(f'podman cp {container}:{filename} logs/{container}-{localfile}')
    host.run('tar caf logs.tar.gz logs/')
    with open('logs.tar.gz', 'wb') as logstar:
        logstar.write(host.file('logs.tar.gz').content)
