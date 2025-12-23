#!/usr/bin/env python3
"""Grant database instance access to the app service principal using the Databricks API."""

import requests
from databricks.sdk import WorkspaceClient

# Initialize workspace client
w = WorkspaceClient(profile="DEFAULT")

# Get the host and token
host = w.config.host
token = w.config.token

# Service principal from the app
sp_client_id = "d90946d6-1656-467b-8879-0ce59027f19e"
database_instance_name = "LPT-LKB-2"

# Get database instance details
instance = w.database.get_database_instance(database_instance_name)
print(f"Database instance: {instance.name}")
print(f"UID: {instance.uid}")

# Try to update the database instance with allowed service principals
# Using the REST API directly
url = f"{host}/api/2.0/postgres-instances/{instance.uid}"

# Try PATCH to add allowed service principals
payload = {
    "allowed_service_principals": [sp_client_id]
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print(f"\nAttempting to grant access to service principal: {sp_client_id}")
response = requests.patch(url, json=payload, headers=headers)

if response.status_code == 200:
    print("✓ Successfully granted database access!")
    print(response.json())
elif response.status_code == 404:
    print(f"⚠️  Database API endpoint not found. Trying alternative...")

    # Try alternative endpoint
    alt_url = f"{host}/api/2.0/database-instances/{instance.uid}"
    response = requests.patch(alt_url, json=payload, headers=headers)

    if response.status_code == 200:
        print("✓ Successfully granted database access via alternative endpoint!")
        print(response.json())
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)
else:
    print(f"✗ Failed: {response.status_code}")
    print(response.text)

print("\n" + "="*70)
print("If automated grant failed, please manually grant access:")
print(f"1. Go to: {host}/database-instances")
print(f"2. Select database: {database_instance_name}")
print(f"3. Add service principal: {sp_client_id}")
print(f"4. Grant: CONNECT and CREATE permissions")
print("="*70)
