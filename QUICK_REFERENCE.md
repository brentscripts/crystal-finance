# 🎯 Crystal Finance - Quick Reference Card

## ⚡ Emergency Quick Commands

```powershell
# Start everything
docker-compose build && docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything (keeps data)
docker-compose stop

# Clean up everything (deletes data!)
docker-compose down -v

# Restart after code changes
docker-compose restart web-api
```

---

## 🌐 Access Services

| Service  | URL                          | Purpose        |
| -------- | ---------------------------- | -------------- |
| Flask UI | http://localhost:5000        | User interface |
| Web API  | http://localhost:8080/health | Health check   |
| MySQL    | localhost:3306               | Database       |

---

## 📋 File Locations

```
📄 Configuration
   .env                          Your credentials
   .env.example                  Template

🐳 Docker
   docker-compose.yml            Services
   .dockerignore                 Build optimization

🐳 Dockerfiles
   frontend/Dockerfile           Flask UI
   src/CrystalFinance.Api/Dockerfile    Web API (NEW)

📚 Documentation
   START_HERE.md                 ← Begin here!
   QUICKSTART.md                 5-minute setup
   ARCHITECTURE.md               Design details
   DEPLOYMENT_GUIDE.md           Production ops
   DATA_MIGRATION.md             SQLite→MySQL
```

---

## 🔄 Common Tasks

### View Logs

```powershell
docker-compose logs -f              # All services
docker-compose logs -f web-api      # Specific service
docker-compose logs --tail=100      # Last 100 lines
```

### Access Database

```powershell
docker exec -it finance-mysql mysql -u root -p
# Inside MySQL: SELECT * FROM transactions;
```

### Execute Commands

```powershell
docker exec -it finance-ui python --version
docker exec -it finance-api dotnet --version
docker exec -it finance-mysql mysql --version
```

### Test Connectivity

```powershell
# Flask → Web API
docker exec finance-ui curl http://web-api:8080/health

# Web API → MySQL
docker exec finance-api ping mysql

# Host → Flask UI
curl http://localhost:5000
```

---

## 🔧 Troubleshooting

### Services Won't Start

```
✅ Check: docker-compose ps
✅ Check: .env file exists
✅ Check: Ports not in use (netstat -ano)
✅ Check: Logs (docker-compose logs)
```

### Connection Refused

```
✅ Check: Service is running (docker-compose ps)
✅ Check: Wait longer (services starting)
✅ Check: Service logs (docker-compose logs web-api)
✅ Check: Port mapped correctly
```

### Database Errors

```
✅ Check: MySQL is healthy (docker-compose ps)
✅ Check: Credentials in .env
✅ Check: Connection string in docker-compose.yml
✅ Check: MySQL logs (docker-compose logs mysql)
```

---

## 📊 Architecture Diagram

```
┌────────────────────────────────────────────┐
│         Docker Bridge Network              │
│       (finance-network internal)           │
├────────────────────────────────────────────┤
│                                            │
│  ┌──────────────┐  ┌──────────────┐      │
│  │  Flask UI    │─→│  Web API     │      │
│  │  :5000       │  │  :8080       │      │
│  └──────────────┘  └──────────────┘      │
│       ↓                  ↓                 │
│     Gunicorn          .NET 10             │
│     Python            Dapper              │
│     Alpine            Connection Pool     │
│                              ↓            │
│                        ┌──────────────┐   │
│                        │   MySQL      │   │
│                        │   :3306      │   │
│                        │              │   │
│                        │  Volume:     │   │
│                        │ finance_data │   │
│                        └──────────────┘   │
│                                            │
└────────────────────────────────────────────┘
      External Ports:
      5000, 8080, 3306
```

---

## 🔐 Security Quick Checklist

```
Development
☐ .env file configured
☐ Docker running
☐ Services starting

Production
☐ HTTPS enabled
☐ Secrets in Key Vault
☐ Strong passwords (20+ chars)
☐ Rate limiting enabled
☐ Audit logging enabled
☐ Base images updated
```

---

## 📈 Performance Tips

```
🚀 Build Faster
   • Use build cache: docker-compose build
   • Don't use: docker-compose build --no-cache

🚀 Images Smaller
   • Alpine Linux (already using)
   • Multi-stage builds (already using)
   • Optimize .dockerignore (already done)

🚀 Runtime Faster
   • Increase workers: gunicorn --workers=4
   • Thread pool: ThreadPool.SetMinThreads()
   • Connection pool: Min/Max pool settings
```

---

## 🎯 Success Indicators

All green? You're ready!

```
✅ docker-compose ps
   finance-mysql       Up (healthy)
   finance-api         Up (healthy)
   finance-ui          Up (healthy)

✅ curl http://localhost:5000
   Status: 200 OK
   Response: HTML page

✅ curl http://localhost:8080/health
   Status: 200 OK
   Response: JSON health info

✅ Data persists
   After restart, data still there

✅ No errors in logs
   docker-compose logs shows no errors
```

