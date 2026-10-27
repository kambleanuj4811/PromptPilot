def test_health_ok(client):
    body = client.get("/api/health").json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["database_ok"] is True
    assert body["data"]["ai"]["check"] is None


def test_health_ai_check_uses_provider(client, fake_provider):
    body = client.get("/api/health?check_ai=true").json()
    assert body["data"]["ai"]["check"] == {"ok": True, "reply": "OK"}
    assert len(fake_provider.calls) == 1


def test_unknown_route_uses_error_envelope(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json()["success"] is False