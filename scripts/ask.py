import json
import sys

from app.services.text_to_sql import answer_question
from app.utils.exceptions import LLMResponseError, TextToSqlError

MAX_ROWS_SHOWN = 10


def main() -> None:
    if len(sys.argv) < 2:
        print('Uso: python -m scripts.ask "tu pregunta"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    try:
        result = answer_question(question)
    except (TextToSqlError, LLMResponseError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    if result.sql is None:
        print(f"Sin consulta: {result.reason}")
        return

    print(f"SQL: {result.sql}")
    print(f"Filas: {len(result.rows)}")
    # default=str: Decimal y fechas no son serializables a JSON de forma nativa.
    print(json.dumps(result.rows[:MAX_ROWS_SHOWN], indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
