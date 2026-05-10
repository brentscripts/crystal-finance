# Crystal Finance - Three-Tier Architecture Deployment Guide

## 📋 Overview

This document provides comprehensive instructions for deploying the refactored three-tier microservice architecture:

- **Tier 1 (Frontend)**: Flask UI container on port 5000
- **Tier 2 (API)**: C# .NET Web API container on port 8080
- **Tier 3 (Database)**: MySQL 8.0 container on port 3306

All services communicate via an internal Docker bridge network (`finance-network`).

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Finance Network (Bridge)             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐  ┌──────────┐   │
│  │  Flask UI    │───→│  Web API     │──→│  MySQL   │   │
│  │  :5000       │    │  :8080       │  │  :3306   │   │
│  │              │    │              │  │          │   │
│  │ Container    │    │ Container    │  │Container │   │
│  │ Port: 5000   │    │ Port: 8080   │  │ Port:3306│   │
│  │ (External)   │    │ (Health      │  │ Mounted: │   │
│  │              │    │  Check)      │  │ finance_ │   │
│  └──────────────┘    └──────────────┘  │ data     │   │
│       ↑                     ↑           │          │   │
│       │                     │           └──────────┘   │
│  HOST Port 5000        HOST Port 8080                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- Docker Desktop (or Docker CE + Docker Compose)
- PowerShell, Bash, or Terminal
- `.env` file configured in the root directory (copy from `.env.example`)

### Step 1: Configure Environment Variables

```powershell
# Copy the example environment file
Copy-Item .env.example .env

# Edit .env and fill in:
# - MYSQL_ROOT_PASSWORD
# - MYSQL_USER and MYSQL_PASSWORD
# - CLIENT_ID, CLIENT_SECRET (for Azure Entra ID)
# - AUTHORITY, REDIRECT_URI
# - SECRET_KEY (generate: python -c "import secrets; print(secrets.token_hex(32))")
```

### Step 2: Build and Start Services

```powershell
# Build all images
docker-compose build

# Start all services (detached mode)
docker-compose up -d

# View logs
docker-compose logs -f

# Verify all services are healthy
docker-compose ps
```

### Step 3: Verify Services

```powershell
# Check MySQL health
curl http://localhost:3306

# Check Web API health
curl http://localhost:8080/health

# Check Flask UI
curl http://localhost:5000

# View specific service logs
docker-compose logs mysql
docker-compose logs web-api
docker-compose logs flask-ui
```

---

## 🔄 Data Migration Strategy

### From SQLite to MySQL

If you have existing data in SQLite (.db files), migrate it as follows:

#### Option A: SQL Export Script (Recommended)

1. **Export from SQLite**:

   ```powershell
   # On your host machine
   sqlite3 your_database.db ".dump" > backup.sql
   ```

2. **Transform SQL (if needed)**:
   - Replace SQLite-specific syntax with MySQL-compatible syntax
   - Update data types (e.g., `DATETIME` vs `TIMESTAMP`)
   - Remove SQLite auto-increment syntax, use MySQL equivalents

3. **Import into MySQL container**:

   ```powershell
   # Copy SQL file into container
   docker cp backup.sql finance-mysql:/tmp/backup.sql

   # Connect to MySQL and import
   docker exec -it finance-mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} < /tmp/backup.sql
   ```

#### Option B: Using mysql/init.sql (Recommended for Fresh Setup)

1. **Place initialization script** in `./mysql/init.sql`:

   ```sql
   -- Create tables and seed data
   CREATE TABLE IF NOT EXISTS transactions (
       id INT AUTO_INCREMENT PRIMARY KEY,
       date DATE NOT NULL,
       description VARCHAR(255),
       amount DECIMAL(10, 2),
       category VARCHAR(50),
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   -- Insert sample data
   INSERT INTO transactions (date, description, amount, category) VALUES
   ('2024-01-01', 'Groceries', 50.00, 'Food'),
   ('2024-01-02', 'Gas', 45.00, 'Transportation');
   ```

2. **Restart services** - Docker automatically runs `init.sql` on first startup:
   ```powershell
   docker-compose down -v
   docker-compose up -d
   ```

#### Option C: Direct Python Script Migration

Create a migration script (`migrate_data.py`):

```python
import sqlite3
import pymysql
import os

# Connect to SQLite
sqlite_conn = sqlite3.connect('finance.db')
sqlite_cursor = sqlite_conn.cursor()

# Connect to MySQL (inside Docker)
mysql_conn = pymysql.connect(
    host='localhost',
    port=3307,  # Using HOST_PORT from .env
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DATABASE')
)
mysql_cursor = mysql_conn.cursor()

# Migrate transactions table
sqlite_cursor.execute('SELECT * FROM transactions')
for row in sqlite_cursor.fetchall():
    mysql_cursor.execute(
        'INSERT INTO transactions (date, description, amount) VALUES (%s, %s, %s)',
        row
    )

mysql_conn.commit()
mysql_cursor.close()
mysql_conn.close()
sqlite_conn.close()
```

Run the migration:

```powershell
pip install pymysql
python migrate_data.py
```

---

## 📡 Internal Service Communication

### Flask UI → Web API

The Flask UI connects to the Web API using the internal service name:

```python
# In frontend/webapp/app.py
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5001')

# Inside Docker: API_BASE_URL=http://web-api:8080
# Outside Docker: API_BASE_URL=http://localhost:8080

# Flask makes HTTP requests to the API
response = requests.get(f'{API_BASE_URL}/api/transactions', timeout=API_TIMEOUT)
```

### Web API → MySQL

The C# Web API connects to MySQL using the internal service name:

