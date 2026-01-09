#!/usr/bin/env python3
"""List all tables and schemas stored in the Databricks Postgres database."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lpt_event.backend.runtime import rt
from lpt_event.backend.logger import logger
from sqlalchemy import inspect, text

def list_schema():
    """List all tables and their schemas from the database."""
    try:
        logger.info("=" * 80)
        logger.info(f"Database Schema Inspector for: {rt.config.db.instance_name}")
        logger.info(f"Database: {rt.config.db.database_name}")
        logger.info("=" * 80)

        # Get SQLAlchemy inspector
        inspector = inspect(rt.engine)

        # Get all schemas
        schemas = inspector.get_schema_names()
        logger.info(f"\nAvailable schemas: {', '.join(schemas)}")

        # Get all table names (default schema is 'public' for PostgreSQL)
        table_names = inspector.get_table_names(schema='public')

        if not table_names:
            logger.info("\nNo tables found in the database.")
            return

        logger.info(f"\nFound {len(table_names)} table(s) in schema 'public':\n")

        for table_name in table_names:
            logger.info("=" * 80)
            logger.info(f"TABLE: {table_name}")
            logger.info("=" * 80)

            # Get columns
            columns = inspector.get_columns(table_name, schema='public')
            logger.info("\nColumns:")
            logger.info("─" * 80)

            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f"DEFAULT {col['default']}" if col.get('default') else ""

                logger.info(f"  • {col_name:25s} {col_type:20s} {nullable:10s} {default}")

            # Get primary keys
            pk = inspector.get_pk_constraint(table_name, schema='public')
            if pk and pk.get('constrained_columns'):
                logger.info("\nPrimary Key:")
                logger.info("─" * 80)
                logger.info(f"  {', '.join(pk['constrained_columns'])}")

            # Get foreign keys
            fks = inspector.get_foreign_keys(table_name, schema='public')
            if fks:
                logger.info("\nForeign Keys:")
                logger.info("─" * 80)
                for fk in fks:
                    logger.info(f"  • {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

            # Get indexes
            indexes = inspector.get_indexes(table_name, schema='public')
            if indexes:
                logger.info("\nIndexes:")
                logger.info("─" * 80)
                for idx in indexes:
                    idx_name = idx['name']
                    idx_cols = ', '.join(col for col in idx['column_names'] if col is not None)
                    unique = "UNIQUE" if idx.get('unique') else ""
                    logger.info(f"  • {idx_name}: ({idx_cols}) {unique}")

            # Get row count
            with rt.get_session() as session:
                row_count = session.scalar(text(f'SELECT COUNT(*) FROM "{table_name}"')) or 0
                logger.info(f"\nRow Count: {row_count}")

            logger.info("")

        logger.info("=" * 80)
        logger.info(f"Total tables: {len(table_names)}")
        logger.info("=" * 80)

        return table_names

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"Error inspecting schema: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    tables = list_schema()
    sys.exit(0 if tables is not None else 1)
