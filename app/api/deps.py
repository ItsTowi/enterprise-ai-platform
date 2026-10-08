from collections.abc import Callable

from app.services.text_to_sql import QueryResult, answer_question

Answerer = Callable[[str], QueryResult]


def get_answerer() -> Answerer:
    # Punto unico de inyeccion: los tests lo sustituyen por una funcion falsa.
    return answer_question
