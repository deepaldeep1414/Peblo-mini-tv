from tests.conftest import EDITOR_HEADERS, ADMIN_HEADERS


def test_no_api_key_rejected(client):
    r = client.get("/admin/shows")
    assert r.status_code == 401


def test_editor_can_create_show(client):
    r = client.post("/admin/shows", json={"title": "Test Show"}, headers=EDITOR_HEADERS)
    assert r.status_code == 201


def test_editor_cannot_publish(client):
    r = client.post("/admin/catalog/publish", headers=EDITOR_HEADERS)
    assert r.status_code == 403


def test_admin_can_publish_even_with_nothing(client):
    r = client.post("/admin/catalog/publish", headers=ADMIN_HEADERS)
    # nothing published yet -> succeeds trivially with an empty catalogue
    assert r.status_code == 201


def test_editor_can_read_validation_report_is_forbidden(client):
    # validation-report is admin-only in this implementation
    r = client.get("/admin/validation-report", headers=EDITOR_HEADERS)
    assert r.status_code == 403
