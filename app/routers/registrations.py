from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.data.db import SessionDep
from app.models.event import Event
from app.models.registration import Registration
from app.models.user import User, UserCreate

router = APIRouter(tags=["registrations"])


@router.post(
    "/events/{id}/register",
    response_model=Registration,
    status_code=status.HTTP_201_CREATED,
)
def register_to_event(
    id: int, user_data: UserCreate, session: SessionDep
) -> Registration:
    """Register a user to the event with the given ID.

    If the user does not exist yet, it is created automatically.
    Returns 404 if the event does not exist and 409 if the user is
    already registered to the event.
    """
    event = session.get(Event, id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {id} not found",
        )

    user = session.get(User, user_data.username)
    if user is None:
        user = User.model_validate(user_data)
        session.add(user)

    existing = session.get(
        Registration, {"username": user_data.username, "event_id": id}
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {user_data.username} is already registered "
                   f"to event {id}",
        )

    registration = Registration(username=user_data.username, event_id=id)
    session.add(registration)
    session.commit()
    session.refresh(registration)
    return registration


@router.get("/registrations", response_model=list[Registration])
def list_registrations(session: SessionDep) -> list[Registration]:
    """Return the list of all existing registrations."""
    registrations = session.exec(select(Registration)).all()
    return list(registrations)


@router.delete("/registrations")
def delete_registration(
    username: str, event_id: int, session: SessionDep
) -> dict[str, str]:
    """Delete the registration identified by username and event_id.

    Returns 404 if the event, the user or the registration does not exist.
    """
    if session.get(Event, event_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found",
        )
    if session.get(User, username) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {username} not found",
        )

    registration = session.get(
        Registration, {"username": username, "event_id": event_id}
    )
    if registration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {username} is not registered to event {event_id}",
        )

    session.delete(registration)
    session.commit()
    return {"message": f"Registration of {username} to event {event_id} deleted"}
