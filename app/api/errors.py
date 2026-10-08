import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.utils.exceptions import LLMResponseError, TextToSqlError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(TextToSqlError)
    async def text_to_sql_error_handler(request: Request, exc: TextToSqlError) -> JSONResponse:
        # El detalle tecnico va al log, no al cliente.
        logger.warning("Text-to-SQL failed: %s", exc)
        return JSONResponse(
            status_code=422,
            content={"detail": "No se pudo generar una consulta valida para esa pregunta. Prueba a reformularla."},
        )

    @app.exception_handler(LLMResponseError)
    async def llm_error_handler(request: Request, exc: LLMResponseError) -> JSONResponse:
        logger.error("LLM error: %s", exc)
        return JSONResponse(
            status_code=502,
            content={"detail": "El servicio de IA no ha respondido correctamente. Intentalo de nuevo mas tarde."},
        )
