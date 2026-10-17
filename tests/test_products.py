from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.auth import require_user
from app.database.session import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def override_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_user] = lambda: None
    # No context manager: startup must not connect to the production MySQL DB.
    with_client = TestClient(app)
    yield with_client
    with_client.close()
    app.dependency_overrides.clear()
    engine.dispose()


def test_crud(client):
    payload = {"name": "Bàn phím", "description": "Cơ", "price": "350000.00", "quantity": 10}
    assert client.get("/products").json() == []
    created = client.post("/products", json=payload)
    assert created.status_code == 201
    product = created.json()
    assert Decimal(product["price"]) == Decimal("350000.00")
    assert product["created_at"] and product["updated_at"]
    url = f"/products/{product['id']}"
    assert client.get(url).json() == product
    assert len(client.get("/products").json()) == 1
    payload.update(price="123.45", quantity=2)
    updated = client.put(url, json=payload)
    assert updated.status_code == 200
    assert Decimal(updated.json()["price"]) == Decimal("123.45")
    assert updated.json()["quantity"] == 2
    deleted = client.delete(url)
    assert deleted.status_code == 204 and deleted.content == b""
    for method in ("get", "put", "delete"):
        kwargs = {"json": payload} if method == "put" else {}
        assert getattr(client, method)(url, **kwargs).status_code == 404


@pytest.mark.parametrize("field,value", [("price", "-1"), ("price", "1.001"),
    ("price", "100000000.00"), ("quantity", -1), ("quantity", 1.5),
    ("name", "  "), ("name", "x" * 256)])
def test_validation(client, field, value):
    payload = {"name": "Test", "price": "1.00", "quantity": 1}
    payload[field] = value
    assert client.post("/products", json=payload).status_code == 422
    assert client.get("/products").json() == []


def test_partial_update(client):
    created = client.post("/products", json={"name": "Test", "description": "Giữ", "price": "12.34", "quantity": 5}).json()
    url = f"/products/{created['id']}"
    response = client.put(url, json={"quantity": 7})
    assert response.status_code == 200
    updated = response.json()
    assert updated["quantity"] == 7
    for field in ("name", "description", "price", "created_at"):
        assert updated[field] == created[field]
    assert client.put(url, json={"description": None}).json()["description"] is None
    assert client.put(url, json={}).status_code == 200


@pytest.mark.parametrize("field,value", [("name", None), ("price", None), ("quantity", None), ("price", "1.001"), ("quantity", -1)])
def test_invalid_partial_update(client, field, value):
    created = client.post("/products", json={"name": "Test", "price": "1.00", "quantity": 1}).json()
    url = f"/products/{created['id']}"
    assert client.put(url, json={field: value}).status_code == 422
    assert client.get(url).json() == created


def test_missing_token(client):
    app.dependency_overrides.pop(require_user)
    assert client.get("/products").status_code == 401


@pytest.mark.parametrize("remote_status,expected", [(200, 200), (401, 401), (403, 403), (500, 503), (302, 503)])
def test_remote_auth(client, monkeypatch, remote_status, expected):
    app.dependency_overrides.pop(require_user)

    async def fake_get(self, url, **kwargs):
        assert url.endswith("/auth")
        assert kwargs["headers"]["Authorization"] == "Bearer test-token"
        return httpx.Response(remote_status, json={"valid": True, "user": {"sub": "sa", "id": 1}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    assert client.get("/products", headers={"Authorization": "Bearer test-token"}).status_code == expected


@pytest.mark.parametrize("body,expected", [
    ({"valid": False, "message": "Token không hợp lệ", "user": None}, 401),
    ({}, 503),
    ({"valid": "true", "user": {"sub": "sa"}}, 503),
    ({"valid": 1, "user": {"sub": "sa"}}, 503),
    ({"valid": True, "user": None}, 503),
    ({"valid": True, "user": {}}, 503),
    ([], 503),
])
def test_auth_response_body(client, monkeypatch, body, expected):
    app.dependency_overrides.pop(require_user)

    async def fake_get(self, url, **kwargs):
        return httpx.Response(200, json=body)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    response = client.get("/products", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == expected
    if expected == 401:
        assert response.headers["WWW-Authenticate"] == "Bearer"


def test_auth_invalid_json(client, monkeypatch):
    app.dependency_overrides.pop(require_user)

    async def fake_get(self, url, **kwargs):
        return httpx.Response(200, text="not JSON")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    assert client.get("/products", headers={"Authorization": "Bearer test-token"}).status_code == 503


@pytest.mark.parametrize("method,path,body", [
    ("GET", "/products", None),
    ("GET", "/products/1", None),
    ("POST", "/products", {"name": "Test", "price": "1.00", "quantity": 1}),
    ("PUT", "/products/1", {"quantity": 2}),
    ("DELETE", "/products/1", None),
])
def test_invalid_token_blocks_all_endpoints(client, monkeypatch, method, path, body):
    # Bài 2 trả HTTP 200 nhưng valid=false: cả 5 endpoint phải từ chối.
    app.dependency_overrides.pop(require_user)

    async def fake_get(self, url, **kwargs):
        return httpx.Response(200, json={"valid": False, "message": "Token sai", "user": None})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    response = client.request(method, path, json=body, headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_auth_unavailable(client, monkeypatch):
    app.dependency_overrides.pop(require_user)

    async def fake_get(self, url, **kwargs):
        raise httpx.ConnectError("Unavailable")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    assert client.get("/products", headers={"Authorization": "Bearer test-token"}).status_code == 503
