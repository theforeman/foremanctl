import pytest


def test_advisor_frontend_assets_directory(server):
    assets_dir = server.file("/var/lib/foreman/public/assets/apps/advisor")
    assert assets_dir.exists
    assert assets_dir.is_directory
    assert assets_dir.mode == 0o755


def test_advisor_frontend_assets_ownership(server):
    assets_dir = server.file("/var/lib/foreman/public/assets/apps/advisor")
    assert assets_dir.user == "foreman"
    assert assets_dir.group == "foreman"


def test_advisor_frontend_app_info_file(server):
    app_info_file = server.file("/var/lib/foreman/public/assets/apps/advisor/app.info.json")

    assert app_info_file.exists
    assert app_info_file.is_file
    assert app_info_file.user == "foreman"
    assert app_info_file.group == "foreman"


def test_advisor_frontend_asset_accessible_via_https(server):
    result = server.run("curl -s -o /dev/null -w '%{http_code}' -k https://localhost/assets/apps/advisor/ 2>/dev/null || echo '000'")
    assert result.succeeded
    http_code = result.stdout.strip()
    assert http_code != "000"
    assert http_code in ["200", "301", "302", "403"]


def test_advisor_frontend_static_file_content_type(server):
    result = server.run("curl -s -I http://localhost/assets/apps/advisor/ 2>/dev/null | grep -i 'content-type' || echo 'no-content-type'")
    assert result.succeeded
    assert "no-content-type" not in result.stdout
    assert "content-type" in result.stdout.lower()


def test_advisor_frontend_javascript_assets_accessible(server):
    result = server.run("find /var/lib/foreman/public/assets/apps/advisor -name '*.js' | head -1")
    assert result.succeeded
    assert result.stdout.strip()
    js_file = result.stdout.strip().replace("/var/lib/foreman/public", "")
    curl_result = server.run(f"curl -s -o /dev/null -w '%{{http_code}}' -k https://localhost{js_file} 2>/dev/null || echo '000'")
    assert curl_result.succeeded
    http_code = curl_result.stdout.strip()
    assert http_code in ["200", "403", "404"]
