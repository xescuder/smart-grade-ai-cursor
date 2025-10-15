#!/usr/bin/env python3
"""
Smart Grade AI - Main Application Entry Point
Clean architecture using FastAPI routers
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from core.config import settings
from database import init_db, close_db

# Set up logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Import routers
from api.routers import (
    assignments_router,
    submissions_router,
    grading_router,
    auth_router,
    users_router
)

# Create FastAPI app
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

### Database

PostgreSQL with async support, storing PDFs directly in database for reliability.

### Architecture

Clean architecture with:
- **Repository Pattern** for data access
- **Service Layer** for business logic
- **Router Layer** for API endpoints
- **Dependency Injection** for testability
    """,
    version="2.0.0",
    contact={
        "name": "Smart Grade AI Team",
        "url": "https://github.com/your-repo/smart-grade-ai-cursor",
        "email": "support@smartgrade.ai"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "assignments",
            "description": "Assignment CRUD operations, PDF upload, and exercise extraction"
        },
        {
            "name": "exercises",
            "description": "Manage exercises within assignments"
        },
        {
            "name": "submissions",
            "description": "Student submission handling and grading"
        },
        {
            "name": "grading",
            "description": "AI-powered grading operations"
        },
        {
            "name": "auth",
            "description": "Authentication and authorization"
        },
        {
            "name": "users",
            "description": "User management"
        },
        {
            "name": "health",
            "description": "System health and status checks"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Register routers
app.include_router(
    assignments_router,
    prefix="/api/assignments",
    tags=["assignments"]
)

app.include_router(
    submissions_router,
    prefix="/api/submissions",
    tags=["submissions"]
)

app.include_router(
    grading_router,
    prefix="/api/grading",
    tags=["grading"]
)

app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["auth"]
)

app.include_router(
    users_router,
    prefix="/api/users",
    tags=["users"]
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    logger.info("🚀 Starting Smart Grade AI...")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🌐 Backend URL: {settings.backend_url}")
    logger.info(f"🎨 Frontend URL: {settings.frontend_url}")
    logger.info(f"🤖 Google AI Model: {settings.GOOGLE_AI_MODEL}")
    
    await init_db()
    logger.info("✅ Database initialized")
    logger.info("✅ Smart Grade AI is ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger.info("👋 Shutting down Smart Grade AI...")
    await close_db()
    logger.info("✅ Cleanup complete")


# Health check endpoints
@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Smart Grade AI API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "google_ai_configured": bool(settings.GOOGLE_AI_API_KEY)
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

