import io

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str, org_name: str = "Doc Test Org") -> dict:
    res = client.post(
        "/api/v1/auth/register",
        json={"organization_name": org_name, "email": email, "password": "correcthorse123", "full_name": "Owner"},
    )
    assert res.status_code == 201, res.text
    return res.json()


def _invite_and_accept(client: TestClient, email: str, role_name: str) -> dict:
    """Invites `email` as `role_name` into the org the client is currently authenticated
    into, accepts on their behalf, and returns their cookies (leaving `client` itself
    still authenticated as whoever called this, since we use a fresh TestClient)."""
    csrf = client.cookies.get("csrf_token")
    invite_res = client.post(
        "/api/v1/auth/invitations",
        json={"email": email, "role_name": role_name},
        headers={"X-CSRF-Token": csrf},
    )
    assert invite_res.status_code == 201, invite_res.text
    token = invite_res.json()["invite_url"].rsplit("/", 1)[-1]

    invitee_client = TestClient(client.app)
    accept_res = invitee_client.post(
        f"/api/v1/auth/invitations/{token}/accept",
        json={"password": "correcthorse123", "full_name": email.split("@")[0]},
    )
    assert accept_res.status_code == 201, accept_res.text
    return invitee_client, accept_res.json()


def _upload_document(client: TestClient, title: str = "Test Doc") -> dict:
    csrf = client.cookies.get("csrf_token")
    res = client.post(
        "/api/v1/documents",
        headers={"X-CSRF-Token": csrf},
        data={"title": title, "description": "A test document"},
        files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_creator_has_manage_permission(client: TestClient):
    _register(client, "owner@doctest-crm.com")
    doc = _upload_document(client)
    assert doc["my_permission"] == "manage"


def test_unshared_user_cannot_access_document(client: TestClient):
    _register(client, "owner@doctest-crm.com")
    doc = _upload_document(client)

    # The `client` fixture's get_db override is set on the shared `app` object, so the
    # second TestClient instance created here (wrapping the same app) sees the same
    # transaction-scoped session automatically.
    viewer_client, _ = _invite_and_accept(client, "viewer@doctest-crm.com", "viewer")

    res = viewer_client.get(f"/api/v1/documents/{doc['id']}")
    assert res.status_code == 403


def test_sharing_grants_access_at_the_correct_level(client: TestClient):
    _register(client, "owner@doctest-crm.com")
    doc = _upload_document(client)
    viewer_client, viewer_body = _invite_and_accept(client, "viewer@doctest-crm.com", "viewer")

    # Not shared yet -> 403.
    assert viewer_client.get(f"/api/v1/documents/{doc['id']}").status_code == 403

    # Share at "view" only.
    csrf = client.cookies.get("csrf_token")
    share_res = client.post(
        f"/api/v1/documents/{doc['id']}/shares",
        headers={"X-CSRF-Token": csrf},
        json={"grantee_type": "user", "grantee_id": viewer_body["id"], "permission": "view"},
    )
    assert share_res.status_code == 201, share_res.text

    get_res = viewer_client.get(f"/api/v1/documents/{doc['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["my_permission"] == "view"

    # view-level share is not enough to edit - blocked by the coarse role gate
    # (viewer role lacks document.edit) even before the resource-level check runs.
    viewer_csrf = viewer_client.cookies.get("csrf_token")
    edit_res = viewer_client.put(
        f"/api/v1/documents/{doc['id']}",
        headers={"X-CSRF-Token": viewer_csrf},
        json={"title": "Hacked title"},
    )
    assert edit_res.status_code == 403


def test_document_download_returns_uploaded_content(client: TestClient):
    _register(client, "owner@doctest-crm.com")
    doc = _upload_document(client)
    res = client.get(f"/api/v1/documents/{doc['id']}/download")
    assert res.status_code == 200
    assert res.content == b"hello world"


def test_soft_deleted_document_disappears_from_list(client: TestClient):
    _register(client, "owner@doctest-crm.com")
    doc = _upload_document(client)
    csrf = client.cookies.get("csrf_token")

    assert any(d["id"] == doc["id"] for d in client.get("/api/v1/documents").json())

    del_res = client.delete(f"/api/v1/documents/{doc['id']}", headers={"X-CSRF-Token": csrf})
    assert del_res.status_code == 204

    assert not any(d["id"] == doc["id"] for d in client.get("/api/v1/documents").json())
    assert client.get(f"/api/v1/documents/{doc['id']}").status_code == 404
