"""
API routes for submission management
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import json
import io
import base64
import aiofiles
from datetime import datetime

from database import get_db
from core.config import settings
from crud import (
    get_submissions,
    get_submission,
    get_submissions_by_assignment,
    create_submission,
    update_submission,
    delete_submission,
    get_groups_by_classroom,
    SubmissionCreate,
    SubmissionUpdate,
    SubmissionResponse,
    SubmissionFile
)

router = APIRouter(tags=["submissions"])

# Constants
SUBMISSION_NOT_FOUND = "Submission not found"
NO_PDF_FILE_FOUND = "No PDF file found for this submission"
FILE_NOT_FOUND = "File not found"
FILE_NOT_FOUND_ON_DISK = "File not found on disk"

# Ensure uploads directory exists (use centralized config)
UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "submissions")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[dict])
async def list_submissions(
    assignment_id: Optional[int] = None,
    classroom_id: Optional[int] = None,
    group_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all submissions, optionally filtered by assignment, classroom, or group"""
    submissions = await get_submissions(db, assignment_id=assignment_id, classroom_id=classroom_id, group_id=group_id, skip=skip, limit=limit)
    
    # Convert to dict and add relationship data
    result = []
    for submission in submissions:
        submission_dict = {
            "id": submission.id,
            "assignment_id": submission.assignment_id,
            "classroom_id": submission.classroom_id,
            "group_id": submission.group_id,
            "comments": submission.comments,
            "status": submission.status,
            "pdf_file_path": submission.pdf_file_path,
            "pdf_file_name": submission.pdf_file_name,
            "pdf_file_size": submission.pdf_file_size,
            "pdf_mime_type": submission.pdf_mime_type,
            "pdf_file_data": base64.b64encode(submission.pdf_file_data).decode('utf-8') if submission.pdf_file_data else None,  # Base64 encoded PDF data
            # Private PDF fields
            "private_pdf_filename": submission.private_pdf_filename,
            "private_pdf_size": submission.private_pdf_size,
            "private_pdf_mime_type": submission.private_pdf_mime_type,
            "private_pdf_uploaded_at": submission.private_pdf_uploaded_at,
            "private_pdf_responsible_students": submission.private_pdf_responsible_students,
            "private_pdf_data": base64.b64encode(submission.private_pdf_data).decode('utf-8') if submission.private_pdf_data else None,  # Base64 encoded PDF data
            # Public PDF fields
            "public_pdf_filename": submission.public_pdf_filename,
            "public_pdf_size": submission.public_pdf_size,
            "public_pdf_mime_type": submission.public_pdf_mime_type,
            "public_pdf_uploaded_at": submission.public_pdf_uploaded_at,
            "public_pdf_responsible_students": submission.public_pdf_responsible_students,
            "public_pdf_data": base64.b64encode(submission.public_pdf_data).decode('utf-8') if submission.public_pdf_data else None,  # Base64 encoded PDF data
            "total_score": submission.total_score,
            "max_score": submission.max_score,
            "percentage_score": submission.percentage_score,
            "teacher_feedback": submission.teacher_feedback,
            "ai_feedback": submission.ai_feedback,
            "grade_breakdown": submission.grade_breakdown,
            "submitted_at": submission.submitted_at,
            "graded_at": submission.graded_at,
            "graded_by": submission.graded_by,
            "is_late": submission.is_late,
            "created_at": submission.created_at,
            "updated_at": submission.updated_at,
            # Add relationship data
            "assignment": {
                "id": submission.assignment.id,
                "name": submission.assignment.name,
                "description": submission.assignment.description,
                "exercises": [
                    {
                        "id": ex.id,
                        "description": ex.description,
                        "evaluation_criteria": ex.evaluation_criteria,
                        "points": ex.points,
                        "order": ex.order
                    } for ex in submission.assignment.exercises
                ] if submission.assignment.exercises else []
            } if submission.assignment else None,
            "classroom": {
                "id": submission.classroom.id,
                "name": submission.classroom.name,
                "teacher_name": submission.classroom.teacher_name,
                "language": submission.classroom.language,
                "course": {
                    "id": submission.classroom.course.id,
                    "name": submission.classroom.course.name,
                    "code": submission.classroom.course.code
                } if submission.classroom.course else None,
                "semester": {
                    "id": submission.classroom.semester.id,
                    "name": submission.classroom.semester.name,
                    "code": submission.classroom.semester.code,
                    "year": submission.classroom.semester.year,
                    "season": submission.classroom.semester.season
                } if submission.classroom.semester else None
            } if submission.classroom else None,
            "group": {
                "id": submission.group.id,
                "name": submission.group.name,
                "description": submission.group.description,
                "members": submission.group.members
            } if submission.group else None
        }
        result.append(submission_dict)
    
    return result

