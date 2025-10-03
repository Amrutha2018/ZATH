# 🖥️ **Environment Setup Guide**

## **📋 Overview**

ZATH now supports separate configurations for:

- **🖥️ Mac Development** - Local development with hot reload
- **🚀 Server Production** - Production deployment with server IP

## **🏗️ File Structure**

```
ZATH/
├── docker-compose.yml          # Base configuration
├── docker-compose.dev.yml      # Development overrides (Mac)
├── docker-compose.prod.yml     # Production overrides (Server)
├── dev.sh                      # Development startup script
├── prod.sh                     # Production startup script
└── ENVIRONMENT_SETUP.md        # This guide
```

## **🖥️ Mac Development Setup**

### **Quick Start:**

```bash
# Make scripts executable
chmod +x dev.sh prod.sh

# Start development environment
./dev.sh
```

### **Manual Commands:**

```bash
# Start development
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Stop development
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

### **Development Features:**

- ✅ **Hot reload** - Code changes reflect immediately
- ✅ **Localhost URLs** - Easy browser access
- ✅ **Volume mounts** - Live code editing
- ✅ **Development environment** - Debug-friendly settings

### **Access URLs:**

- **Frontend**: `http://localhost:3001`
- **API**: `http://localhost:8001`
- **API Docs**: `http://localhost:8001/docs`

## **🚀 Server Production Setup**

### **Quick Start:**

```bash
# Set your server IP (optional, defaults to 31.97.229.227)
export SERVER_IP=your-server-ip

# Start production environment
./prod.sh
```

### **Manual Commands:**

```bash
# Start production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Stop production
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

### **Production Features:**

- ✅ **Production environment** - Optimized settings
- ✅ **Server IP URLs** - External access configured
- ✅ **Restart policies** - Automatic recovery
- ✅ **Security settings** - Production-ready

### **Access URLs:**

- **Frontend**: `http://your-server-ip:3001`
- **API**: `http://your-server-ip:8001`
- **API Docs**: `http://your-server-ip:8001/docs`

## **🔧 Configuration Differences**

### **Development (Mac):**

```yaml
# docker-compose.dev.yml
services:
  zathfrontend:
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8001
      - NODE_ENV=development
    volumes:
      - ./zath_frontend:/app
      - /app/node_modules
      - /app/.next # Exclude build cache
```

### **Production (Server):**

```yaml
# docker-compose.prod.yml
services:
  zathfrontend:
    environment:
      - NEXT_PUBLIC_API_URL=http://${SERVER_IP:-31.97.229.227}:8001
      - NODE_ENV=production
    volumes:
      - ./zath_frontend:/app
      - /app/node_modules
```

## **🔄 Switching Environments**

### **From Development to Production:**

```bash
# Stop development
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# Start production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### **From Production to Development:**

```bash
# Stop production
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Start development
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## **🔍 Troubleshooting**

### **Common Issues:**

1. **Port Conflicts:**

   ```bash
   # Check what's using the ports
   lsof -i :3001
   lsof -i :8001
   ```

2. **Environment Variables:**

   ```bash
   # Check environment
   docker compose -f docker-compose.yml -f docker-compose.prod.yml config
   ```

3. **Service Logs:**
   ```bash
   # View specific service logs
   docker compose -f docker-compose.yml -f docker-compose.dev.yml logs zathapi
   docker compose -f docker-compose.yml -f docker-compose.prod.yml logs zathfrontend
   ```

### **Reset Everything:**

```bash
# Stop all containers
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Remove all containers and volumes
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v

# Rebuild from scratch
./dev.sh  # or ./prod.sh
```

## **📝 Environment Variables**

### **Development (.env):**

```env
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=zathdb
DB_USER=zathuser
DB_PASSWORD=zathpass

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# JWT
JWT_SECRET_KEY=dev-secret-key
```

### **Production (.env):**

```env
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=zathdb
DB_USER=zathuser
DB_PASSWORD=secure-production-password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# JWT
JWT_SECRET_KEY=your-secure-production-secret-key

# Server
SERVER_IP=31.97.229.227
```

## **🎯 Best Practices**

### **Development:**

- ✅ Use `./dev.sh` for quick startup
- ✅ Keep hot reload enabled
- ✅ Use localhost URLs
- ✅ Enable debug logging

### **Production:**

- ✅ Use `./prod.sh` for deployment
- ✅ Set secure passwords
- ✅ Use environment variables for IP
- ✅ Enable restart policies
- ✅ Monitor logs regularly

## **🚀 Quick Commands Reference**

| **Action** | **Development**                                                          | **Production**                                                            |
| ---------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| **Start**  | `./dev.sh`                                                               | `./prod.sh`                                                               |
| **Stop**   | `docker compose -f docker-compose.yml -f docker-compose.dev.yml down`    | `docker compose -f docker-compose.yml -f docker-compose.prod.yml down`    |
| **Logs**   | `docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f` | `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f` |
| **Status** | `docker compose -f docker-compose.yml -f docker-compose.dev.yml ps`      | `docker compose -f docker-compose.yml -f docker-compose.prod.yml ps`      |

---

**🎉 Now you can easily switch between development and production environments!**
