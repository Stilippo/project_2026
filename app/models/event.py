from datetime import datetime, timezone
from pydantic import field_validator
from sqlmodel import SQLModel, Field


class EventBase(SQLModel):
    title: str
    description: str
    date: datetime
    location: str

    @field_validator("date")
    @classmethod
    def ensure_timezone(cls, v: datetime) -> datetime:
        """Ensure datetime has timezone info (default UTC) for SQLModel storage."""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class Event(EventBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class EventCreate(EventBase):
    pass


class EventUpdate(EventBase):
    pass