@router.get("/{submission_id}/pdf")
async def get_submission_pdf(
    submission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the PDF file for a submission"""
    
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
    if not submission.pdf_file_data:
        raise HTTPException(status_code=404, detail=NO_PDF_FILE_FOUND)
    
    # Create a streaming response from the binary data
    pdf_stream = io.BytesIO(submission.pdf_file_data)
    
    return StreamingResponse(
        pdf_stream,
        media_type=submission.pdf_mime_type or "application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={submission.pdf_file_name or 'submission.pdf'}"
        }
    )

@router.put("/{submission_id}/pdf")
async def upload_submission_pdf(
    submission_id: int,
    pdf_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload PDF file for a submission"""
    
    # Check if submission exists
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
    # Validate file type
    if not pdf_file.content_type or not pdf_file.content_type.startswith('application/pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Read file data
        pdf_data = await pdf_file.read()
        
        # Update submission with PDF data
        submission.pdf_file_data = pdf_data
        submission.pdf_mime_type = pdf_file.content_type
        submission.pdf_file_size = len(pdf_data)
        submission.pdf_file_name = pdf_file.filename or f"submission_{submission_id}.pdf"
        
        # Save to database
        await db.commit()
        await db.refresh(submission)
        
        return {
            "message": "PDF uploaded successfully",
            "submission_id": submission_id,
            "file_size": len(pdf_data),
            "file_name": submission.pdf_file_name
        }
        
    except Exception as e:
        await db.rollback()
        print(f"Error uploading PDF for submission {submission_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload PDF file")

@router.get("/{submission_id}/private-pdf")
async def get_private_pdf(
    submission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get private PDF for a submission"""
    
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
    if not submission.private_pdf_data:
        raise HTTPException(status_code=404, detail="Private PDF not found")
    
    return StreamingResponse(
        io.BytesIO(submission.private_pdf_data),
        media_type=submission.private_pdf_mime_type or "application/pdf",
        headers={"Content-Disposition": f"inline; filename={submission.private_pdf_filename or 'private.pdf'}"}
    )

@router.put("/{submission_id}/private-pdf")
async def upload_private_pdf(
    submission_id: int,
    pdf_file: UploadFile = File(...),
    coordinators: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload private PDF file for a submission"""
    
    # Check if submission exists
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
    # Validate file type
    if not pdf_file.content_type or not pdf_file.content_type.startswith('application/pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Read file data
        pdf_data = await pdf_file.read()
        
        # Update submission with private PDF data
        submission.private_pdf_data = pdf_data
        submission.private_pdf_mime_type = pdf_file.content_type
        submission.private_pdf_size = len(pdf_data)
        submission.private_pdf_filename = pdf_file.filename
        submission.private_pdf_uploaded_at = datetime.utcnow()
        submission.private_pdf_responsible_students = coordinators
        
        await db.commit()
        await db.refresh(submission)
        
        return {
            "message": "Private PDF uploaded successfully",
            "submission_id": submission_id,
            "file_size": len(pdf_data),
            "file_name": submission.private_pdf_filename,
            "coordinators": coordinators
        }
        
    except Exception as e:
        await db.rollback()
        print(f"Error uploading private PDF for submission {submission_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload private PDF")

@router.get("/{submission_id}/public-pdf")
async def get_public_pdf(
    submission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get public PDF for a submission"""
    
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
    if not submission.public_pdf_data:
        raise HTTPException(status_code=404, detail="Public PDF not found")
    
    return StreamingResponse(
        io.BytesIO(submission.public_pdf_data),
        media_type=submission.public_pdf_mime_type or "application/pdf",
        headers={"Content-Disposition": f"inline; filename={submission.public_pdf_filename or 'public.pdf'}"}
    )

@router.put("/{submission_id}/public-pdf")
async def upload_public_pdf(
    submission_id: int,
    pdf_file: UploadFile = File(...),
    coordinators: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload public PDF file for a submission"""
    
    # Check if submission exists
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
    # Validate file type
    if not pdf_file.content_type or not pdf_file.content_type.startswith('application/pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Read file data
        pdf_data = await pdf_file.read()
        
        # Update submission with public PDF data
        submission.public_pdf_data = pdf_data
        submission.public_pdf_mime_type = pdf_file.content_type
        submission.public_pdf_size = len(pdf_data)
        submission.public_pdf_filename = pdf_file.filename
        submission.public_pdf_uploaded_at = datetime.utcnow()
        submission.public_pdf_responsible_students = coordinators
        
        await db.commit()
        await db.refresh(submission)
        
        return {
            "message": "Public PDF uploaded successfully",
            "submission_id": submission_id,
            "file_size": len(pdf_data),
            "file_name": submission.public_pdf_filename,
            "coordinators": coordinators
        }
        
    except Exception as e:
        await db.rollback()
        print(f"Error uploading public PDF for submission {submission_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload public PDF")

@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission_by_id(submission_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific submission by ID"""
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    return submission

@router.get("/assignment/{assignment_id}", response_model=List[SubmissionResponse])
async def list_submissions_by_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Get all submissions for a specific assignment"""
    submissions = await get_submissions_by_assignment(db, assignment_id)
    return submissions

@router.post("/", response_model=SubmissionResponse)
async def create_new_submission(
    assignment_id: int = Form(...),
    classroom_id: int = Form(...),
    group_id: Optional[int] = Form(None),
    comments: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a new submission with optional file uploads"""
    
    # Handle file uploads
    pdf_file_path = None
    pdf_file_name = None
    pdf_file_data = None
    pdf_mime_type = None
    pdf_file_size = None
    
    if files and len(files) > 0:
        file = files[0]  # Take the first file as PDF
        if file.filename:
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            # Save file
            content = await file.read()
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            
            pdf_file_path = file_path
            pdf_file_name = file.filename
            pdf_file_data = content
            pdf_mime_type = file.content_type or "application/pdf"
            pdf_file_size = len(content)
    
    # Create submission
    submission_data = SubmissionCreate(
        assignment_id=assignment_id,
        classroom_id=classroom_id,
        group_id=group_id,
        comments=comments,
        pdf_file_path=pdf_file_path,
        pdf_file_name=pdf_file_name,
        pdf_file_data=pdf_file_data,
        pdf_mime_type=pdf_mime_type,
        pdf_file_size=pdf_file_size
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
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    return submission

@router.delete("/{submission_id}")
async def delete_submission_by_id(submission_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a submission"""
    success = await delete_submission(db, submission_id)
    if not success:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
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
    print("=== GRADING ENDPOINT CALLED ===")
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
    print("DEBUG: About to call update_submission")
    
    submission = await update_submission(db, submission_id, grade_update)
    print(f"DEBUG: update_submission returned: {submission}")
    
    if not submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
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
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
    if not submission.submission_files or file_index >= len(submission.submission_files):
        raise HTTPException(status_code=404, detail=FILE_NOT_FOUND)
    
    file_info = submission.submission_files[file_index]
    file_path = file_info["path"]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=FILE_NOT_FOUND_ON_DISK)
    
    return FileResponse(
        path=file_path,
        filename=file_info["name"],
        media_type=file_info["content_type"]
    )

class GenerateExpectedSubmissionsRequest(BaseModel):
    assignment_id: int
    classroom_id: int

@router.post("/generate-expected")
async def generate_expected_submissions(
    request: GenerateExpectedSubmissionsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate expected submissions for all groups in a classroom"""
    
    print(f"=== GENERATE EXPECTED SUBMISSIONS ===")
    print(f"Assignment ID: {request.assignment_id}")
    print(f"Classroom ID: {request.classroom_id}")
    
    # Get all groups in the classroom
    groups = await get_groups_by_classroom(db, request.classroom_id)
    print(f"Found {len(groups)} groups in classroom {request.classroom_id}")
    
    if not groups:
        print(f"No groups found for classroom {request.classroom_id}")
        raise HTTPException(
            status_code=404, 
            detail=f"No groups found for classroom {request.classroom_id}"
        )
    
    created_submissions = []
    
    for group in groups:
        print(f"Processing group: {group.id} - {group.name}")
        
        # Check if submission already exists for this group and assignment
        existing_submissions = await get_submissions(
            db, 
            assignment_id=request.assignment_id,
            group_id=group.id
        )
        
        print(f"Found {len(existing_submissions)} existing submissions for group {group.id}")
        
        if existing_submissions:
            # Skip if submission already exists
            print(f"Skipping group {group.id} - submission already exists")
            continue
            
        # Create a new submission for this group
        submission_data = SubmissionCreate(
            assignment_id=request.assignment_id,
            classroom_id=request.classroom_id,
            group_id=group.id,
            comments=f"Expected submission for {group.name}",
            status="pending"
        )
        
        try:
            submission = await create_submission(db, submission_data)
            created_submissions.append(submission)
            print(f"Created submission for group {group.id}: {submission.id}")
        except Exception as e:
            print(f"Error creating submission for group {group.id}: {e}")
            continue
    
    return {
        "message": f"Generated {len(created_submissions)} expected submissions",
        "count": len(created_submissions),
        "submissions": [
            {
                "id": sub.id,
                "group_id": sub.group_id,
                "group_name": next((g.name for g in groups if g.id == sub.group_id), "Unknown"),
                "status": sub.status
            } for sub in created_submissions
        ]
    }