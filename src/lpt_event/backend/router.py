from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from databricks.sdk.service.iam import User as UserOut

from .config import conf
from .models import Event, EventCreate, EventRead, EventUpdate, VersionOut
from .runtime import rt

api = APIRouter(prefix=conf.api_prefix)


def get_session():
    """Provide a SQLModel session for request scope."""
    with rt.get_session() as session:
        yield session


@api.get("/version", response_model=VersionOut, operation_id="version")
async def version():
    return VersionOut.from_metadata()


@api.get("/current-user", response_model=UserOut, operation_id="currentUser")
def me_mock() -> UserOut:
    """
    Mocked current-user endpoint for local development.

    This avoids requiring a Databricks OBO token when running the app locally.
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


@api.get("/events", response_model=List[EventRead], operation_id="listEvents")
def list_events(session: Annotated[Session, Depends(get_session)]):
    """List all events.

    Initially this will return whatever is in the database; seeding of mock data
    is handled during startup.
    """
    events = session.exec(select(Event)).all()
    return [EventRead.model_validate(e) for e in events]


@api.post("/events", response_model=EventRead, operation_id="createEvent")
def create_event(
    payload: EventCreate,
    session: Annotated[Session, Depends(get_session)],
):
    """Create a new event."""
    # Convert HttpUrl to string for database storage
    event_data = payload.model_dump()
    event_data['picture_url'] = str(payload.picture_url)
    event = Event(**event_data)
    session.add(event)
    session.commit()
    session.refresh(event)
    return EventRead.model_validate(event)


@api.get("/events/{event_id}", response_model=EventRead, operation_id="getEvent")
def get_event(
    event_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    """Fetch a single event by id."""
    event = session.get(Event, event_id)
    if not event:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Event not found")
    return EventRead.model_validate(event)


@api.put("/events/{event_id}", response_model=EventRead, operation_id="updateEvent")
def update_event(
    event_id: int,
    payload: EventUpdate,
    session: Annotated[Session, Depends(get_session)],
):
    """Update an existing event."""
    from fastapi import HTTPException

    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    # Convert HttpUrl to string if present
    if 'picture_url' in update_data and update_data['picture_url'] is not None:
        update_data['picture_url'] = str(update_data['picture_url'])

    for field, value in update_data.items():
        setattr(event, field, value)

    session.add(event)
    session.commit()
    session.refresh(event)
    return EventRead.model_validate(event)


@api.delete("/events/{event_id}", operation_id="deleteEvent")
def delete_event(
    event_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    """Delete an event by id."""
    from fastapi import HTTPException

    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    session.delete(event)
    session.commit()
    return {"ok": True, "message": f"Event {event_id} deleted successfully"}
