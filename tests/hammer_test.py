def test_hammer_ping(server):
    hammer = server.run("hammer ping")
    assert hammer.succeeded
