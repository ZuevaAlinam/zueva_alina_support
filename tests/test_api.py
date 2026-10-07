"""Тесты операций контракта."""
def _login(client, username="user0", password="demo"):
    return client.post("/api/auth/login", json={"username": username, "password": password})

def test_unauthorized_returns_401(client):
    r = client.get("/api/tickets")
    assert r.status_code == 401

def test_login_and_list(client, db_session):
    from app import models, auth
    u = models.User(username="user0", password_hash=auth.hash_password("demo"), role="user")
    db_session.add(u); db_session.commit()
    r = _login(client)
    assert r.status_code == 200
    r = client.get("/api/tickets")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body

def test_create_ticket_requires_auth(client):
    r = client.post("/api/tickets", json={"title": "T", "body": "B", "category_id": 1})
    assert r.status_code == 401