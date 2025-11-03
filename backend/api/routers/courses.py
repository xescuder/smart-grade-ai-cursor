"""
Course management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from database import get_db, Course
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.inspection import inspect
from crud import (
    get_courses,
    get_course,
    get_course_by_code,
    create_course,
    update_course,
    delete_course,
    permanently_delete_course,
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
    credits: Optional[int] = None


@router.get("/")
async def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department: Optional[str] = Query(None),
    created_by: Optional[int] = Query(None),
    include_semesters: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get all courses with optional filtering.

    If include_semesters=true, returns courses with their semesters preloaded.
    """
    if include_semesters:
        courses = await get_courses_with_semesters(db, created_by, skip, limit)
    elif department:
        courses = await get_courses_by_department(db, department, created_by)
    else:
        courses = await get_courses(db, created_by, skip, limit)
    
    # Manually serialize courses to avoid lazy loading issues
    result = []
    for course in courses:
        # Access semesters while still in async context
        # Check if relationship is loaded using SQLAlchemy inspection
        try:
            course_insp = inspect(course)
            if course_insp.attrs.semesters.loaded_value is not None:
                semesters_list = list(course.semesters)
            else:
                # Relationship not loaded, use empty list
                semesters_list = []
        except Exception:
            # If accessing triggers lazy load error, use empty list
            semesters_list = []
        semesters_data = []
        for semester in semesters_list:
            semesters_data.append({
                "id": int(semester.id),
                "year": int(semester.year),
                "season": str(semester.season),
                "course_id": int(semester.course_id),
                "start_date": semester.start_date.isoformat() if semester.start_date else None,
                "end_date": semester.end_date.isoformat() if semester.end_date else None,
                "created_by": int(semester.created_by),
                "created_at": semester.created_at.isoformat() if semester.created_at else None,
                "updated_at": semester.updated_at.isoformat() if semester.updated_at else None,
            })
        
        result.append({
            "id": int(course.id),
            "name": str(course.name),
            "code": str(course.code),
            "credits": int(course.credits) if course.credits is not None else None,
            "created_by": int(course.created_by),
            "created_at": course.created_at.isoformat() if course.created_at else None,
            "updated_at": course.updated_at.isoformat() if course.updated_at else None,
            "semesters": semesters_data
        })
    
    # Return JSONResponse to bypass FastAPI validation
    return JSONResponse(content=result)


@router.get("/with-semesters")
async def list_courses_with_semesters(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    created_by: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all courses with their semesters"""
    courses = await get_courses_with_semesters(db, created_by, skip, limit)
    
    # Manually serialize courses to avoid lazy loading issues
    result = []
    for course in courses:
        # Access semesters while still in async context
        # Check if relationship is loaded using SQLAlchemy inspection
        try:
            course_insp = inspect(course)
            if course_insp.attrs.semesters.loaded_value is not None:
                semesters_list = list(course.semesters)
            else:
                # Relationship not loaded, use empty list
                semesters_list = []
        except Exception:
            # If accessing triggers lazy load error, use empty list
            semesters_list = []
        semesters_data = []
        for semester in semesters_list:
            semesters_data.append({
                "id": int(semester.id),
                "year": int(semester.year),
                "season": str(semester.season),
                "course_id": int(semester.course_id),
                "start_date": semester.start_date.isoformat() if semester.start_date else None,
                "end_date": semester.end_date.isoformat() if semester.end_date else None,
                "created_by": int(semester.created_by),
                "created_at": semester.created_at.isoformat() if semester.created_at else None,
                "updated_at": semester.updated_at.isoformat() if semester.updated_at else None,
            })
        
        result.append({
            "id": int(course.id),
            "name": str(course.name),
            "code": str(course.code),
            "credits": int(course.credits) if course.credits is not None else None,
            "created_by": int(course.created_by),
            "created_at": course.created_at.isoformat() if course.created_at else None,
            "updated_at": course.updated_at.isoformat() if course.updated_at else None,
            "semesters": semesters_data
        })
    
    # Return JSONResponse to bypass FastAPI validation
    return JSONResponse(content=result)


@router.get("/{course_id}")
async def get_course_by_id(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific course by ID"""
    # Need to load with semesters to avoid lazy loading
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.semesters))
        .where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    
    # Manually serialize to avoid lazy loading
    # Use getattr to safely check if semesters relationship is loaded
    try:
        # Check if relationship is loaded by accessing it
        if hasattr(course, '__dict__') and 'semesters' in course.__dict__:
            semesters_list = list(course.semesters)
        else:
            # Relationship not loaded, use empty list
            semesters_list = []
    except Exception:
        # If accessing triggers lazy load error, use empty list
        semesters_list = []
    semesters_data = []
    for semester in semesters_list:
        semesters_data.append({
            "id": int(semester.id),
            "year": int(semester.year),
            "season": str(semester.season),
            "course_id": int(semester.course_id),
            "start_date": semester.start_date.isoformat() if semester.start_date else None,
            "end_date": semester.end_date.isoformat() if semester.end_date else None,
            "created_by": int(semester.created_by),
            "created_at": semester.created_at.isoformat() if semester.created_at else None,
            "updated_at": semester.updated_at.isoformat() if semester.updated_at else None,
        })
    
    # Return JSONResponse to bypass FastAPI validation
    response_data = {
        "id": int(course.id),
        "name": str(course.name),
        "code": str(course.code),
        "credits": int(course.credits) if course.credits is not None else None,
        "created_by": int(course.created_by),
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "updated_at": course.updated_at.isoformat() if course.updated_at else None,
        "semesters": semesters_data
    }
    return JSONResponse(content=response_data)


