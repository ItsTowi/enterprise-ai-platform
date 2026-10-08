import pytest

from app.services.sql_validator import validate_sql
from app.utils.exceptions import InvalidSQLException

VALID = [
    "SELECT name FROM customers",
    "SELECT c.name FROM customers c JOIN sales_invoice_headers h ON h.sell_to_customer_no = c.no",
    "SELECT name FROM customers UNION SELECT name FROM suppliers",
    "WITH t AS (SELECT no FROM customers) SELECT * FROM t",
    "SELECT name FROM customers;",
]

INVALID = [
    "SELECT 1; DROP TABLE customers",
    "DELETE FROM customers",
    "DROP TABLE customers",
    "",
    ";",
    "SELECT * FROM customers WHERE (",
    "SELECT * FROM mysql.user",
    "SELECT * FROM information_schema.tables",
    "SELECT name FROM customers UNION SELECT user FROM mysql.user",
    "SELECT name FROM customers WHERE no IN (SELECT user FROM mysql.user)",
    "SELECT * FROM customers INTO OUTFILE '/tmp/x'",
    "SELECT SLEEP(10)",
    "SELECT * FROM customers FOR UPDATE",
]


@pytest.mark.parametrize("sql", VALID)
def test_valid_queries_pass(sql):
    assert validate_sql(sql)


@pytest.mark.parametrize("sql", INVALID)
def test_hostile_queries_are_rejected(sql):
    with pytest.raises(InvalidSQLException):
        validate_sql(sql)


def test_limit_is_added_when_missing():
    assert "LIMIT 100" in validate_sql("SELECT name FROM customers")


def test_small_limit_is_preserved():
    result = validate_sql("SELECT name FROM customers LIMIT 5")
    assert "LIMIT 5" in result and "LIMIT 100" not in result


def test_large_limit_is_capped():
    result = validate_sql("SELECT name FROM customers LIMIT 100000")
    assert "LIMIT 100" in result and "100000" not in result