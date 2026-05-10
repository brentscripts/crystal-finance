# 🚀 Crystal Finance - Three-Tier Microservice Architecture

## 📑 Quick Navigation

> **New to this refactoring?** Start here!

```
┌─ START HERE ─────────────────────────────────────────────────┐
│                                                              │
│  📖 Reading Guide:                                           │
│                                                              │
│  1️⃣  QUICKSTART.md           ← 5-minute setup               │
│  2️⃣  ARCHITECTURE.md         ← Understand the design        │
│  3️⃣  DEPLOYMENT_GUIDE.md     ← Production deployment        │
│  4️⃣  DATA_MIGRATION.md       ← Move data from SQLite        │
│  5️⃣  DELIVERABLES.md         ← What's included              │
│                                                              │
│  🎯 Quick Commands:           (See QUICKSTART.md)           │
│                                                              │
│     docker-compose build                                    │
│     docker-compose up -d                                    │
│     docker-compose ps                                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🏗️ What You Have

### Three-Tier Architecture

```
                     ┌─────────────────────┐
                     │   External Users    │
                     └──────────┬──────────┘
                                │
                    ┌───────────▼───────────┐
                    │    Flask UI :5000     │
                    │   (Python/Gunicorn)   │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Web API :8080        │
                    │  (C# .NET)            │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  MySQL :3306          │
                    │  (Database)           │
                    └───────────────────────┘
```

### Services

| Service      | Port | Technology  | Role                    |
| ------------ | ---- | ----------- | ----------------------- |
| **Flask UI** | 5000 | Python 3.12 | Frontend user interface |
| **Web API**  | 8080 | C# .NET 10  | Backend business logic  |
| **MySQL**    | 3306 | MySQL 8.0   | Data persistence        |

### Files Created

```
crystal-finance/
├── 📄 ARCHITECTURE.md           ← How it all works
├── 📄 DEPLOYMENT_GUIDE.md       ← How to deploy
├── 📄 DATA_MIGRATION.md         ← How to move data
├── 📄 QUICKSTART.md             ← 5-minute start
├── 📄 DELIVERABLES.md           ← What's included
├── 📄 REFACTORING_COMPLETE.md   ← Summary of changes
├── 📄 .env.example              ← Configuration template
│
├── 🐳 docker-compose.yml        ← Orchestration (UPDATED)
├── 🐳 .dockerignore             ← Build optimization (UPDATED)
│
├── src/CrystalFinance.Api/
│   └── 🐳 Dockerfile            ← Multi-stage C# build (NEW)
│
└── frontend/
    └── 🐳 Dockerfile            ← Flask production build (UPDATED)
```

---

## ⚡ Get Started in 5 Minutes

### Step 1: Configure (1 min)

```powershell
# Copy template
Copy-Item .env.example .env

# Edit with your credentials
notepad .env
```

### Step 2: Build (2 min)

```powershell
docker-compose build
```

### Step 3: Run (1 min)

```powershell
docker-compose up -d
```

### Step 4: Verify (1 min)

```powershell
# Check services
docker-compose ps

# Test Flask UI
curl http://localhost:5000

# Test Web API
curl http://localhost:8080/health

# Test MySQL
docker exec finance-mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1;"
```

✅ **You're done!** All services should be healthy.

---

## 📚 Documentation Guide

### 🎯 Choose Your Path

#### **I want to get started NOW**

→ Read: `QUICKSTART.md` (5 min)

- Configure .env
- Run docker-compose
- Verify services

#### **I want to understand the architecture**

→ Read: `ARCHITECTURE.md` (20 min)

- Three-tier design
- Service communication
- Docker networking
- Security model

#### **I need to deploy to production**

→ Read: `DEPLOYMENT_GUIDE.md` (30 min)

- Step-by-step procedures
- Health check verification
- Troubleshooting guide
- Performance optimization
- Security checklist

#### **I have SQLite data to migrate**

→ Read: `DATA_MIGRATION.md` (15 min)

- 4 migration methods
- Data verification
- Backup procedures
- Rollback steps

#### **I want to know what changed**

→ Read: `REFACTORING_COMPLETE.md` (10 min)

- Before/after comparison
- Files created/updated
- Improvements summary

---

## 🔍 Service Details

### Flask UI (Port 5000)

**Access**: http://localhost:5000

```
├── Features
│   ├── Azure AD Authentication (MSAL)
│   ├── Dashboard UI
│   ├── Transaction Management
│   └── Session Management
│
├── Technology Stack
│   ├── Python 3.12
│   ├── Alpine Linux
│   ├── Gunicorn (production server)
│   ├── Flask (web framework)
│   └── Jinja2 (templating)
│
├── Communication
│   └── HTTP/REST to Web API (http://web-api:8080)
│
└── Health Check
    └── GET http://localhost:5000 (every 30s)
```

### Web API (Port 8080)

**Access**: http://localhost:8080

```
├── Features
│   ├── REST API Endpoints
│   ├── JWT Authentication
│   ├── Health Check Endpoints
│   ├── Swagger/OpenAPI Documentation
│   └── Dapper ORM Data Access
│
├── Technology Stack
│   ├── C# .NET 10.0
│   ├── Multi-stage Docker build
│   ├── Minimal runtime image
│   └── Connection pooling
│
├── Communication
│   └── SQL to MySQL Database (mysql:3306)
│
└── Health Checks
    ├── GET /health (overall)
    ├── GET /health/live (liveness probe)
    └── GET /health/ready (readiness probe)
```

### MySQL Database (Port 3306)

**Access**: localhost:3306 (external via docker)

```
├── Features
│   ├── Persistent Data Storage
│   ├── Automatic Initialization
│   ├── Named Volume Backup
│   └── Health Monitoring
│
├── Technology Stack
│   ├── MySQL 8.0
│   ├── Docker Volume (finance_data)
│   └── Connection pooling in Web API
│
├── Communication
│   └── SQL Queries from Web API
│
└── Health Check
    └── MySQL CLI probe (every 10s)
```

---

## 🌐 Internal Service Discovery

Services communicate using internal Docker DNS:

```powershell
# From Flask UI container, connect to Web API:
requests.get('http://web-api:8080/api/transactions')

# From Web API container, connect to MySQL:
# Server=mysql;Database=finance;Uid=user;Pwd=pass;
```

| Service  | Internal URL | Port |
| -------- | ------------ | ---- |
| MySQL    | `mysql`      | 3306 |
| Web API  | `web-api`    | 8080 |
| Flask UI | `flask-ui`   | 5000 |

---

## 🔧 Common Commands

### Service Management

```powershell
# View all containers
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f web-api

# Stop services
docker-compose stop

# Start services
docker-compose start

# Restart services
docker-compose restart

# Stop and remove (keeps data)
docker-compose down

# Stop and remove everything (deletes data!)
docker-compose down -v
```

### Access Services

```powershell
# Access Flask UI
Start-Process http://localhost:5000

# Test Web API
curl http://localhost:8080/health

# Access MySQL CLI
docker exec -it finance-mysql mysql -u root -p

# Run database query
docker exec finance-mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -e "SELECT * FROM transactions LIMIT 5;"
```

### Debugging

```powershell
# Check container details
docker inspect finance-api

# Check resource usage
docker stats

# Execute command in container
docker exec -it finance-api /bin/bash

# View container environment
docker exec finance-ui env
```

---

## 📊 Architecture Highlights

### ✅ **Separation of Concerns**

- UI layer (Flask)
- API layer (C# Web API)
- Data layer (MySQL)

### ✅ **Microservices**

- Independent deployment
- Technology-appropriate stacks
- Horizontal scaling capability

### ✅ **Containerization**

- Consistent environments
- Reproducible builds
- Easy deployment

### ✅ **Health Monitoring**

- Health checks at each tier
- Automatic service restart
- Dependency management

### ✅ **Data Persistence**

- Named Docker volumes
- Database initialization script
- Backup capability

### ✅ **Networking**

- Internal Docker bridge network
- Service DNS resolution
- External port mapping

---

## 🔐 Security

### Built-in Protections

- ✅ Network isolation (MySQL only accessible from Web API)
- ✅ Credentials via environment variables
- ✅ CSRF protection (Flask)
- ✅ Session management

### Environment Variables

```env
MYSQL_ROOT_PASSWORD      # Database root password
MYSQL_DATABASE           # Database name
MYSQL_USER              # Database user
MYSQL_PASSWORD          # Database password
SECRET_KEY              # Flask session key
CLIENT_ID               # Azure AD app ID
CLIENT_SECRET           # Azure AD app secret
```

### Production Security

See: `DEPLOYMENT_GUIDE.md` → "Security Considerations" section

---

## 🐛 Troubleshooting

### Services Won't Start

```powershell
# Check logs
docker-compose logs

# Verify .env file exists
Test-Path .env

# Verify Docker daemon is running
docker ps
```

### Connection Errors

```powershell
# Check Flask can reach Web API
docker exec finance-ui curl http://web-api:8080/health

# Check Web API can reach MySQL
docker exec finance-api ping mysql
```

### Port Already in Use

```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process or change HOST_PORT in .env
```

### Data Not Persisting

```powershell
# Verify volume exists
docker volume ls | findstr finance_data

# Verify volume mount in container
docker inspect finance-mysql | findstr -A 5 Mounts
```

For more help: See `DEPLOYMENT_GUIDE.md` → "Troubleshooting" section

---

## 📈 Next Steps

1. **Review Documentation** (20 min)
   - `QUICKSTART.md` - Overview
   - `ARCHITECTURE.md` - Design details

2. **Configure Environment** (5 min)
   - Copy `.env.example` → `.env`
   - Fill in your credentials

3. **Build & Deploy** (5 min)
   - `docker-compose build`
   - `docker-compose up -d`

4. **Verify Setup** (2 min)
   - `docker-compose ps`
   - Test endpoints

5. **Migrate Data** (5-30 min, if needed)
   - See `DATA_MIGRATION.md`

6. **Production Deployment** (as needed)
   - See `DEPLOYMENT_GUIDE.md`

---

## 📞 Documentation Index

| Document                    | Purpose                  | Time   |
| --------------------------- | ------------------------ | ------ |
| **QUICKSTART.md**           | Get running in 5 minutes | 5 min  |
| **ARCHITECTURE.md**         | Understand the design    | 20 min |
| **DEPLOYMENT_GUIDE.md**     | Production deployment    | 30 min |
| **DATA_MIGRATION.md**       | Migrate from SQLite      | 15 min |
| **REFACTORING_COMPLETE.md** | See what changed         | 10 min |
| **DELIVERABLES.md**         | Complete checklist       | 10 min |

---

## ✨ What Makes This Architecture Great

| Feature                | Benefit                       |
| ---------------------- | ----------------------------- |
| **Three-Tier**         | Scalability & maintainability |
| **Containerized**      | Consistency & portability     |
| **Microservices**      | Independent deployment        |
| **Health Checks**      | Reliability & monitoring      |
| **Data Persistence**   | Information safety            |
| **Internal DNS**       | Simplified configuration      |
| **Multi-stage Builds** | Optimized image sizes         |
| **Documentation**      | Easy onboarding               |

---

## 🎯 Success Criteria

When everything works:

```
✅ docker-compose ps
   All services: Up (healthy)

✅ curl http://localhost:5000
   Flask UI responds: 200 OK

✅ curl http://localhost:8080/health
   Web API responds: 200 OK + JSON

✅ docker exec finance-mysql ...
   MySQL responds: Successfully

✅ Data persists
   After restart, data unchanged

✅ Services communicate
   Flask → API → Database works
```

---

## 🚀 You're Ready!

This refactored three-tier architecture is:

- ✅ Fully documented
- ✅ Production ready
- ✅ Easily deployable
- ✅ Scalable & maintainable
- ✅ Industry best practices

**Start with**: `QUICKSTART.md`

---

**Status**: ✅ Production Ready  
**Version**: 3.0  
**Last Updated**: 2024

Need help? See the relevant documentation file above.
