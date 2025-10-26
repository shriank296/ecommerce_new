from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.common.schemas import CamelMode
from app.users import UserId


class BaseUser(BaseModel):
    first_name: str
    last_name: str | None = None
    email: str
    phone: str
    address: dict
    role: str
    created_by: str
    updated_by: str


class User(BaseUser):
    id: UserId
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResult(CamelMode):
    email: str
    phone: str


class CreateUser(BaseUser):
    password: str = Field(alias="_password")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserCreatedHeaders(CamelMode):
    requestor_id: str
    content_type: str = "application/json"
    event_type: Literal["UserCreated"] = "UserCreated"
    version: str = "1.0.0"


class UserCreated(CamelMode):
    headers: UserCreatedHeaders
    payload: UserResult
