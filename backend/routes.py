"""
Centralized route registration
All API routers are registered here
"""
from fastapi import FastAPI
from api.routers import (
    assignments_router,
    submissions_router,
    grading_router,
    auth_router,
    users_router,
    classrooms_router,
    courses_router,
    semesters_router,
    groups_router
)


def register_routes(app: FastAPI) -> None:
    """
    Register all API routers with the FastAPI application

    This centralizes all route registration in one place, making it easy to:
    - See all available routes at a glance
    - Add/remove routes
    - Change route prefixes and tags
    - Maintain consistent API versioning
    """

    # ============================================================================
    # VERSIONED ROUTES (/api/v1/*)
    # ============================================================================

    # Authentication routes
    app.include_router(
        auth_router,
        prefix="/api/v1/auth",
        tags=["authentication"]
    )

    # User management routes
    app.include_router(
        users_router,
        prefix="/api/v1/users",
        tags=["users"]
    )

    # Assignment management routes
    app.include_router(
        assignments_router,
        prefix="/api/v1/assignments",
        tags=["assignments"]
    )

    # Submission management routes
    app.include_router(
        submissions_router,
        prefix="/api/v1/submissions",
        tags=["submissions"]
    )

    # Grading routes
    app.include_router(
        grading_router,
        prefix="/api/v1/grading",
        tags=["grading"]
    )

    # Classroom management routes
    app.include_router(
        classrooms_router,
        prefix="/api/v1/classrooms",
        tags=["classrooms"]
    )

    # Course management routes
    app.include_router(
        courses_router,
        prefix="/api/v1/courses",
        tags=["courses"]
    )

    # Semester management routes
    app.include_router(
        semesters_router,
        prefix="/api/v1/semesters",
        tags=["semesters"]
    )

    # Group management routes
    app.include_router(
        groups_router,
        prefix="/api/v1/groups",
        tags=["groups"]
    )


# Route configuration constants
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Router metadata for OpenAPI documentation
ROUTER_METADATA = [
    {
        "name": "health",
        "description": "System health and status checks"
    },
    {
        "name": "authentication",
        "description": "User authentication and authorization"
    },
    {
        "name": "users",
        "description": "User management and profile operations"
    },
    {
        "name": "assignments",
        "description": "Assignment CRUD operations, PDF upload, and AI extraction"
    },
    {
        "name": "submissions",
        "description": "Student submission handling and file management"
    },
    {
        "name": "grading",
        "description": "AI-powered grading operations and batch processing"
    },
    {
        "name": "classrooms",
        "description": "Classroom management and enrollment operations"
    },
    {
        "name": "courses",
        "description": "Course management and content delivery"
    },
    {
        "name": "semesters",
        "description": "Semester management and course scheduling"
    },
    {
        "name": "groups",
        "description": "Group management within classrooms and semesters"
    },
]
