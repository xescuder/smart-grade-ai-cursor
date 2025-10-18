"""
Assignments router for assignment management with exercises
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ai_prompts import get_exercise_extraction_prompt
from core.config import settings
from crud import (
    get_assignments as crud_get_assignments,
    get_assignment as crud_get_assignment,
    update_assignment as crud_update_assignment,
    delete_assignment as crud_delete_assignment,
    get_assignment_exercises as crud_get_assignment_exercises,
    update_assignment_exercises as crud_update_assignment_exercises,
    AssignmentCreate as CrudAssignmentCreate,
    AssignmentUpdate as CrudAssignmentUpdate,
    AssignmentResponse,
    ExerciseUpdate,
    ExerciseResponse,
    create_assignment as crud_create_assignment
)
from database import get_db

router = APIRouter()

# Constants
ASSIGNMENT_NOT_FOUND = "Assignment not found"
TEACHER_ONLY_CREATE = "Only teachers can create assignments"
TEACHER_ONLY_UPDATE = "Only teachers can update assignments"  
TEACHER_ONLY_DELETE = "Only teachers can delete assignments"

@router.get("/", response_model=List[AssignmentResponse])
async def get_assignments(db: AsyncSession = Depends(get_db)):
    """Get all assignments"""
    return await crud_get_assignments(db)


@router.post("/", response_model=AssignmentResponse)
async def create_assignment(assignment: CrudAssignmentCreate, db: AsyncSession = Depends(get_db)):
    return await crud_create_assignment(db, assignment)


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
    assignment = await crud_update_assignment(db, assignment_id, assignment_update)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    return assignment


@router.delete("/{assignment_id}")
async def delete_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
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
    from services.google_ai_service import GoogleAIService
    from logging_config import logger
    from crud import get_assignment

    logger.debug(f"Extracting exercises from assignment {assignment_id}")

    # Fetch assignment and PDF bytes
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if not assignment.pdf_file_data:
        raise HTTPException(status_code=404, detail="No PDF file found for this assignment")

    try:
        # Get prompt for exercise extraction depending on language of assignment
        prompt = get_exercise_extraction_prompt(assignment.language)
        logger.info(f"Using exercise extraction prompt for language '{assignment.language}':")
        logger.info(f"Prompt: {prompt}")
        
        # Get api key from settings or environment
        google_ai_service = GoogleAIService(api_key=settings.GOOGLE_AI_API_KEY)
        
        result = google_ai_service.analyse_pdf(
            pdf_bytes=assignment.pdf_file_data,
            prompt=prompt
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )
