"""
Assignments router for assignment management with exercises
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid
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
from .auth import User, get_current_user

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
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = ".pdf"
    unique_filename = f"assignment_{assignment_id}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as f:  # pylint: disable=unspecified-encoding
        f.write(content)
    
    # Update assignment in database
    from crud import update_assignment_pdf
    updated_assignment = await update_assignment_pdf(db, assignment_id, f"/{file_path}", file.filename)
    
    return {
        "success": True,
        "message": "PDF uploaded successfully",
        "file_name": file.filename,
        "file_path": updated_assignment.statement_file_path
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
    
    # Check if assignment has a PDF file
    if not assignment.statement_file_path:
        raise HTTPException(status_code=404, detail="No PDF file found for this assignment")
    
    # Construct full file path
    file_path = assignment.statement_file_path
    if not file_path.startswith('/'):
        file_path = f"./{file_path}"
    
    # Check if file exists, if not try alternative paths
    if not os.path.exists(file_path):
        # Try to find the file in the uploads directory with a different pattern
        uploads_dir = "uploads"
        if os.path.exists(uploads_dir):
            # Look for files that might match this assignment
            for filename in os.listdir(uploads_dir):
                if filename.startswith(f"assignment_{assignment_id}_") and filename.endswith('.pdf'):
                    file_path = os.path.join(uploads_dir, filename)
                    break
            else:
                raise HTTPException(status_code=404, detail="PDF file not found on server")
        else:
            raise HTTPException(status_code=404, detail="PDF file not found on server")
    
    # Return the PDF file inline for viewing (not download)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"}
    )
