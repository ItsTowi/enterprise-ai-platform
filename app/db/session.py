from functools import lru_cache
from sqlalchemy import Engine, create_engine, event
from app.core.config import get_settings


QUERY_TIMEOUT_MS = 5000

@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    engine = create_engine(
        settings.readonly_database_url, 
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True, 
        pool_recycle=300
        )
    
    @event.listens_for(engine, "connect")
    def set_query_timeout(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(f"SET SESSION max_execution_time = {QUERY_TIMEOUT_MS}")
        finally:
            cursor.close()

    return engine
