"""Repositories for interacting with users domain."""

from app.database.repository import BaseRepository
from app.users import UserId
from app.users import models as M
from app.users import schemas as S


class UserRepository(BaseRepository[M.User, UserId, S.User]):
    model = M.User