---

## 📞 Documentation Quick Links

```
Need...                    Read...
────────────────────────────────────────────
Quick setup                QUICKSTART.md
Architecture overview      ARCHITECTURE.md
Production deployment      DEPLOYMENT_GUIDE.md
Data migration             DATA_MIGRATION.md
What changed              REFACTORING_COMPLETE.md
Everything                DELIVERABLES.md
Navigation guide          README_ARCHITECTURE.md
THIS CARD                 START_HERE.md (this file)
```

---

## 🚀 Deployment Timeline

```
Total: ~20-45 minutes to production

5 min   Configure .env
3 min   Build images (docker-compose build)
1 min   Start services (docker-compose up -d)
2 min   Verify health (docker-compose ps + tests)
5-30min Migrate data (if needed)
────────────────────────
20-45min TOTAL
```

---

## 🔗 Service Internal URLs

These work INSIDE Docker containers:

```
MySQL:        mysql:3306
Web API:      web-api:8080
Flask UI:     flask-ui:5000

From Flask UI to Web API:
  http://web-api:8080/api/transactions

From Web API to MySQL:
  Server=mysql;Database=finance;...
```

---

## ⚙️ Environment Variables Summary

```
Database
MYSQL_ROOT_PASSWORD    # Root user password
MYSQL_DATABASE         # Database name
MYSQL_USER             # App user
MYSQL_PASSWORD         # App user password

Flask
SECRET_KEY             # Session encryption
FLASK_ENV              # development/production

Azure AD
CLIENT_ID              # Azure app ID
CLIENT_SECRET          # Azure app secret
AUTHORITY              # Token endpoint
REDIRECT_URI           # After login
AZURE_TENANT           # Tenant ID
```

---

## 🔄 Update/Rebuild

```
After Python code changes:
  docker-compose build flask-ui
  docker-compose restart flask-ui

After C# code changes:
  docker-compose build web-api
  docker-compose restart web-api

After schema changes:
  docker-compose down -v
  docker-compose up -d
```

---

## 💡 Pro Tips

```
1. Use named volumes
   → Data persists across restarts

2. Use health checks
   → Services start in correct order

3. Use bridge network
   → Internal DNS resolution

4. Use .env
   → Different configs per environment

5. Use multi-stage builds
   → 80% smaller images

6. Use .dockerignore
   → Faster builds

7. Use compose dependencies
   → Reliable startup order

8. Use persistent logs
   → Better debugging
```

---

## 📊 Container Resources

```
Typical Usage (Production)

Flask UI      50-100 MB memory    5-10% CPU
Web API       100-200 MB memory   10-20% CPU
MySQL         100-500 MB memory   5-15% CPU
────────────────────────────────────────
Total         250-800 MB memory   20-45% CPU

(Exact usage depends on data volume & traffic)
```

---

## 🎓 Learning Path

```
1. Read START_HERE.md (this file)           5 min
2. Read QUICKSTART.md                       5 min
3. Run docker-compose build                 3 min
4. Run docker-compose up -d                 1 min
5. Test services                            2 min
6. Read ARCHITECTURE.md                     20 min
7. Read DEPLOYMENT_GUIDE.md                 30 min
                                          ─────────
Total: ~65 minutes to full understanding
```

---

## ✨ What's Special About This Setup

```
✅ Multi-stage Docker builds
   Modern .NET image optimization

✅ Alpine Linux
   Minimal, secure base images

✅ Health checks
   Reliable service startup

✅ Named volumes
   Data persistence

✅ Internal DNS
   Simplified service discovery

✅ Production ready
   Out of the box

✅ Comprehensive docs
   2,100+ lines of guidance

✅ Best practices
   Industry standard setup
```

---

## 🆘 Emergency Help

```
PANIC?  Start here:
┌─────────────────────────────────────────┐
│ 1. docker-compose ps                    │
│ 2. docker-compose logs -f               │
│ 3. Check START_HERE.md                  │
│ 4. Check QUICKSTART.md                  │
│ 5. See DEPLOYMENT_GUIDE.md Troubleshooting
└─────────────────────────────────────────┘
```

---

## 📝 Notes

```
Remember:
- Never commit .env (it has secrets!)
- Always use docker-compose.ps to verify
- Check logs for actual errors
- Wait 30-60 seconds for cold startup
- Health checks take a few seconds
```

---

## 🎯 One-Liner Commands

```
# Full restart
docker-compose down -v && docker-compose build && docker-compose up -d

# Check everything
docker-compose ps && docker-compose logs --tail=5

# Emergency stop
docker-compose stop

# Full cleanup (⚠️ deletes data)
docker-compose down -v

# View specific service
docker-compose logs -f web-api | tail -50
```

---

**Quick Reference Version**: 1.0  
**Last Updated**: 2024  
**Status**: Production Ready

---

**👉 Start here**: `QUICKSTART.md` or `README_ARCHITECTURE.md`
