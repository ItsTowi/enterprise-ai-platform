import pytest
from sqlalchemy.exc import DBAPIError

from app.llm.client import SqlGeneration
from app.services import text_to_sql
from app.utils.exceptions import TextToSqlError

VALID_SQL = "SELECT name FROM customers"
INVALID_SQL = "DELETE FROM customers"


@pytest.fixture(autouse=True)
def fake_prompt(monkeypatch):
    monkeypatch.setattr(text_to_sql, "get_system_prompt", lambda: "SYSTEM")


def script_llm(monkeypatch, generations):
    """Sustituye al LLM por respuestas prefijadas y registra los mensajes recibidos."""
    calls: list[list[dict[str, str]]] = []

    def fake_generate(messages):
        calls.append([dict(m) for m in messages])
        return generations[len(calls) - 1]

    monkeypatch.setattr(text_to_sql, "generate_sql", fake_generate)
    return calls


def test_returns_rows_on_first_attempt(monkeypatch):
    calls = script_llm(monkeypatch, [SqlGeneration(sql=VALID_SQL, reason=None)])
    monkeypatch.setattr(text_to_sql, "_execute", lambda sql: [{"name": "Ana"}])

    result = text_to_sql.answer_question("clientes?")

    assert result.rows == [{"name": "Ana"}]
    assert "LIMIT 100" in result.sql
    assert len(calls) == 1


def test_returns_reason_when_llm_cannot_answer(monkeypatch):
    script_llm(monkeypatch, [SqlGeneration(sql=None, reason="No hay datos")])

    def must_not_run(sql):
        raise AssertionError("no debe ejecutarse nada")

    monkeypatch.setattr(text_to_sql, "_execute", must_not_run)

    result = text_to_sql.answer_question("pedidos pendientes?")

    assert result.sql is None
    assert result.reason == "No hay datos"


def test_retries_with_validator_error_as_feedback(monkeypatch):
    calls = script_llm(
        monkeypatch,
        [
            SqlGeneration(sql=INVALID_SQL, reason=None),
            SqlGeneration(sql=VALID_SQL, reason=None),
        ],
    )
    monkeypatch.setattr(text_to_sql, "_execute", lambda sql: [{"name": "Ana"}])

    result = text_to_sql.answer_question("clientes?")

    assert result.rows == [{"name": "Ana"}]
    assert len(calls) == 2
    feedback = calls[1][-1]
    assert feedback["role"] == "user"
    assert INVALID_SQL in feedback["content"]
    assert "Delete" in feedback["content"]


def test_retries_after_mysql_error(monkeypatch):
    calls = script_llm(
        monkeypatch,
        [
            SqlGeneration(sql=VALID_SQL, reason=None),
            SqlGeneration(sql=VALID_SQL, reason=None),
        ],
    )
    attempts = {"n": 0}

    def flaky_execute(sql):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise DBAPIError("SELECT", None, Exception("Unknown column 'x'"))
        return [{"name": "Ana"}]

    monkeypatch.setattr(text_to_sql, "_execute", flaky_execute)

    result = text_to_sql.answer_question("clientes?")

    assert result.rows == [{"name": "Ana"}]
    assert "Unknown column 'x'" in calls[1][-1]["content"]


def test_raises_after_max_attempts(monkeypatch):
    calls = script_llm(
        monkeypatch,
        [SqlGeneration(sql=INVALID_SQL, reason=None)] * text_to_sql.MAX_ATTEMPTS,
    )

    with pytest.raises(TextToSqlError):
        text_to_sql.answer_question("borra todo")

    assert len(calls) == text_to_sql.MAX_ATTEMPTS
