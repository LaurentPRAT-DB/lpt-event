from typing import List

from pydantic import BaseModel, HttpUrl, ConfigDict
from sqlmodel import SQLModel, Field, Column, JSON

from .. import __version__


class VersionOut(BaseModel):
    version: str

    @classmethod
    def from_metadata(cls):
        return cls(version=__version__)


# --- Event models ---
#
# We separate the SQLModel table (which needs SQLAlchemy-friendly field types)
# from the Pydantic I/O models (which can use richer types like HttpUrl).


class EventBase(SQLModel):
    """Base fields shared by Event table and I/O models."""

    title: str = Field(index=True, description="Short title of the event")
    short_description: str = Field(description="Short teaser description")
    detailed_description: str = Field(description="Full event description")
    city: str = Field(index=True, description="City where the event takes place")
    days_of_week: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="One or multiple days of the week (e.g. ['Monday', 'Wednesday'])",
    )
    cost_usd: float = Field(description="Cost of the event in USD", ge=0)
    # Stored as a plain string in the database to avoid SQLAlchemy type issues.
    picture_url: str = Field(description="URL of the event picture")


class Event(EventBase, table=True):
    """SQLModel table for events."""

    id: int | None = Field(default=None, primary_key=True)


class EventCreate(BaseModel):
    """Payload for creating an event (Pydantic, with URL validation)."""

    title: str
    short_description: str
    detailed_description: str
    city: str
    days_of_week: List[str]
    cost_usd: float
    picture_url: HttpUrl


class EventUpdate(BaseModel):
    """Payload for updating an event (all fields optional)."""

    title: str | None = None
    short_description: str | None = None
    detailed_description: str | None = None
    city: str | None = None
    days_of_week: List[str] | None = None
    cost_usd: float | None = None
    picture_url: HttpUrl | None = None


class EventRead(BaseModel):
    """Payload returned to clients (includes ID)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    short_description: str
    detailed_description: str
    city: str
    days_of_week: List[str]
    cost_usd: float
    picture_url: str  # Plain string for reading from database
