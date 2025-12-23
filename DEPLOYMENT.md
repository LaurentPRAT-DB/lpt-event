# Databricks App Deployment Guide

## Application Status

✅ **Application Deployed Successfully**
- **App Name**: lpt-event
- **URL**: https://lpt-event-1444828305810485.aws.databricksapps.com
- **Service Principal**: `app-40zbx9 lpt-event`
- **Service Principal ID**: `d90946d6-1656-467b-8879-0ce59027f19e`
- **Status**: RUNNING

## ⚠️ Required Manual Step: Grant Database Permissions

The app service principal needs access to the database instance to function properly.

### Method 1: Via Databricks UI (Recommended)

1. Navigate to: https://e2-demo-field-eng.cloud.databricks.com/database-instances
2. Click on database instance: **LPT-LKB-2**
3. Go to the **Permissions** or **Access Control** tab
4. Click **Add** or **Grant**
5. Search for and select the service principal:
   - Name: `app-40zbx9 lpt-event`
   - ID: `d90946d6-1656-467b-8879-0ce59027f19e`
6. Grant the following permissions:
   - **CONNECT** - allows the app to connect to the database
   - **CREATE** - allows the app to create tables

### Method 2: Via Workspace Admin Settings

1. Go to: https://e2-demo-field-eng.cloud.databricks.com/settings/workspace
2. Navigate to **Service Principals**
3. Find: `app-40zbx9 lpt-event`
4. Add database access entitlements
5. Grant access to **LPT-LKB-2** with CONNECT and CREATE permissions

## Deployment Configuration

### Files Modified
- `databricks.yml` - Databricks bundle configuration
- `app.yml` - App runtime configuration with environment variables

### Environment Variables (in app.yml)
```yaml
env:
  - name: "LPT_EVENT_DB__INSTANCE_NAME"
    value: "LPT-LKB-2"
  - name: "LPT_EVENT_DB__PORT"
    value: "5432"
  - name: "LPT_EVENT_DB__DATABASE_NAME"
    value: "databricks_postgres"
```

## Deployment Commands

### Build and Deploy
```bash
# Build the application
uv run apx build

# Deploy to Databricks
databricks bundle deploy -p DEFAULT
```

### Start/Stop App
```bash
# Start the app
databricks bundle run lpt-event-app -p DEFAULT

# Stop the app
databricks apps stop lpt-event -p DEFAULT

# Check app status
databricks apps get lpt-event -p DEFAULT
```

## Testing the Deployment

Once database permissions are granted:

### 1. Test API Endpoints
```bash
# Test version endpoint (no auth required)
curl https://lpt-event-1444828305810485.aws.databricksapps.com/api/version

# Access the app (requires browser for OAuth)
open https://lpt-event-1444828305810485.aws.databricksapps.com
```

### 2. Verify Database Connection
The app will:
1. Connect to LPT-LKB-2 using the service principal credentials
2. Create the `event` table if it doesn't exist
3. Seed demo data on first startup
4. Use on-behalf-of authentication for user requests

## Security Features

### On-Behalf-Of (OBO) Authentication
- When users access the app, their identity is passed via `X-Forwarded-Access-Token` header
- The app creates per-user database connections
- Each database operation is performed with the user's own credentials
- Enables proper audit trails and row-level security

### OAuth2 Authentication
- Users must authenticate via Databricks OAuth before accessing the app
- The app automatically redirects unauthenticated users to login
- Token scopes: `iam.current-user:read`, `iam.access-control:read`

## Troubleshooting

### App Not Starting
```bash
# Check app status
databricks apps get lpt-event -p DEFAULT

# View recent deployments
databricks apps list-deployments lpt-event -p DEFAULT
```

### Database Connection Errors
1. Verify service principal has database permissions (see above)
2. Check that LPT-LKB-2 is running:
   ```bash
   databricks database get-database-instance LPT-LKB-2 -p DEFAULT
   ```
3. Verify environment variables in app.yml match database configuration

### Permission Errors
- Ensure the service principal `d90946d6-1656-467b-8879-0ce59027f19e` has CONNECT and CREATE permissions on LPT-LKB-2
- For user-specific errors, verify users have appropriate workspace permissions

## Next Steps After Granting Permissions

1. Restart the app to apply new permissions:
   ```bash
   databricks apps stop lpt-event -p DEFAULT
   databricks bundle run lpt-event-app -p DEFAULT
   ```

2. Test the application:
   - Open https://lpt-event-1444828305810485.aws.databricksapps.com
   - Login with your Databricks credentials
   - Verify you can view and manage events

3. Monitor the app:
   - Check app status regularly
   - Monitor database connections
   - Review user access patterns
