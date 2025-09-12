"""Database connectivity tools."""

from typing import NewType, cast
from uuid import UUID

import sqlalchemy
from sqlalchemy.dialects.postgresql import UUID as PUUID
from sqlalchemy.orm import Session

# A generic postgresql UUID.
PostgreSQLUUID = cast("sqlalchemy.types.TypeEngine[UUID]", PUUID(as_uuid=True))

RootSession = NewType("RootSession", Session)
