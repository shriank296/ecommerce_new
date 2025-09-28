"""Users router module.

Provides external access to Users domain.
"""

import logging

from fastapi import Depends, Form, HTTPException, Request, status

from app.common.router import APIRouter
from app.common.schemas import ErrorResponse
from app.database import RootSession
from app.database.session import get_database_session, session_manager
from app.extensions import get_token_service
from app.users import UserId
from app.users import expections as E
from app.users import schemas as S

logger = logging.getLogger(__name__)

user_router = APIRouter(include_in_schema=True, tags=["Users"])


@user_router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db_session: RootSession = Depends(get_database_session),
    jwt_service=Depends(get_token_service),
):
    with session_manager(db_session) as uow:
        user = uow.users.get_authenticated_user(email, password)
        if user:
            token = jwt_service.create_token(user_name=email, role=user.role)
            return {"token": token, "token_type": "bearer"}
        raise HTTPException(status_code=401, detail="Invalid credential")


@user_router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": S.User},
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid input data",
            "model": ErrorResponse,
        },
    },
)
def create_user(
    user: S.CreateUser,
    request: Request,
    db_session: RootSession = Depends(get_database_session),
) -> S.User:
    """Create new user."""
    with session_manager(db_session) as uow:
        user_model = uow.users.add(user, flush=True)
        uow.commit()
        return S.User.model_validate(user_model)


@user_router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": S.User},
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "model": ErrorResponse,
        },
    },
)
def get_user(
    id: UserId,
    request: Request,
    db_session: RootSession = Depends(get_database_session),
) -> S.User:
    """Fetch user from id."""
    with session_manager(db_session) as uow:
        _user = uow.users.get(id)
        if not _user:
            raise E.UserNotFound(
                title="Not found",
                path=request.url.path,
                http_status_code=status.HTTP_404_NOT_FOUND,
                errors=[],
            )
    return S.User.model_validate(_user)