@router.get("/{course_id}/with-semesters")
async def get_course_with_semesters_by_id(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific course with its semesters by ID"""
    course = await get_course_with_semesters(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    
    # Manually serialize to avoid lazy loading
    # Use getattr to safely check if semesters relationship is loaded
    try:
        # Check if relationship is loaded by accessing it
        if hasattr(course, '__dict__') and 'semesters' in course.__dict__:
            semesters_list = list(course.semesters)
        else:
            # Relationship not loaded, use empty list
            semesters_list = []
    except Exception:
        # If accessing triggers lazy load error, use empty list
        semesters_list = []
    semesters_data = []
    for semester in semesters_list:
        semesters_data.append({
            "id": int(semester.id),
            "year": int(semester.year),
            "season": str(semester.season),
            "course_id": int(semester.course_id),
            "start_date": semester.start_date.isoformat() if semester.start_date else None,
            "end_date": semester.end_date.isoformat() if semester.end_date else None,
            "created_by": int(semester.created_by),
            "created_at": semester.created_at.isoformat() if semester.created_at else None,
            "updated_at": semester.updated_at.isoformat() if semester.updated_at else None,
        })
    
    # Return JSONResponse to bypass FastAPI validation
    response_data = {
        "id": int(course.id),
        "name": str(course.name),
        "code": str(course.code),
        "credits": int(course.credits) if course.credits is not None else None,
        "created_by": int(course.created_by),
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "updated_at": course.updated_at.isoformat() if course.updated_at else None,
        "semesters": semesters_data
    }
    return JSONResponse(content=response_data)


@router.get("/code/{code}")
async def get_course_by_code_endpoint(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific course by code"""
    # Load with semesters to avoid lazy loading
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.semesters))
        .where(Course.code == code)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    
    # Manually serialize to avoid lazy loading
    # Use getattr to safely check if semesters relationship is loaded
    try:
        # Check if relationship is loaded by accessing it
        if hasattr(course, '__dict__') and 'semesters' in course.__dict__:
            semesters_list = list(course.semesters)
        else:
            # Relationship not loaded, use empty list
            semesters_list = []
    except Exception:
        # If accessing triggers lazy load error, use empty list
        semesters_list = []
    semesters_data = []
    for semester in semesters_list:
        semesters_data.append({
            "id": int(semester.id),
            "year": int(semester.year),
            "season": str(semester.season),
            "course_id": int(semester.course_id),
            "start_date": semester.start_date.isoformat() if semester.start_date else None,
            "end_date": semester.end_date.isoformat() if semester.end_date else None,
            "created_by": int(semester.created_by),
            "created_at": semester.created_at.isoformat() if semester.created_at else None,
            "updated_at": semester.updated_at.isoformat() if semester.updated_at else None,
        })
    
    # Return JSONResponse to bypass FastAPI validation
    response_data = {
        "id": int(course.id),
        "name": str(course.name),
        "code": str(course.code),
        "credits": int(course.credits) if course.credits is not None else None,
        "created_by": int(course.created_by),
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "updated_at": course.updated_at.isoformat() if course.updated_at else None,
        "semesters": semesters_data
    }
    return JSONResponse(content=response_data)


