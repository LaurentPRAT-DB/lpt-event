from typing import List

from pydantic import BaseModel, HttpUrl, ConfigDict
from sqlmodel import SQLModel, Field, Column, JSON

from .. import __version__


class VersionOut(BaseModel):
    """API version information response model.

    Returns the current version of the application API, extracted from
    the package metadata (__version__).

    Attributes:
        version (str): Semantic version string (e.g., "1.0.0").

    Example:
        >>> version_info = VersionOut.from_metadata()
        >>> print(version_info.version)
        1.0.0
    """

    version: str

    @classmethod
    def from_metadata(cls):
        """Create a VersionOut instance from package metadata.

        Returns:
            VersionOut: Version information with the current package version.
        """
        return cls(version=__version__)


# --- Event models ---
#
# We separate the SQLModel table (which needs SQLAlchemy-friendly field types)
# from the Pydantic I/O models (which can use richer types like HttpUrl).
#
# This separation allows us to:
# 1. Use Pydantic's rich validation types (HttpUrl) in API payloads
# 2. Keep database schema simple with basic SQLAlchemy-compatible types
# 3. Validate input at API boundaries while storing efficiently in database


class EventBase(SQLModel):
    """Base fields shared by Event table and I/O models.

    Defines the core fields that are common across all event-related models:
    the database table (Event), creation payload (EventCreate), update payload
    (EventUpdate), and response model (EventRead).

    This pattern separates concerns:
    - EventBase: Shared field definitions
    - Event (table): Database representation with ID
    - EventCreate/EventUpdate: API request payloads with validation
    - EventRead: API response with from_attributes support

    Attributes:
        title (str): Short, descriptive event title (indexed for search).
        short_description (str): Brief teaser description for event listings.
        detailed_description (str): Full event description with all details.
        city (str): City where the event takes place (indexed for filtering).
        days_of_week (List[str]): Days when the event occurs (e.g., ["Monday", "Wednesday"]).
            Stored as JSON in database to avoid separate table.
        cost_usd (float): Event cost in USD. Must be non-negative (ge=0).
        picture_url (str): URL of the event picture. Stored as string in database,
            but validated as HttpUrl in create/update models.

    Note:
        - Fields with index=True will have database indexes created
        - days_of_week uses JSON column type for efficient storage
        - picture_url is a string here but HttpUrl in I/O models for validation
    """

    title: str = Field(index=True, description="Short title of the event")
    short_description: str = Field(description="Short teaser description")
    detailed_description: str = Field(description="Full event description")
    city: str = Field(index=True, description="City where the event takes place")

    # Store list as JSON in database rather than creating a separate table
    # This is acceptable because days_of_week has a fixed small size and no complex queries
    days_of_week: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),  # Use SQLAlchemy's JSON column type
        description="One or multiple days of the week (e.g. ['Monday', 'Wednesday'])",
    )

    cost_usd: float = Field(description="Cost of the event in USD", ge=0)  # ge=0 ensures non-negative values

    # Stored as a plain string in the database to avoid SQLAlchemy type issues with URLs
    # API models use HttpUrl type for validation, then convert to string for storage
    picture_url: str = Field(description="URL of the event picture")


class Event(EventBase, table=True):
    """
    SQLModel table for events stored in the database.

    The table=True parameter tells SQLModel to create a database table for this class.
    """

    id: int | None = Field(default=None, primary_key=True)


class EventCreate(BaseModel):
    """
    Payload for creating an event (Pydantic-only, with URL validation).

    Uses pure Pydantic (not SQLModel) to leverage rich validation types like HttpUrl.
    The HttpUrl type ensures picture_url is a valid URL format before accepting it.
    """

    title: str
    short_description: str
    detailed_description: str
    city: str
    days_of_week: List[str]
    cost_usd: float
    picture_url: HttpUrl  # Pydantic validates this as a proper URL


class EventUpdate(BaseModel):
    """
    Payload for updating an event (all fields optional).

    All fields are optional to support partial updates.
    Only fields provided in the request will be updated in the database.
    """

    title: str | None = None
    short_description: str | None = None
    detailed_description: str | None = None
    city: str | None = None
    days_of_week: List[str] | None = None
    cost_usd: float | None = None
    picture_url: HttpUrl | None = None  # Validated if provided


class EventRead(BaseModel):
    """
    Payload returned to clients (includes ID and database values).

    This model is used to serialize Event table rows into JSON responses.
    """

    # Allow this model to be created from SQLAlchemy/SQLModel ORM objects
    # This enables: EventRead.model_validate(event_row)
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    short_description: str
    detailed_description: str
    city: str
    days_of_week: List[str]
    cost_usd: float
    picture_url: str  # Plain string (already stored as string in database)
