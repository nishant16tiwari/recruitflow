def test_login_success(client, recruiter):
    resp = client.post("/auth/login", json={"email": recruiter.email, "password": "testpass123"})
    assert resp.status_code == 200
    assert resp.json()["email"] == recruiter.email


def test_login_wrong_password(client, recruiter):
    resp = client.post("/auth/login", json={"email": recruiter.email, "password": "wrong"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_password_is_hashed(db_session, recruiter):
    assert recruiter.password_hash != "testpass123"
    assert recruiter.password_hash.startswith("$2b$")
