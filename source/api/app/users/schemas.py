from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.users import UserId


class BaseUser(BaseModel):
    first_name: str
    last_name: str | None = None
    email: str
    phone: str
    address: dict
    role: str


class User(BaseUser):
    id: UserId
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateUser(BaseUser):
    password: str

    model_config = ConfigDict(from_attributes=True)
