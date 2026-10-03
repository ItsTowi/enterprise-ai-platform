from app.db.session import get_engine
from app.db.schema_inspector import describe_schema

print(describe_schema(get_engine()))