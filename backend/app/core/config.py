from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "riskdb"
    POSTGRES_TEST_DB: str = "riskdb_test"

    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Simulated slow evaluation (seconds) before persisting results
    RISK_EVALUATION_DELAY_SECONDS: float = 2.0

    def _database_url(self, scheme: str) -> str:
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"{scheme}://{user}:{password}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri_async(self) -> str:
        return self._database_url("postgresql+psycopg_async")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri_sync(self) -> str:
        return self._database_url("postgresql+psycopg")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
