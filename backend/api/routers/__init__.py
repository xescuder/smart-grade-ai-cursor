"""
API routers package
"""
from .assignments import router as assignments_router
from .submissions import router as submissions_router
from .grading import router as grading_router
from .classrooms import router as classrooms_router
from .courses import router as courses_router
from .semesters import router as semesters_router
from .groups import router as groups_router

__all__ = [
    "assignments_router",
    "submissions_router",
    "grading_router",
    "classrooms_router",
    "courses_router",
    "semesters_router",
    "groups_router"
]
