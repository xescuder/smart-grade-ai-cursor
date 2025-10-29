# Smart Grade AI - Deployment Guide

This guide covers deploying Smart Grade AI to a server using Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 4GB RAM
- 20GB free disk space

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd smart-grade-ai-cursor
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your production values
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database** (first time only)
   ```bash
   docker-compose exec backend python init_db.py
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Production Configuration

### Environment Variables

Key variables to configure in `.env`:

**Required:**
- `POSTGRES_PASSWORD`: Strong password for database
- `SECRET_KEY`: Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `GOOGLE_AI_API_KEY`: Your Google AI API key (for AI grading)

**Important for Production:**
- `ENVIRONMENT=production`
- `DEBUG=false`
- `FRONTEND_HOST`: Your domain name
- `ALLOWED_ORIGINS`: Your frontend domain(s)
- `NEXT_PUBLIC_API_URL`: Your backend API URL

### Example Production .env

```env
POSTGRES_PASSWORD=very-secure-password-123
SECRET_KEY=your-generated-secret-key-here
ENVIRONMENT=production
DEBUG=false
FRONTEND_HOST=smartgrade.yourdomain.com
ALLOWED_ORIGINS=https://smartgrade.yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com/api
GOOGLE_AI_API_KEY=your-actual-api-key
```

## Reverse Proxy Setup (Nginx)

For production, use Nginx as a reverse proxy:

```nginx
# Frontend
server {
    listen 80;
    server_name smartgrade.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Security Best Practices

1. **Use strong passwords** for PostgreSQL
2. **Generate secure SECRET_KEY**
3. **Enable HTTPS** with SSL certificates (Let's Encrypt)
4. **Restrict database access** - don't expose port 5432 publicly
5. **Regular backups** of the PostgreSQL volume
6. **Keep Docker images updated**

## Backup and Restore

### Backup Database

```bash
docker-compose exec postgres pg_dump -U smartgrade smartgrade_db > backup.sql
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U smartgrade smartgrade_db < backup.sql
```

### Backup Uploads

```bash
docker run --rm -v smartgrade_uploads_volume:/data -v $(pwd):/backup alpine tar czf /backup/uploads_backup.tar.gz /data
```

## Monitoring and Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Service Status

```bash
docker-compose ps
```

## Troubleshooting

### Database Connection Issues

Check database is healthy:
```bash
docker-compose ps postgres
```

Test connection:
```bash
docker-compose exec backend python -c "from database import async_engine; print('OK')"
```

### Frontend Can't Connect to Backend

1. Check `NEXT_PUBLIC_API_URL` in `.env`
2. Ensure backend is running: `docker-compose ps backend`
3. Check backend logs: `docker-compose logs backend`

### Port Conflicts

If ports 3000, 8000, or 5432 are in use, modify `.env`:
```env
FRONTEND_PORT=3001
BACKEND_PORT=8001
POSTGRES_PORT=5433
```

## Scaling

For higher traffic, consider:
- Using a managed PostgreSQL service
- Adding more backend instances
- Using a load balancer
- Implementing Redis for caching

## Maintenance

### Update Application

```bash
git pull
docker-compose build
docker-compose up -d
```

### Clean Up

```bash
# Remove unused images
docker system prune -a

# Reset everything (careful!)
docker-compose down -v
```

## Health Checks

Services include health checks. Monitor with:
```bash
docker-compose ps
```

All services should show "healthy" status.

## Support

For issues, check:
- Logs: `docker-compose logs`
- Database: `docker-compose exec postgres psql -U smartgrade -d smartgrade_db`
- Backend API: http://localhost:8000/docs