@router.post("/")
async def create_new_course(
    course_request: CourseCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new course"""
    try:
        # Convert API request to CourseCreate model with created_by
        course = CourseCreate(
            name=course_request.name,
            code=course_request.code,
            credits=course_request.credits,
            created_by=1  # For now, use a default created_by user ID (1)
        )
        db_course = await create_course(db, course)
        
        # Re-query with eager loading to ensure relationship is properly loaded
        result = await db.execute(
            select(Course)
            .options(selectinload(Course.semesters))
            .where(Course.id == db_course.id)
        )
        course_with_semesters = result.scalar_one_or_none()
        if not course_with_semesters:
            raise HTTPException(status_code=500, detail="Failed to retrieve created course")
        
        # CRITICAL: Convert ALL data to plain Python types IMMEDIATELY while session is active
        # Start with semesters - convert to list FIRST to force evaluation while session is active
        semesters_data = []
        try:
            # Force list conversion immediately using list() - this ensures we're in the session context
            # and forces evaluation of the eagerly loaded relationship
            semesters_list = list(course_with_semesters.semesters)
            # Now iterate over the list and convert to dicts
            for semester in semesters_list:
                semesters_data.append({
                    "id": int(semester.id),
                    "year": int(semester.year),
                    "season": str(semester.season),
                    "course_id": int(semester.course_id),
                    "start_date": semester.start_date.isoformat() if semester.start_date else None,
                    "end_date": semester.end_date.isoformat() if semester.end_date else None,
                    "created_by": int(semester.created_by),
                    "created_at": semester.created_at.isoformat() if semester.created_at else None,
                    "updated_at": semester.updated_at.isoformat() if semester.updated_at else None,
                })
        except Exception as e:
            # If accessing semesters fails, use empty list
            from logging_config import logger
            logger.warning(f"Failed to access semesters: {e}", exc_info=True)
            semesters_data = []
        
        # Now extract course attributes - all as plain Python types
        response_data = {
            "id": int(course_with_semesters.id),
            "name": str(course_with_semesters.name),
            "code": str(course_with_semesters.code),
            "credits": int(course_with_semesters.credits) if course_with_semesters.credits is not None else None,
            "created_by": int(course_with_semesters.created_by),
            "created_at": course_with_semesters.created_at.isoformat() if course_with_semesters.created_at else None,
            "updated_at": course_with_semesters.updated_at.isoformat() if course_with_semesters.updated_at else None,
            "semesters": semesters_data  # Already a plain list of dicts
        }
        
        # Return JSONResponse with plain dict to explicitly bypass FastAPI validation
        return JSONResponse(content=response_data)
    except HTTPException:
        raise
    except Exception as e:
        from logging_config import logger
        logger.error(f"Error creating course: {e}", exc_info=True)
        # Re-raise HTTPException if it was already raised by create_course
        if isinstance(e, HTTPException):
            raise
        # Otherwise, raise a generic error
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create course: {str(e)}"
        )


@router.put("/{course_id}")
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
    if not updated_course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    
    # Manually serialize to avoid lazy loading
    semesters_list = list(updated_course.semesters) if hasattr(updated_course, 'semesters') else []
    semesters_data = []
    for semester in semesters_list:
        semesters_data.append({
            "id": int(semester.id),
            "year": int(semester.year),
            "season": str(semester.season),
            "course_id": int(semester.course_id),
            "start_date": semester.start_date.isoformat() if semester.start_date else None,
            "end_date": semester.end_date.isoformat() if semester.end_date else None,
            "created_by": int(semester.created_by),
            "created_at": semester.created_at.isoformat() if semester.created_at else None,
            "updated_at": semester.updated_at.isoformat() if semester.updated_at else None,
        })
    
    # Return JSONResponse to bypass FastAPI validation
    response_data = {
        "id": int(updated_course.id),
        "name": str(updated_course.name),
        "code": str(updated_course.code),
        "credits": int(updated_course.credits) if updated_course.credits is not None else None,
        "created_by": int(updated_course.created_by),
        "created_at": updated_course.created_at.isoformat() if updated_course.created_at else None,
        "updated_at": updated_course.updated_at.isoformat() if updated_course.updated_at else None,
        "semesters": semesters_data
    }
    return JSONResponse(content=response_data)


@router.delete("/{course_id}")
async def delete_course_by_id(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Permanently delete a course"""
    course = await get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    
    success = await delete_course(db, course_id)
    if not success:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    return {"message": "Course deleted successfully"}
