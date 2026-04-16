import pytest

pytestmark = pytest.mark.iop


def test_inventory_frontend_assets_directory(server):
    assets_dir = server.file("/var/www/iop/assets/apps/inventory")
    assert assets_dir.exists
    assert assets_dir.is_directory
    assert assets_dir.mode == 0o755


def test_inventory_frontend_app_info_file(server):
    app_info_file = server.file("/var/www/iop/assets/apps/inventory/app.info.json")

    assert app_info_file.exists
    assert app_info_file.is_file


def test_inventory_frontend_javascript_assets_accessible(server):
    result = server.run("find /var/www/iop/assets/apps/inventory -name '*.js' | head -1")
    assert result.succeeded
    assert result.stdout.strip()
    js_file = result.stdout.strip().replace("/var/www/iop", "")
    curl_result = server.run(f"curl -s -o /dev/null -w '%{{http_code}}' -k https://localhost{js_file}")
    assert curl_result.succeeded
    http_code = curl_result.stdout.strip()
    assert http_code in ["200"]
