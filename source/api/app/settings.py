"""Application settings.

Don't forget to include these within the test dependecy overrides.
"""

from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Base application configuration."""

    SERVER_API_DOMAIN: str
    ENVIRONMENT: Literal["local", "testing", "dev", "tst", "uat", "prd"]
    RELEASE: str
    DATABASE_URI: str = "placeholder"
    APP_POOL_SIZE: int = 10
    # Database connection details.
    DB_USER: str
    DB_PASSWORD: str | None = None
    DB_HOST: str
    DB_NAME: str
    AZURE_CLIENT_ID: str | None = None
    DB_PORT: str = "5432"
    SB_NAMESPACE: str
    SB_TOPIC: str
    SB_SUBSCRIPTION: str
    SECRET_KEY: str
    ALGORITHM: str

    @property
    def IN_AZURE(self) -> bool:
        return self.ENVIRONMENT in ("dev", "tst", "uat", "prd")


def get_app_settings() -> AppSettings:
    return AppSettings()  # type: ignore[call-arg]


class ExternalApiSettings(BaseSettings):
    EXTERNAL_API_SECRET: SecretStr


def get_external_api_settings() -> ExternalApiSettings:
    return ExternalApiSettings()  # type: ignore[call-arg]
