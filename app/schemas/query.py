from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(
        min_length=3,
        max_length=500,
        description="Pregunta en lenguaje natural sobre los datos del ERP.",
        examples=["Top 5 clientes por importe facturado"],
    )


class QueryResponse(BaseModel):
    sql: str | None = Field(description="Consulta ejecutada. Null si no se pudo responder.")
    rows: list[dict[str, Any]] = Field(
        description="Filas devueltas. Los importes (Decimal) y las fechas se serializan como texto."
    )
    reason: str | None = Field(description="Motivo por el que no hay consulta, si sql es null.")
