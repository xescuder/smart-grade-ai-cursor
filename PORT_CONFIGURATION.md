# Port Configuration Guide

## Overview

Both frontend and backend ports are now configurable through environment variables, following twelve-factor app principles.

## Backend Configuration

### Environment Variables

Edit `backend/.env`:

```env
# Backend API server
HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend server (for CORS)
FRONTEND_PORT=3000
FRONTEND_HOST=localhost

# CORS will auto-include frontend URLs
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_PORT` | 8000 | Port for backend API server |
| `FRONTEND_PORT` | 3000 | Port for frontend (used in CORS) |
| `FRONTEND_HOST` | localhost | Frontend hostname |
| `HOST` | 0.0.0.0 | Backend bind address |

### Computed Properties

The configuration includes helpful computed properties:

```python
from core.config import settings

# Full URLs
settings.backend_url   # http://0.0.0.0:8000
settings.frontend_url  # http://localhost:3000

# Auto-generated CORS origins (includes frontend port)
settings.cors_origins_list  # ['http://localhost:3000', 'http://127.0.0.1:3000', ...]
```

## Frontend Configuration

### Setup

1. **Create environment file:**
   ```bash
   cd frontend
   cp env.example.txt .env.local
   ```

2. **Edit `.env.local`:**
   ```env
   PORT=3000
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
   ```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 3000 | Next.js dev server port |
| `NEXT_PUBLIC_API_URL` | http://localhost:8000 | Backend API base URL |
| `NEXT_PUBLIC_API_BASE_URL` | http://localhost:8000/api/v1 | Backend API v1 endpoint |

## Common Scenarios

### Scenario 1: Default Configuration
**Backend**: Port 8000  
**Frontend**: Port 3000

```env
# backend/.env
BACKEND_PORT=8000
FRONTEND_PORT=3000

# frontend/.env.local
PORT=3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Scenario 2: Custom Ports
**Backend**: Port 9000  
**Frontend**: Port 4000

```env
# backend/.env
BACKEND_PORT=9000
FRONTEND_PORT=4000
ALLOWED_ORIGINS=http://localhost:4000,http://127.0.0.1:4000

# frontend/.env.local
PORT=4000
NEXT_PUBLIC_API_URL=http://localhost:9000
NEXT_PUBLIC_API_BASE_URL=http://localhost:9000/api/v1
```

### Scenario 3: Production Deployment
**Backend**: Port 8000 (behind nginx)  
**Frontend**: Port 3000 (behind nginx)

```env
# backend/.env
BACKEND_PORT=8000
FRONTEND_PORT=3000
FRONTEND_HOST=yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com

# frontend/.env.local (production)
PORT=3000
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com/api/v1
NODE_ENV=production
```

### Scenario 4: Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - BACKEND_PORT=8000
      - FRONTEND_PORT=3000
      - FRONTEND_HOST=frontend
      - ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000
    ports:
      - "8000:8000"
  
  frontend:
    build: ./frontend
    environment:
      - PORT=3000
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

## Starting the Application

### Backend

```bash
cd backend

# Start with configured port
python3 db_server.py

# Or with uvicorn for reload
uvicorn db_server:app --host 0.0.0.0 --port $BACKEND_PORT --reload
```

Server will display:
```
🚀 Starting Smart Grade AI Backend
   Backend:  http://0.0.0.0:8000
   Frontend: http://localhost:3000
   CORS Origins: 2 configured
```

### Frontend

```bash
cd frontend

# Install dependencies (first time)
npm install

# Start development server (uses PORT from .env.local)
npm run dev

# Or specify port manually
PORT=3000 npm run dev
```

## Verification

### Check Backend Configuration

```bash
cd backend
python3 -c "from core.config import settings; \
  print('Backend Port:', settings.BACKEND_PORT); \
  print('Frontend Port:', settings.FRONTEND_PORT); \
  print('Backend URL:', settings.backend_url); \
  print('Frontend URL:', settings.frontend_url); \
  print('CORS Origins:', settings.cors_origins_list)"
```

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# API root
curl http://localhost:8000/api/v1/assignments
```

### Test Frontend

```bash
# Frontend should be accessible at configured port
curl http://localhost:3000

# Or open in browser
open http://localhost:3000
```

## CORS Configuration

The backend automatically configures CORS origins based on `FRONTEND_PORT`:

```python
# Automatically included in CORS origins:
- http://localhost:{FRONTEND_PORT}
- http://127.0.0.1:{FRONTEND_PORT}
- http://{FRONTEND_HOST}:{FRONTEND_PORT}
```

### Manual CORS Override

If you need additional origins:

```env
# backend/.env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:4000,https://app.example.com
```

## Troubleshooting

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
# Edit backend/.env
BACKEND_PORT=8001
```

### CORS Errors

**Error**: `Access to fetch at 'http://localhost:8000' has been blocked by CORS policy`

**Solution**:
1. Check `FRONTEND_PORT` in `backend/.env` matches your frontend port
2. Verify `ALLOWED_ORIGINS` includes your frontend URL
3. Restart backend server after changing configuration

### Frontend Can't Connect to Backend

**Issue**: API calls fail with network errors

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local`
3. Ensure ports match between backend and frontend config

## Configuration Files Summary

### Backend
- **Template**: `backend/env.example`
- **Active**: `backend/.env`
- **Configuration**: `backend/core/config.py`

### Frontend
- **Template**: `frontend/env.example.txt`
- **Active**: `frontend/.env.local`
- **Next.js**: Automatically reads `.env.local`

## Environment-Specific Configs

### Development
```env
# backend/.env
BACKEND_PORT=8000
DEBUG=true
ENVIRONMENT=development

# frontend/.env.local
PORT=3000
NODE_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Staging
```env
# backend/.env
BACKEND_PORT=8000
DEBUG=false
ENVIRONMENT=staging
FRONTEND_HOST=staging.yourdomain.com

# frontend/.env.local
PORT=3000
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api-staging.yourdomain.com
```

### Production
```env
# backend/.env
BACKEND_PORT=8000
DEBUG=false
ENVIRONMENT=production
FRONTEND_HOST=yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com

# frontend/.env.local
PORT=3000
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## Quick Reference

### Change Backend Port
```bash
# Edit backend/.env
BACKEND_PORT=9000

# Restart server
cd backend && python3 db_server.py
```

### Change Frontend Port
```bash
# Edit frontend/.env.local
PORT=4000

# Also update backend CORS
# Edit backend/.env
FRONTEND_PORT=4000

# Restart both servers
```

### View Current Configuration
```bash
# Backend
cd backend && python3 -c "from core.config import settings; print(f'Backend: {settings.BACKEND_PORT}, Frontend: {settings.FRONTEND_PORT}')"

# Frontend
cd frontend && cat .env.local | grep PORT
```

---

**Configuration Status**: ✅ COMPLETE  
**Backend Port**: Configurable via `BACKEND_PORT`  
**Frontend Port**: Configurable via `FRONTEND_PORT` & `PORT`  
**CORS**: Auto-configured from frontend port  
**Date**: October 14, 2025

