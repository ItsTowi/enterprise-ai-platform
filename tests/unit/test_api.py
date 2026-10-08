from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_answerer
from app.main import app
from app.services.text_to_sql import QueryResult
from app.utils.exceptions import LLMResponseError, TextToSqlError

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def override_answerer(fake):
    app.dependency_overrides[get_answerer] = lambda: fake


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_serializes_decimals_and_dates_as_text():
    rows = [{"total": Decimal("724556.290"), "day": date(2026, 1, 2), "n": 5}]
    override_answerer(lambda q: QueryResult(sql="SELECT 1", rows=rows, reason=None))

    response = client.post("/v1/query", json={"question": "top clientes"})

    assert response.status_code == 200
    assert response.json() == {
        "sql": "SELECT 1",
        "rows": [{"total": "724556.290", "day": "2026-01-02", "n": 5}],
        "reason": None,
    }


def test_query_passes_stripped_question_to_answerer():
    received = []

    def fake(question):
        received.append(question)
        return QueryResult(sql=None, rows=[], reason="sin datos")

    override_answerer(fake)

    response = client.post("/v1/query", json={"question": "  hola mundo  "})

    assert received == ["hola mundo"]
    assert response.json() == {"sql": None, "rows": [], "reason": "sin datos"}


@pytest.mark.parametrize("payload", [{}, {"question": ""}, {"question": "ab"}, {"question": "x" * 501}, {"question": 123}])
def test_invalid_request_is_rejected_before_reaching_the_answerer(payload):
    def must_not_run(question):
        raise AssertionError("no debe llamarse")

    override_answerer(must_not_run)

    response = client.post("/v1/query", json=payload)

    assert response.status_code == 422


def test_text_to_sql_error_returns_422_without_internal_details():
    def failing(question):
        raise TextToSqlError("Tabla no permitida: mysql.user")

    override_answerer(failing)

    response = client.post("/v1/query", json={"question": "dame los usuarios"})

    assert response.status_code == 422
    assert "mysql" not in response.json()["detail"]


def test_llm_error_returns_502_without_internal_details():
    def failing(question):
        raise LLMResponseError("Incorrect API key provided: sk-123")

    override_answerer(failing)

    response = client.post("/v1/query", json={"question": "cuantos clientes hay"})

    assert response.status_code == 502
    assert "sk-123" not in response.text
