"""
Semester management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date

from database import get_db
from crud import (
    get_semesters,
    get_semester,
    get_semester_any_status,
    create_semester,
    update_semester,
    delete_semester,
    get_semesters_by_course,
    SemesterCreate,
    SemesterUpdate,
    SemesterResponse
)

router = APIRouter()

# Error messages
SEMESTER_NOT_FOUND = "Semester not found"

# API request model without created_by
class SemesterCreateRequest(BaseModel):
    year: int
    season: str
    course_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None


@router.get("/by-course/{course_id}", response_model=List[SemesterResponse])
async def get_semesters_by_course_id(
    course_id: int,
    created_by: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all semesters for a specific course"""
    semesters = await get_semesters_by_course(db, course_id=course_id, created_by=created_by)
    return semesters


@router.get("/{semester_id}", response_model=SemesterResponse)
async def get_semester_by_id(
    semester_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific semester by ID"""
    semester = await get_semester(db, semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail=SEMESTER_NOT_FOUND)
    return semester


@router.get("/", response_model=List[SemesterResponse])
async def list_semesters(
    created_by: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all semesters, optionally filtered by creator"""
    semesters = await get_semesters(db, created_by=created_by, skip=skip, limit=limit)
    return semesters


@router.post("/", response_model=SemesterResponse)
async def create_new_semester(
    semester_request: SemesterCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new semester"""
    # Convert API request to SemesterCreate model with created_by
    semester = SemesterCreate(
        year=semester_request.year,
        season=semester_request.season,
        course_id=semester_request.course_id,
        # Removed is_active field
        start_date=semester_request.start_date,
        end_date=semester_request.end_date,
        created_by=1  # For now, use a default created_by user ID (1)
    )
    try:
        db_semester = await create_semester(db, semester)
        return db_semester
    except IntegrityError as e:
        # Most likely unique constraint on year and season combination
        detail = "Semester with this year and season already exists"
        raise HTTPException(status_code=409, detail=detail)


@router.put("/{semester_id}", response_model=SemesterResponse)
async def update_semester_by_id(
    semester_id: int,
    semester: SemesterUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a semester"""
    db_semester = await get_semester(db, semester_id)
    if not db_semester:
        raise HTTPException(status_code=404, detail=SEMESTER_NOT_FOUND)

    updated_semester = await update_semester(db, semester_id, semester)
    return updated_semester


@router.delete("/{semester_id}")
async def delete_semester_by_id(
    semester_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a semester"""
    # Allow deleting inactive or active, but error if not found
    semester = await get_semester_any_status(db, semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail=SEMESTER_NOT_FOUND)
    try:
        await delete_semester(db, semester_id)
        return {"message": "Semester deleted successfully"}
    except IntegrityError:
        # Foreign key constraint from classrooms -> semesters
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot delete semester: there are classrooms linked to this semester. "
                "Delete or reassign those classrooms first."
            ),
        )

