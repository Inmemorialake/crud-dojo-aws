"""Tests del CRUD usando mongomock (MongoDB en memoria): no requieren Docker.

    pip install -r requirements.txt pytest httpx mongomock
    pytest -q
"""
import mongomock
import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture()
def client():
    db.set_client(mongomock.MongoClient())
    return TestClient(app)


def test_crud_completo(client):
    r = client.post("/api/productos", json={"nombre": " Teclado ", "precio": 189900, "stock": 12})
    assert r.status_code == 201
    creado = r.json()
    pid = creado["id"]
    assert creado["nombre"] == "Teclado"
    assert r.headers["location"] == f"/api/productos/{pid}"

    assert len(client.get("/api/productos").json()) == 1
    assert client.get(f"/api/productos/{pid}").json()["precio"] == 189900

    r = client.put(f"/api/productos/{pid}", json={"nombre": "Teclado TKL", "precio": 175000, "stock": 8})
    assert r.status_code == 200 and r.json()["stock"] == 8

    assert client.delete(f"/api/productos/{pid}").status_code == 204
    r = client.get(f"/api/productos/{pid}")
    assert r.status_code == 404 and r.json() == {"error": "Producto no encontrado"}


def test_validaciones(client):
    assert client.post("/api/productos", json={"precio": -5}).status_code == 400
    assert client.post("/api/productos", json={"nombre": "   ", "precio": 1}).status_code == 400
    assert client.get("/api/productos/no-es-un-id").status_code == 400
    assert client.delete("/api/productos/" + "0" * 24).status_code == 404


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "db": "up"}
