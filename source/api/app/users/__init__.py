"""Domain for app users"""

from typing import NewType, cast
from uuid import UUID

from sqlalchemy import types

from app.database import PostgreSQLUUID

UserId = NewType("UserId", UUID)
_UserId = cast("types.TypeEngine[UserId]", PostgreSQLUUID)
