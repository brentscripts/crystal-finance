# Crystal Finance - Three-Tier Microservice Architecture

## 🏗️ Architecture Overview

This repository implements a **three-tier microservice architecture** with containerized services orchestrated by Docker Compose:

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER BRIDGE NETWORK                    │
│                      (finance-network)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐   ┌──────────────────┐   ┌─────────┐│
│  │   FRONTEND       │   │   WEB API        │   │ MySQL  ││
│  │  Flask UI        │──→│  C# .NET         │──→│Database││
│  │                  │   │                  │   │        ││
│  │ • Python 3.12    │   │ • .NET 10.0      │   │ 8.0    ││
│  │ • Alpine Linux   │   │ • Health Check   │   │ Stores ││
│  │ • Gunicorn       │   │ • JWT Auth       │   │ Data   ││
│  │ • Port 5000      │   │ • Dapper ORM     │   │        ││
│  │                  │   │ • Port 8080      │   │Port3306││
│  └──────────────────┘   └──────────────────┘   └─────────┘│
│          ↑                      ↑                    ↑      │
│          └──────────────────────┴────────────────────┘      │
│                   Internal DNS Resolution                  │
│   (flask-ui, web-api, mysql service names)                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↑
                    HOST PORTS (External Access)
              5000: Flask UI
              8080: Web API
              3306: MySQL
```

---

## 📂 Repository Structure

```
crystal-finance/
├── docker-compose.yml           # Orchestrates all three services
├── .dockerignore                # Optimizes Docker build context
├── .env                         # Environment configuration (not in git)
├── .env.example                 # Template for .env
├── DEPLOYMENT_GUIDE.md          # Step-by-step deployment instructions
├── DATA_MIGRATION.md            # SQLite to MySQL migration strategies
├── ARCHITECTURE.md              # This file
│
├── frontend/                    # Tier 1: Flask UI
│   ├── Dockerfile               # Alpine-based Python image
│   ├── requirements.txt          # Python dependencies
│   ├── webapp/
│   │   ├── app.py               # Flask application entry point
│   │   ├── templates/           # Jinja2 HTML templates
│   │   │   ├── index.html
│   │   │   ├── dashboard.html
│   │   │   └── ...
│   │   ├── static/              # CSS, JavaScript, images
│   │   │   ├── style.css
│   │   │   ├── dashboard.js
│   │   │   └── ...
│   │   └── __init__.py
│   └── tests/
│       ├── test_app.py
│       └── ...
│
├── src/                         # Tier 2: C# Web API
│   ├── CrystalFinance.sln       # Visual Studio solution
│   ├── CrystalFinance.Api/      # Main API project
│   │   ├── Dockerfile           # Multi-stage .NET build
│   │   ├── Program.cs           # Application entry point
│   │   ├── appsettings.json     # Configuration
│   │   ├── Controllers/
│   │   │   ├── TransactionsController.cs
│   │   │   └── CrystalFinanceController.cs
│   │   ├── HealthChecks/        # Health check implementations
│   │   ├── Startup/             # DI, CORS, OpenAPI config
│   │   └── Properties/
│   │       └── launchSettings.json
│   ├── CrystalFinanceLibrary/   # Shared C# logic
│   │   ├── Models/
│   │   ├── DataAccess/
│   │   ├── Logic/
│   │   └── ...
│   └── CrystalFinance.Tests/    # Unit tests
│       └── ...
│
└── mysql/                       # Tier 3: MySQL Database
    └── init.sql                 # Database initialization script
