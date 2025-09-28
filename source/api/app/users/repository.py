"""Repositories for interacting with users domain."""

from app.database.repository import BaseRepository
from app.users import UserId
from app.users import models as M
from app.users import schemas as S


class UserRepository(BaseRepository[M.User, UserId, S.BaseUser]):
    model = M.User

    def get_authenticated_user(self, email: str, password: str):
        stored_user = self.get_one(self.model.email == email)
        if not stored_user or not stored_user.verify_password(password):
            return None
        return S.User.model_validate(stored_user)
