# Crystal Finance - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Prerequisites Check

```powershell
# Verify Docker is installed and running
docker --version        # Docker version 20+
docker-compose --version  # Docker Compose 2.0+
```

### 2. Clone & Configure

```powershell
# Navigate to project root
cd crystal-finance

# Copy environment template
Copy-Item .env.example .env

# Edit .env with your values (use any text editor)
notepad .env
```

**Required .env Variables**:

```env
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=finance
MYSQL_USER=financeuser
MYSQL_PASSWORD=your_user_password
HOST_PORT=3306
SECRET_KEY=generate_random_key
CLIENT_ID=your_azure_client_id
CLIENT_SECRET=your_azure_client_secret
AUTHORITY=https://login.microsoftonline.com/your_tenant_id
REDIRECT_URI=http://localhost:5000/getAToken
AZURE_TENANT=your_tenant_id
```

### 3. Build & Run

```powershell
# Build all services
docker-compose build

# Start services
docker-compose up -d

# Wait 30-60 seconds for services to initialize
Start-Sleep -Seconds 45

# Verify all services are healthy
docker-compose ps
```

### 4. Verify Services

```powershell
# Check MySQL
docker exec finance-mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1;" 2>/dev/null
# Expected: | 1 |

# Check Web API
curl http://localhost:8080/health
# Expected: 200 OK with health JSON

# Check Flask UI
curl http://localhost:5000
# Expected: 200 OK with HTML

# View containers
docker-compose ps
# Expected: All services "Up" and "healthy"
```

### 5. Access Applications

| Application | URL                   | Purpose        |
| ----------- | --------------------- | -------------- |
| Flask UI    | http://localhost:5000 | User dashboard |
| Web API     | http://localhost:8080 | API endpoints  |
| MySQL       | localhost:3306        | Database       |

---

## 🆚 Common Tasks

### View Live Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web-api
docker-compose logs -f flask-ui
docker-compose logs -f mysql
```

### Restart Services

```powershell
# Restart specific service (keeps data)
docker-compose restart web-api

# Restart all services
docker-compose restart

# Stop all (keeps data and volumes)
docker-compose stop

# Stop and remove everything (deletes data!)
docker-compose down -v
```

### Database Access

```powershell
# MySQL CLI
docker exec -it finance-mysql mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}

# Run query without interactive mode
docker exec finance-mysql mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} -e "SELECT * FROM transactions LIMIT 5;"

# Backup database
docker exec finance-mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} > backup.sql
```

### Rebuild After Code Changes

```powershell
# Web API (C#) changes
docker-compose build web-api
docker-compose restart web-api

# Flask UI (Python) changes
docker-compose build flask-ui
docker-compose restart flask-ui

# Database schema changes
# Edit mysql/init.sql, then:
docker-compose down -v
docker-compose up -d
```

### Run Database Migration

```powershell
# If you have SQLite data to migrate:
python migrate_data.py
# See DATA_MIGRATION.md for full instructions
```

---

## 🐛 Troubleshooting

### "Connection refused" errors

```powershell
# Check if service is running and healthy
docker-compose ps

# View service logs
docker-compose logs web-api

# Wait longer and retry (services may still be starting)
Start-Sleep -Seconds 30
curl http://localhost:8080/health
```

### "Address already in use"

```powershell
# Find process using port
netstat -ano | findstr :5000

# Kill the process
taskkill /PID <PID> /F

# Or change HOST_PORT in .env to 5001, 5002, etc.
```

### "Database connection failed"

```powershell
# Verify MySQL is running
docker-compose ps mysql

# Check MySQL is responding
docker exec finance-mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1;"

# Verify credentials in Web API
docker exec finance-api env | grep ConnectionStrings

# Check MySQL logs
docker-compose logs mysql | tail -50
```

### "Flask can't reach Web API"

```powershell
# From inside Flask container
docker exec finance-ui curl http://web-api:8080/health

# Check environment variables
docker exec finance-ui env | grep API

# Verify network connectivity
docker exec finance-ui ping web-api
```

### Azure AD Authentication Fails

```powershell
# Verify environment variables
docker exec finance-ui env | grep -E "CLIENT_|AUTHORITY|REDIRECT"

# Check that REDIRECT_URI matches Azure AD app registration
# Must include: http://localhost:5000/getAToken

# Verify tokens aren't expired
# Check Flask session logs for specific error
docker-compose logs flask-ui | grep -i auth
```

---

## 📊 Verify Architecture

### Confirm Three-Tier Setup

```powershell
# 1. Verify containers are running
docker-compose ps
# Should show: finance-mysql, finance-api, finance-ui

# 2. Verify networking
docker exec finance-ui ping -c 1 web-api
docker exec finance-api ping -c 1 mysql

