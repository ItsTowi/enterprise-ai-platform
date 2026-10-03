from sqlalchemy import text

from app.db.session import get_engine

engine = get_engine()

with engine.connect() as conn:
    print(conn.execute(text("SELECT COUNT(*) FROM customers")).scalar())
    print(conn.execute(text("SELECT @@SESSION.max_execution_time")).scalar())