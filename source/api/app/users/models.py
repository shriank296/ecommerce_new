"""Database models for user domain"""

from enum import Enum
from typing import Optional
from uuid import uuid4

import bcrypt
from sqlalchemy import JSON
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models import CreatedMixin, UpdateMixin
from app.users import UserId, _UserId

# class UserRole(Enum):
#     CUSTOMER = "customer"
#     ADMIN = "admin"


class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class User(Base, CreatedMixin, UpdateMixin):
    __tablename__ = "users"

    id: Mapped[UserId] = mapped_column(_UserId, primary_key=True, default=uuid4)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[Optional[str]]
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    _password: Mapped[str] = mapped_column("password", String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=False)
    address: Mapped[dict] = mapped_column(JSON)
    role: Mapped[UserRole] = mapped_column(SQLAlchemyEnum(UserRole), nullable=False)
    # orders = relationship(
    #     "Order", back_populates="user", cascade="all,delete", lazy="select"
    # )
    # cart = relationship(
    #     "Cart", back_populates="user", cascade="all,delete", lazy="select"
    # )

    @property
    def password(self):
        raise AttributeError("Password is write only!")

    @password.setter
    def password(self, raw_password: str):
        hashed_password = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())
        self._password = hashed_password.decode("utf-8")

    def verify_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(
            raw_password.encode("utf-8"), self._password.encode("utf-8")
        )
