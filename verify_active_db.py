#!/usr/bin/env python3
"""Verify which database the application is configured to use."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lpt_event.backend.config import conf
from lpt_event.backend.runtime import rt
from lpt_event.backend.logger import logger

def verify_database():
    """Verify the database configuration."""
    logger.info("=" * 80)
    logger.info("DATABASE CONFIGURATION VERIFICATION")
    logger.info("=" * 80)

    logger.info(f"\n📋 Configuration from .env:")
    logger.info(f"  Instance Name:    {conf.db.instance_name}")
    logger.info(f"  Database Name:    {conf.db.database_name}")
    logger.info(f"  Port:             {conf.db.port}")

    logger.info(f"\n🔗 Database Engine URL:")
    engine_url = rt.engine_url
    logger.info(f"  {engine_url}")

    logger.info(f"\n🎯 Database Type:")
    if engine_url.startswith("sqlite"):
        logger.info("  ⚠️  SQLITE (In-Memory or File-based)")
        logger.info("  ❌ NOT using Databricks Postgres!")
        logger.info("\n💡 Action Required:")
        logger.info("  1. Verify .env has: SENSOR_MAGIC_DB__INSTANCE_NAME=LPT-LKB-2")
        logger.info("  2. Restart the backend server to pick up changes")
        logger.info("  3. If using uvicorn --reload, stop and restart it")
        logger.info("  4. If using 'uv run apx dev start', run 'uv run apx dev stop' then start again")
        return False
    elif engine_url.startswith("postgresql"):
        logger.info("  ✅ POSTGRESQL (Databricks Postgres)")
        logger.info(f"  ✅ Using instance: {conf.db.instance_name}")
        logger.info("\n🎉 Backend is correctly configured to use Databricks Postgres!")
        return True
    else:
        logger.info("  ❓ UNKNOWN database type")
        return None

    logger.info("=" * 80)

if __name__ == "__main__":
    result = verify_database()
    if result is True:
        sys.exit(0)
    elif result is False:
        sys.exit(1)
    else:
        sys.exit(2)
