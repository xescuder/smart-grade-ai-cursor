# Configuration Guide - Twelve-Factor App Principles

This project follows the [twelve-factor app methodology](https://12factor.net/), specifically the **Config** principle: "Store config in the environment."

## Overview

All configuration is centralized in **environment variables** managed through a `.env` file. This approach provides:

- ✅ **Separation of configuration from code**: No hardcoded values in source code
- ✅ **Security**: Sensitive credentials never committed to version control
- ✅ **Environment flexibility**: Easy switching between development, staging, and production
- ✅ **Consistency**: Single source of truth for all configuration
- ✅ **Portability**: Deploy to any environment by changing `.env` file

## Quick Start

### 1. Create Your Configuration File

Copy the example configuration template:

```bash
cd backend
cp env.example .env
```

### 2. Edit Configuration Values

Open `.env` and update values for your environment:

```bash
# Edit with your preferred editor
nano .env
# or
code .env
```

### 3. Required Configuration

At minimum, update these values:

```env
# Database connection
DATABASE_URL=postgresql+asyncpg://smartgrade:YOUR_PASSWORD@localhost:5432/smartgrade_db

# Security (generate a secure key)
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Ollama configuration (if using local AI)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## Configuration Structure

### Application Settings

```env
APP_NAME="Smart Grade AI"
DEBUG=false                    # Enable debug mode (development only)
ENVIRONMENT=development        # development, staging, production
```

### Server Settings

```env
HOST=0.0.0.0                  # Server host
PORT=8000                     # Server port
RELOAD=true                   # Auto-reload on code changes (development)
```

### Security

```env
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**IMPORTANT**: Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### CORS Settings

```env
# Comma-separated list of allowed origins
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Database Configuration

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
DATABASE_ECHO=true            # Log SQL queries (development)
DATABASE_POOL_SIZE=5          # Connection pool size
DATABASE_MAX_OVERFLOW=10      # Max overflow connections
```

### AI Service Configuration

#### Ollama (Local LLM)

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=120
OLLAMA_TEMPERATURE=0.1
```

#### OpenAI (Optional)

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.7
```

#### Anthropic Claude (Optional)

```env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_MAX_TOKENS=4000
```

### File Upload Settings

```env
MAX_FILE_SIZE=10485760        # 10MB in bytes
ALLOWED_FILE_TYPES=.pdf,.docx,.txt,.md
UPLOAD_DIR=uploads            # Base upload directory
```

### AI Grading Settings

```env
DEFAULT_AI_PROVIDER=ollama    # ollama, openai, anthropic
DEFAULT_AI_MODEL=llama2
MAX_CONCURRENT_GRADINGS=5
PDF_TEXT_MAX_LENGTH=30000
ENABLE_VISION_MODEL=false
VISION_MODEL_NAME=gpt-4-vision-preview
```

### Logging

```env
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=backend.log
```

### Feature Flags

```env
ENABLE_AI_EXTRACTION=true
ENABLE_AI_GRADING=true
ENABLE_ANALYTICS=true
ENABLE_NOTIFICATIONS=false
```

## Environment-Specific Configuration

### Development

```env
DEBUG=true
ENVIRONMENT=development
DATABASE_ECHO=true
LOG_LEVEL=DEBUG
RELOAD=true
```

### Production

```env
DEBUG=false
ENVIRONMENT=production
DATABASE_ECHO=false
LOG_LEVEL=INFO
RELOAD=false
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql+asyncpg://user:strongpassword@prod-host:5432/prod_db
```

## Configuration Architecture

### Central Configuration Module

All configuration is defined in `backend/core/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # All configuration fields
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    # ... more settings
    
    model_config = {"env_file": ".env", "case_sensitive": True}

settings = Settings()
```

### Using Configuration in Code

Import and use the `settings` object:

```python
from core.config import settings

# Access configuration values
print(settings.OLLAMA_BASE_URL)
print(settings.DATABASE_URL)

# Use in API calls
response = requests.get(settings.ollama_api_tags_url)
```

### Benefits of Centralized Configuration

1. **Type Safety**: Pydantic validates all configuration values
2. **Defaults**: Sensible defaults for development
3. **Computed Properties**: Helper methods like `ollama_api_generate_url`
4. **IDE Support**: Autocomplete and type checking
5. **Single Import**: `from core.config import settings`

## Security Best Practices

### ✅ DO

- Store `.env` files outside version control (add to `.gitignore`)
- Use strong, randomly generated secrets
- Rotate credentials regularly
- Use different credentials per environment
- Limit environment variable access
- Use password-protected databases

### ❌ DON'T

- Commit `.env` files to git
- Share `.env` files via insecure channels
- Use default/example secrets in production
- Hardcode secrets in source code
- Log sensitive configuration values

## Environment Variables Priority

Configuration is loaded in this order (later overrides earlier):

1. Default values in `Settings` class
2. `.env` file values
3. System environment variables
4. Explicitly set environment variables

## Validation and Error Handling

Pydantic automatically validates configuration:

```python
class Settings(BaseSettings):
    PORT: int = 8000              # Must be an integer
    DEBUG: bool = False           # Must be boolean
    ALLOWED_ORIGINS: List[str]    # Must be a list
```

Invalid configuration will raise clear error messages at startup.

## Docker and Containerization

### Using .env with Docker Compose

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    env_file:
      - ./backend/.env
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

### Environment Variables in Dockerfile

```dockerfile
# Use ARG for build-time variables
ARG PORT=8000

# Use ENV for runtime variables
ENV PORT=${PORT}
```

## Troubleshooting

### Configuration Not Loading

1. Check `.env` file location (should be in `backend/` directory)
2. Verify file name is exactly `.env` (not `env` or `.env.txt`)
3. Check for syntax errors (no spaces around `=`)
4. Ensure values with spaces are quoted: `APP_NAME="Smart Grade AI"`

### Missing Required Values

If you see "field required" errors:

```bash
pydantic.error_wrappers.ValidationError: 1 validation error for Settings
DATABASE_URL
  field required (type=value_error.missing)
```

Add the missing value to your `.env` file.

### Configuration Not Updating

1. Restart the application after changing `.env`
2. Check for typos in variable names (case-sensitive)
3. Clear Python cache: `rm -rf __pycache__`

## Migration from Hardcoded Values

The following values have been migrated to configuration:

| Old Location | New Configuration | File |
|--------------|-------------------|------|
| `OLLAMA_BASE_URL = "http://..."` | `settings.OLLAMA_BASE_URL` | `ai_service.py` |
| `OLLAMA_MODEL = "llama2"` | `settings.OLLAMA_MODEL` | `ai_service.py` |
| `DATABASE_URL = os.getenv(...)` | `settings.DATABASE_URL` | `database.py` |
| `UPLOAD_DIR = "uploads"` | `settings.UPLOAD_DIR` | `submissions.py` |
| `host="0.0.0.0", port=8000` | `settings.HOST, settings.PORT` | `main.py` |

## Further Reading

- [Twelve-Factor App: Config](https://12factor.net/config)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Environment Variables Best Practices](https://12factor.net/config)

## Support

For questions or issues with configuration:

1. Check this guide
2. Review `env.example` for all available options
3. Check application logs for validation errors
4. Verify `.env` file syntax and location

