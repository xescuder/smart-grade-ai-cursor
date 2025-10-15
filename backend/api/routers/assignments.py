"""
Assignments router for assignment management with exercises
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from crud import (
    create_assignment as crud_create_assignment,
    get_assignments as crud_get_assignments,
    get_assignment as crud_get_assignment,
    update_assignment as crud_update_assignment,
    delete_assignment as crud_delete_assignment,
    get_assignment_exercises as crud_get_assignment_exercises,
    update_assignment_exercises as crud_update_assignment_exercises,
    AssignmentCreate as CrudAssignmentCreate,
    AssignmentUpdate as CrudAssignmentUpdate,
    AssignmentResponse,
    ExerciseCreate,
    ExerciseUpdate,
    ExerciseResponse
)

router = APIRouter()

# Constants
ASSIGNMENT_NOT_FOUND = "Assignment not found"
TEACHER_ONLY_CREATE = "Only teachers can create assignments"
TEACHER_ONLY_UPDATE = "Only teachers can update assignments"  
TEACHER_ONLY_DELETE = "Only teachers can delete assignments"


def get_mock_user():
    """Return mock user for demo purposes"""
    # Create mock user without importing User class to avoid circular imports
    class MockUser:
        def __init__(self):
            self.id = 1
            self.username = "teacher"
            self.email = "teacher@example.com" 
            self.full_name = "Demo Teacher"
            self.role = "teacher"
            self.is_active = True
    
    return MockUser()


@router.get("/", response_model=List[AssignmentResponse])
async def get_assignments(db: AsyncSession = Depends(get_db)):
    """Get all assignments"""
    return await crud_get_assignments(db)


@router.post("/", response_model=AssignmentResponse)
async def create_assignment(assignment: CrudAssignmentCreate, db: AsyncSession = Depends(get_db)):
    """Create new assignment (teachers only)"""
    current_user = get_mock_user()  # Use mock user for demo
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail=TEACHER_ONLY_CREATE)
    
    return await crud_create_assignment(db, assignment, current_user.id)


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Get assignment by ID"""
    assignment = await crud_get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    return assignment


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_update: CrudAssignmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update assignment (teachers only)"""
    current_user = get_mock_user()  # Use mock user for demo
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail=TEACHER_ONLY_UPDATE)
    
    assignment = await crud_update_assignment(db, assignment_id, assignment_update)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    return assignment


@router.delete("/{assignment_id}")
async def delete_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Delete assignment (teachers only)"""
    current_user = get_mock_user()  # Use mock user for demo
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail=TEACHER_ONLY_DELETE)
    
    success = await crud_delete_assignment(db, assignment_id)
    if not success:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    return {"message": "Assignment deleted successfully"}


# Exercise Management Endpoints

@router.get("/{assignment_id}/exercises", response_model=List[ExerciseResponse])
async def get_assignment_exercises(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Get exercises for an assignment"""
    # Check if assignment exists
    assignment = await crud_get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    return await crud_get_assignment_exercises(db, assignment_id)


@router.put("/{assignment_id}/exercises", response_model=List[ExerciseResponse])
async def update_assignment_exercises(
    assignment_id: int,
    exercises: List[ExerciseUpdate],
    db: AsyncSession = Depends(get_db)
):
    """Update exercises for an assignment (teachers only)"""
    current_user = get_mock_user()  # Use mock user for demo
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail=TEACHER_ONLY_UPDATE)
    
    # Check if assignment exists
    assignment = await crud_get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    # Validate total points
    if exercises:
        total = sum(exercise.points for exercise in exercises)
        if total != 100:
            raise HTTPException(
                status_code=400, 
                detail=f"Total points of exercises must equal 100, got {total}"
            )
    
    return await crud_update_assignment_exercises(db, assignment_id, exercises)

# PDF Upload Endpoint

@router.post("/{assignment_id}/upload/statement")
async def upload_assignment_pdf(
    assignment_id: int, 
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload PDF statement file for assignment"""
    
    # Check if assignment exists
    assignment = await crud_get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Validate file size (max 10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    # Store PDF content directly in database
    from crud import update_assignment_pdf_bytes
    updated_assignment = await update_assignment_pdf_bytes(db, assignment_id, content, file.filename)
    
    return {
        "success": True,
        "message": "PDF uploaded successfully",
        "file_name": file.filename,
        "file_size": len(content),
        "storage_type": "database"
    }

@router.get("/{assignment_id}/pdf")
async def get_assignment_pdf(
    assignment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get PDF file for assignment"""
    
    # Check if assignment exists
    assignment = await crud_get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    # Check if assignment has PDF data in database
    if not assignment.pdf_file_data:
        raise HTTPException(status_code=404, detail="No PDF file found for this assignment")
    
    # Return PDF content from database
    return Response(
        content=assignment.pdf_file_data,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"}
    )


# AI Extraction Endpoint

@router.post("/{assignment_id}/extract-exercises-ai")
async def extract_exercises_ai(
    assignment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract exercises from assignment PDF using Google AI (Gemini)

    This endpoint:
    1. Retrieves the PDF bytes from the database
    2. Creates a temporary file
    3. Sends the PDF to Google AI for analysis
    4. Parses the exercises from the AI response
    5. Replaces existing exercises with the extracted ones
    6. Cleans up the temporary file

    Returns the extracted exercises with their descriptions, points, and criteria.
    """
    from services.ai_service import ai_extraction_service
    from logging_config import logger
    
    logger.debug(f"Extracting exercises from assignment {assignment_id}")

    try:
        result = await ai_extraction_service.extract_exercises_from_pdf(
            assignment_id=assignment_id,
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )
