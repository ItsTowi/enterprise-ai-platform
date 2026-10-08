import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from app.utils.exceptions import InvalidSQLException

ALLOWED_TABLES: frozenset[str] = frozenset({
    "cust_ledger_entries",
    "customers",
    "item_ledger_entries",
    "products",
    "purchase_order_headers",
    "purchase_order_lines",
    "sales_invoice_headers",
    "sales_invoice_lines",
    "sales_order_headers",
    "sales_order_lines",
    "sales_persons",
    "suppliers",
})

ALLOWED_ROOT_TYPES = (exp.Select, exp.Union, exp.Intersect, exp.Except)
FORBIDDEN_FUNCTIONS: frozenset[str] = frozenset({
    "SLEEP", "BENCHMARK", "LOAD_FILE", "GET_LOCK", "RELEASE_LOCK",
})
MAX_ROWS = 100


def validate_sql(sql: str) -> str:
    statement = _parse_single_statement(sql)
    _check_root_type(statement)
    _check_forbidden_constructs(statement)
    _check_tables(statement)
    return _enforce_limit(statement).sql(dialect="mysql")


def _parse_single_statement(sql: str) -> exp.Expression:
    try:
        statements = sqlglot.parse(sql, read="mysql")
    except SqlglotError as exc:
        raise InvalidSQLException(f"SQL mal formado: {exc}") from exc

    if len(statements) != 1:
        raise InvalidSQLException(
            f"Solo se permite una sentencia, se recibieron {len(statements)}"
        )
    statement = statements[0]
    if statement is None:
        raise InvalidSQLException("SQL vacio")
    return statement


def _check_root_type(statement: exp.Expression) -> None:
    if not isinstance(statement, ALLOWED_ROOT_TYPES):
        raise InvalidSQLException(
            f"Solo se permiten consultas de lectura, se recibio: {type(statement).__name__}"
        )


def _check_forbidden_constructs(statement: exp.Expression) -> None:
    if statement.find(exp.Into) or statement.find(exp.Lock):
        raise InvalidSQLException("INTO y FOR UPDATE no estan permitidos")

    for func in statement.find_all(exp.Func):
        name = func.name.upper() if isinstance(func, exp.Anonymous) else func.sql_name().upper()
        if name in FORBIDDEN_FUNCTIONS:
            raise InvalidSQLException(f"Funcion no permitida: {name}")


def _check_tables(statement: exp.Expression) -> None:
    cte_names = {cte.alias_or_name for cte in statement.find_all(exp.CTE)}

    for table in statement.find_all(exp.Table):
        if table.db or table.catalog:
            raise InvalidSQLException(
                f"No uses nombres calificados con esquema: {table.sql(dialect='mysql')}"
            )
        if table.name in cte_names:
            continue
        if table.name not in ALLOWED_TABLES:
            raise InvalidSQLException(f"Tabla no permitida: {table.name}")


def _enforce_limit(statement: exp.Expression) -> exp.Expression:
    current = statement.args.get("limit")
    if current is not None:
        value = current.expression
        if isinstance(value, exp.Literal) and value.is_int and int(value.this) <= MAX_ROWS:
            return statement
    return statement.limit(MAX_ROWS)