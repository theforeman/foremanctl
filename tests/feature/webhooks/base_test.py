import time
import uuid

import pytest

LISTENER_PORT = 9999
LISTENER_HOST = "host.containers.internal"


@pytest.fixture
def webhook_listener(server):
    """Start a netcat listener that captures one request."""
    output_file = f"/tmp/webhook-test-{uuid.uuid4()}"
    # Just listen and dump to file - no HTTP response needed
    server.run(f"nohup nc -l {LISTENER_PORT} > {output_file} 2>&1 &")
    time.sleep(1)

    yield output_file

    server.run(f"fuser -k {LISTENER_PORT}/tcp 2>/dev/null || true")
    server.run(f"rm -f {output_file}")


@pytest.fixture
def webhook_template(foremanapi):
    """Create a webhook template that includes event object details."""
    template = foremanapi.create(
        "webhook_templates",
        {
            "name": f"Test Payload {uuid.uuid4()}",
            "template": '{"id": <%= @object.id %>, "name": "<%= @object.name %>"}',
        },
    )
    yield template
    foremanapi.delete("webhook_templates", template)


@pytest.fixture
def webhook(foremanapi, server_fqdn, webhook_listener, webhook_template):
    hook = foremanapi.create(
        "webhooks",
        {
            "name": str(uuid.uuid4()),
            "target_url": f"http://{LISTENER_HOST}:{LISTENER_PORT}",
            "http_method": "POST",
            "event": "domain_created.event.foreman",
            "http_content_type": "application/json",
            "webhook_template_id": webhook_template["id"],
            "enabled": True,
            "ssl_verification": False,
        },
    )
    yield hook
    foremanapi.delete("webhooks", hook)


def test_foreman_webhooks(foreman_plugins):
    assert "foreman_webhooks" in foreman_plugins


def test_webhook_fires_on_domain_create(foremanapi, webhook, webhook_listener, server):
    domain_name = f"{uuid.uuid4()}.example.com"
    domain = foremanapi.create("domains", {"name": domain_name})

    try:
        # Wait for the webhook to be delivered (async via dynflow)
        for _ in range(30):
            result = server.run(f"cat {webhook_listener}")
            if domain_name in result.stdout:
                break
            time.sleep(1)
        else:
            pytest.fail(f"Webhook was not received within 30 seconds. Listener output: {result.stdout!r}")

        assert "POST" in result.stdout
        assert domain_name in result.stdout
    finally:
        foremanapi.delete("domains", domain)
