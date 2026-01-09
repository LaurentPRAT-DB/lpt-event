from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from databricks.sdk.service.iam import User as UserOut

from .config import conf
from .models import Event, EventCreate, EventRead, EventUpdate, VersionOut
from .dependencies import get_obo_session

api = APIRouter(prefix=conf.api_prefix)


@api.get("/version", response_model=VersionOut, operation_id="version")
async def version():
    """Return application version from package metadata."""
    return VersionOut.from_metadata()


@api.get("/current-user", response_model=UserOut, operation_id="currentUser")
def me_mock() -> UserOut:
    """
    Mocked current-user endpoint for local development.

    In production on Databricks Apps, the APX framework provides a real
    current-user endpoint that returns the authenticated user's information.
    This mock allows the frontend to work seamlessly in local development
    without requiring OAuth/OBO tokens.
    """
    return UserOut(
        id="local-user",
        user_name="local.user@example.com",
        display_name="Local User",
        active=True,
        emails=[],
        roles=[],
        groups=[],
        entitlements=[],
    )


# --- Event endpoints ---
# All endpoints use get_obo_session for database access with user authentication


@api.get("/events", response_model=List[EventRead], operation_id="listEvents")
def list_events(session: Annotated[Session, Depends(get_obo_session)]):
    """
    List all events from the database.

    Returns whatever is in the database - seeding of demo data happens during startup.
    """
    # Query all events from the database
    events = session.exec(select(Event)).all()

    # Convert ORM objects to Pydantic response models
    # model_validate() handles the conversion from SQLModel attributes to Pydantic fields
    return [EventRead.model_validate(e) for e in events]


@api.post("/events", response_model=EventRead, operation_id="createEvent")
def create_event(
    payload: EventCreate,
    session: Annotated[Session, Depends(get_obo_session)],
):
    """
    Create a new event.

    The payload uses Pydantic's HttpUrl for validation, but we store it as a plain string
    in the database to avoid SQLAlchemy type complexity.
    """
    # Convert Pydantic model to dict
    event_data = payload.model_dump()

    # Convert HttpUrl to string for database storage
    # Pydantic's HttpUrl is a special type that doesn't play well with SQLAlchemy
    event_data['picture_url'] = str(payload.picture_url)

    # Create Event table instance and persist to database
    event = Event(**event_data)
    session.add(event)
    session.commit()  # Write to database
    session.refresh(event)  # Load back the auto-generated ID

    # Convert ORM object to response model
    return EventRead.model_validate(event)


@api.get("/events/{event_id}", response_model=EventRead, operation_id="getEvent")
def get_event(
    event_id: int,
    session: Annotated[Session, Depends(get_obo_session)],
):
    """
    Fetch a single event by ID.

    Returns 404 if event doesn't exist.
    """
    # session.get() is the shorthand for querying by primary key
    event = session.get(Event, event_id)

    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Event not found")

    return EventRead.model_validate(event)


@api.put("/events/{event_id}", response_model=EventRead, operation_id="updateEvent")
def update_event(
    event_id: int,
    payload: EventUpdate,
    session: Annotated[Session, Depends(get_obo_session)],
):
    """
    Update an existing event with partial data.

    Only fields provided in the payload will be updated.
    All fields are optional in EventUpdate model.
    """
    from fastapi import HTTPException

    # First verify the event exists
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Extract only the fields that were provided in the request
    # exclude_unset=True means fields not sent in the request are ignored
    # This enables partial updates (e.g., only updating the title)
    update_data = payload.model_dump(exclude_unset=True)

    # Convert HttpUrl to string if picture_url was provided
    if 'picture_url' in update_data and update_data['picture_url'] is not None:
        update_data['picture_url'] = str(update_data['picture_url'])

    # Update each provided field on the existing event object
    for field, value in update_data.items():
        setattr(event, field, value)

    session.add(event)
    session.commit()  # Persist changes to database
    session.refresh(event)  # Reload to get any database-computed fields

    return EventRead.model_validate(event)


@api.delete("/events/{event_id}", operation_id="deleteEvent")
def delete_event(
    event_id: int,
    session: Annotated[Session, Depends(get_obo_session)],
):
    """
    Delete an event by ID.

    Returns 404 if event doesn't exist.
    Returns success message if deletion succeeds.
    """
    from fastapi import HTTPException

    # Verify event exists before attempting deletion
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Delete the event from the database
    session.delete(event)
    session.commit()

    # Return success response
    return {"ok": True, "message": f"Event {event_id} deleted successfully"}
