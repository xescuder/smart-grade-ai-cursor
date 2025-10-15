"""
Smart Grade AI - FastAPI Backend
Main application entry point with modular router architecture
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from core.config import settings
from database import init_db, close_db
from routes import register_routes, ROUTER_METADATA
from logging_config import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Smart Grade AI Backend starting up...")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🌐 Backend URL: {settings.backend_url}")
    logger.info(f"🎨 Frontend URL: {settings.frontend_url}")
    logger.info(f"🤖 Google AI Model: {settings.GOOGLE_AI_MODEL}")

    await init_db()
    logger.success("✅ Database initialized")
    logger.success("✅ Smart Grade AI is ready!")

    yield

    # Shutdown
    logger.info("👋 Smart Grade AI Backend shutting down...")
    await close_db()
    logger.success("✅ Cleanup complete")


# Create FastAPI instance
app = FastAPI(
    title="Smart Grade AI API",
    description="""
## AI-Powered Grading System API

Smart Grade AI automates assignment grading using advanced AI models, providing
consistent, detailed feedback to students while saving teachers valuable time.

### Key Features

* 🎓 **Assignment Management**: Create, update, and organize assignments
* 📄 **PDF Processing**: Upload and extract exercises from PDF statements  
* 🤖 **AI Grading**: Automatic submission evaluation with detailed feedback
* 👥 **Group Management**: Organize students into groups and classrooms
* 📊 **Analytics**: Track performance and grading statistics
* 🔧 **Configuration**: Customize AI models and extraction settings

### AI Providers Supported

- **Google AI (Gemini)**: Advanced vision models for PDF analysis
- **Ollama** (Local, Free): Privacy-focused, offline-capable
- **OpenAI GPT-4**: Advanced cloud-based grading
- **Anthropic Claude**: High-quality AI analysis

### Architecture

Clean architecture with:
- **Repository Pattern** for data access
- **Service Layer** for business logic
- **Router Layer** for API endpoints
- **Dependency Injection** for testability
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=ROUTER_METADATA
)

# Configure CORS - Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Mount static files for uploads
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Register all routes from routes.py
register_routes(app)


# Health check endpoints
@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Smart Grade AI API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "architecture": "modular_routers"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "google_ai_configured": bool(settings.GOOGLE_AI_API_KEY),
        "database": "postgresql",
        "architecture": "repository_pattern"
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
