"""
Semester management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from crud import (
    get_semesters,
    get_semester,
    create_semester,
    update_semester,
    delete_semester,
    SemesterCreate,
    SemesterUpdate,
    SemesterResponse
)

router = APIRouter()

# Error messages
SEMESTER_NOT_FOUND = "Semester not found"

# API request model without created_by
class SemesterCreateRequest(BaseModel):
    name: str
    code: str
    year: int
    season: str
    start_date: str
    end_date: str
    course_id: int
    is_active: bool = True


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


@router.post("/", response_model=SemesterResponse)
async def create_new_semester(
    semester_request: SemesterCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new semester"""
    # Convert API request to SemesterCreate model with created_by
    semester = SemesterCreate(
        name=semester_request.name,
        code=semester_request.code,
        year=semester_request.year,
        season=semester_request.season,
        start_date=datetime.fromisoformat(semester_request.start_date),
        end_date=datetime.fromisoformat(semester_request.end_date),
        course_id=semester_request.course_id,
        is_active=semester_request.is_active,
        created_by=1  # For now, use a default created_by user ID (1)
    )
    db_semester = await create_semester(db, semester)
    return db_semester


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
    semester = await get_semester(db, semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail=SEMESTER_NOT_FOUND)

    await delete_semester(db, semester_id)
    return {"message": "Semester deleted successfully"}

