from app.db.schema_inspector import describe_schema
from app.db.session import get_engine
from app.llm.client import generate_sql
from app.llm.prompts import build_system_prompt

system = build_system_prompt(describe_schema(get_engine()))
messages = [
    {"role": "system", "content": system},
    {"role": "user", "content": "Cuantos pedidos hay pendientes?"},
]
print(generate_sql(messages))