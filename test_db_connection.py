#!/usr/bin/env python3
"""Test script to verify Databricks Postgres connection."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lpt_event.backend.config import conf
from lpt_event.backend.runtime import rt
from lpt_event.backend.logger import logger

def test_connection():
    """Test the database connection."""
    try:
        logger.info("=" * 60)
        logger.info("Testing Databricks Postgres Connection")
        logger.info("=" * 60)

        # Display configuration
        logger.info(f"Configuration:")
        logger.info(f"  Instance Name: {conf.db.instance_name}")
        logger.info(f"  Database Name: {conf.db.database_name}")
        logger.info(f"  Port: {conf.db.port}")

        # Test database validation
        logger.info("\nValidating database connection...")
        rt.validate_db()

        logger.info("\n" + "=" * 60)
        logger.info("✓ Connection successful!")
        logger.info("=" * 60)

        # Test creating tables
        logger.info("\nInitializing database models...")
        rt.initialize_models()

        logger.info("\n" + "=" * 60)
        logger.info("✓ Database initialized successfully!")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error("\n" + "=" * 60)
        logger.error(f"✗ Connection failed: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
