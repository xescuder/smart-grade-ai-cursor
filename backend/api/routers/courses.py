"""
Course management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from crud import (
    get_courses,
    get_course,
    get_course_by_code,
    create_course,
    update_course,
    delete_course,
    get_courses_by_department,
    get_courses_with_semesters,
    get_course_with_semesters,
    CourseCreate,
    CourseUpdate,
    CourseResponse
)

router = APIRouter()

# Error messages
COURSE_NOT_FOUND = "Course not found"

# API request model without created_by
class CourseCreateRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = ""
    department: Optional[str] = ""
    credits: int


@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department: Optional[str] = Query(None),
    created_by: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all courses with optional filtering"""
    if department:
        courses = await get_courses_by_department(db, department, created_by)
    else:
        courses = await get_courses(db, created_by, skip, limit)
    return courses


@router.get("/with-semesters", response_model=List[CourseResponse])
async def list_courses_with_semesters(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    created_by: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all courses with their semesters"""
    courses = await get_courses_with_semesters(db, created_by, skip, limit)
    return courses


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course_by_id(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific course by ID"""
    course = await get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    return course


@router.get("/{course_id}/with-semesters", response_model=CourseResponse)
async def get_course_with_semesters_by_id(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific course with its semesters by ID"""
    course = await get_course_with_semesters(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    return course


@router.get("/code/{code}", response_model=CourseResponse)
async def get_course_by_code_endpoint(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific course by code"""
    course = await get_course_by_code(db, code)
    if not course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    return course


@router.post("/", response_model=CourseResponse)
async def create_new_course(
    course_request: CourseCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new course"""
    # Convert API request to CourseCreate model with created_by
    course = CourseCreate(
        name=course_request.name,
        code=course_request.code,
        description=course_request.description,
        department=course_request.department,
        credits=course_request.credits,
        created_by=1  # For now, use a default created_by user ID (1)
    )
    db_course = await create_course(db, course)
    return db_course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course_by_id(
    course_id: int,
    course: CourseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a course"""
    db_course = await get_course(db, course_id)
    if not db_course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    
    updated_course = await update_course(db, course_id, course)
    return updated_course


@router.delete("/{course_id}")
async def delete_course_by_id(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a course"""
    course = await get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    
    await delete_course(db, course_id)
    return {"message": "Course deleted successfully"}
