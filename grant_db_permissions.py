#!/usr/bin/env python3
"""Grant database permissions to the lpt-event app service principal."""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import PermissionsChange, Privilege

# Initialize workspace client (uses DEFAULT profile)
w = WorkspaceClient(profile="DEFAULT")

# Service principal client ID from the app
sp_client_id = "d90946d6-1656-467b-8879-0ce59027f19e"
database_instance = "LPT-LKB-2"

# Get the database instance UID
instance = w.database.get_database_instance(database_instance)
print(f"Database instance: {instance.name} (UID: {instance.uid})")

# Grant CONNECT and CREATE permissions
try:
    # Grant database connection permission to the service principal
    w.grants.update(
        securable_type="DATABASE",
        full_name=database_instance,
        changes=[
            PermissionsChange(
                principal=sp_client_id,
                add=[Privilege.USAGE, Privilege.CREATE]
            )
        ]
    )
    print(f"✓ Granted USAGE and CREATE permissions to service principal {sp_client_id}")
except Exception as e:
    print(f"Error granting permissions: {e}")
    print("\nTrying alternative approach...")

    # Alternative: Use database-specific permissions if available
    try:
        w.grants.update(
            securable_type="DATABASE",
            full_name=database_instance,
            changes=[
                PermissionsChange(
                    principal=sp_client_id,
                    add=[Privilege.ALL_PRIVILEGES]
                )
            ]
        )
        print(f"✓ Granted ALL_PRIVILEGES to service principal {sp_client_id}")
    except Exception as e2:
        print(f"Alternative approach also failed: {e2}")
        print("\nManual action required:")
        print(f"1. Go to Databricks workspace")
        print(f"2. Navigate to Database instance: {database_instance}")
        print(f"3. Grant CONNECT and CREATE permissions to: {sp_client_id}")