# 3. Check API health
curl http://localhost:8080/health

# 4. Check Flask UI
curl http://localhost:5000 | Select-Object -First 10

# 5. Query database through API
curl http://localhost:8080/api/transactions | ConvertFrom-Json | Select-Object -First 5
```

### Verify Volume Persistence

```powershell
# Data should survive restart
docker-compose restart mysql

# Verify data is still there
docker exec finance-mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -e "SELECT COUNT(*) FROM transactions;"
```

---

## 🔄 Update Services

### Update Base Images

```powershell
# Pull latest base images
docker pull python:3.12-alpine
docker pull mcr.microsoft.com/dotnet/sdk:10.0
docker pull mcr.microsoft.com/dotnet/aspnet:10.0
docker pull mysql:8

# Rebuild with new base images
docker-compose build --no-cache
```

### Update Dependencies

**Python (Flask)**:

```powershell
# Update requirements.txt, then:
docker-compose build flask-ui
docker-compose restart flask-ui
```

**C# (.NET)**:

```powershell
# Update .csproj file, then:
docker-compose build web-api
docker-compose restart web-api
```

**MySQL**:

```powershell
# Database schema changes go in mysql/init.sql
# For existing data, use ALTER TABLE commands
docker exec finance-mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -e "ALTER TABLE transactions ADD COLUMN new_col INT;"
```

---

## 🚀 Performance Tips

### Improve Build Speed

```powershell
# Use build cache
docker-compose build --no-cache  # Forces full rebuild
docker-compose build              # Uses cache (faster)

# Reduce image size
# Edit .dockerignore to exclude more files
# Use Alpine Linux as base image (already done)
```

### Improve Runtime Performance

```powershell
# Increase gunicorn workers for Flask
# Edit frontend/Dockerfile:
# CMD ["gunicorn", "--workers=4", ...]

# Increase .NET thread pool for Web API
# Set in Program.cs:
# ThreadPool.GetMinThreads(out int workers, out int io);
# ThreadPool.SetMinThreads(workers * 2, io);
```

### Monitoring

```powershell
# Watch resource usage
docker stats

# Check container details
docker inspect finance-api
docker inspect finance-mysql

# View container processes
docker top finance-api
```

---

## 📝 Environment Variables Reference

| Variable              | Service | Required | Default             |
| --------------------- | ------- | -------- | ------------------- |
| `MYSQL_ROOT_PASSWORD` | MySQL   | Yes      | N/A                 |
| `MYSQL_DATABASE`      | MySQL   | Yes      | N/A                 |
| `MYSQL_USER`          | MySQL   | Yes      | N/A                 |
| `MYSQL_PASSWORD`      | MySQL   | Yes      | N/A                 |
| `HOST_PORT`           | MySQL   | No       | 3306                |
| `SECRET_KEY`          | Flask   | Yes      | N/A                 |
| `FLASK_ENV`           | Flask   | No       | production          |
| `API_BASE_URL`        | Flask   | No       | http://web-api:8080 |
| `API_TIMEOUT`         | Flask   | No       | 10                  |
| `CLIENT_ID`           | Flask   | Yes      | N/A                 |
| `CLIENT_SECRET`       | Flask   | Yes      | N/A                 |
| `AUTHORITY`           | Flask   | Yes      | N/A                 |
| `REDIRECT_URI`        | Flask   | Yes      | N/A                 |
| `AZURE_TENANT`        | Flask   | Yes      | N/A                 |

---

## 🎯 Next Steps

1. **Read Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
2. **Deployment**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
3. **Data Migration**: See [DATA_MIGRATION.md](DATA_MIGRATION.md)
4. **Flask Frontend**: See [frontend/FRONTEND_ARCHITECTURE.md](frontend/FRONTEND_ARCHITECTURE.md)
5. **API Development**: See [src/CrystalFinance.Api/](src/CrystalFinance.Api/)

---

## ✅ Success Indicators

When everything is working correctly:

- ✅ `docker-compose ps` shows all containers "Up" and "healthy"
- ✅ `curl http://localhost:5000` returns Flask UI (200 OK)
- ✅ `curl http://localhost:8080/health` returns health status (200 OK)
- ✅ `curl http://localhost:8080/api/transactions` returns data from MySQL
- ✅ Azure AD login works on Flask UI
- ✅ Data persists after `docker-compose restart`
- ✅ No errors in `docker-compose logs`

---

## 💬 Getting Help

- **Logs**: `docker-compose logs -f [service]`
- **Debug**: `docker exec -it [container] /bin/bash`
- **Docs**: See DEPLOYMENT_GUIDE.md and DATA_MIGRATION.md
- **Issues**: Check logs for specific error messages

---

**Last Updated**: 2024  
**Status**: Ready to use
