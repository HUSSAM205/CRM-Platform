from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "owner@pytest-crm.com") -> dict:
    res = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Pytest Org",
            "email": email,
            "password": "correcthorse123",
            "full_name": "Test Owner",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_register_creates_org_and_admin_user(client: TestClient):
    body = _register(client)
    assert body["email"] == "owner@pytest-crm.com"
    assert "admin" in body["roles"]
    assert "admin.access" in body["permissions"]
    assert "document.view" in body["permissions"]
    # Session cookies should be set so the caller is immediately logged in.
    assert "access_token" in client.cookies
    assert "csrf_token" in client.cookies


def test_register_duplicate_email_rejected(client: TestClient):
    _register(client)
    res = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Another Org",
            "email": "owner@pytest-crm.com",
            "password": "correcthorse123",
            "full_name": "Someone Else",
        },
    )
    assert res.status_code == 409


def test_login_wrong_password_rejected(client: TestClient):
    _register(client)
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@pytest-crm.com", "password": "wrong-password"},
    )
    assert res.status_code == 401


def test_login_success_returns_user_and_sets_cookies(client: TestClient):
    _register(client)
    client.cookies.clear()
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@pytest-crm.com", "password": "correcthorse123"},
    )
    assert res.status_code == 200
    assert res.json()["email"] == "owner@pytest-crm.com"
    assert "access_token" in client.cookies


def test_unauthenticated_request_rejected(client: TestClient):
    res = client.get("/api/v1/users/me")
    assert res.status_code == 401


def test_invite_requires_user_invite_permission(client: TestClient):
    _register(client)
    csrf = client.cookies.get("csrf_token")

    # Admin (has user.invite) can invite.
    res = client.post(
        "/api/v1/auth/invitations",
        json={"email": "teammate@pytest-crm.com", "role_name": "viewer"},
        headers={"X-CSRF-Token": csrf},
    )
    assert res.status_code == 201, res.text
    token = res.json()["invite_url"].rsplit("/", 1)[-1]

    # Accepting swaps the client's session cookies from the admin's to the new viewer's.
    accept_res = client.post(
        f"/api/v1/auth/invitations/{token}/accept",
        json={"password": "viewerpass123", "full_name": "Test Viewer"},
    )
    assert accept_res.status_code == 201, accept_res.text
    viewer_body = accept_res.json()
    assert viewer_body["roles"] == ["viewer"]
    assert "user.invite" not in viewer_body["permissions"]

    # Now acting as the viewer: they cannot invite others.
    viewer_csrf = client.cookies.get("csrf_token")
    no_permission_res = client.post(
        "/api/v1/auth/invitations",
        json={"email": "another@pytest-crm.com", "role_name": "viewer"},
        headers={"X-CSRF-Token": viewer_csrf},
    )
    assert no_permission_res.status_code == 403


def test_csrf_required_for_mutating_request(client: TestClient):
    _register(client)
    # No X-CSRF-Token header attached.
    res = client.post(
        "/api/v1/auth/invitations",
        json={"email": "teammate@pytest-crm.com", "role_name": "viewer"},
    )
    assert res.status_code == 403
    assert "CSRF" in res.json()["detail"]
