# Port Configuration Changes Summary

## What Changed

### 1. Backend Environment Template (`backend/env.example`)

**Before:**
```env
HOST=0.0.0.0
PORT=8000
RELOAD=true
```

**After:**
```env
# Backend API server
HOST=0.0.0.0
BACKEND_PORT=8000
RELOAD=true

# Frontend server (for CORS and development)
FRONTEND_PORT=3000
FRONTEND_HOST=localhost
```

### 2. Backend Configuration (`backend/core/config.py`)

**Added:**
```python
# Backend API server
BACKEND_PORT: int = 8000
PORT: int = 8000  # Alias for backward compatibility

# Frontend server (for CORS and development)
FRONTEND_PORT: int = 3000
FRONTEND_HOST: str = "localhost"
```

**New Computed Properties:**
```python
@property
def backend_url(self) -> str:
    """Get the full backend URL"""
    return f"http://{self.HOST}:{self.BACKEND_PORT}"

@property
def frontend_url(self) -> str:
    """Get the full frontend URL"""
    return f"http://{self.FRONTEND_HOST}:{self.FRONTEND_PORT}"

@property
def cors_origins_list(self) -> List[str]:
    """Get CORS origins including frontend URL"""
    # Auto-includes frontend URLs in CORS
    origins = self.ALLOWED_ORIGINS
    frontend_urls = [
        f"http://localhost:{self.FRONTEND_PORT}",
        f"http://127.0.0.1:{self.FRONTEND_PORT}",
        self.frontend_url
    ]
    # Add unique frontend URLs
    for url in frontend_urls:
        if url not in origins:
            origins.append(url)
    return origins
```

### 3. Server Startup (`backend/db_server.py`)

**Before:**
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

**After:**
```python
if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting Smart Grade AI Backend")
    print(f"   Backend:  {settings.backend_url}")
    print(f"   Frontend: {settings.frontend_url}")
    print(f"   CORS Origins: {len(settings.cors_origins_list)} configured")
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.BACKEND_PORT,  # Uses BACKEND_PORT from .env
        log_level=settings.LOG_LEVEL.lower()
    )
```

### 4. CORS Configuration (`backend/db_server.py`)

**Before:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    ...
)
```

**After:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Auto-includes frontend URLs
    ...
)
```

### 5. Frontend Environment Template (NEW)

**Created:** `frontend/env.example.txt`
```env
# Port for Next.js development server
PORT=3000

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api

# Feature flags
NEXT_PUBLIC_ENABLE_AI_GRADING=true
NEXT_PUBLIC_ENABLE_PDF_VIEWER=true
```

## Benefits

### ✅ Centralized Port Management
- Single place to configure both frontend and backend ports
- Backend automatically knows frontend port for CORS

### ✅ Environment Flexibility
- Easy to switch ports for different environments
- No hardcoded port numbers in code

### ✅ Auto CORS Configuration
- Frontend URLs automatically added to CORS origins
- Based on FRONTEND_PORT and FRONTEND_HOST settings

### ✅ Clear Server Information
- Server displays configured URLs on startup
- Easy to verify configuration

## Usage Examples

### Change Backend Port

```bash
# Edit backend/.env
BACKEND_PORT=9000

# Restart server
cd backend && python3 db_server.py
```

### Change Frontend Port

```bash
# Edit backend/.env (for CORS)
FRONTEND_PORT=4000

# Edit frontend/.env.local
PORT=4000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Restart both servers
```

### Production Configuration

```env
# backend/.env
BACKEND_PORT=8000
FRONTEND_PORT=3000
FRONTEND_HOST=app.yourdomain.com
ALLOWED_ORIGINS=https://app.yourdomain.com

# frontend/.env.local
PORT=3000
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NODE_ENV=production
```

## Migration Guide

### For Existing Installations

1. **Update backend/.env:**
   ```bash
   cd backend
   # Add new variables
   echo "BACKEND_PORT=8000" >> .env
   echo "FRONTEND_PORT=3000" >> .env
   echo "FRONTEND_HOST=localhost" >> .env
   ```

2. **Create frontend/.env.local:**
   ```bash
   cd frontend
   cp env.example.txt .env.local
   # Edit as needed
   ```

3. **Restart servers:**
   ```bash
   # Backend
   cd backend && python3 db_server.py
   
   # Frontend
   cd frontend && npm run dev
   ```

## Backward Compatibility

The configuration maintains backward compatibility:

- `PORT` variable still exists as alias for `BACKEND_PORT`
- Existing `.env` files will work with defaults
- CORS origins can still be manually configured

## Testing

### Verify Configuration

```bash
cd backend
python3 -c "
from core.config import settings
print('Backend Port:', settings.BACKEND_PORT)
print('Frontend Port:', settings.FRONTEND_PORT)
print('Backend URL:', settings.backend_url)
print('Frontend URL:', settings.frontend_url)
print('CORS Origins:', settings.cors_origins_list)
"
```

### Test Server

```bash
# Start backend
cd backend && python3 db_server.py

# In another terminal, test
curl http://localhost:8000/health

# Should show server info on startup:
# 🚀 Starting Smart Grade AI Backend
#    Backend:  http://0.0.0.0:8000
#    Frontend: http://localhost:3000
#    CORS Origins: 2 configured
```

## Files Modified

1. ✅ `backend/env.example` - Added port variables
2. ✅ `backend/core/config.py` - Added port settings and properties
3. ✅ `backend/db_server.py` - Use BACKEND_PORT and CORS list
4. ✅ `backend/main.py` - Use BACKEND_PORT
5. ✅ `frontend/env.example.txt` - Created frontend template
6. ✅ `PORT_CONFIGURATION.md` - Complete documentation

## Summary

All port configuration is now centralized in environment files:

- **Backend**: `backend/.env` → `BACKEND_PORT`, `FRONTEND_PORT`
- **Frontend**: `frontend/.env.local` → `PORT`, `NEXT_PUBLIC_API_URL`

CORS is automatically configured based on frontend port settings, and server startup displays all configured URLs for easy verification.

---

**Status**: ✅ COMPLETE  
**Date**: October 14, 2025  
**Impact**: All servers use centralized port configuration


