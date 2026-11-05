import os

from pymongo import MongoClient
from pymongo.collection import Collection

# MongoClient mantiene su propio pool de conexiones; se crea una sola vez por proceso.
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "productos_db")

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    return _client


def set_client(client: MongoClient) -> None:
    """Permite inyectar un cliente distinto (p. ej. mongomock en los tests)."""
    global _client
    _client = client


def productos() -> Collection:
    # En MongoDB no hay CREATE TABLE: la colección se crea al insertar el primer documento.
    return get_client()[MONGO_DB]["productos"]
