# Crystal Finance Frontend - Migration Guide

## Overview

This guide helps you migrate from the SQLite-based Flask application to the new API-based architecture with Azure Entra ID authentication and C# Web API backend.

## Pre-Migration Checklist

Before starting the migration, ensure you have:

- [ ] Access to Azure Portal
- [ ] C# Web API deployed and running
- [ ] MySQL database initialized with transaction schema
- [ ] Python 3.9+ installed
- [ ] Git repository access
- [ ] Environment variables documentation

## Step 1: Azure Entra ID Setup

### Register Application in Azure Portal

1. **Navigate to Azure AD**
   - Go to https://portal.azure.com
   - Search for "Azure Active Directory"
   - Click "App registrations" → "New registration"

2. **Register App**
   - Name: `Crystal Finance Frontend` (or your preferred name)
   - Supported account types: "Accounts in any organizational directory"
   - Redirect URI: `Web` → `http://localhost:5000/getAToken`
   - Click "Register"

3. **Configure Credentials**
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Copy and save the secret value (won't be shown again!)
   - Copy Client ID from Overview tab

4. **Configure API Permissions**
   - Click "API permissions"
   - Click "Add a permission"
   - Select "APIs my organization uses"
   - Find your C# Web API (should be registered as API)
   - Select permissions: `user_impersonation` or your API scope
   - Click "Grant admin consent"

### Collect Configuration Values

You'll need:

- **CLIENT_ID**: From Overview tab
- **CLIENT_SECRET**: From Certificates & secrets
- **AZURE_TENANT**: From Overview tab (Directory ID)
- **API_SCOPE**: Scope from your C# API registration (usually `api://{API_CLIENT_ID}/.default`)

## Step 2: Prepare Environment

### Create .env File

```bash
cd frontend

# Copy template
cp .env.example .env

# Edit with your values
nano .env  # or use your preferred editor
```

### Required Environment Variables

```env
# MSAL Configuration (from Azure AD)
CLIENT_ID=your_app_client_id
CLIENT_SECRET=your_app_client_secret
AZURE_TENANT=your_tenant_id
API_SCOPE=api://your_api_client_id/.default

# Flask Configuration
SECRET_KEY=your_secure_random_key
FLASK_ENV=production

# API Configuration
API_BASE_URL=http://your_api_server:5001
API_TIMEOUT=30

# Application Settings
PORT=5000
```

### Generate Secure Keys

```bash
# Generate a random SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

## Step 3: Backup Existing Data

### Export SQLite Data

If migrating from old SQLite database:

```bash
# Backup the existing database
cp transactions.db transactions.db.backup

# Export transactions to CSV (from old app)
python -c "
import sqlite3
conn = sqlite3.connect('transactions.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM transactions')
rows = cursor.fetchall()
for row in rows:
    print(','.join(map(str, row)))
"
```

### Import to New System

Use the C# API import endpoint:

```bash
# Create CSV file with transactions
# Headers: trxDate,amount,source,description,category

# Then import via the web interface:
# 1. Login to Flask app
# 2. Click "Add Transaction" → "Import CSV"
# 3. Select your CSV file
# 4. Choose source type
# 5. Click "Import"
```

## Step 4: Deploy Updated Frontend

### Install Updated Code

```bash
cd frontend

# Pull latest changes (if using Git)
git pull origin main

# Or manual copy of new app.py and templates
```

### Install Dependencies

```bash
# Create virtual environment (if needed)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# For production, also install gunicorn
pip install gunicorn
```

## Step 5: Verify Setup

### Test Components

1. **Verify C# Web API is Running**

   ```bash
   curl http://your_api_server:5001/health
   # Should return 200 OK
   ```

2. **Test MSAL Configuration**

   ```bash
   python -c "
   import msal
   from your_config import CLIENT_ID, CLIENT_SECRET, AUTHORITY
   app = msal.ConfidentialClientApplication(
       CLIENT_ID,
       authority=AUTHORITY,
       client_credential=CLIENT_SECRET
   )
   print('✓ MSAL configured correctly')
   "
   ```

3. **Test Environment Variables**
   ```bash
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   required_vars = ['CLIENT_ID', 'CLIENT_SECRET', 'API_BASE_URL']
   missing = [v for v in required_vars if not os.getenv(v)]
   if missing:
       print(f'✗ Missing: {missing}')
   else:
       print('✓ All environment variables configured')
   "
   ```

## Step 6: Run Development Test

```bash
# Set Flask app
export FLASK_APP=webapp/app.py
# or on Windows:
set FLASK_APP=webapp/app.py

# Run development server
python -m flask run

# Open browser: http://localhost:5000
```

### Test Workflow

1. **Homepage** - Should load without errors
2. **Login** - Click "Sign in with Microsoft"
3. **Authentication** - Redirected to Azure AD
4. **Dashboard** - After login, should show user name
5. **Add Transaction** - Form should load
6. **View Transactions** - Should show paginated list from API
7. **Logout** - Should clear session

## Step 7: Production Deployment

### Using Gunicorn

```bash
# Install gunicorn (if not already done)
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 webapp.app:app

# With custom config file
gunicorn -c gunicorn_config.py webapp.app:app
```

### Using Docker

```bash
# Build image
docker build -t crystal-finance-frontend .

# Run container
docker run -d \
  --name crystal-frontend \
  -e CLIENT_ID=your_client_id \
  -e CLIENT_SECRET=your_client_secret \
  -e API_BASE_URL=http://api:5001 \
  -p 5000:5000 \
  crystal-finance-frontend
```

### Using Docker Compose

```yaml
version: "3.8"
services:
  frontend:
    build: ./frontend
    ports:
      - "5000:5000"
    environment:
      - CLIENT_ID=your_client_id
      - CLIENT_SECRET=your_client_secret
      - API_BASE_URL=http://api:5001
    depends_on:
      - api

  api:
    image: crystal-finance-api:latest
    ports:
      - "5001:5001"
    environment:
      - CONNECTION_STRING=your_mysql_connection
```

### Using Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Step 8: Post-Migration

### Verify Production

1. **Check Application Health**
   - Visit https://your-domain
   - Login and navigate through application
   - Test add/edit/delete transaction

2. **Monitor Logs**
   - Check Flask application logs
   - Check C# API logs
   - Monitor error rates

3. **Test Error Scenarios**
   - Disconnect C# API → should see error message
   - Invalid credentials → should show auth error
   - Network timeout → should handle gracefully

4. **Performance Test**
   - Load transaction list
   - Check response times
   - Monitor resource usage

### Cleanup

```bash
# Remove old SQLite database (after data migration)
rm transactions.db transactions.db.backup

# Archive old code (if desired)
tar czf crystal-finance-old-version.tar.gz old_code/
```

## Troubleshooting

### "Connection refused" error

**Problem:** Cannot connect to C# Web API

**Solution:**

```bash
# 1. Verify API is running
curl http://your_api_server:5001/health

# 2. Check API_BASE_URL in .env
cat .env | grep API_BASE_URL

# 3. Check firewall/network connectivity
ping your_api_server
```

### "Invalid redirect_uri" error

**Problem:** Azure AD rejects redirect URI

**Solution:**

1. Check Azure Portal > App registration > Authentication
2. Verify redirect URI matches exactly: `http://localhost:5000/getAToken`
3. For production, update to: `https://your-domain.com/getAToken`
4. Wait 5 minutes for changes to propagate

### "CSRF validation failed" error

**Problem:** Session or CSRF token issue

**Solution:**

```bash
# 1. Verify SECRET_KEY is set
grep SECRET_KEY .env

# 2. Clear browser cookies and try again
# 3. Check that session type is 'filesystem'
# 4. Verify session folder has write permissions
ls -la flask_session/
```

### Transactions not showing

**Problem:** API call fails silently

**Solution:**

```bash
# 1. Check C# API is running and responding
curl http://your_api_server:5001/api/CrystalFinance

# 2. Check API response format
# Should return: { success: true, data: {...}, message: "..." }

# 3. Check Flask logs for errors
# Run with debug mode enabled
export FLASK_DEBUG=True
python -m flask run
```

### Slow performance

**Problem:** Application feels sluggish

**Solution:**

1. Check API_TIMEOUT setting (increase if needed)
2. Add caching to API responses
3. Optimize database queries in C# API
4. Use CDN for static files
5. Enable gzip compression in Nginx

## Rollback Plan

If issues occur:

```bash
# 1. Keep backup of old code
cp -r /opt/crystal-finance /opt/crystal-finance-backup

# 2. Keep backup of old database
cp transactions.db transactions.db.backup

# 3. If needed, revert to old version
git checkout old-version-tag
pip install -r requirements-old.txt
python app-old.py
```

## Performance Optimization

### Enable Caching

```python
# In app.py - add Redis caching
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@app.route('/transactions')
@cache.cached(timeout=300)  # Cache for 5 minutes
def transactions():
    ...
```

### Enable Compression

```python
# In app.py - enable Gzip compression
from flask_compress import Compress
Compress(app)
```

### Database Connection Pooling

Ensure C# API has connection pooling configured.

## Monitoring

### Application Monitoring

```bash
# Install monitoring tools
pip install prometheus-client

# Track metrics
- Request latency
- Error rate
- Cache hit rate
- API availability
```

### Logging

```python
# Enhanced logging in Flask
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Support & Help

If you encounter issues:

1. **Check Documentation**
   - Read FRONTEND_ARCHITECTURE.md
   - Review .env.example

2. **Check Logs**
   - Flask application logs
   - C# API logs
   - Browser console

3. **Verify Prerequisites**
   - Python version
   - Dependencies installed
   - Environment variables set
   - Ports available
   - Firewall rules

4. **Contact Support**
   - Provide error message
   - Share logs (sanitized)
   - Describe what was attempted
   - List environment details

---

**Migration Guide Version:** 1.0
**Last Updated:** May 2, 2026
**Estimated Migration Time:** 1-2 hours
**Rollback Time:** 15-30 minutes
