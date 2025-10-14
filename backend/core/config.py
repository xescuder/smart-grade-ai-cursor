"""
Core configuration settings for Smart Grade AI
Follows twelve-factor app configuration best practices
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All configuration should be managed through .env file or environment variables.
    """
    
    # ============================================================================
    # APPLICATION SETTINGS
    # ============================================================================
    APP_NAME: str = "Smart Grade AI"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # ============================================================================
    # SERVER SETTINGS
    # ============================================================================
    # Backend API server
    HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    PORT: int = 8000  # Alias for backward compatibility
    RELOAD: bool = True
    
    # Frontend server (for CORS and development)
    FRONTEND_PORT: int = 3000
    FRONTEND_HOST: str = "localhost"
    
    # ============================================================================
    # SECURITY
    # ============================================================================
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ============================================================================
    # CORS SETTINGS
    # ============================================================================
    ALLOWED_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://127.0.0.1:3000"
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # ============================================================================
    # DATABASE CONFIGURATION
    # ============================================================================
    DATABASE_URL: str = "postgresql+asyncpg://smartgrade:@localhost:5432/smartgrade_db"
    DATABASE_ECHO: bool = True
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # ============================================================================
    # REDIS CONFIGURATION
    # ============================================================================
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_CONNECTIONS: int = 10
    
    # ============================================================================
    # AI SERVICE CONFIGURATION - OLLAMA
    # ============================================================================
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    OLLAMA_TIMEOUT: int = 120
    OLLAMA_TEMPERATURE: float = 0.1
    
    # ============================================================================
    # AI SERVICE CONFIGURATION - OPENAI
    # ============================================================================
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.7
    
    # ============================================================================
    # AI SERVICE CONFIGURATION - ANTHROPIC
    # ============================================================================
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    ANTHROPIC_MAX_TOKENS: int = 4000
    
    # ============================================================================
    # FILE UPLOAD SETTINGS
    # ============================================================================
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: Union[List[str], str] = ".pdf,.docx,.txt,.md"
    UPLOAD_DIR: str = "uploads"
    
    @field_validator('ALLOWED_FILE_TYPES', mode='before')
    @classmethod
    def parse_file_types(cls, v):
        """Parse ALLOWED_FILE_TYPES from comma-separated string or list"""
        if isinstance(v, str):
            return [ft.strip() for ft in v.split(',')]
        return v
    
    # ============================================================================
    # AI GRADING SETTINGS
    # ============================================================================
    DEFAULT_AI_PROVIDER: str = "ollama"
    DEFAULT_AI_MODEL: str = "llama2"
    MAX_CONCURRENT_GRADINGS: int = 5
    PDF_TEXT_MAX_LENGTH: int = 30000
    ENABLE_VISION_MODEL: bool = False
    VISION_MODEL_NAME: str = "gpt-4-vision-preview"
    
    # ============================================================================
    # LOGGING CONFIGURATION
    # ============================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = "backend.log"
    
    # ============================================================================
    # EXTERNAL SERVICES
    # ============================================================================
    GOOGLE_DRIVE_ENABLED: bool = False
    GOOGLE_DRIVE_CLIENT_ID: str = ""
    GOOGLE_DRIVE_CLIENT_SECRET: str = ""
    GOOGLE_DRIVE_REDIRECT_URI: str = ""
    
    # ============================================================================
    # FEATURE FLAGS
    # ============================================================================
    ENABLE_AI_EXTRACTION: bool = True
    ENABLE_AI_GRADING: bool = True
    ENABLE_ANALYTICS: bool = True
    ENABLE_NOTIFICATIONS: bool = False
    
    # ============================================================================
    # MONITORING & ANALYTICS
    # ============================================================================
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    
    model_config = {"env_file": ".env", "case_sensitive": True}
    
    @property
    def ollama_api_generate_url(self) -> str:
        """Get the full Ollama API generate endpoint URL"""
        return f"{self.OLLAMA_BASE_URL}/api/generate"
    
    @property
    def ollama_api_tags_url(self) -> str:
        """Get the full Ollama API tags endpoint URL"""
        return f"{self.OLLAMA_BASE_URL}/api/tags"
    
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
        origins = self.ALLOWED_ORIGINS if isinstance(self.ALLOWED_ORIGINS, list) else []
        # Ensure frontend URLs are included
        frontend_urls = [
            f"http://localhost:{self.FRONTEND_PORT}",
            f"http://127.0.0.1:{self.FRONTEND_PORT}",
            self.frontend_url
        ]
        # Add unique frontend URLs that aren't already in origins
        for url in frontend_urls:
            if url not in origins:
                origins.append(url)
        return origins


settings = Settings()
