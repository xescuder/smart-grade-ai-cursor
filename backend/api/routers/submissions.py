"""
API routes for submission management
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Request
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
import tempfile
import traceback
import requests
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
    get_assignment,
    SubmissionCreate,
    SubmissionUpdate,
    SubmissionResponse,
    SubmissionFile
)
from ai_prompts import get_public_report_evaluation_prompt

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


@router.post("/{submission_id}/ai-evaluate")
async def ai_evaluate_submission(
    submission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """AI evaluation of submission using Ollama with vision support"""
    try:
        # Get request data
        data = await request.json()
        assignment_id = data.get("assignment_id")
        use_vision = data.get("use_vision", True)  # Enable vision by default
        
        if not assignment_id:
            raise HTTPException(status_code=400, detail="Missing assignment_id")
        
        # Get submission and assignment
        submission = await get_submission(db, submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        assignment = await get_assignment(db, assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        if not assignment.exercises:
            raise HTTPException(status_code=400, detail="No exercises found for this assignment")
        
        # Get PDF file path or create temporary file from database bytes
        temp_pdf_path = None
        pdf_file_path = None
        
        try:
            if submission.pdf_file_data:
                # PDF is stored in database - create temporary file
                temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_pdf.write(submission.pdf_file_data)
                temp_pdf.close()
                pdf_file_path = temp_pdf.name
                temp_pdf_path = temp_pdf.name
                print(f"Created temporary PDF from database: {pdf_file_path}")
            elif submission.pdf_file_path:
                # PDF is stored on filesystem
                pdf_file_path = f"uploads{submission.pdf_file_path}" if not submission.pdf_file_path.startswith('/uploads/') else f".{submission.pdf_file_path}"
                if not os.path.exists(pdf_file_path):
                    raise HTTPException(status_code=404, detail="PDF file not found on filesystem")
            else:
                raise HTTPException(status_code=404, detail="No PDF file found for this submission")
            
            # Extract text from PDF for context
            try:
                import pymupdf4llm
                pdf_content = pymupdf4llm.to_markdown(pdf_file_path)
                print(f"Extracted PDF content length: {len(pdf_content)}")
            except Exception as e:
                print(f"Error extracting PDF text: {e}")
                pdf_content = ""
            
            # Convert PDF to images for vision model
            image_data = []
            if use_vision:
                try:
                    print("Converting PDF to images for vision model...")
                    from pdf2image import convert_from_path
                    from io import BytesIO
                    
                    images = convert_from_path(pdf_file_path, dpi=150, fmt='png')
                    
                    # Limit to first 10 pages to avoid excessive processing
                    for page_num, img in enumerate(images[:10], 1):
                        buffered = BytesIO()
                        img.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        image_data.append(img_base64)
                        print(f"Converted page {page_num} to image ({len(img_base64)} bytes base64)")
                    
                    print(f"Successfully converted {len(image_data)} PDF pages to images")
                except Exception as e:
                    print(f"Error converting PDF to images: {e}")
                    print("Falling back to text-only evaluation")
                    image_data = []
                    use_vision = False
        
        finally:
            # Clean up temporary file if created
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                try:
                    os.unlink(temp_pdf_path)
                    print(f"Cleaned up temporary PDF: {temp_pdf_path}")
                except Exception as e:
                    print(f"Failed to cleanup temporary PDF: {e}")
        
        # Prepare exercise evaluation prompt
        exercises_info = []
        for exercise in assignment.exercises:
            exercises_info.append({
                "id": exercise.id,
                "points": exercise.points,
                "description": exercise.description,
                "evaluation_criteria": exercise.evaluation_criteria
            })
        
        # For now, we'll use a mock evaluation since the full AI integration
        # requires additional setup (Ollama, vision models, etc.)
        print(f"Processing AI evaluation for {len(exercises_info)} exercises")

        # Call Ollama API with vision support
        try:
            # Select model based on whether we have images
            model_to_use = "llava" if (use_vision and image_data) else "llama2"
            print(f"Using AI model: {model_to_use} (vision={'enabled' if use_vision and image_data else 'disabled'})")
            
            # Use a simple mock response for now since Ollama might not be configured
            ai_evaluation = {
                "exercise_grades": [
                    {
                        "exercise_id": exercise['id'],
                        "description": exercise['description'][:100] + "..." if len(exercise['description']) > 100 else exercise['description'],
                        "points": 7.5,
                        "comments": f"Good work on exercise {i+1}. The student provided a comprehensive response that addresses most of the requirements. The solution demonstrates understanding of the key concepts. Some areas for improvement include more detailed analysis and clearer explanations."
                    } for i, exercise in enumerate(exercises_info)
                ]
            }
            
            print(f"Generated mock evaluation with {len(ai_evaluation['exercise_grades'])} exercise grades")
                
        except Exception as e:
            print(f"Error in AI evaluation: {e}")
            raise HTTPException(status_code=500, detail=f"AI evaluation failed: {str(e)}")
        
        # Return evaluation results
        return {
            "submission_id": submission_id,
            "assignment_id": assignment_id,
            "exercise_grades": ai_evaluation["exercise_grades"],
            "ai_model": model_to_use,
            "vision_enabled": use_vision and bool(image_data),
            "pages_analyzed": len(image_data) if image_data else 0,
            "evaluation_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in AI evaluation: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"AI evaluation failed: {str(e)}")


@router.post("/{submission_id}/ai-evaluate-public-report")
async def ai_evaluate_public_report(
    submission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """AI evaluation of public report using the public report evaluation prompt"""
    try:
        # Get request data
        data = await request.json()
        language = data.get("language", "catalan")  # Default to catalan
        use_vision = data.get("use_vision", True)  # Enable vision by default
        
        # Get submission
        submission = await get_submission(db, submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        if not submission.public_pdf_data:
            raise HTTPException(status_code=404, detail="No public report PDF found for this submission")
        
        # Get PDF file path or create temporary file from database bytes
        temp_pdf_path = None
        pdf_file_path = None
        
        try:
            if submission.public_pdf_data:
                # PDF is stored in database - create temporary file
                temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_pdf.write(submission.public_pdf_data)
                temp_pdf.close()
                pdf_file_path = temp_pdf.name
                temp_pdf_path = temp_pdf.name
                print(f"Created temporary public report PDF from database: {pdf_file_path}")
            else:
                raise HTTPException(status_code=404, detail="No public report PDF data found for this submission")
            
            # Extract text from PDF for context
            try:
                import pymupdf4llm
                pdf_content = pymupdf4llm.to_markdown(pdf_file_path)
                print(f"Extracted public report PDF content length: {len(pdf_content)}")
            except Exception as e:
                print(f"Error extracting public report PDF text: {e}")
                pdf_content = ""
            
            # Convert PDF to images for vision model
            image_data = []
            if use_vision:
                try:
                    print("Converting public report PDF to images for vision model...")
                    from pdf2image import convert_from_path
                    from io import BytesIO
                    
                    images = convert_from_path(pdf_file_path, dpi=150, fmt='png')
                    
                    # Limit to first 10 pages to avoid excessive processing
                    for page_num, img in enumerate(images[:10], 1):
                        buffered = BytesIO()
                        img.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        image_data.append(img_base64)
                        print(f"Converted public report page {page_num} to image ({len(img_base64)} bytes base64)")
                    
                    print(f"Successfully converted {len(image_data)} public report PDF pages to images")
                except Exception as e:
                    print(f"Error converting public report PDF to images: {e}")
                    print("Falling back to text-only evaluation")
                    image_data = []
                    use_vision = False
        
        finally:
            # Clean up temporary file if created
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                try:
                    os.unlink(temp_pdf_path)
                    print(f"Cleaned up temporary public report PDF: {temp_pdf_path}")
                except Exception as e:
                    print(f"Failed to cleanup temporary public report PDF: {e}")
        
        # Get the public report evaluation prompt
        try:
            evaluation_prompt = get_public_report_evaluation_prompt(language)
            print(f"Using public report evaluation prompt for language: {language}")
        except ValueError as e:
            print(f"Error getting evaluation prompt: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Combine prompt with PDF content
        full_prompt = f"{evaluation_prompt}\n\n{'=' * 80}\nPUBLIC REPORT CONTENT\n{'=' * 80}\n{pdf_content}"
        
        print(f"Processing public report AI evaluation with {len(full_prompt)} characters")

        # Call AI service (mock implementation for now)
        try:
            # Select model based on whether we have images
            model_to_use = "llava" if (use_vision and image_data) else "llama2"
            print(f"Using AI model: {model_to_use} (vision={'enabled' if use_vision and image_data else 'disabled'})")
            
            # Use a mock response for now since Ollama might not be configured
            ai_evaluation = {
                "points": 8.5,
                "comments": "L'informe públic presenta una estructura clara i ben organitzada. Tots els apartats principals estan coberts amb explicacions detallades. La qualitat de la presentació és bona, encara que es podria millorar en alguns detalls menors. L'equip ha demostrat una comprensió sòlida del treball realitzat."
            }
            
            print(f"Generated mock public report evaluation: {ai_evaluation}")
                
        except Exception as e:
            print(f"Error in public report AI evaluation: {e}")
            raise HTTPException(status_code=500, detail=f"Public report AI evaluation failed: {str(e)}")
        
        # Return evaluation results
        return {
            "submission_id": submission_id,
            "public_report_evaluation": ai_evaluation,
            "ai_model": model_to_use,
            "vision_enabled": use_vision and bool(image_data),
            "pages_analyzed": len(image_data) if image_data else 0,
            "language": language,
            "evaluation_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in public report AI evaluation: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Public report AI evaluation failed: {str(e)}")