"""Server extensions.

This is here to stop circular dependencies forming. Please do not import 
packages that will lead to circular deps.
"""

from prometheus_fastapi_instrumentator import Instrumentator

from app.common.security import JWTTokenService, TokenService
from app.settings import get_app_settings

instrumentator = Instrumentator()

app_settings = get_app_settings()

token_service = JWTTokenService(
    algorithm=app_settings.ALGORITHM, secret_key=app_settings.SECRET_KEY
)


def get_token_service() -> TokenService:
    """Returns singleton JWT service instance for FASTAPI routes."""
    return token_service
