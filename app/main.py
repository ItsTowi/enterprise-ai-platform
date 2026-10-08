from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.v1.query import router as query_router

app = FastAPI(
    title="Enterprise AI Platform",
    version="0.1.0",
    description="Preguntas en lenguaje natural sobre el ERP (Text-to-SQL).",
)

register_exception_handlers(app)
app.include_router(query_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
