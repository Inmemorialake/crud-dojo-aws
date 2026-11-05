from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductoIn(BaseModel):
    """Body de POST y PUT. Pydantic valida tipos y rangos antes de llegar al handler
    (si falla, FastAPI responde 422 automáticamente; aquí lo normalizamos a 400)."""

    # Recorta espacios antes de validar: "   " cuenta como nombre vacío.
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = ""
    precio: float = Field(ge=0)
    stock: int = Field(default=0, ge=0)


class ProductoOut(ProductoIn):
    id: str
    creado_en: datetime
