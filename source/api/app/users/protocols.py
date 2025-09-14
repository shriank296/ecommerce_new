from typing import Protocol

from app.database.repository import BaseRepositoryProtocol
from app.users import UserId
from app.users import models as M
from app.users import schemas as S


class UserProtocol(BaseRepositoryProtocol[M.User, UserId, S.User], Protocol):
    pass
