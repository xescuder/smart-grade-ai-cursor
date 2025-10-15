"""
API routes for submission management
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import json

from database import get_db
from core.config import settings
from crud import (
    get_submissions,
    get_submission,
    get_submissions_by_assignment,
    create_submission,
    update_submission,
    delete_submission,
    SubmissionCreate,
    SubmissionUpdate,
    SubmissionResponse,
    StudentInfo,
    SubmissionFile
)

router = APIRouter(tags=["submissions"])

# Ensure uploads directory exists (use centralized config)
UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "submissions")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[SubmissionResponse])
async def list_submissions(
    assignment_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all submissions, optionally filtered by assignment"""
    submissions = await get_submissions(db, assignment_id=assignment_id, skip=skip, limit=limit)
    return submissions

@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission_by_id(submission_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific submission by ID"""
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

@router.get("/assignment/{assignment_id}", response_model=List[SubmissionResponse])
async def list_submissions_by_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Get all submissions for a specific assignment"""
    submissions = await get_submissions_by_assignment(db, assignment_id)
    return submissions

@router.post("/", response_model=SubmissionResponse)
async def create_new_submission(
    assignment_id: int = Form(...),
    group_name: str = Form(...),
    group_members: str = Form(...),  # JSON string
    description: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a new submission with optional file uploads"""
    
    # Parse group members JSON
    try:
        group_members_data = json.loads(group_members)
        group_members_list = [StudentInfo(**member) for member in group_members_data]
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid group_members JSON: {str(e)}")
    
    # Handle file uploads
    submission_files = []
    if files:
        for file in files:
            if file.filename:
                # Generate unique filename
                file_extension = os.path.splitext(file.filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = os.path.join(UPLOAD_DIR, unique_filename)
                
                # Save file
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)
                
                # Create file info
                submission_files.append(SubmissionFile(
                    name=file.filename,
                    path=file_path,
                    size=len(content),
                    content_type=file.content_type or "application/octet-stream"
                ))
    
    # Create submission
    submission_data = SubmissionCreate(
        assignment_id=assignment_id,
        group_name=group_name,
        group_members=group_members_list,
        description=description,
        submission_files=submission_files
    )
    
    submission = await create_submission(db, submission_data)
    return submission

@router.put("/{submission_id}", response_model=SubmissionResponse)
async def update_submission_by_id(
    submission_id: int,
    submission_update: SubmissionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a submission"""
    submission = await update_submission(db, submission_id, submission_update)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

@router.delete("/{submission_id}")
async def delete_submission_by_id(submission_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a submission"""
    success = await delete_submission(db, submission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"message": "Submission deleted successfully"}

class GradeSubmissionRequest(BaseModel):
    total_score: float
    teacher_feedback: Optional[str] = None
    grade_breakdown: List[dict] = []

@router.post("/{submission_id}/grade")
async def grade_submission(
    submission_id: int,
    grade_request: GradeSubmissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Grade a submission with detailed breakdown"""
    print(f"=== GRADING ENDPOINT CALLED ===")
    print(f"DEBUG: Received grade request for submission {submission_id}")
    print(f"DEBUG: Grade request data: {grade_request}")
    
    grade_update = SubmissionUpdate(
        total_score=grade_request.total_score,
        teacher_feedback=grade_request.teacher_feedback,
        graded_by=1,  # Default teacher ID
        status="graded",
        grade_breakdown=grade_request.grade_breakdown
    )
    
    print(f"DEBUG: Grade update object: {grade_update}")
    print(f"DEBUG: About to call update_submission")
    
    submission = await update_submission(db, submission_id, grade_update)
    print(f"DEBUG: update_submission returned: {submission}")
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return {
        "message": "Submission graded successfully",
        "total_score": submission.total_score,
        "percentage_score": submission.percentage_score
    }

@router.get("/{submission_id}/download/{file_index}")
async def download_submission_file(submission_id: int, file_index: int, db: AsyncSession = Depends(get_db)):
    """Download a specific submission file"""
    from fastapi.responses import FileResponse
    
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if not submission.submission_files or file_index >= len(submission.submission_files):
        raise HTTPException(status_code=404, detail="File not found")
    
    file_info = submission.submission_files[file_index]
    file_path = file_info["path"]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=file_info["name"],
        media_type=file_info["content_type"]
    )