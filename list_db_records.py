#!/usr/bin/env python3
"""List all records stored in the Databricks Postgres database."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lpt_event.backend.runtime import rt
from lpt_event.backend.models import Event
from lpt_event.backend.logger import logger
from sqlmodel import select

def list_records():
    """List all records from the database."""
    try:
        logger.info("=" * 80)
        logger.info(f"Listing all records from database instance: {rt.config.db.instance_name}")
        logger.info("=" * 80)

        with rt.get_session() as session:
            # Query all events
            events = session.exec(select(Event)).all()

            if not events:
                logger.info("\nNo records found in the database.")
                return

            logger.info(f"\nFound {len(events)} record(s):\n")

            for i, event in enumerate(events, 1):
                logger.info("─" * 80)
                logger.info(f"Record #{i}")
                logger.info("─" * 80)
                logger.info(f"  ID:                  {event.id}")
                logger.info(f"  Title:               {event.title}")
                logger.info(f"  Short Description:   {event.short_description}")
                logger.info(f"  Detailed Description:{event.detailed_description}")
                logger.info(f"  City:                {event.city}")
                logger.info(f"  Days of Week:        {', '.join(event.days_of_week)}")
                logger.info(f"  Cost (USD):          ${event.cost_usd:.2f}")
                logger.info(f"  Picture URL:         {event.picture_url}")
                logger.info("")

        logger.info("=" * 80)
        logger.info(f"Total records: {len(events)}")
        logger.info("=" * 80)

        return events

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"Error listing records: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    records = list_records()
    sys.exit(0 if records is not None else 1)
