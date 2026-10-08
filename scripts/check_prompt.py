from app.db.schema_inspector import describe_schema
from app.db.session import get_engine
from app.llm.prompts import build_system_prompt

print(build_system_prompt(describe_schema(get_engine()))[:1500])