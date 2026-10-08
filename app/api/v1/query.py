from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import Answerer, get_answerer
from app.schemas.query import QueryRequest, QueryResponse

router = APIRouter(prefix="/v1", tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(
    body: QueryRequest,
    answerer: Annotated[Answerer, Depends(get_answerer)],
) -> QueryResponse:
    # "def" y no "async def": answer_question es bloqueante (OpenAI y MySQL
    # sincronos). FastAPI ejecuta las rutas "def" en un pool de hilos y no
    # congela el servidor mientras espera.
    result = answerer(body.question)
    return QueryResponse(sql=result.sql, rows=result.rows, reason=result.reason)
