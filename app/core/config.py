from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_host: str = "127.0.0.1"
    db_port: int = 3306 
    db_name: str = "middleware"
    db_readonly_user: str
    db_readonly_password: SecretStr

    @property
    def readonly_database_url(self) -> URL:
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_readonly_user,
            password=self.db_readonly_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()