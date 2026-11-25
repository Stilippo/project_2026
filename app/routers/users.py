from collections.abc import Sequence
from sqlite3 import SQLITE_CONSTRAINT_PRIMARYKEY

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, delete, select

from app.data.db import SessionDep
from app.models.registration import Registration
from app.models.user import User, UserBase, UserCreate


router = APIRouter(prefix="/users", tags=["users"])


def _get_user_or_404(username: str, session: Session) -> User:
    user = session.get(User, username)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.get("", response_model=list[UserBase])
def list_users(session: SessionDep) -> Sequence[User]:
    """Return all users stored in the database."""
    return session.exec(select(User)).all()


@router.post(
    "",
    response_model=UserBase,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"description": "User already exists"}},
)
def create_user(user: UserCreate, session: SessionDep) -> User:
    """Create a user with a unique username."""
    if session.get(User, user.username) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "User already exists")

    new_user = User.model_validate(user)
    session.add(new_user)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        # Another request can insert the same username after the lookup.
        if getattr(error.orig, "sqlite_errorcode", None) == SQLITE_CONSTRAINT_PRIMARYKEY:
            raise HTTPException(status.HTTP_409_CONFLICT, "User already exists") from error
        raise

    session.refresh(new_user)
    return new_user


@router.get(
    "/{username}",
    response_model=UserBase,
    responses={status.HTTP_404_NOT_FOUND: {"description": "User not found"}},
)
def get_user(username: str, session: SessionDep) -> User:
    """Return the user identified by username."""
    return _get_user_or_404(username, session)


@router.delete("", response_class=Response)
def delete_users(session: SessionDep) -> Response:
    """Delete all users and their event registrations."""
    session.exec(delete(Registration))
    session.exec(delete(User))
    session.commit()
    return Response()


@router.delete(
    "/{username}",
    response_class=Response,
    responses={status.HTTP_404_NOT_FOUND: {"description": "User not found"}},
)
def delete_user(username: str, session: SessionDep) -> Response:
    """Delete the selected user and their event registrations."""
    user = _get_user_or_404(username, session)
    session.exec(delete(Registration).where(Registration.username == username))
    session.delete(user)
    session.commit()
    return Response()
