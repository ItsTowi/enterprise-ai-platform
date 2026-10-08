import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.schema_inspector import describe_schema
from app.db.session import get_engine
from app.llm.client import generate_sql
from app.llm.prompts import build_retry_message, build_system_prompt
from app.services.sql_validator import validate_sql
from app.utils.exceptions import InvalidSQLException, TextToSqlError

MAX_ATTEMPTS = 2


@dataclass(frozen=True)
class QueryResult:
    sql: str | None
    rows: list[dict[str, Any]]
    reason: str | None


@lru_cache
def get_system_prompt() -> str:
    # El esquema no cambia entre preguntas: se lee de MySQL una sola vez.
    return build_system_prompt(describe_schema(get_engine()))


def answer_question(question: str) -> QueryResult:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": question},
    ]
    last_error = ""

    for _ in range(MAX_ATTEMPTS):
        generation = generate_sql(messages)

        if generation.sql is None:
            return QueryResult(sql=None, rows=[], reason=generation.reason)

        try:
            safe_sql = validate_sql(generation.sql)
            rows = _execute(safe_sql)
        except InvalidSQLException as exc:
            last_error = str(exc)
        except DBAPIError as exc:
            last_error = str(exc.orig)
        else:
            return QueryResult(sql=safe_sql, rows=rows, reason=None)

        # Reintento: el modelo ve su propia respuesta y el error que provoco.
        previous = json.dumps({"sql": generation.sql, "reason": None})
        messages.append({"role": "assistant", "content": previous})
        messages.append(
            {
                "role": "user",
                "content": build_retry_message(generation.sql, last_error),
            }
        )

    raise TextToSqlError(
        f"No se pudo generar una consulta valida tras {MAX_ATTEMPTS} intentos. "
        f"Ultimo error: {last_error}"
    )


def _execute(sql: str) -> list[dict[str, Any]]:
    # text() trata ":nombre" como parametro; se escapan los ":" por si el SQL
    # los lleva dentro de un literal (por ejemplo 'Sala :A').
    statement = text(sql.replace(":", r"\:"))
    with get_engine().connect() as conn:
        return [dict(row) for row in conn.execute(statement).mappings().all()]
