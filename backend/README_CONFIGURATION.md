# Configuration Management - Quick Reference

This document provides a quick reference for the twelve-factor configuration implementation in Smart Grade AI.

## Quick Setup

```bash
# 1. Copy the environment template
cd backend
cp env.example .env

# 2. Edit your configuration
nano .env

# 3. Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 4. Update at minimum these values:
# - DATABASE_URL
# - SECRET_KEY
# - OLLAMA_BASE_URL (if using Ollama)
```

## Configuration Files

| File | Purpose |
|------|---------|
| `env.example` | Template with all available configuration options |
| `.env` | Your actual configuration (not committed to git) |
| `core/config.py` | Central configuration module |
| `CONFIGURATION_GUIDE.md` | Comprehensive configuration documentation |

## Key Configuration Settings

### Essential

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SECRET_KEY=<generated-secure-key>
```

### AI Services

```env
# Ollama (Local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=120

# OpenAI (Optional)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Anthropic (Optional)
ANTHROPIC_API_KEY=sk-ant-...
```

### Server

```env
HOST=0.0.0.0
PORT=8000
DEBUG=false
ENVIRONMENT=production
```

## Usage in Code

```python
# Import settings
from core.config import settings

# Access configuration
print(settings.OLLAMA_BASE_URL)
print(settings.DATABASE_URL)
print(settings.MAX_FILE_SIZE)

# Use computed properties
response = requests.get(settings.ollama_api_tags_url)
```

## Migration Summary

All hardcoded configuration values have been moved to centralized settings:

### Before (Hardcoded)

```python
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama2"
DATABASE_URL = "postgresql+asyncpg://..."
UPLOAD_DIR = "uploads"
```

### After (Centralized)

```python
from core.config import settings

OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL
# Database.py uses settings.DATABASE_URL directly
UPLOAD_DIR = settings.UPLOAD_DIR
```

## Files Updated

1. ✅ `core/config.py` - Comprehensive settings class
2. ✅ `services/ai_service.py` - Uses settings for Ollama config
3. ✅ `database.py` - Uses settings for DB connection
4. ✅ `main.py` - Uses settings for server config
5. ✅ `api/routers/submissions.py` - Uses settings for upload dir
6. ✅ `db_server.py` - Uses settings throughout

## Environment-Specific Configuration

### Development

```env
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_ECHO=true
RELOAD=true
```

### Production

```env
DEBUG=false
LOG_LEVEL=INFO
DATABASE_ECHO=false
RELOAD=false
SECRET_KEY=<strong-random-key>
```

## Validation

Configuration is validated at startup using Pydantic:

```python
class Settings(BaseSettings):
    PORT: int = 8000              # Must be integer
    DEBUG: bool = False           # Must be boolean
    ALLOWED_ORIGINS: List[str]    # Must be list
```

Invalid values will raise clear error messages.

## Security Checklist

- [ ] `.env` is in `.gitignore`
- [ ] Strong `SECRET_KEY` generated
- [ ] Database has password protection
- [ ] Different credentials per environment
- [ ] No secrets in source code
- [ ] `.env.example` has no real secrets

## Troubleshooting

**Configuration not loading?**
- Check `.env` file location (must be in `backend/`)
- Verify file name is exactly `.env`
- Restart application after changes

**Missing values?**
- Check `env.example` for required fields
- Add missing values to your `.env` file

**Values not updating?**
- Restart the application
- Clear Python cache: `rm -rf __pycache__`

## See Also

- [CONFIGURATION_GUIDE.md](./CONFIGURATION_GUIDE.md) - Comprehensive guide
- [env.example](./env.example) - All available options
- [Twelve-Factor App](https://12factor.net/config) - Methodology

