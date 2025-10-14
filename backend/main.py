"""
Smart Grade AI - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routers import auth, assignments, submissions, grading, users
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Smart Grade AI Backend starting up...")
    yield
    # Shutdown
    print("👋 Smart Grade AI Backend shutting down...")


# Create FastAPI instance
app = FastAPI(
    title="Smart Grade AI API",
    description="AI-powered grading system for educational assignments",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(assignments.router, prefix="/api/v1/assignments", tags=["assignments"])
app.include_router(submissions.router, prefix="/api/v1/submissions", tags=["submissions"])
app.include_router(grading.router, prefix="/api/v1/grading", tags=["grading"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Smart Grade AI API",
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting Smart Grade AI Backend")
    print(f"   Backend:  {settings.backend_url}")
    print(f"   Frontend: {settings.frontend_url}")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.BACKEND_PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )

