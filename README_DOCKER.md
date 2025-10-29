# Docker Deployment Guide

## Quick Start

```bash
# 1. Copy environment example
cp .env.example .env

# 2. Edit .env with your configuration
# Important: Set POSTGRES_PASSWORD and SECRET_KEY

# 3. Start all services
docker-compose up -d

# 4. Initialize database (first time only)
docker-compose exec backend python init_db.py

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## Environment Variables

All configuration is done through `.env` file. Key variables:

- **POSTGRES_PASSWORD**: Database password (REQUIRED)
- **SECRET_KEY**: Application secret (REQUIRED - generate a strong one)
- **GOOGLE_AI_API_KEY**: For AI grading features
- **NEXT_PUBLIC_API_URL**: Public backend URL (for browser requests)
- **ALLOWED_ORIGINS**: CORS allowed origins

See `.env.example` for all available options.

## Services

- **postgres**: PostgreSQL 15 database
- **backend**: FastAPI application (port 8000)
- **frontend**: Next.js application (port 3000)

## Network

All services communicate via `smartgrade-network` bridge network. Frontend can reach backend at `http://backend:8000` internally.

## Volumes

- **postgres_data**: Database persistence
- **uploads_volume**: Uploaded files storage

## Production Deployment

For production:

1. Set `ENVIRONMENT=production` and `DEBUG=false`
2. Use strong passwords and secret keys
3. Configure `FRONTEND_HOST` with your domain
4. Set `NEXT_PUBLIC_API_URL` to your public backend URL
5. Configure `ALLOWED_ORIGINS` with your domain(s)
6. Use reverse proxy (Nginx/Traefik) with SSL

See `DEPLOYMENT.md` for detailed production setup.


