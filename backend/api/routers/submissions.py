"""
API routes for submission management
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import json
import io
import base64
import aiofiles
import tempfile
import traceback
import requests
from datetime import datetime

from database import get_db
from core.config import settings
from crud import (
    get_assignment_exercises,
    get_submissions,
    get_submission,
    get_submissions_by_assignment,
    create_submission,
    update_submission,
    delete_submission,
    get_groups_by_classroom,
    get_group,
    get_assignment,
    SubmissionCreate,
    SubmissionUpdate,
    SubmissionResponse,
    SubmissionFile
)
from ai_prompts import get_private_report_evaluation_prompt, get_public_report_evaluation_prompt, get_exercise_extraction_prompt, get_submission_evaluation_prompt
from logging import getLogger
from services.google_ai_service import GoogleAIService
from services.excel_grade_service import ExcelGradeService
from database import Submission, Assignment, Classroom, Group, Exercise, Course, Semester

logger = getLogger(__name__)

router = APIRouter(tags=["submissions"])

# Constants
SUBMISSION_NOT_FOUND = "Submission not found"
NO_PDF_FILE_FOUND = "No PDF file found for this submission"
FILE_NOT_FOUND = "File not found"
FILE_NOT_FOUND_ON_DISK = "File not found on disk"

# Ensure uploads directory exists (use centralized config)
UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "submissions")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/grading", response_model=List[dict])
async def list_submissions_grading_data(
    assignment_id: Optional[int] = None,
    classroom_id: Optional[int] = None,
    group_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get submissions grading data only (no PDF data)"""
    submissions = await get_submissions(db, assignment_id=assignment_id, classroom_id=classroom_id, group_id=group_id, skip=skip, limit=limit)
    
    # Convert to dict with only grading data (no PDF data)
    result = []
    for submission in submissions:
        submission_dict = {
            "id": submission.id,
            "assignment_id": submission.assignment_id,
            "classroom_id": submission.classroom_id,
            "group_id": submission.group_id,
            "comments": submission.comments,
            "status": submission.status,
            # PDF metadata only (no actual PDF data)
            "pdf_file_name": submission.pdf_file_name,
            "pdf_file_size": submission.pdf_file_size,
            "pdf_mime_type": submission.pdf_mime_type,
            "has_submission_pdf": bool(submission.pdf_file_name and submission.pdf_file_size > 0),
            # Private PDF metadata only
            "private_pdf_filename": submission.private_pdf_filename,
            "private_pdf_size": submission.private_pdf_size,
            "private_pdf_mime_type": submission.private_pdf_mime_type,
            "private_pdf_uploaded_at": submission.private_pdf_uploaded_at,
            "coordinators": submission.coordinators,
            "has_private_pdf": bool(submission.private_pdf_filename and submission.private_pdf_size > 0),
            # Public PDF metadata only
            "public_pdf_filename": submission.public_pdf_filename,
            "public_pdf_size": submission.public_pdf_size,
            "public_pdf_mime_type": submission.public_pdf_mime_type,
            "public_pdf_uploaded_at": submission.public_pdf_uploaded_at,
            "public_pdf_responsible_students": submission.public_pdf_responsible_students,
            "has_public_pdf": bool(submission.public_pdf_filename and submission.public_pdf_size > 0),
            # Grading data
            "total_score": submission.total_score,
            "max_score": submission.max_score,
            "percentage_score": submission.percentage_score,
            "teacher_feedback": submission.teacher_feedback,
            "ai_feedback": submission.ai_feedback,
            "grade_breakdown": submission.grade_breakdown,
            "private_report_evaluation": submission.private_report_evaluation,
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
                    "id": submission.classroom.semester.course.id,
                    "name": submission.classroom.semester.course.name,
                    "code": submission.classroom.semester.course.code
                } if submission.classroom.semester and submission.classroom.semester.course else None,
                "semester": {
                    "id": submission.classroom.semester.id,
                    "name": f"{submission.classroom.semester.season} {submission.classroom.semester.year}",
                    "code": f"{submission.classroom.semester.year}{submission.classroom.semester.season[0]}",
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
    meeting_notes: bool = Form(False),
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
        submission.meeting_notes = meeting_notes
        # auto-set presence flag
        submission.has_submission_pdf = True
        
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
    pdf_file: Optional[UploadFile] = File(None),
    coordinators: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload private PDF file for a submission, or update coordinators only"""
    
    # Check if submission exists
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
    try:
        # Update PDF if provided
        if pdf_file:
            # Validate file type
            if not pdf_file.content_type or not pdf_file.content_type.startswith('application/pdf'):
                raise HTTPException(status_code=400, detail="Only PDF files are allowed")
            
            # Read file data
            pdf_data = await pdf_file.read()
            
            # Update submission with private PDF data
            submission.private_pdf_data = pdf_data
            submission.private_pdf_mime_type = pdf_file.content_type
            submission.private_pdf_size = len(pdf_data)
            submission.private_pdf_filename = pdf_file.filename
            submission.private_pdf_uploaded_at = datetime.utcnow()
            submission.has_private_pdf = True
        
        # Update coordinators if provided
        if coordinators is not None:
            submission.coordinators = coordinators
        
        await db.commit()
        await db.refresh(submission)
        
        return {
            "message": "Private PDF updated successfully",
            "submission_id": submission_id,
            "file_size": submission.private_pdf_size,
            "file_name": submission.private_pdf_filename,
            "coordinators": coordinators
        }
        
    except HTTPException:
        raise
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
    coordinators: Optional[str] = Form(None),
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
        submission.has_public_pdf = True
        
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

@router.get("/{submission_id}/grading")
async def get_submission_grading_data(submission_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific submission's grading data only (no PDF data)"""
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
    # Convert to dict with only grading data (no PDF data)
    submission_dict = {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "classroom_id": submission.classroom_id,
        "group_id": submission.group_id,
        "comments": submission.comments,
        "status": submission.status,
        # PDF metadata only (no actual PDF data)
        "pdf_file_name": submission.pdf_file_name,
        "pdf_file_size": submission.pdf_file_size,
        "pdf_mime_type": submission.pdf_mime_type,
        "has_submission_pdf": bool(submission.pdf_file_name and submission.pdf_file_size > 0),
        # Private PDF metadata only
        "private_pdf_filename": submission.private_pdf_filename,
        "private_pdf_size": submission.private_pdf_size,
        "private_pdf_mime_type": submission.private_pdf_mime_type,
        "private_pdf_uploaded_at": submission.private_pdf_uploaded_at,
        "coordinators": submission.coordinators,
        "has_private_pdf": bool(submission.private_pdf_filename and submission.private_pdf_size > 0),
        # Public PDF metadata only
        "public_pdf_filename": submission.public_pdf_filename,
        "public_pdf_size": submission.public_pdf_size,
        "public_pdf_mime_type": submission.public_pdf_mime_type,
        "public_pdf_uploaded_at": submission.public_pdf_uploaded_at,
        "public_pdf_responsible_students": submission.public_pdf_responsible_students,
        "has_public_pdf": bool(submission.public_pdf_filename and submission.public_pdf_size > 0),
        # Grading data
        "total_score": submission.total_score,
        "max_score": submission.max_score,
        "percentage_score": submission.percentage_score,
        "teacher_feedback": submission.teacher_feedback,
        "ai_feedback": submission.ai_feedback,
        "grade_breakdown": submission.grade_breakdown,
        "private_report_evaluation": submission.private_report_evaluation,
        "submitted_at": submission.submitted_at,
        "graded_at": submission.graded_at,
        "graded_by": submission.graded_by,
        "is_late": submission.is_late,
        "created_at": submission.created_at,
        "updated_at": submission.updated_at,
        "meeting_notes": submission.meeting_notes,
        # Add relationship data
        "assignment": {
            "id": submission.assignment.id,
            "name": submission.assignment.name,
            "description": submission.assignment.description,
            "due_date": submission.assignment.due_date,
            "language": submission.assignment.language
        } if submission.assignment else None,
        "classroom": {
            "id": submission.classroom.id,
            "name": submission.classroom.name,
            "teacher_name": submission.classroom.teacher_name,
            "language": submission.classroom.language
        } if submission.classroom else None,
        "group": {
            "id": submission.group.id,
            "name": submission.group.name,
            "description": submission.group.description,
            "members": submission.group.members
        } if submission.group else None
    }
    
    return submission_dict

@router.get("/{submission_id}")
async def get_submission_by_id(submission_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific submission by ID"""
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
    # Convert to dict and exclude large PDF data to avoid serialization issues
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
        # Private PDF fields
        "private_pdf_filename": submission.private_pdf_filename,
        "private_pdf_size": submission.private_pdf_size,
        "private_pdf_mime_type": submission.private_pdf_mime_type,
        "private_pdf_uploaded_at": submission.private_pdf_uploaded_at,
        "coordinators": submission.coordinators,
        # Public PDF fields
        "public_pdf_filename": submission.public_pdf_filename,
        "public_pdf_size": submission.public_pdf_size,
        "public_pdf_mime_type": submission.public_pdf_mime_type,
        "public_pdf_uploaded_at": submission.public_pdf_uploaded_at,
        "public_pdf_responsible_students": submission.public_pdf_responsible_students,
        "total_score": submission.total_score,
        "max_score": submission.max_score,
        "percentage_score": submission.percentage_score,
        "teacher_feedback": submission.teacher_feedback,
        "ai_feedback": submission.ai_feedback,
        "grade_breakdown": submission.grade_breakdown,
        "private_report_evaluation": submission.private_report_evaluation,
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
                "name": f"{submission.classroom.semester.season} {submission.classroom.semester.year}",
                "code": f"{submission.classroom.semester.year}{submission.classroom.semester.season[0]}",
                "year": submission.classroom.semester.year,
                "season": submission.classroom.semester.season
            } if submission.classroom.semester else None
        } if submission.classroom else None,
        "group": {
            "id": submission.group.id,
            "name": submission.group.name,
            "nickname": submission.group.nickname,
            "description": submission.group.description,
            "members": submission.group.members
        } if submission.group else None
    }
    
    return submission_dict

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
    meeting_notes: bool = Form(False),
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
        meeting_notes=meeting_notes,
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
    
    # Get the submission first to access its max_score
    db_submission = await get_submission(db, submission_id)
    if not db_submission:
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)
    
    grade_update = SubmissionUpdate(
        total_score=grade_request.total_score,
        max_score=db_submission.max_score,  # Use existing max_score from submission
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


class PublicReportGradeRequest(BaseModel):
    points: float
    comments: Optional[str] = None


@router.post("/{submission_id}/public-report-grade")
async def save_public_report_grade(
    submission_id: int,
    body: PublicReportGradeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Persist public report grade/comments into ai_feedback as JSON."""
    logger.info(f"=== PUBLIC REPORT GRADE SAVE ===")
    logger.info(f"Submission ID: {submission_id}")
    logger.info(f"Request body: {body}")
    
    submission = await get_submission(db, submission_id)
    if not submission:
        logger.error(f"Submission {submission_id} not found")
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)

    logger.info(f"Found submission: ID={submission.id}, Group ID={submission.group_id}")
    
    # Build/merge ai_feedback JSON
    ai_feedback_obj = {}
    if submission.ai_feedback:
        try:
            ai_feedback_obj = json.loads(submission.ai_feedback)
            logger.info(f"Existing AI feedback keys: {list(ai_feedback_obj.keys())}")
        except Exception:
            ai_feedback_obj = {"raw": submission.ai_feedback}

    ai_feedback_obj["public_report"] = {
        "points": body.points,
        "comments": body.comments or ""
    }
    
    logger.info(f"Updated AI feedback: {ai_feedback_obj}")

    update = SubmissionUpdate(ai_feedback=json.dumps(ai_feedback_obj))
    updated = await update_submission(db, submission_id, update)
    if not updated:
        logger.error(f"Failed to update submission {submission_id}")
        raise HTTPException(status_code=404, detail=SUBMISSION_NOT_FOUND)

    logger.info(f"Successfully updated submission {submission_id}")
    return {"message": "Public report grade saved", "public_report": ai_feedback_obj["public_report"]}

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
    
    skipped_groups = []
    error_groups = []
    
    for group in groups:
        print(f"Processing group: {group.id} - {group.name}")
        
        # Check if submission already exists for this group and assignment and classroom
        existing_submissions = await get_submissions(
            db, 
            assignment_id=request.assignment_id,
            classroom_id=request.classroom_id,
            group_id=group.id
        )
        
        print(f"Found {len(existing_submissions)} existing submissions for group {group.id}")
        
        if existing_submissions:
            # Skip if submission already exists
            print(f"Skipping group {group.id} - submission already exists")
            skipped_groups.append(group.name)
            continue
            
        # Create a new submission for this group
        submission_data = SubmissionCreate(
            assignment_id=request.assignment_id,
            classroom_id=request.classroom_id,
            group_id=group.id,
            comments=f"Empty submission for {group.name}",
            status="draft"
        )
        
        try:
            submission = await create_submission(db, submission_data)
            created_submissions.append(submission)
            print(f"Created submission for group {group.id}: {submission.id}")
        except Exception as e:
            print(f"Error creating submission for group {group.id}: {e}")
            error_groups.append(group.name)
            continue
    
    message_parts = []
    if created_submissions:
        message_parts.append(f"Generated {len(created_submissions)} new submission(s)")
    if skipped_groups:
        message_parts.append(f"Skipped {len(skipped_groups)} group(s) (already have submissions)")
    if error_groups:
        message_parts.append(f"Failed to create {len(error_groups)} submission(s)")
    
    return {
        "message": ". ".join(message_parts) if message_parts else "No submissions created",
        "count": len(created_submissions),
        "skipped": len(skipped_groups),
        "errors": len(error_groups),
        "submissions": [
            {
                "id": sub.id,
                "group_id": sub.group_id,
                "group_name": next((g.name for g in groups if g.id == sub.group_id), "Unknown"),
                "status": sub.status
            } for sub in created_submissions
        ],
        "skipped_groups": skipped_groups,
        "error_groups": error_groups
    }


@router.post("/{submission_id}/ai-evaluate")
async def ai_evaluate_submission(
    submission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """AI evaluation of submission exercises using Google AI service"""
   
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    assignment = await get_assignment(db, submission.assignment_id)# Get exercises for assignment
    exercises = await get_assignment_exercises(db, submission.assignment_id)
    try:
        # Get prompt for submission evaluation depending on language of assignment
        assignment_language = assignment.language if assignment.language else 'catalan'
        prompt = get_submission_evaluation_prompt(exercises, assignment_language)
        
        logger.info(f"Using submission evaluation prompt for language '{assignment_language}':")
        logger.info(f"Prompt: {prompt}")
        # Get api key from settings or environment
        google_ai_service = GoogleAIService(api_key=settings.GOOGLE_AI_API_KEY)

        result = google_ai_service.analyse_pdf(
            pdf_bytes=submission.pdf_file_data,
            prompt=prompt
        )
        
        logger.info(f"Exercise evaluation result: {result}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI evaluation failed: {str(e)}")


@router.post("/{submission_id}/ai-evaluate-public-report")
async def ai_evaluate_public_report(
    submission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """AI evaluation of public report using the public report evaluation prompt"""

    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if not submission.public_pdf_data:
        raise HTTPException(status_code=404, detail="No public report PDF found for this submission")

    assignment = await get_assignment(db, submission.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    try:
        # Get prompt for exercise extraction depending on language of assignment
        # Use assignment language if available, otherwise default to 'catalan'
        assignment_language = assignment.language if assignment.language else 'catalan'
        prompt = get_public_report_evaluation_prompt(assignment_language)
        
        logger.info(f"Using public report evaluation prompt for language '{assignment_language}':")
        logger.info(f"Prompt: {prompt}")
        # Get api key from settings or environment
        google_ai_service = GoogleAIService(api_key=settings.GOOGLE_AI_API_KEY)

        result = google_ai_service.analyse_pdf(
            pdf_bytes=submission.public_pdf_data,  # Use submission's public PDF data, sheet assignment's
            prompt=prompt
        )

        logger.info(f"Public report evaluation result: {result}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )



@router.post("/{submission_id}/ai-evaluate-private-report")
async def ai_evaluate_private_report(
    submission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """AI evaluation of private report using the private report evaluation prompt"""

    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if not submission.private_pdf_data:
        raise HTTPException(status_code=404, detail="No private report PDF found for this submission")

    assignment = await get_assignment(db, submission.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Get group information
    group = None
    if submission.group_id:
        group = await get_group(db, submission.group_id)
    
    # Extract member names from group.members (JSON array of dicts)
    members_str = ""
    if group and group.members:
        try:
            member_names = [member.get("name", "Unknown") for member in group.members if isinstance(member, dict)]
            members_str = ', '.join(member_names)
        except (AttributeError, TypeError) as e:
            logger.warning(f"Failed to extract member names: {e}")
            members_str = "Unknown members"
    
    # Parse coordinators from submission.coordinators (JSON string)
    coordinators_str = ""
    if submission.coordinators:
        try:
            if submission.coordinators.startswith('['):
                # JSON format
                coordinators = json.loads(submission.coordinators)
                coordinators_str = ', '.join(coordinators) if isinstance(coordinators, list) else str(coordinators)
            else:
                # Already a string
                coordinators_str = submission.coordinators
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Failed to parse coordinators: {e}")
            coordinators_str = submission.coordinators or ""
    
    # Fallback values if no data found
    if not members_str:
        raise HTTPException(status_code=400, detail="No members found for the submission assignment")
        members_str = "Unknown members"
    if not coordinators_str:
        raise HTTPException(status_code=400, detail="No coordinators found for the submission assignment")
        
    
    try:
        # Get prompt for exercise extraction depending on language of assignment
        # Use assignment language if available, otherwise default to 'catalan'
        assignment_language = assignment.language if assignment.language else 'catalan'
        prompt = get_private_report_evaluation_prompt(coordinators_str, members_str, assignment_language)
        
        logger.info(f"Using private report evaluation prompt for language '{assignment_language}':")
        logger.info(f"Coordinators: {coordinators_str}")
        logger.info(f"Members: {members_str}")
        logger.info(f"Prompt: {prompt}")
        # Get api key from settings or environment
        google_ai_service = GoogleAIService(api_key=settings.GOOGLE_AI_API_KEY)

        result = google_ai_service.analyse_pdf(
            pdf_bytes=submission.private_pdf_data,
            prompt=prompt
        )

        logger.info(f"Private report evaluation result: {result}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Private report evaluation failed: {str(e)}"
        )

@router.get("/classroom/{classroom_id}/assignment/{assignment_id}/grades.xlsx")
async def generate_classroom_assignment_grades_xlsx(
    classroom_id: int,
    assignment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate XLS file with grades for a specific classroom and assignment"""
    
    try:
        # Get assignment with exercises
        assignment_result = await db.execute(
            select(Assignment)
            .options(selectinload(Assignment.exercises))
            .where(Assignment.id == assignment_id)
        )
        assignment = assignment_result.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Get classroom
        classroom_result = await db.execute(
            select(Classroom).where(Classroom.id == classroom_id)
        )
        classroom = classroom_result.scalar_one_or_none()
        
        if not classroom:
            raise HTTPException(status_code=404, detail="Classroom not found")
        
        # Get submissions for this assignment and classroom
        submissions_result = await db.execute(
            select(Submission)
            .options(
                selectinload(Submission.group),
                joinedload(Submission.assignment)
            )
            .where(
                and_(
                    Submission.assignment_id == assignment_id,
                    Submission.classroom_id == classroom_id
                )
            )
            .order_by(Submission.submitted_at.desc())
        )
        submissions = submissions_result.scalars().all()
        
        if not submissions:
            raise HTTPException(status_code=404, detail="No submissions found for this assignment and classroom")
        
        # Convert to dictionaries for Excel service
        assignment_dict = {
            "id": assignment.id,
            "name": assignment.name,
            "description": assignment.description,
            "due_date": assignment.due_date,
            "language": assignment.language,
            "exercises": [
                {
                    "id": exercise.id,
                    "description": exercise.description,
                    "points": exercise.points,
                    "order": exercise.order,
                    "evaluation_criteria": exercise.evaluation_criteria
                }
                for exercise in assignment.exercises
            ]
        }
        
        classroom_dict = {
            "id": classroom.id,
            "name": classroom.name,
            "teacher_name": classroom.teacher_name,
            "language": classroom.language,
            "course_id": classroom.course_id,
            "semester_id": classroom.semester_id
        }
        
        submissions_list = []
        for submission in submissions:
            submission_dict = {
                "id": submission.id,
                "group_id": submission.group_id,
                "group": {
                    "id": submission.group.id if submission.group else None,
                    "name": submission.group.name if submission.group else None,
                    "members": submission.group.members if submission.group else []
                } if submission.group else None,
                "meeting_notes": submission.meeting_notes,
                "total_score": submission.total_score,
                "percentage_score": submission.percentage_score,
                "grade_breakdown": submission.grade_breakdown or [],
                "ai_feedback": submission.ai_feedback,
                "teacher_feedback": submission.teacher_feedback,
                "status": submission.status,
                "submitted_at": submission.submitted_at
            }
            submissions_list.append(submission_dict)
        
        # Generate Excel file
        excel_service = ExcelGradeService()
        excel_bytes = excel_service.generate_classroom_assignment_grades(
            assignment_dict, 
            submissions_list, 
            classroom_dict
        )
        
        # Create filename
        assignment_name = assignment.name.replace(" ", "_").replace("/", "_")
        classroom_name = classroom.name.replace(" ", "_").replace("/", "_")
        filename = f"grades_{classroom_name}_{assignment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating XLS grades: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate XLS file: {str(e)}")


@router.put("/{submission_id}/private-report-evaluation")
async def save_private_report_evaluation(
    submission_id: int,
    evaluation_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Save private report evaluation results"""
    
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    try:
        # Update the submission with the evaluation data
        submission.private_report_evaluation = evaluation_data
        submission.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(submission)
        
        logger.info(f"Private report evaluation saved for submission {submission_id}")
        
        return {"message": "Private report evaluation saved successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error saving private report evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save evaluation: {str(e)}")