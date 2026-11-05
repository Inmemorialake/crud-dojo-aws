from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import db
from .models import ProductoIn, ProductoOut

app = FastAPI(
    title="API Productos — Python + MongoDB",
    description="CRUD REST de productos con FastAPI y MongoDB (dojo AWS).",
    version="1.0.0",
)


# Mismo contrato que la API de Node: errores de validación → 400 con lista de errores.
@app.exception_handler(RequestValidationError)
async def validation_handler(_req: Request, exc: RequestValidationError):
    errores = [f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=400, content={"errores": errores})


# Errores HTTP con el mismo formato que la API de Node: {"error": "..."}.
@app.exception_handler(StarletteHTTPException)
async def http_handler(_req: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


def to_out(doc: dict) -> ProductoOut:
    # MongoDB usa `_id` (ObjectId); la API expone `id` como string.
    return ProductoOut(id=str(doc.pop("_id")), **doc)


def parse_id(raw: str) -> ObjectId:
    try:
        return ObjectId(raw)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="id inválido")


@app.get("/", tags=["info"])
def root():
    return {"api": "productos", "stack": "Python (FastAPI) + MongoDB", "docs": "/docs"}


@app.get("/health", tags=["info"])
def health():
    try:
        db.get_client().admin.command("ping")
        return {"status": "ok", "db": "up"}
    except PyMongoError:
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "down"})


# READ (todos)
@app.get("/api/productos", response_model=list[ProductoOut], tags=["productos"])
def listar():
    return [to_out(d) for d in db.productos().find().sort("creado_en", 1)]


# READ (uno)
@app.get("/api/productos/{producto_id}", response_model=ProductoOut, tags=["productos"])
def obtener(producto_id: str):
    doc = db.productos().find_one({"_id": parse_id(producto_id)})
    if doc is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return to_out(doc)


# CREATE
@app.post("/api/productos", response_model=ProductoOut, status_code=status.HTTP_201_CREATED,
          tags=["productos"])
def crear(producto: ProductoIn, response: Response):
    doc = producto.model_dump()
    doc["creado_en"] = datetime.now(timezone.utc)
    result = db.productos().insert_one(doc)  # insert_one agrega `_id` al dict
    response.headers["Location"] = f"/api/productos/{result.inserted_id}"
    return to_out(doc)


# UPDATE (reemplazo completo de los campos editables)
@app.put("/api/productos/{producto_id}", response_model=ProductoOut, tags=["productos"])
def actualizar(producto_id: str, producto: ProductoIn):
    cambios = producto.model_dump()
    doc = db.productos().find_one_and_update(
        {"_id": parse_id(producto_id)},
        {"$set": cambios},
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return to_out(doc)


# DELETE
@app.delete("/api/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT,
            tags=["productos"])
def eliminar(producto_id: str):
    result = db.productos().delete_one({"_id": parse_id(producto_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
