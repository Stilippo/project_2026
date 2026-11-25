from fastapi import APIRouter, HTTPException, status
from sqlmodel import delete, select

from app.data.db import SessionDep
from app.models.event import Event, EventCreate, EventUpdate
from app.models.registration import Registration

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[Event])
def list_events(session: SessionDep) -> list[Event]:
    """Return the list of all existing events."""
    events = session.exec(select(Event)).all()
    return list(events)


@router.post("", response_model=Event, status_code=status.HTTP_201_CREATED)
def create_event(event_data: EventCreate, session: SessionDep) -> Event:
    """Create a new event and persist it in the database."""
    event = Event.model_validate(event_data)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@router.get("/{id}", response_model=Event)
def get_event(id: int, session: SessionDep) -> Event:
    """Return a single event by its ID, or 404 if it does not exist."""
    event = session.get(Event, id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {id} not found",
        )
    return event


@router.put("/{id}", response_model=Event)
def update_event(id: int, event_data: EventUpdate, session: SessionDep) -> Event:
    """Update an existing event by its ID, or return 404 if it does not exist."""
    event = session.get(Event, id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {id} not found",
        )
    event.title = event_data.title
    event.description = event_data.description
    event.date = event_data.date
    event.location = event_data.location
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@router.delete("")
def delete_all_events(session: SessionDep) -> dict[str, str]:
    """Delete all events from the database."""
    session.exec(delete(Event))
    session.commit()
    return {"message": "All events deleted"}


@router.delete("/{id}")
def delete_event(id: int, session: SessionDep) -> dict[str, str]:
    """Delete an event by its ID along with all associated registrations (cascade)."""
    event = session.get(Event, id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {id} not found",
        )
    session.exec(delete(Registration).where(Registration.event_id == id))
    session.delete(event)
    session.commit()
    return {"message": f"Event {id} deleted"}