```csharp
// In appsettings.json (environment-specific override)
// ConnectionStrings__DefaultConnection is set by Docker
// Format: Server=mysql;Database=finance;Uid=financeuser;Pwd=...;

// Dapper/ADO.NET automatically handles connection pooling
```

### Network Resolution

Docker's embedded DNS server automatically resolves:

- `mysql` → MySQL container IP
- `web-api` → Web API container IP
- `flask-ui` → Flask UI container IP

---

## 🔧 Managing Services

### View Logs

```powershell
# All services
docker-compose logs

# Specific service with live updates
docker-compose logs -f web-api

# Last 100 lines
docker-compose logs --tail=100 flask-ui
```

### Stop/Start Services

```powershell
# Stop all services (keeps containers)
docker-compose stop

# Start services again
docker-compose start

# Restart specific service
docker-compose restart web-api

# Stop and remove containers
docker-compose down

# Stop and remove everything (including volumes)
docker-compose down -v
```

### Execute Commands Inside Containers

```powershell
# Access MySQL CLI
docker exec -it finance-mysql mysql -u root -p

# Execute .NET CLI commands in Web API
docker exec -it finance-api dotnet --version

# Execute Python commands in Flask UI
docker exec -it finance-ui python --version

# View Flask logs
docker exec -it finance-ui tail -f /app/logs/app.log
```

---

## 🏥 Health Checks

Each service has a health check endpoint:

| Service  | Endpoint                       | Expected Response              |
| -------- | ------------------------------ | ------------------------------ |
| MySQL    | N/A                            | Responds to health check probe |
| Web API  | `http://localhost:8080/health` | `200 OK` + JSON health info    |
| Flask UI | `http://localhost:5000`        | `200 OK` + HTML page           |

View health status:

```powershell
docker-compose ps

# Output shows "healthy", "unhealthy", or "starting"
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused" from Flask to Web API

**Solution**:

```powershell
# Verify Web API is running
docker-compose ps web-api

# Check logs
docker-compose logs web-api

# Verify connectivity inside Flask container
docker exec finance-ui curl http://web-api:8080/health
```

### Issue: "Access denied" from Web API to MySQL

**Solution**:

```powershell
# Verify MySQL credentials in .env
# Verify environment variables are set in Web API container
docker exec finance-api env | grep ConnectionStrings

# Check MySQL is accepting connections
docker exec -it finance-mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1"
```

### Issue: Port already in use

**Solution**:

```powershell
# Change HOST_PORT in .env (e.g., HOST_PORT=3307)
# Or kill the process using the port

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS
lsof -i :5000
kill -9 <PID>
```

### Issue: Flask UI can't authenticate with Azure

**Solution**:

```powershell
# Verify Azure AD configuration
# Check CLIENT_ID, CLIENT_SECRET, AUTHORITY are correct
# Ensure REDIRECT_URI matches Azure AD app registration
# Verify REDIRECT_URI includes full path: http://hostname:5000/getAToken
```

---

## 📊 Performance Optimization

### Docker Build Optimization

The `.dockerignore` file excludes unnecessary files, reducing build context:

- Build artifacts (`bin/`, `obj/`)
- Virtual environments (`venv/`)
- Git history (`.git/`)
- IDE files (`.vs/`, `.vscode/`)

### Database Connection Pooling

The C# Web API automatically pools connections to MySQL. Adjust in `appsettings.json`:

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=mysql;...;Min Pool Size=5;Max Pool Size=50;"
  }
}
```

### Flask UI Optimization

Use `gunicorn` worker processes (already configured in Dockerfile):

```dockerfile
CMD ["gunicorn", "--workers=4", "--bind", "0.0.0.0:5000", "webapp.app:app"]
```

---

## 📝 .env File Best Practices

- **Never commit `.env` to git** (use `.env.example` instead)
- Use strong, unique passwords for production
- Rotate secrets regularly
- Use environment-specific .env files (`.env.prod`, `.env.dev`)
- Document required variables in `.env.example`

---

## 🔐 Security Considerations

### For Production Deployment

1. **Use environment-specific secrets management**:
   - Azure Key Vault (if using Azure)
   - AWS Secrets Manager (if using AWS)
   - Docker Secrets (for Swarm mode)

2. **Enable HTTPS**:
   - Use reverse proxy (Nginx, Caddy)
   - Manage SSL certificates (Let's Encrypt)
   - Set `ASPNETCORE_URLS=https://+:443;http://+:80`

3. **Network isolation**:
   - Don't expose MySQL port to external network
   - Use separate networks for backend/frontend if possible
   - Implement API authentication (JWT, OAuth)

4. **Update base images**:
   ```powershell
   docker pull mcr.microsoft.com/dotnet/aspnet:10.0
   docker pull python:3.12-alpine
   docker pull mysql:8
   ```

---

## 📚 Related Documentation

- [Flask Deployment Guide](frontend/README.md)
- [C# Web API README](src/CrystalFinance.Api/README.md)
- [Architecture Documentation](frontend/FRONTEND_ARCHITECTURE.md)
- [Migration Guide](frontend/MIGRATION_GUIDE.md)

---

## 💡 Quick Reference Commands

```powershell
# Full clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# View everything
docker-compose ps
docker-compose logs -f

# Restart after code changes
docker-compose restart web-api

# Access database directly
docker exec -it finance-mysql mysql -u ${MYSQL_USER} -p ${MYSQL_PASSWORD} ${MYSQL_DATABASE}

# Run database query
docker exec finance-mysql mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} -e "SELECT * FROM transactions;"
```

---

**Last Updated**: 2024  
**Status**: Production Ready
