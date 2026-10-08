import json
from dataclasses import dataclass
from functools import lru_cache

from openai import OpenAI, OpenAIError

from app.core.config import get_settings
from app.utils.exceptions import LLMResponseError

REQUEST_TIMEOUT_SECONDS = 30.0
MAX_SDK_RETRIES = 2


@dataclass(frozen=True)
class SqlGeneration:
    sql: str | None
    reason: str | None


@lru_cache
def get_openai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_retries=MAX_SDK_RETRIES,
    )


def generate_sql(messages: list[dict[str, str]]) -> SqlGeneration:
    settings = get_settings()
    try:
        response = get_openai_client().chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )
    except OpenAIError as exc:
        raise LLMResponseError(f"Error llamando al LLM: {exc}") from exc

    content = response.choices[0].message.content
    return _parse_response(content)


def _parse_response(content: str | None) -> SqlGeneration:
    if not content:
        raise LLMResponseError("Respuesta vacia del LLM")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"El LLM no devolvio JSON valido: {exc}") from exc

    if not isinstance(data, dict) or "sql" not in data:
        raise LLMResponseError("Falta la clave 'sql' en la respuesta del LLM")

    sql, reason = data.get("sql"), data.get("reason")
    if sql is None and not reason:
        raise LLMResponseError("El LLM no devolvio ni sql ni reason")
    if sql is not None and not isinstance(sql, str):
        raise LLMResponseError("El campo 'sql' debe ser texto")

    return SqlGeneration(sql=sql, reason=reason)