```

---

## 🔄 Data Flow

### Request Flow: User → API → Database

```
1. User accesses Flask UI (http://localhost:5000)
   ↓
2. Flask app receives request
   ↓
3. Flask makes HTTP request to Web API (internal: http://web-api:8080)
   ↓
4. Web API receives request, validates JWT/auth
   ↓
5. Web API queries MySQL using Dapper ORM
   ↓
6. MySQL executes query, returns results
   ↓
7. Web API processes results, returns JSON response
   ↓
8. Flask receives response, renders template
   ↓
9. User receives HTML page
```

---

## 🌐 Service Communication

### Internal DNS Names (Inside Docker Network)

Services communicate using container names as hostnames:

| Service  | Internal URL | Port | Use             |
| -------- | ------------ | ---- | --------------- |
| MySQL    | `mysql`      | 3306 | Database access |
| Web API  | `web-api`    | 8080 | API endpoints   |
| Flask UI | `flask-ui`   | 5000 | Web interface   |

### Configuration

**Flask UI** (`frontend/webapp/app.py`):

```python
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5001')
# Set by docker-compose: http://web-api:8080
```

**Web API** (`src/CrystalFinance.Api/Program.cs`):

```csharp
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
// Set by docker-compose: Server=mysql;Database=...;Uid=...;Pwd=...;
```

---

## 🐳 Docker Containers

### 1. Flask UI Container (`finance-ui`)

- **Base Image**: `python:3.12-alpine`
- **Size**: ~200-300 MB
- **Port**: 5000 (external), 5000 (internal)
- **Health Check**: HTTP GET `/` every 30 seconds
- **Command**: `gunicorn --workers=2 --bind 0.0.0.0:5000 webapp.app:app`

**Environment Variables**:

- `API_BASE_URL=http://web-api:8080`
- `API_TIMEOUT=10`
- `SECRET_KEY=<from .env>`
- Azure AD configuration (CLIENT_ID, CLIENT_SECRET, etc.)

### 2. Web API Container (`finance-api`)

- **Base Image**: `mcr.microsoft.com/dotnet/aspnet:10.0`
- **Size**: ~200-400 MB (multi-stage optimized)
- **Port**: 8080 (external), 8080 (internal)
- **Health Check**: HTTP GET `/health` every 30 seconds
- **Command**: `dotnet CrystalFinance.Api.dll`

**Build Process** (Multi-stage):

1. **Builder Stage**: Compiles C# code in SDK image
2. **Runtime Stage**: Copies only compiled artifacts to runtime image

**Environment Variables**:

- `ConnectionStrings__DefaultConnection=Server=mysql;...`
- `ASPNETCORE_ENVIRONMENT=Production`
- `ASPNETCORE_URLS=http://+:8080`

### 3. MySQL Container (`finance-mysql`)

- **Base Image**: `mysql:8`
- **Size**: ~500 MB-2 GB (depends on data)
- **Port**: 3306 (external), 3306 (internal)
- **Storage**: Docker volume `finance_data` (persistent)
- **Health Check**: MySQL health check probe every 10 seconds
- **Initialization**: `./mysql/init.sql` runs on first startup

**Environment Variables**:

- `MYSQL_ROOT_PASSWORD=<from .env>`
- `MYSQL_DATABASE=<from .env>`
- `MYSQL_USER=<from .env>`
- `MYSQL_PASSWORD=<from .env>`

---

## 📋 Dockerfile Details

### C# Web API - Multi-Stage Dockerfile

**Stage 1 (Builder)**:

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS builder
# Restore dependencies
# Build application
# Publish to /app/publish
```

**Stage 2 (Runtime)**:

```dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
# Copy only compiled artifacts from builder
# Reduces final image size significantly
```

**Benefits**:

- ✅ Small image size (~200 MB vs ~600 MB)
- ✅ Faster deployment
- ✅ No compilation dependencies in production image
- ✅ Better security (source code not included)

### Flask UI - Single-Stage Dockerfile

Uses `python:3.12-alpine` for minimal size:

- ✅ Alpine Linux: ~150 MB base image
- ✅ Only production dependencies installed
- ✅ Gunicorn as production WSGI server

---

## ♻️ Environment Configuration

### .env File Structure

```env
# MySQL
MYSQL_ROOT_PASSWORD=secure_password
MYSQL_DATABASE=finance
MYSQL_USER=financeuser
MYSQL_PASSWORD=secure_password
HOST_PORT=3306

# Flask
SECRET_KEY=generated_secure_key
FLASK_ENV=production

# Azure AD
CLIENT_ID=azure_app_id
CLIENT_SECRET=azure_app_secret
AUTHORITY=https://login.microsoftonline.com/tenant_id
REDIRECT_URI=http://localhost:5000/getAToken
AZURE_TENANT=tenant_id
```

### Environment Variable Injection

1. **Via .env file**: `docker-compose` loads `.env` automatically
2. **Via docker-compose.yml**: `environment:` section overrides
3. **Via env_file**: `flask-ui` service uses `env_file: - .env`

---

## 🔗 Docker Networking

### Bridge Network: `finance-network`

- **Type**: Bridge driver (default)
- **Scope**: All three services connected
- **DNS**: Docker embedded DNS resolves service names
- **Isolation**: Network isolated from host by default

**Service Discovery**:

- Container A resolves `web-api` to Web API container's IP
- Container B resolves `mysql` to MySQL container's IP
- Automatic IP assignment and load balancing

---

## 📊 Docker Volumes

### Volume: `finance_data`

- **Type**: Named volume (managed by Docker)
- **Attached to**: MySQL container
- **Mount Path**: `/var/lib/mysql`
- **Persistence**: Data survives container restart

**Location**:

- Windows: `C:\ProgramData\Docker\volumes\finance_data\_data`
- Linux: `/var/lib/docker/volumes/finance_data/_data`
- macOS: `~/Library/Containers/com.docker.docker/Data/vms/0/data/volumes`

**Backup**:

```powershell
docker cp finance-mysql:/var/lib/mysql ./mysql_backup
```

---

## ✅ Health Checks

Each service includes a health check for reliability:

### Flask UI Health Check

- **Type**: HTTP GET request
- **URL**: `http://localhost:5000`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Expected**: 200 OK status

### Web API Health Check

- **Type**: HTTP GET request
- **URL**: `http://localhost:8080/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Expected**: 200 OK + health status JSON

### MySQL Health Check

- **Type**: Shell command (mysql CLI)
- **Command**: `mysql -h 127.0.0.1 -u root -p$MYSQL_ROOT_PASSWORD -e 'SELECT 1'`
- **Interval**: 10 seconds
- **Timeout**: 5 seconds
- **Expected**: Command succeeds (exit code 0)

**Dependency Chain**:

- Flask UI depends on Web API being healthy
- Web API depends on MySQL being healthy
- Ensures services start in correct order

---

## 🚀 Service Startup Sequence

```
1. Docker Compose starts MySQL container
   ↓
2. MySQL performs initialization (init.sql)
   ↓
3. MySQL health check succeeds
   ↓
4. Docker Compose starts Web API container
   ↓
5. Web API initializes, connects to MySQL
   ↓
6. Web API health check succeeds
   ↓
7. Docker Compose starts Flask UI container
   ↓
8. Flask UI initializes, connects to Web API
   ↓
9. Flask UI health check succeeds
   ↓
10. All services ready (docker-compose up completes)
```

---

## 🔐 Security Architecture

### Network Isolation

- MySQL only accessible from Web API (internal network)
- Flask UI only accessible from external world on port 5000
- All internal communication encrypted by TLS (optional setup)

### Authentication

1. **External Users** → Azure AD (MSAL) via Flask UI
2. **Flask UI** → Web API (JWT or API Key)
3. **Web API** → MySQL (Encrypted password in connection string)

### Best Practices

- [ ] Never commit `.env` to Git (use `.env.example`)
- [ ] Use strong, unique passwords for production
- [ ] Rotate secrets regularly
- [ ] Enable HTTPS for production (reverse proxy)
- [ ] Use Azure Key Vault for secret management
- [ ] Implement API rate limiting
- [ ] Log all API requests

---

## 📈 Scaling Considerations

### Horizontal Scaling

**Flask UI**:

```yaml
flask-ui:
  deploy:
    replicas: 3 # Run 3 instances
```

**Web API**:

```yaml
web-api:
  deploy:
    replicas: 2 # Run 2 instances
```

**Load Balancing**: Use reverse proxy (Nginx, Caddy, Traefik)

### Vertical Scaling

Adjust resource limits:

```yaml
services:
  web-api:
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 1G
```

---

## 🔄 CI/CD Integration

### Build Pipeline

```
1. Code Push → GitHub
2. GitHub Actions triggered
3. Build: docker build web-api
4. Test: pytest, xunit
5. Push: docker push registry.example.com/web-api:latest
6. Deploy: docker-compose pull && docker-compose up -d
```

### Dockerfile Considerations

- ✅ Multi-stage builds (C# API)
- ✅ Layer caching optimization
- ✅ Minimal base images (Alpine Linux)
- ✅ Health checks included
- ✅ Non-root user execution (optional)

---

## 📚 Related Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Step-by-step deployment
- [Data Migration Guide](DATA_MIGRATION.md) - SQLite to MySQL migration
- [Flask Frontend Architecture](frontend/FRONTEND_ARCHITECTURE.md)
- [Frontend Migration Guide](frontend/MIGRATION_GUIDE.md)

---

## 🛠️ Quick Commands

```powershell
# Build all images
docker-compose build

# Start services
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f

# Execute command in container
docker exec -it finance-api dotnet --version

# Access MySQL CLI
docker exec -it finance-mysql mysql -u root -p

# Stop services
docker-compose stop

# Clean up everything
docker-compose down -v
```

---

## 📊 Performance Metrics

| Component | Memory         | CPU        | Disk         |
| --------- | -------------- | ---------- | ------------ |
| Flask UI  | 50-100 MB      | 5-10%      | 200 MB image |
| Web API   | 100-200 MB     | 10-20%     | 200 MB image |
| MySQL     | 100-500 MB     | 5-15%      | 500 MB+ data |
| **Total** | **250-800 MB** | **20-45%** | **900 MB+**  |

---

## 🎯 Success Criteria

- ✅ All three containers start successfully
- ✅ Health checks pass
- ✅ Flask UI accessible at `http://localhost:5000`
- ✅ Web API accessible at `http://localhost:8080/health`
- ✅ MySQL accessible via Web API
- ✅ Data persists across container restarts
- ✅ Azure AD authentication works
- ✅ API requests from Flask to Web API successful

---

**Architecture Version**: 3.0  
**Status**: Production Ready  
**Last Updated**: 2024
