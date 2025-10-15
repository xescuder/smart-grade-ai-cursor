#!/usr/bin/env python3
"""
FastAPI server with PostgreSQL database integration
"""

from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import csv
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from pydantic import ValidationError, BaseModel
from datetime import datetime
import os
import tempfile
import uuid
import json
from typing import List, Dict, Any, Optional

# AI Processing imports
import pymupdf4llm
import fitz  # PyMuPDF direct import
import re  # Regular expressions for pattern matching
import requests
from dotenv import load_dotenv
import logging
import traceback

# Configuration
from core.config import settings

# Set up logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
ASSIGNMENT_NOT_FOUND = "Assignment not found"
NO_PDF_FOUND = "No PDF file found for this assignment"

from database import get_db, init_db, close_db, Assignment, Exercise, SectionExtractionConfig, Submission, Group, Course, Semester, AiSetting, Classroom
from crud import (
    create_assignment, get_assignments, get_assignment, update_assignment, delete_assignment,
    get_assignment_exercises, update_assignment_exercises, update_assignment_pdf, remove_assignment_pdf,
    AssignmentCreate, AssignmentUpdate, AssignmentResponse, ExerciseUpdate, ExerciseResponse,
    get_section_extraction_configs, get_section_extraction_config, create_section_extraction_config,
    update_section_extraction_config, delete_section_extraction_config,
    SectionExtractionConfigCreate, SectionExtractionConfigUpdate, SectionExtractionConfigResponse,
    get_submissions, get_submission, get_submissions_by_assignment, create_submission, update_submission, delete_submission,
    SubmissionCreate, SubmissionUpdate, SubmissionResponse, StudentInfo, SubmissionFile, ExerciseGrade,
    get_groups, get_group, get_group_by_name, create_group, update_group, delete_group, get_groups_by_course,
    GroupCreate, GroupUpdate, GroupResponse, GroupMember,
    get_courses, get_course, get_course_by_code, create_course, update_course, delete_course, get_courses_by_department,
    get_courses_with_semesters, get_course_with_semesters,
    CourseCreate, CourseUpdate, CourseResponse,
    get_semesters, get_semester, get_semester_any_status, get_semester_by_code, create_semester, update_semester, delete_semester,
    get_semesters_by_year, get_semesters_by_course, get_current_semester, SemesterCreate, SemesterUpdate, SemesterResponse,
    update_assignment_pdf_bytes,
    get_classrooms, get_classroom, get_classroom_with_details, create_classroom, update_classroom, delete_classroom,
    ClassroomCreate, ClassroomUpdate, ClassroomResponse
)
from ai_prompts import get_submission_evaluation_prompt

# FastAPI app with comprehensive OpenAPI/Swagger configuration
app = FastAPI(
    title="Smart Grade AI API",
    description="""
## AI-Powered Grading System API

Smart Grade AI automates assignment grading using advanced AI models, providing
consistent, detailed feedback to students while saving teachers valuable time.

### Key Features

* 🎓 **Assignment Management**: Create, update, and organize assignments
* 📄 **PDF Processing**: Upload and extract exercises from PDF statements
* 🤖 **AI Grading**: Automatic submission evaluation with detailed feedback
* 👥 **Group Management**: Organize students into groups and classrooms
* 📊 **Analytics**: Track performance and grading statistics
* 🔧 **Configuration**: Customize AI models and extraction settings

### AI Providers Supported

- **Ollama** (Local, Free): Privacy-focused, offline-capable
- **OpenAI GPT-4**: Advanced cloud-based grading
- **Anthropic Claude**: High-quality AI analysis

### Database

PostgreSQL with async support, storing PDFs directly in database for reliability.

### Authentication

JWT-based authentication with role-based access control (Teachers/Students).
    """,
    version="1.0.0",
    contact={
        "name": "Smart Grade AI Team",
        "url": "https://github.com/your-repo/smart-grade-ai-cursor",
        "email": "support@smartgrade.ai"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "assignments",
            "description": "Assignment CRUD operations, PDF upload, and exercise extraction"
        },
        {
            "name": "exercises",
            "description": "Manage exercises within assignments"
        },
        {
            "name": "submissions",
            "description": "Student submission handling and grading"
        },
        {
            "name": "courses",
            "description": "Course and semester management"
        },
        {
            "name": "classrooms",
            "description": "Classroom and student group organization"
        },
        {
            "name": "groups",
            "description": "Student group management"
        },
        {
            "name": "semesters",
            "description": "Academic semester management"
        },
        {
            "name": "admin",
            "description": "Administrative settings and configuration"
        },
        {
            "name": "health",
            "description": "System health and status checks"
        }
    ]
)

# Mount static files for uploads
import os
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Initialize Ollama client (local LLM) - use centralized configuration
OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL
ollama_available = False

async def get_dynamic_section_markers(db: AsyncSession):
    """Get section markers from database configuration"""
    try:
        configs = await get_section_extraction_configs(db)
        all_markers = []
        
        for config in configs:
            try:
                markers_list = json.loads(config.markers)
                all_markers.extend(markers_list)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in section config {config.id}: {config.markers}")
                continue
                
        # If no configs found, return default markers
        if not all_markers:
            all_markers = [
                "què s'ha de lliurar", "que s'ha de lliurar", "qué s'ha de lliurar",
                "deliverables", "entregables", "tasques", "tareas", "tasks",
                "lliurar", "entregar", "deliver", "submission", "submissió",
                "consisteix en", "consta de", "exercicis:", "ejercicios:",
                "activitat", "actividades", "activities", "exercici", "ejercicio",
                "exercise", "práctica", "pràctica", "practice",
                "pac 1 consisteix", "pac consisteix", "assignació consisteix",
                "descripció de la pac", "descripcio de la pac", "descripció"
            ]
            
        return all_markers
    except Exception as e:
        logger.error(f"Error getting dynamic section markers: {e}")
        # Return default markers as fallback
        return [
            "què s'ha de lliurar", "que s'ha de lliurar", "descripció",
            "deliverables", "entregables", "lliurar", "consisteix en"
        ]

def check_ollama_availability():
    """Check if Ollama is running and available"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            available_models = [model["name"] for model in models]
            if available_models:
                print(f"✅ Ollama is running with models: {', '.join(available_models[:3])}")
                # Check if exact model exists, or if model base name exists with any tag
                model_found = False
                if OLLAMA_MODEL in available_models:
                    model_found = True
                else:
                    # Check for model without tag (e.g., llama2 matches llama2:latest)
                    base_model = OLLAMA_MODEL.split(':')[0]
                    for model in available_models:
                        if model.startswith(f"{base_model}:") or model == base_model:
                            print(f"✅ Using model: {model} (requested: {OLLAMA_MODEL})")
                            model_found = True
                            break
                
                if not model_found:
                    print(f"⚠️  Model '{OLLAMA_MODEL}' not found. Available: {', '.join(available_models)}")
                    print(f"   Set OLLAMA_MODEL environment variable to use a different model.")
                return True
            else:
                print("⚠️  Ollama is running but no models are available.")
                print("   Please install a model: ollama pull llama2")
                return False
        else:
            print("⚠️  Ollama server responded with error")
            return False
    except requests.exceptions.RequestException:
        print("⚠️  Ollama not running. AI extraction will not be available.")
        print("   Start Ollama: ollama serve")
        print("   Install a model: ollama pull llama2")
        return False

ollama_available = check_ollama_availability()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist (use centralized config)
UPLOAD_DIR = settings.UPLOAD_DIR
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    await close_db()

@app.get("/")
def root():
    return {"message": "Smart Grade AI API with PostgreSQL", "status": "active"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "database": "postgresql"}

@app.get("/debug-early")
def debug_early():
    return {"message": "Early debug endpoint works"}

# === WORKING COURSE AND SEMESTER ENDPOINTS ===
# Removed duplicate course endpoints - using the full CRUD versions with proper validation instead

@app.get("/api/semesters")
async def get_semesters_working(db: AsyncSession = Depends(get_db)):
    """Get all semesters - working version"""
    try:
        semesters = await get_semesters(db, created_by=1)
        return semesters
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch semesters: {str(e)}")

@app.post("/api/semesters")
async def create_semester_working(request: Request, db: AsyncSession = Depends(get_db)):
    """Create a semester - working version"""
    try:
        data = await request.json()
        
        # Fix datetime timezone issues - convert to naive datetimes
        from datetime import datetime
        if 'start_date' in data and isinstance(data['start_date'], str):
            # Remove timezone info completely
            date_str = data['start_date'].replace('Z', '').replace('+00:00', '')
            if 'T' in date_str:
                data['start_date'] = datetime.fromisoformat(date_str)
            else:
                data['start_date'] = datetime.fromisoformat(date_str + 'T00:00:00')
        if 'end_date' in data and isinstance(data['end_date'], str):
            # Remove timezone info completely  
            date_str = data['end_date'].replace('Z', '').replace('+00:00', '')
            if 'T' in date_str:
                data['end_date'] = datetime.fromisoformat(date_str)
            else:
                data['end_date'] = datetime.fromisoformat(date_str + 'T00:00:00')
        
        semester_data = SemesterCreate(**data)
        semester = await create_semester(db, semester_data)
        return semester
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create semester: {str(e)}")

# Assignment endpoints
@app.get("/api/assignments")
async def get_all_assignments(db: AsyncSession = Depends(get_db)):
    """Get all assignments with exercises and classrooms"""
    assignments = await get_assignments(db)
    # Convert to dict to avoid lazy loading issues
    result = []
    for assignment in assignments:
        assignment_dict = {
            "id": assignment.id,
            "name": assignment.name,
            "description": assignment.description,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "language": assignment.language,
            "pdf_file_path": assignment.pdf_file_path,
            "pdf_file_name": assignment.pdf_file_name,
            "created_by": assignment.created_by,
            "is_active": assignment.is_active,
            "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
            "updated_at": assignment.updated_at.isoformat() if assignment.updated_at else None,
            "exercises": [
                {
                    "id": ex.id,
                    "assignment_id": ex.assignment_id,
                    "description": ex.description,
                    "evaluation_criteria": ex.evaluation_criteria,
                    "points": ex.points,
                    "order": ex.order,
                    "created_at": ex.created_at.isoformat() if ex.created_at else None,
                    "updated_at": ex.updated_at.isoformat() if ex.updated_at else None,
                }
                for ex in assignment.exercises
            ],
            "classrooms": [
                {
                    "id": classroom.id,
                    "name": classroom.name,
                    "teacher_name": classroom.teacher_name,
                    "language": classroom.language,
                }
                for classroom in assignment.classrooms
            ]
        }
        result.append(assignment_dict)
    return result

@app.get("/api/assignments/{assignment_id}", response_model=AssignmentResponse)
async def get_single_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single assignment by ID"""
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    return assignment

@app.post("/api/assignments", response_model=AssignmentResponse)
async def create_new_assignment(assignment: AssignmentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new assignment"""
    try:
        logger.info(f"Creating assignment: {assignment}")
        logger.info(f"Assignment type: {type(assignment)}")
        logger.info(f"Due date type: {type(assignment.due_date)}")
        logger.info(f"Due date value: {assignment.due_date}")
        
        # Validate classrooms exist and all have matching language
        if assignment.classroom_ids:
            for classroom_id in assignment.classroom_ids:
                classroom = await get_classroom(db, classroom_id)
                if not classroom:
                    raise HTTPException(status_code=404, detail=f"Classroom {classroom_id} not found")
                
                if assignment.language != classroom.language:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Assignment language ({assignment.language}) must match all classroom languages. Classroom '{classroom.name}' has language '{classroom.language}'"
                    )
        
        # Mock user ID for demo - in production, get from authentication
        created_by = 1
        result = await create_assignment(db, assignment, created_by)
        logger.info(f"Assignment created successfully: {result.id}")
        
        # Get the assignment with exercises loaded
        from crud import get_assignment
        full_assignment = await get_assignment(db, result.id)
        if not full_assignment:
            raise HTTPException(status_code=500, detail="Failed to retrieve created assignment")
        
        logger.info(f"Retrieved assignment with exercises: {len(full_assignment.exercises)}")
        return full_assignment
    except Exception as e:
        logger.error(f"Error creating assignment: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create assignment: {str(e)}")


@app.put("/api/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_existing_assignment(assignment_id: int, assignment_update: AssignmentUpdate, db: AsyncSession = Depends(get_db)):
    """Update an assignment"""
    updated_assignment = await update_assignment(db, assignment_id, assignment_update)
    if not updated_assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    return updated_assignment

@app.delete("/api/assignments/{assignment_id}")
async def delete_existing_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an assignment"""
    success = await delete_assignment(db, assignment_id)
    if not success:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    return {"success": True, "message": "Assignment deleted"}

@app.get("/api/assignments/{assignment_id}/export")
async def export_assignment_submissions(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Export assignment submissions as CSV"""
    try:
        # Get assignment with exercises
        assignment = await get_assignment(db, assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
        
        # Get all submissions for this assignment with related data
        result = await db.execute(
            select(Submission)
            .options(
                selectinload(Submission.group),
                selectinload(Submission.course),
                selectinload(Submission.semester)
            )
            .where(Submission.assignment_id == assignment_id)
            .order_by(Submission.submitted_at.desc())
        )
        submissions = result.scalars().all()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Create header row
        header = ["Group"]
        for i, exercise in enumerate(assignment.exercises):
            header.extend([
                f"Exercise {i + 1} - Points",
                f"Exercise {i + 1} - Comments"
            ])
        header.append("Final Score (0-10)")
        writer.writerow(header)
        
        # Process each submission
        for submission in submissions:
            row = []
            
            # Group name
            group_name = submission.group.name if submission.group else f"Group {submission.group_id}"
            row.append(group_name)
            
            # Exercise grades
            grade_breakdown = submission.grade_breakdown or []
            total_weighted_score = 0
            max_possible_score = 0
            
            for exercise in assignment.exercises:
                # Find grade for this exercise
                exercise_grade = next(
                    (grade for grade in grade_breakdown if grade.get('exercise_id') == exercise.id),
                    None
                )
                
                if exercise_grade:
                    points = exercise_grade.get('score', exercise_grade.get('points', 0))
                    comments = exercise_grade.get('feedback', exercise_grade.get('comments', ''))
                else:
                    points = 0
                    comments = ''
                
                row.extend([points, comments])
                
                # Calculate weighted score (points * exercise_weight / 10)
                # Each exercise is worth exercise.points out of 100 total
                weighted_points = points * exercise.points / 10
                total_weighted_score += weighted_points
                max_possible_score += exercise.points  # Max points for this exercise
            
            # Calculate final score (0-10 scale)
            if max_possible_score > 0:
                final_score = (total_weighted_score / max_possible_score) * 10
            else:
                final_score = 0
            
            row.append(round(final_score, 2))
            writer.writerow(row)
        
        # Prepare CSV response
        csv_content = output.getvalue()
        output.close()
        
        # Create filename
        assignment_name = assignment.name.replace(' ', '_').replace('/', '_')
        filename = f"{assignment_name}_submissions.csv"
        
        # Return CSV file
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting assignment submissions: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to export submissions: {str(e)}")

# Exercise endpoints
@app.get("/api/assignments/{assignment_id}/exercises", response_model=List[ExerciseResponse])
async def get_exercises_for_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Get all exercises for an assignment"""
    exercises = await get_assignment_exercises(db, assignment_id)
    return exercises

@app.put("/api/assignments/{assignment_id}/exercises", response_model=List[ExerciseResponse])
async def update_exercises_for_assignment(assignment_id: int, exercises: List[ExerciseUpdate], db: AsyncSession = Depends(get_db)):
    """Update exercises for an assignment"""
    # Validate assignment exists
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    # Validate total points
    total_points = sum(exercise.points for exercise in exercises)
    if total_points != 100:
        raise HTTPException(status_code=400, detail=f"Total points must equal 100, got {total_points}")
    
    
    updated_exercises = await update_assignment_exercises(db, assignment_id, exercises)
    return updated_exercises

# PDF endpoints
@app.post("/api/assignments/{assignment_id}/upload-pdf")
async def upload_assignment_pdf(assignment_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Upload PDF file for assignment (stored as bytes in Postgres)."""
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)

    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")

    # Persist in DB as bytes and clear any filesystem path
    updated_assignment = await update_assignment_pdf_bytes(
        db=db,
        assignment_id=assignment_id,
        file_bytes=content,
        file_name=file.filename,
        mime_type="application/pdf",
    )

    return {
        "success": True,
        "message": "PDF uploaded successfully",
        "file_name": updated_assignment.pdf_file_name,
        "stored_in": "database",
    }

@app.get("/api/assignments/{assignment_id}/pdf")
async def view_assignment_pdf(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """View/download PDF file for assignment (DB bytes preferred)."""
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)

    # Serve from DB if bytes available
    if getattr(assignment, "pdf_file_data", None):
        return StreamingResponse(
            io.BytesIO(assignment.pdf_file_data),
            media_type=(assignment.pdf_mime_type or "application/pdf"),
            headers={"Content-Disposition": f"inline; filename={assignment.pdf_file_name or 'assignment.pdf'}"},
        )

    if not assignment.pdf_file_path:
        raise HTTPException(status_code=404, detail=NO_PDF_FOUND)
    
    # Handle Google Drive reference
    if assignment.pdf_file_path and assignment.pdf_file_path.startswith("gdrive:"):
        drive_file_id = assignment.pdf_file_path.split(":", 1)[1]
        # Redirect to Google Drive viewer/download URL; relies on file being shared/accessible
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"https://drive.google.com/uc?export=download&id={drive_file_id}")

    file_path = assignment.pdf_file_path.lstrip('/')
    
    # For demo purposes, return a mock PDF if file doesn't exist
    if not os.path.exists(file_path):
        mock_pdf_content = b"""%PDF-1.4
1 0 obj
<</Type/Catalog/Pages 2 0 R>>
endobj
2 0 obj
<</Type/Pages/Kids[3 0 R]/Count 1>>
endobj
3 0 obj
<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>
endobj
4 0 obj
<</Length 44>>
stream
BT
/F1 12 Tf
100 700 Td
(Assignment Instructions) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000010 00000 n
0000000053 00000 n
0000000100 00000 n
0000000179 00000 n
trailer
<</Size 5/Root 1 0 R>>
startxref
273
%%EOF"""
        return Response(content=mock_pdf_content, media_type="application/pdf")
    
    return FileResponse(
        file_path, 
        media_type="application/pdf", 
        filename=assignment.pdf_file_name,
        headers={"Content-Disposition": "inline; filename=" + assignment.pdf_file_name}
    )

@app.delete("/api/assignments/{assignment_id}/pdf")
async def delete_assignment_pdf(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Delete PDF file for assignment"""
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    if not assignment.pdf_file_path:
        raise HTTPException(status_code=404, detail=NO_PDF_FOUND)
    
    # Remove file from filesystem
    file_path = assignment.pdf_file_path.lstrip('/')
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Remove PDF info from database
    await remove_assignment_pdf(db, assignment_id)
    
    return {"success": True, "message": "PDF deleted successfully"}

# Add inline PDF viewing endpoint for the frontend
@app.get("/api/assignments/{assignment_id}/download/statement")
async def view_assignment_pdf_inline(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """View PDF file inline for assignment (DB bytes preferred)"""
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    # Serve from DB if bytes available (preferred method)
    if getattr(assignment, "pdf_file_data", None):
        return StreamingResponse(
            io.BytesIO(assignment.pdf_file_data),
            media_type=(assignment.pdf_mime_type or "application/pdf"),
            headers={"Content-Disposition": "inline"}
        )
    
    # Fallback to filesystem
    if not assignment.pdf_file_path:
        raise HTTPException(status_code=404, detail=NO_PDF_FOUND)
    
    # Handle Google Drive reference
    if assignment.pdf_file_path.startswith("gdrive:"):
        drive_file_id = assignment.pdf_file_path.split(":", 1)[1]
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"https://drive.google.com/uc?export=download&id={drive_file_id}")
    
    file_path = assignment.pdf_file_path.lstrip('/')
    
    # Try to find the file
    if not os.path.exists(file_path):
        # Try to find the file with a different pattern
        uploads_dir = settings.UPLOAD_DIR
        if os.path.exists(uploads_dir):
            for filename in os.listdir(uploads_dir):
                if filename.startswith(f"assignment_{assignment_id}_") and filename.endswith('.pdf'):
                    file_path = os.path.join(uploads_dir, filename)
                    break
            else:
                raise HTTPException(status_code=404, detail=NO_PDF_FOUND)
        else:
            raise HTTPException(status_code=404, detail=NO_PDF_FOUND)
    
    # Return the PDF file inline for viewing
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"}
    )

# Admin endpoints for Section Extraction Configuration
@app.get("/api/admin/section-configs", response_model=List[SectionExtractionConfigResponse])
async def get_section_configs(db: AsyncSession = Depends(get_db)):
    """Get all section extraction configurations"""
    configs = await get_section_extraction_configs(db)
    return configs

@app.get("/api/admin/section-configs/{config_id}", response_model=SectionExtractionConfigResponse)
async def get_section_config(config_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific section extraction configuration"""
    config = await get_section_extraction_config(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Section configuration not found")
    return config

@app.post("/api/admin/section-configs", response_model=SectionExtractionConfigResponse)
async def create_section_config(config: SectionExtractionConfigCreate, db: AsyncSession = Depends(get_db)):
    """Create a new section extraction configuration"""
    try:
        # Validate that markers is valid JSON
        json.loads(config.markers)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Markers must be a valid JSON array")
    
    return await create_section_extraction_config(db, config)

@app.put("/api/admin/section-configs/{config_id}", response_model=SectionExtractionConfigResponse)
async def update_section_config(config_id: int, config: SectionExtractionConfigUpdate, db: AsyncSession = Depends(get_db)):
    """Update a section extraction configuration"""
    try:
        # Validate that markers is valid JSON
        json.loads(config.markers)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Markers must be a valid JSON array")
    
    updated_config = await update_section_extraction_config(db, config_id, config)
    if not updated_config:
        raise HTTPException(status_code=404, detail="Section configuration not found")
    return updated_config

@app.delete("/api/admin/section-configs/{config_id}")
async def delete_section_config(config_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a section extraction configuration"""
    success = await delete_section_extraction_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Section configuration not found")
    return {"success": True, "message": "Section configuration deleted successfully"}

# ===== AI SETTINGS (SYSTEM PROMPTS) =====
class AiSettingsBody(BaseModel):
    extract_system_prompt: Optional[str] = None
    evaluate_system_prompt: Optional[str] = None

AI_EXTRACT_KEY = "extract_system_prompt"
AI_EVALUATE_KEY = "evaluate_system_prompt"

async def _get_setting(db: AsyncSession, key: str) -> Optional[str]:
    res = await db.execute(select(AiSetting).where(AiSetting.key == key))
    row = res.scalar_one_or_none()
    return row.value if row else None

async def _set_setting(db: AsyncSession, key: str, value: str) -> None:
    res = await db.execute(select(AiSetting).where(AiSetting.key == key))
    row = res.scalar_one_or_none()
    if row:
        row.value = value
    else:
        row = AiSetting(key=key, value=value)
        db.add(row)
    await db.commit()

@app.get("/api/admin/ai-settings")
async def get_ai_settings(db: AsyncSession = Depends(get_db)):
    extract_prompt = await _get_setting(db, AI_EXTRACT_KEY)
    evaluate_prompt = await _get_setting(db, AI_EVALUATE_KEY)
    return {
        "extract_system_prompt": extract_prompt or "",
        "evaluate_system_prompt": evaluate_prompt or "",
    }

@app.put("/api/admin/ai-settings")
async def update_ai_settings(body: AiSettingsBody, db: AsyncSession = Depends(get_db)):
    if body.extract_system_prompt is not None:
        await _set_setting(db, AI_EXTRACT_KEY, body.extract_system_prompt)
    if body.evaluate_system_prompt is not None:
        await _set_setting(db, AI_EVALUATE_KEY, body.evaluate_system_prompt)
    return {"success": True}

# PDF Extraction Testing endpoint
@app.get("/api/debug/pdf-extraction-test/{assignment_id}")
async def test_pdf_extraction_methods(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Test different PDF extraction methods to compare results"""
    
    # Get assignment and verify PDF exists
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    # Determine PDF source: prefer DB bytes, else filesystem path (GDrive not supported here)
    temp_path = None
    if getattr(assignment, "pdf_file_data", None):
        try:
            fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix=f"assignment_{assignment_id}_")
            with os.fdopen(fd, "wb") as tmp:
                tmp.write(assignment.pdf_file_data)
            file_path = temp_path
        except Exception as e:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail=f"Failed to prepare PDF bytes for extraction: {str(e)}")
    else:
        if not assignment.pdf_file_path:
            raise HTTPException(status_code=400, detail="No PDF file found for this assignment")
        if assignment.pdf_file_path.startswith("gdrive:"):
            raise HTTPException(status_code=400, detail="AI extraction from Google Drive reference not supported")
        file_path = assignment.pdf_file_path.lstrip('/')
        if not os.path.exists(file_path):
            raise HTTPException(status_code=400, detail="PDF file not found on server")
    
    results = {}
    
    try:
        # Method 1: PyMuPDF4LLM (current method)
        try:
            pymupdf4llm_text = pymupdf4llm.to_markdown(file_path)
            results['pymupdf4llm'] = {
                'method': 'PyMuPDF4LLM to_markdown',
                'characters': len(pymupdf4llm_text),
                'words': len(pymupdf4llm_text.split()),
                'lines': len(pymupdf4llm_text.splitlines()),
                'last_500_chars': pymupdf4llm_text[-500:] if len(pymupdf4llm_text) > 500 else pymupdf4llm_text,
                'success': True
            }
        except Exception as e:
            results['pymupdf4llm'] = {'method': 'PyMuPDF4LLM', 'error': str(e), 'success': False}
        
        # Method 2: Direct PyMuPDF text extraction
        try:
            doc = fitz.open(file_path)
            direct_text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                direct_text += page.get_text()
            doc.close()
            
            results['pymupdf_direct'] = {
                'method': 'PyMuPDF direct get_text()',
                'characters': len(direct_text),
                'words': len(direct_text.split()),
                'lines': len(direct_text.splitlines()),
                'last_500_chars': direct_text[-500:] if len(direct_text) > 500 else direct_text,
                'success': True
            }
        except Exception as e:
            results['pymupdf_direct'] = {'method': 'PyMuPDF direct', 'error': str(e), 'success': False}
            
        # Method 3: PyMuPDF with different extraction options
        try:
            doc = fitz.open(file_path)
            textpage_text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Use textpage extraction with flags
                textpage_text += page.get_text("text", flags=fitz.TEXTFLAGS_TEXT)
            doc.close()
            
            results['pymupdf_textpage'] = {
                'method': 'PyMuPDF textpage with flags',
                'characters': len(textpage_text),
                'words': len(textpage_text.split()),
                'lines': len(textpage_text.splitlines()),
                'last_500_chars': textpage_text[-500:] if len(textpage_text) > 500 else textpage_text,
                'success': True
            }
        except Exception as e:
            results['pymupdf_textpage'] = {'method': 'PyMuPDF textpage', 'error': str(e), 'success': False}
            
        # Summary comparison
        successful_results = {k: v for k, v in results.items() if v.get('success')}
        if successful_results:
            best_method = max(successful_results.keys(), key=lambda k: successful_results[k]['characters'])
            results['comparison'] = {
                'best_method': best_method,
                'best_character_count': successful_results[best_method]['characters'],
                'methods_tested': len(results),
                'successful_methods': len(successful_results)
            }
        
        return {
            'success': True,
            'assignment_name': assignment.name,
            'file_path': file_path,
            'extraction_results': results
        }
        
    except Exception as e:
        logger.error(f"PDF extraction test failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PDF extraction test failed: {str(e)}")

# Debug endpoint to test Ollama connectivity
@app.get("/api/debug/ollama-test")
async def test_ollama_connection():
    """
    Test Ollama connectivity with a simple request
    """
    if not ollama_available:
        return {
            "success": False,
            "error": "Ollama not available",
            "details": "Ollama server is not running or models not installed"
        }
    
    try:
        # Test with a simple prompt
        test_prompt = "Hello, respond with just 'OK'"
        
        ollama_request = {
            "model": OLLAMA_MODEL,
            "prompt": test_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 10,
            }
        }
        
        logger.info(f"Testing Ollama connection with model: {OLLAMA_MODEL}")
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=ollama_request,
            timeout=30
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Ollama API error: {response.status_code}",
                "details": response.text
            }
        
        result = response.json()
        
        return {
            "success": True,
            "message": "Ollama is working correctly",
            "test_prompt": test_prompt,
            "ai_response": result.get("response", ""),
            "model_used": OLLAMA_MODEL,
            "response_time": "< 30s"
        }
        
    except Exception as e:
        logger.error(f"Ollama test failed: {str(e)}")
        return {
            "success": False,
            "error": f"Connection test failed: {type(e).__name__}",
            "details": str(e)
        }

# Debug endpoint specifically for cross-reference handling
@app.post("/api/debug/test-cross-references/{assignment_id}")
async def debug_cross_references(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Debug cross-reference detection and resolution in PDF content"""
    
    # Get assignment and verify PDF exists (prefer DB bytes)
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)

    # Enforce bytes-only source and log branch
    temp_path = None
    if not getattr(assignment, "pdf_file_data", None):
        logger.warning(f"AI Extract (assignment_id={assignment_id}): pdf_file_data missing; rejecting request")
        raise HTTPException(status_code=400, detail="No PDF bytes found for this assignment. Please re-upload the PDF.")
    logger.info(
        f"AI Extract (assignment_id={assignment_id}): using pdf_file_data bytes, size={getattr(assignment,'pdf_file_size', None)} mime={getattr(assignment,'pdf_mime_type', None)}"
    )
    try:
        fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix=f"assignment_{assignment_id}_")
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(assignment.pdf_file_data)
        file_path = temp_path
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to prepare PDF bytes for extraction: {str(e)}")
    
    try:
        # Extract full text
        doc = fitz.open(file_path)
        pdf_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pdf_text += page.get_text()
        doc.close()
        # Cleanup temp file if used
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        # Cleanup temp file if used
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        
        # Debug: Look for cross-reference patterns
        import re
        
        cross_ref_patterns = [
            r'exercicis?\s+(\d+\.\d+(?:\s*,\s*\d+\.\d+)*(?:\s*i\s*\d+\.\d+)*)',  # exercicis 1.2, 1.3 i 2.1
            r'resultat\s+dels?\s+exercicis?\s+(\d+\.\d+(?:\s*,\s*\d+\.\d+)*(?:\s*i\s*\d+\.\d+)*)',  # resultat dels exercicis 1.2, 1.3 i 2.1
            r'secció\s+(\d+\.\d+)', # secció 1.2
            r'apartats?\s+(\d+\.\d+(?:\s*,\s*\d+\.\d+)*)', # apartat 1.2, 1.3
            r'veure\s+(\d+\.\d+)', # veure 1.2
        ]
        
        found_references = {}
        for pattern_name, pattern in enumerate(cross_ref_patterns):
            matches = re.findall(pattern, pdf_text.lower(), re.IGNORECASE)
            if matches:
                found_references[f"pattern_{pattern_name}"] = {
                    "pattern": pattern,
                    "matches": matches,
                    "count": len(matches)
                }
        
        # Look for section headers/numbers
        section_patterns = [
            r'^(\d+\.\d+)\s+(.+)$',  # 1.2 Title
            r'^(\d+\.\d+)\.?\s+(.+)$',  # 1.2. Title
            r'^\s*(\d+\.\d+)\s+(.+)',  # whitespace + 1.2 Title
        ]
        
        found_sections = {}
        lines = pdf_text.split('\n')
        for line_num, line in enumerate(lines):
            for pattern_name, pattern in enumerate(section_patterns):
                match = re.match(pattern, line.strip())
                if match:
                    section_num = match.group(1)
                    section_title = match.group(2)
                    if section_num not in found_sections:
                        found_sections[section_num] = []
                    found_sections[section_num].append({
                        "line_number": line_num + 1,
                        "title": section_title,
                        "full_line": line.strip()
                    })
        
        # Test AI with cross-reference specific prompt
        test_prompt = f"""PDF CONTENT WITH CROSS-REFERENCES TEST:

{pdf_text[:3000]}...

CROSS-REFERENCE ANALYSIS TASK:
1. Find any references to numbered sections (like "exercicis 1.2, 1.3 i 2.1")
2. Locate the actual content of those referenced sections
3. Create complete exercise descriptions that include the referenced content

RESPOND WITH JSON containing:
{{"found_references": ["list of references found"], "sections_content": {{"1.2": "content", "1.3": "content"}}, "exercises": [exercises_array]}}"""

        if ollama_available:
            try:
                ollama_request = {
                    "model": OLLAMA_MODEL,
                    "prompt": test_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 2000,
                    }
                }
                
                response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json=ollama_request,
                    timeout=60
                )
                
                ai_response = response.json().get("response", "") if response.status_code == 200 else "AI request failed"
            except Exception as e:
                ai_response = f"AI test failed: {str(e)}"
        else:
            ai_response = "Ollama not available"
        
        return {
            "success": True,
            "document_stats": {
                "total_characters": len(pdf_text),
                "total_lines": len(lines)
            },
            "cross_reference_analysis": {
                "patterns_searched": len(cross_ref_patterns),
                "references_found": found_references,
                "total_references": sum(ref["count"] for ref in found_references.values())
            },
            "section_analysis": {
                "sections_found": found_sections,
                "total_sections": len(found_sections)
            },
            "ai_cross_reference_test": {
                "prompt_sent": test_prompt[:500] + "..." if len(test_prompt) > 500 else test_prompt,
                "ai_response": ai_response
            }
        }
        
    except Exception as e:
        logger.error(f"Cross-reference debug failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

# Debug the actual AI prompt being sent for extraction
@app.post("/api/debug/ai-prompt-debug/{assignment_id}")
async def debug_ai_prompt(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Debug the exact prompt being sent to AI and its response"""
    
    # Get assignment and verify PDF exists
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    if not assignment.pdf_file_path:
        raise HTTPException(status_code=400, detail="No PDF file found for this assignment")
    
    file_path = assignment.pdf_file_path.lstrip('/')
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="PDF file not found on server")
    
    try:
        # Extract text from PDF using direct PyMuPDF (same as main function)
        doc = fitz.open(file_path)
        pdf_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pdf_text += page.get_text()
        doc.close()
        
        # Pre-process the document to identify cross-references (same as main function)
        import re
        
        cross_ref_patterns = [
            r'exercicis?\s+(\d+\.\d+(?:\s*,\s*\d+\.\d+)*(?:\s*i\s*\d+\.\d+)*)',
            r'resultat\s+dels?\s+exercicis?\s+(\d+\.\d+(?:\s*,\s*\d+\.\d+)*(?:\s*i\s*\d+\.\d+)*)',
            r'secció\s+(\d+\.\d+)',
            r'apartats?\s+(\d+\.\d+(?:\s*,\s*\d+\.\d+)*)',
            r'veure\s+(\d+\.\d+)',
        ]
        
        cross_references_found = []
        for pattern in cross_ref_patterns:
            matches = re.findall(pattern, pdf_text.lower(), re.IGNORECASE)
            cross_references_found.extend(matches)
        
        # Extract section content for found references (same as main function)
        section_content_map = {}
        lines = pdf_text.split('\n')
        
        current_section = None
        current_content = []
        
        for line_num, line in enumerate(lines):
            section_match = re.match(r'^\s*(\d+\.\d+)\.?\s+(.+)', line.strip())
            if section_match:
                if current_section and current_content:
                    section_content_map[current_section] = '\n'.join(current_content)
                
                current_section = section_match.group(1)
                current_content = [line.strip()]
            elif current_section:
                current_content.append(line.strip())
        
        if current_section and current_content:
            section_content_map[current_section] = '\n'.join(current_content)
        
        # Create cross-reference context for AI (same as main function)
        cross_ref_context = ""
        if cross_references_found:
            cross_ref_context = "\n\nCROSS-REFERENCE MAPPINGS:\n"
            unique_refs = list(set([ref.replace(',', '').replace(' i ', ' ').strip() for ref_group in cross_references_found for ref in ref_group.split()]))
            
            for ref in unique_refs:
                if ref in section_content_map:
                    cross_ref_context += f"\nSection {ref}:\n{section_content_map[ref][:500]}...\n"
        
        # Extract ONLY the deliverables section (same as main function)
        deliverables_start = pdf_text.lower().find("què s'ha de lliurar")
        if deliverables_start == -1:
            deliverables_section = pdf_text[:5000]
        else:
            deliverables_section = pdf_text[deliverables_start:deliverables_start + 3000]
        
        # Create the exact same prompts as the main function
        system_prompt = f"""You are extracting deliverables from a university assignment. 

INSTRUCTIONS:
1. Extract the numbered deliverables exactly as listed
2. When you see "Resultat dels exercicis X.Y", expand it with the corresponding section content from below
3. Keep the original language (Catalan/Spanish) - DO NOT translate to English
4. Return JSON array with points that sum to 100
5. Format: {{"description": "expanded text", "points": number, "order": number}}

CROSS-REFERENCE MAPPINGS:
{cross_ref_context}

Return ONLY the JSON array, nothing else."""

        user_prompt = f"""DELIVERABLES TO EXTRACT:

{deliverables_section}

Extract the numbered deliverables (1, 2, 3, 4...) from above. Expand any "Resultat dels exercicis X.Y" references using the section mappings provided in the system prompt."""

        full_prompt = f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
        
        # Test with AI
        ai_response = "AI not available"
        if ollama_available:
            try:
                ollama_request = {
                    "model": OLLAMA_MODEL,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 2000,
                    }
                }
                
                response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json=ollama_request,
                    timeout=60
                )
                
                if response.status_code == 200:
                    ai_response = response.json().get("response", "")
                else:
                    ai_response = f"API Error: {response.status_code}"
                    
            except Exception as e:
                ai_response = f"Exception: {str(e)}"
        
        return {
            "success": True,
            "debug_info": {
                "cross_references_found": cross_references_found,
                "sections_mapped": list(section_content_map.keys()),
                "deliverables_section_length": len(deliverables_section),
                "cross_ref_context_length": len(cross_ref_context)
            },
            "deliverables_section": deliverables_section[:1000] + "..." if len(deliverables_section) > 1000 else deliverables_section,
            "cross_ref_context": cross_ref_context,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "full_prompt_length": len(full_prompt),
            "ai_response": ai_response
        }
        
    except Exception as e:
        logger.error(f"AI prompt debug failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

# Test deliverables extraction specifically
@app.post("/api/debug/test-deliverables-extraction/{assignment_id}")
async def test_deliverables_extraction(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Test if the AI can properly extract deliverables with cross-references"""
    
    # Get assignment and verify PDF exists
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    if not assignment.pdf_file_path:
        raise HTTPException(status_code=400, detail="No PDF file found for this assignment")
    
    file_path = assignment.pdf_file_path.lstrip('/')
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="PDF file not found on server")
    
    try:
        # Extract full text
        doc = fitz.open(file_path)
        pdf_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pdf_text += page.get_text()
        doc.close()
        
        # Find the deliverables section specifically
        deliverables_start = pdf_text.lower().find("què s'ha de lliurar")
        if deliverables_start == -1:
            return {"error": "No 'Què s'ha de lliurar' section found"}
        
        # Extract just the deliverables section (next 2000 characters)
        deliverables_section = pdf_text[deliverables_start:deliverables_start + 2000]
        
        # Create a simple test with just the deliverables
        test_prompt = f"""Here is the deliverables section from a PDF:

{deliverables_section}

Extract the numbered deliverables (what students must submit). For each deliverable that mentions "Resultat dels exercicis X.Y", expand it with this content:

Section 1.2: Fitxa de grup - Create group information sheet including group name, member names with brief justification of profiles and experience
Section 1.3: Debat en grup - Group debate analyzing agile methodologies and Scrum principles  
Section 2.1: Configuració de l'equip - Team configuration with Scrum Master and Product Owner assignments

Return JSON array with expanded descriptions in original language:"""

        if not ollama_available:
            return {"error": "Ollama not available"}
        
        try:
            ollama_request = {
                "model": OLLAMA_MODEL,
                "prompt": test_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 1500,
                }
            }
            
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=ollama_request,
                timeout=60
            )
            
            ai_response = response.json().get("response", "") if response.status_code == 200 else "AI request failed"
            
            return {
                "success": True,
                "deliverables_section": deliverables_section,
                "test_prompt": test_prompt,
                "ai_response": ai_response,
                "deliverables_start_position": deliverables_start
            }
            
        except Exception as e:
            return {"success": False, "error": f"AI test failed: {str(e)}"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

# Test AI prompt with sample text
@app.post("/api/debug/test-ai-prompt")
async def test_ai_prompt_format():
    """
    Test the AI prompt with sample exercise text to validate JSON response format
    """
    if not ollama_available:
        raise HTTPException(status_code=500, detail="Ollama not available")
    
    # Sample text that should definitely produce exercises
    sample_text = """
Assignment: Data Structures and Algorithms

Exercise 1: Binary Search Implementation (25 points)
Implement a binary search algorithm in Python. Your solution should handle edge cases.

Exercise 2: Time Complexity Analysis (30 points) 
Analyze the time complexity of your binary search implementation and explain why.

Exercise 3: Test Cases (45 points)
Write comprehensive test cases for your binary search function.
"""
    
    try:
        # Use the same prompt as the real extraction
        system_prompt = """You are an educational content analyzer. Extract exercises/problems from the provided PDF content.

CRITICAL INSTRUCTIONS:
1. Look specifically for the section "Què s'ha de lliurar" (What needs to be delivered)
2. Extract ONLY the exercises/deliverables from this section
3. Each exercise needs a description and point value
4. Points must sum to exactly 100 total
5. Return ONLY a valid JSON array, nothing else
6. Each exercise object format: {"description": "text", "points": number, "order": number}
7. PRESERVE THE ORIGINAL LANGUAGE - DO NOT TRANSLATE to English
8. Keep descriptions in the same language as the source PDF (Catalan, Spanish, etc.)
9. If no "Què s'ha de lliurar" section is found, look for similar sections like "Deliverables", "Entregables", or "Tasques"

EXAMPLE FORMAT (maintain source language):
[
{"description": "Descripció de l'exercici en idioma original", "points": 25, "order": 1},
{"description": "Una altra descripció en llengua original", "points": 30, "order": 2},
{"description": "Tercer exercici en idioma original", "points": 45, "order": 3}
]

If no deliverables section or exercises found, return: []"""

        user_prompt = f"""PDF Content:
{sample_text}

Find the "Què s'ha de lliurar" section and extract exercises as JSON array (no other text):"""
        
        full_prompt = f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
        
        ollama_request = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 1000,
            }
        }
        
        logger.info(f"Testing AI prompt with sample data...")
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=ollama_request,
            timeout=60
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Ollama API error: {response.status_code}",
                "details": response.text
            }
        
        ollama_response = response.json()
        ai_content = ollama_response.get("response", "").strip()
        
        # Try to extract JSON
        json_start = ai_content.find('[')
        json_end = ai_content.rfind(']') + 1
        
        return {
            "success": True,
            "sample_text": sample_text,
            "ai_raw_response": ai_content,
            "json_found": json_start != -1 and json_end > 0,
            "json_start_pos": json_start,
            "json_end_pos": json_end,
            "extracted_json": ai_content[json_start:json_end] if json_start != -1 and json_end > 0 else None,
            "model_used": OLLAMA_MODEL
        }
        
    except Exception as e:
        logger.error(f"AI prompt test failed: {str(e)}")
        return {
            "success": False,
            "error": f"Test failed: {type(e).__name__}",
            "details": str(e)
        }

# Debug endpoint to test cross-reference expansion directly
@app.post("/api/debug/test-expansion")
async def test_expansion_directly():
    """Test cross-reference expansion directly with OpenEuroLLM-Catalan"""
    
    if not ollama_available:
        return {"error": "Ollama not available"}
    
    # Test data
    deliverable = "Fitxa i configuració del grup, incloent el nom triat pel grup, nom dels seus membres amb una breu justificació dels perfils i experiència, i la configuració de l'equip de treball indicant clarament qui exercirà de Scrum Master i de Product Owner en cadascuna de les Activitats. Resultat dels exercicis 1.2, 1.3 i 2.1 (màx. 3 pàgs)."
    
    # Simple test context
    test_context = """
Section 1.2: Presentació personal mitjançant un CV breu que inclogui els vostres punts forts i febles
Section 1.3: Identificació de perfils i rols al grup segons les habilitats de cada membre
Section 2.1: Configuració inicial de l'equip amb designació de Scrum Master i Product Owner
"""
    
    system_prompt = f"""Expand cross-references in this deliverable text using the section content below. Keep the original Catalan language.

SECTION CONTENT:
{test_context}

TASK: Replace "Resultat dels exercicis X.Y" with the actual content from those sections. Keep everything else exactly the same.

Return ONLY the expanded text, nothing else."""

    user_prompt = f"""DELIVERABLE TO EXPAND:
{deliverable}

Expand the cross-references using the section content provided in the system prompt."""

    try:
        full_prompt = f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
        
        ollama_request = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 800,
            }
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=ollama_request,
            timeout=60
        )
        
        if response.status_code == 200:
            ai_response = response.json().get("response", "").strip()
            return {
                "success": True,
                "original": deliverable,
                "expanded": ai_response,
                "model_used": OLLAMA_MODEL,
                "prompt_length": len(full_prompt)
            }
        else:
            return {
                "success": False,
                "error": f"Ollama API error: {response.status_code}",
                "response_text": response.text
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception: {str(e)}"
        }

# Debug endpoint to test detection logic
@app.post("/api/debug/test-detection")
async def test_detection_logic():
    """Test the cross-reference detection logic for all deliverables"""
    
    deliverables_raw = [
        "Fitxa i configuració del grup, incloent el nom triat pel grup, nom dels seus membres amb una breu justificació dels perfils i experiència, i la configuració de l'equip de treball indicant clarament qui exercirà de Scrum Master i de Product Owner en cadascuna de les Activitats. Resultat dels exercicis 1.2, 1.3 i 2.1 (màx. 3 pàgs).",
        "Informe de la configuració i proves de GitLab i Miro (incloent captures de pantalla) amb una breu explicació dels problemes trobats. Resultat de l'exercici 2.2. (màx. 3 pàgs).",
        "Informe de l'anàlisi sobre les metodologies i principis àgils i Scrum com a resultat del debat en el grup a l'exercici 1.4 (màx. 3 pàgs).",
        "Inception Deck del producte amb la resposta a les cinc preguntes plantejades a l'exercici 3 (màx. 3 pàgs)."
    ]
    
    results = []
    for i, deliverable in enumerate(deliverables_raw):
        has_cross_ref = (
            "resultat dels exercicis" in deliverable.lower() or 
            "resultat de l'exercici" in deliverable.lower() or 
            "resultat dels exercici" in deliverable.lower() or
            re.search(r"exercici \d+\.\d+", deliverable.lower()) or
            re.search(r"exercici \d+", deliverable.lower())
        )
        
        results.append({
            "deliverable_number": i+1,
            "detected": has_cross_ref,
            "content_preview": deliverable[:150] + "...",
            "regex_matches": {
                "exercici_xy": bool(re.search(r"exercici \d+\.\d+", deliverable.lower())),
                "exercici_x": bool(re.search(r"exercici \d+", deliverable.lower())),
                "found_patterns": re.findall(r"exercici \d+(?:\.\d+)?", deliverable.lower())
            }
        })
    
    return {"detection_results": results}

# PDF Text Preview endpoint
@app.get("/api/assignments/{assignment_id}/preview-pdf-text")
async def preview_pdf_text(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """
    Preview the text extracted from PDF using PyMuPDF4LLM
    This shows what text will be sent to the AI without running AI processing
    """
    
    # Get assignment and verify PDF exists
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    if not assignment.pdf_file_path:
        raise HTTPException(status_code=400, detail=NO_PDF_FOUND)
    
    file_path = assignment.pdf_file_path.lstrip('/')
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="PDF file not found on server")
    
    try:
        # Extract text from PDF using direct PyMuPDF (more complete than PyMuPDF4LLM)
        doc = fitz.open(file_path)
        pdf_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pdf_text += page.get_text()
        doc.close()
        
        if not pdf_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Create different views of the text
        preview_truncated = pdf_text[:3000] + "..." if len(pdf_text) > 3000 else pdf_text
        
        # Find deliverables section for guidance, but send full document to AI
        found_marker = None
        section_position = None
        section_markers = await get_dynamic_section_markers(db)
        
        for marker in section_markers:
            start_idx = pdf_text.lower().find(marker)
            if start_idx != -1:
                found_marker = marker
                section_position = start_idx
                logger.info(f"✅ Found section marker '{marker}' at position {start_idx}")
                break
            else:
                logger.debug(f"❌ Marker '{marker}' not found")
        
        # AI will now receive the FULL document to handle references properly
        text_for_ai = pdf_text  # Full document will be sent to AI
        
        # Extract section preview for user display
        section_preview = ""
        if found_marker and section_position is not None:
            section_start = max(0, section_position - 200)
            section_end = min(len(pdf_text), section_start + 1000)  # Just for preview
            section_preview = pdf_text[section_start:section_end]
        
        return {
            "success": True,
            "assignment_name": assignment.name,
            "file_name": assignment.pdf_file_name,
            "text_stats": {
                "total_characters": len(pdf_text),
                "total_words": len(pdf_text.split()),
                "total_lines": len(pdf_text.splitlines()),
                "ai_input_characters": len(text_for_ai)
            },
            "text_preview": preview_truncated,
            "text_for_ai": text_for_ai,
            "extraction_method": "Direct PyMuPDF",
            "section_analysis": {
                "found_deliverables_section": found_marker is not None,
                "section_marker_used": found_marker,
                "section_position": section_position,
                "ai_processing_approach": "FULL_DOCUMENT_WITH_SECTION_GUIDANCE",
                "ai_will_receive_full_document": True,
                "reason": "Full document needed to handle cross-references in exercises",
                "section_preview": section_preview[:500] + "..." if len(section_preview) > 500 else section_preview
            },
            "content_analysis": {
                "has_numbers": any(char.isdigit() for char in pdf_text),
                "has_questions": '?' in pdf_text,
                "has_exercises": any(word in pdf_text.lower() for word in ['exercise', 'problem', 'question', 'task']),
                "has_points": any(word in pdf_text.lower() for word in ['point', 'pts', 'score', 'mark']),
                "word_exercise_count": pdf_text.lower().count('exercise'),
                "word_problem_count": pdf_text.lower().count('problem')
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")

# AI PDF Exercise Extraction endpoint
@app.post("/api/assignments/{assignment_id}/extract-exercises-ai")
async def extract_exercises_from_pdf_ai(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """
    Extract exercises from PDF using AI
    This will replace all existing exercises for the assignment
    """
    from services.ai_service import ai_extraction_service
    
    try:
        result = await ai_extraction_service.extract_exercises_from_pdf(assignment_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = f"Unexpected error during AI processing: {type(e).__name__}: {str(e)}"
        logger.error(f"Unexpected error in AI extraction: {error_msg}")
        raise HTTPException(status_code=500, detail=f"{error_msg}\n\nFor debugging: Check server logs for full error details.")

# === NON-VERSIONED ALIASES (/api) ===
# These mirror the /api endpoints to support unversioned API usage

# Assignments
@app.get("/api/assignments", response_model=List[AssignmentResponse])
async def get_all_assignments_alias(db: AsyncSession = Depends(get_db)):
    return await get_all_assignments(db)

@app.get("/api/assignments/{assignment_id}", response_model=AssignmentResponse)
async def get_single_assignment_alias(assignment_id: int, db: AsyncSession = Depends(get_db)):
    return await get_single_assignment(assignment_id, db)

@app.post("/api/assignments", response_model=AssignmentResponse)
async def create_new_assignment_alias(assignment: AssignmentCreate, db: AsyncSession = Depends(get_db)):
    return await create_new_assignment(assignment, db)

@app.put("/api/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_existing_assignment_alias(assignment_id: int, assignment_update: AssignmentUpdate, db: AsyncSession = Depends(get_db)):
    return await update_existing_assignment(assignment_id, assignment_update, db)

@app.delete("/api/assignments/{assignment_id}")
async def delete_existing_assignment_alias(assignment_id: int, db: AsyncSession = Depends(get_db)):
    return await delete_existing_assignment(assignment_id, db)

# Exercises
@app.get("/api/assignments/{assignment_id}/exercises", response_model=List[ExerciseResponse])
async def get_exercises_for_assignment_alias(assignment_id: int, db: AsyncSession = Depends(get_db)):
    return await get_exercises_for_assignment(assignment_id, db)

@app.put("/api/assignments/{assignment_id}/exercises", response_model=List[ExerciseResponse])
async def update_exercises_for_assignment_alias(assignment_id: int, exercises: List[ExerciseUpdate], db: AsyncSession = Depends(get_db)):
    return await update_exercises_for_assignment(assignment_id, exercises, db)

# PDFs
@app.post("/api/assignments/{assignment_id}/upload-pdf")
async def upload_assignment_pdf_alias(assignment_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    return await upload_assignment_pdf(assignment_id, file, db)

@app.get("/api/assignments/{assignment_id}/pdf")
async def view_assignment_pdf_alias(assignment_id: int, db: AsyncSession = Depends(get_db)):
    return await view_assignment_pdf(assignment_id, db)

# --- Reference an existing Google Drive PDF (no upload) ---
from pydantic import BaseModel

class PdfReferenceBody(BaseModel):
    drive_file_id: str
    file_name: str | None = None
    mime_type: str | None = None
    size: int | None = None

@app.patch("/api/assignments/{assignment_id}/pdf-ref")
async def set_assignment_pdf_reference(
    assignment_id: int,
    body: PdfReferenceBody,
    db: AsyncSession = Depends(get_db)
):
    """Attach an existing Google Drive file to the assignment without uploading.

    Stores a special path prefix gdrive:{fileId} and optional metadata.
    """
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)

    # Persist reference using existing columns for minimal changes
    assignment.pdf_file_path = f"gdrive:{body.drive_file_id}"
    if body.file_name:
        assignment.pdf_file_name = body.file_name
    await db.commit()
    await db.refresh(assignment)
    return {
        "success": True,
        "message": "PDF reference set",
        "drive_file_id": body.drive_file_id,
        "file_name": assignment.pdf_file_name,
    }

@app.patch("/api/assignments/{assignment_id}/pdf-ref")
async def set_assignment_pdf_reference_v1(
    assignment_id: int,
    body: PdfReferenceBody,
    db: AsyncSession = Depends(get_db)
):
    return await set_assignment_pdf_reference(assignment_id, body, db)

@app.delete("/api/assignments/{assignment_id}/pdf")
async def delete_assignment_pdf_alias(assignment_id: int, db: AsyncSession = Depends(get_db)):
    return await delete_assignment_pdf(assignment_id, db)

# AI extraction
@app.post("/api/assignments/{assignment_id}/extract-exercises-ai")
async def extract_exercises_from_pdf_ai_alias(assignment_id: int, db: AsyncSession = Depends(get_db)):
    return await extract_exercises_from_pdf_ai(assignment_id, db)

# === TEST ENDPOINT ===
@app.get("/api/test-endpoint")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Test endpoint works"}

# === SUBMISSION MANAGEMENT ENDPOINTS ===

@app.get("/api/submissions")
async def get_submissions_endpoint(
    assignment_id: Optional[int] = None,
    course_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    group_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all submissions with optional filtering"""
    submissions = await get_submissions(
        db, assignment_id=assignment_id, course_id=course_id, 
        semester_id=semester_id, group_id=group_id, skip=skip, limit=limit
    )
    # Return submissions as dicts without binary data
    return [
        {
            "id": s.id,
            "assignment_id": s.assignment_id,
            "course_id": s.course_id,
            "semester_id": s.semester_id,
            "group_id": s.group_id,
            "comments": s.comments,
            "pdf_file_name": s.pdf_file_name,
            "pdf_file_path": s.pdf_file_path,
            "pdf_file_size": s.pdf_file_size,
            "pdf_mime_type": s.pdf_mime_type,
            "status": s.status,
            "total_score": s.total_score,
            "max_score": s.max_score,
            "percentage_score": s.percentage_score,
            "teacher_feedback": s.teacher_feedback,
            "ai_feedback": s.ai_feedback,
            "grade_breakdown": s.grade_breakdown,
            "submitted_at": s.submitted_at,
            "graded_at": s.graded_at,
            "graded_by": s.graded_by,
            "is_late": s.is_late,
            "created_at": s.created_at,
            "updated_at": s.updated_at
        }
        for s in submissions
    ]

@app.post("/api/submissions")
async def create_submission_endpoint(
    assignment_id: int = Form(...),
    course_id: int = Form(None),
    semester_id: int = Form(None),
    group_id: int = Form(None),
    comments: str = Form(None),
    pdf_file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a new submission"""
    try:
        submission_data = {
            "assignment_id": assignment_id,
            "course_id": course_id,
            "semester_id": semester_id,
            "group_id": group_id,
            "comments": comments
        }
        
        # Handle PDF file upload - store as binary data in database
        if pdf_file and pdf_file.filename:
            # Read PDF file bytes
            pdf_bytes = await pdf_file.read()
            
            submission_data["pdf_file_name"] = pdf_file.filename
            submission_data["pdf_file_path"] = f"/uploads/{pdf_file.filename}"
            submission_data["pdf_file_data"] = pdf_bytes
            submission_data["pdf_mime_type"] = pdf_file.content_type or "application/pdf"
            submission_data["pdf_file_size"] = len(pdf_bytes)
            
            logger.info(f"PDF file uploaded: {pdf_file.filename}, size: {len(pdf_bytes)} bytes")
        
        logger.info(f"Creating submission with data: {submission_data}")
        submission_create = SubmissionCreate(**submission_data)
        logger.info(f"SubmissionCreate object created: {submission_create}")
        submission = await create_submission(db, submission_create)
        logger.info(f"Submission created successfully: {submission.id}")
        
        # Return submission as dict without binary data and without relationships to avoid lazy loading
        return {
            "id": submission.id,
            "assignment_id": submission.assignment_id,
            "course_id": submission.course_id,
            "semester_id": submission.semester_id,
            "group_id": submission.group_id,
            "comments": submission.comments,
            "pdf_file_name": submission.pdf_file_name,
            "pdf_file_path": submission.pdf_file_path,
            "pdf_file_size": submission.pdf_file_size,
            "pdf_mime_type": submission.pdf_mime_type,
            "status": submission.status,
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
            "updated_at": submission.updated_at
        }
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating submission: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to create submission")

@app.get("/api/submissions/{submission_id}")
async def get_submission_endpoint(submission_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single submission by ID"""
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Return submission as dict without binary data
    return {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "course_id": submission.course_id,
        "semester_id": submission.semester_id,
        "group_id": submission.group_id,
        "comments": submission.comments,
        "pdf_file_name": submission.pdf_file_name,
        "pdf_file_path": submission.pdf_file_path,
        "pdf_file_size": submission.pdf_file_size,
        "pdf_mime_type": submission.pdf_mime_type,
        "status": submission.status,
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
        "updated_at": submission.updated_at
    }

@app.get("/api/submissions/{submission_id}/pdf")
async def view_submission_pdf(submission_id: int, db: AsyncSession = Depends(get_db)):
    """View/download PDF file for submission (from DB bytes)."""
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Serve from DB if bytes available
    if getattr(submission, "pdf_file_data", None):
        return StreamingResponse(
            io.BytesIO(submission.pdf_file_data),
            media_type=(submission.pdf_mime_type or "application/pdf"),
            headers={"Content-Disposition": f"inline; filename={submission.pdf_file_name or 'submission.pdf'}"},
        )

    if not submission.pdf_file_path:
        raise HTTPException(status_code=404, detail="No PDF file found for this submission")
    
    # Fallback to file path if no bytes in DB (legacy support)
    file_path = submission.pdf_file_path.lstrip('/')
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(file_path, media_type="application/pdf", filename=submission.pdf_file_name or "submission.pdf")

@app.put("/api/submissions/{submission_id}")
async def update_submission_endpoint(submission_id: int, submission_data: dict, db: AsyncSession = Depends(get_db)):
    """Update a submission"""
    try:
        submission_update = SubmissionUpdate(**submission_data)
        submission = await update_submission(db, submission_id, submission_update)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        return submission
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating submission: {e}")
        raise HTTPException(status_code=500, detail="Failed to update submission")

@app.delete("/api/submissions/{submission_id}")
async def delete_submission_endpoint(submission_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a submission (soft delete)"""
    success = await delete_submission(db, submission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"message": "Submission deleted successfully"}

@app.put("/api/submissions/{submission_id}/pdf")
async def upload_submission_pdf_endpoint(
    submission_id: int,
    pdf_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload PDF file for a submission"""
    try:
        # Check if submission exists
        submission = await get_submission(db, submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Validate file type
        if not pdf_file.filename or not pdf_file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Generate unique filename to avoid conflicts
        file_extension = os.path.splitext(pdf_file.filename)[1]
        unique_filename = f"submission_{submission_id}_{uuid.uuid4().hex}{file_extension}"
        save_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save the file to disk
        with open(save_path, "wb") as buffer:
            content = await pdf_file.read()
            buffer.write(content)
        
        pdf_file_path = f"/uploads/{unique_filename}"
        
        # Update submission with PDF file info
        submission_update = SubmissionUpdate(
            pdf_file_path=pdf_file_path,
            pdf_file_name=pdf_file.filename
        )
        
        updated_submission = await update_submission(db, submission_id, submission_update)
        if not updated_submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        logger.info(f"PDF uploaded for submission {submission_id}: {pdf_file.filename}")
        return updated_submission
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading PDF for submission {submission_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to upload PDF")

class GradeSubmissionRequest(BaseModel):
    total_score: float
    teacher_feedback: Optional[str] = None
    grade_breakdown: Optional[List[Dict[str, Any]]] = None
    graded_by: Optional[str] = "1"  # Accept string, convert to int in endpoint

@app.post("/api/submissions/{submission_id}/grade")
async def grade_submission_endpoint(
    submission_id: int, 
    grade_data: GradeSubmissionRequest, 
    db: AsyncSession = Depends(get_db)
):
    """Grade a submission with exercise-by-exercise breakdown"""
    # Convert grade_breakdown to dictionaries if provided
    grade_breakdown = []
    if grade_data.grade_breakdown:
        for grade_item in grade_data.grade_breakdown:
            grade_breakdown.append({
                'exercise_id': grade_item['exercise_id'],
                'score': float(grade_item.get('points', grade_item.get('score', 0))),
                'feedback': grade_item.get('comments', grade_item.get('feedback', ''))
            })
    
    # Create submission update with grading data
    # Convert graded_by to int (default to 1 if not provided or invalid)
    graded_by = 1
    if grade_data.graded_by:
        try:
            graded_by = int(grade_data.graded_by) if isinstance(grade_data.graded_by, (int, str)) else 1
        except (ValueError, TypeError):
            graded_by = 1
    
    submission_update = SubmissionUpdate(
        total_score=grade_data.total_score,
        teacher_feedback=grade_data.teacher_feedback,
        grade_breakdown=grade_breakdown,
        graded_by=graded_by
    )
    
    # Update the submission
    updated_submission = await update_submission(db, submission_id, submission_update)
    if not updated_submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    logger.info(f"Submission {submission_id} graded with total score: {grade_data.total_score}")
    return updated_submission

# === COURSE MANAGEMENT ENDPOINTS ===

@app.get("/api/courses")
async def get_courses_endpoint(
    created_by: int = 1,
    skip: int = 0,
    limit: int = 100,
    include_semesters: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get all courses, optionally with their semesters"""
    try:
        if include_semesters:
            courses = await get_courses_with_semesters(db, created_by=created_by, skip=skip, limit=limit)
        else:
            courses = await get_courses(db, created_by=created_by, skip=skip, limit=limit)
        return courses
    except Exception as e:
        logger.error(f"Error getting courses: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch courses")

@app.get("/api/courses/{course_id}")
async def get_course_endpoint(
    course_id: int, 
    include_semesters: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific course by ID, optionally with its semesters"""
    try:
        if include_semesters:
            course = await get_course_with_semesters(db, course_id)
        else:
            course = await get_course(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting course {course_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch course")

@app.post("/api/courses")
async def create_course_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create a new course"""
    try:
        data = await request.json()
        logger.info(f"Attempting to create course with data: {data}")
        
        # Check if course code already exists
        existing = await get_course_by_code(db, data.get("code"))
        if existing:
            raise HTTPException(status_code=400, detail="Course code already exists")
        
        logger.info(f"Creating CourseCreate object with data: {data}")
        course_data = CourseCreate(**data)
        logger.info(f"CourseCreate object created successfully: {course_data}")
        course = await create_course(db, course_data)
        return course
    except ValidationError as e:
        logger.error(f"Pydantic ValidationError: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"General Exception creating course: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to create course")

@app.put("/api/courses/{course_id}")
async def update_course_endpoint(
    course_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Update a course"""
    try:
        data = await request.json()
        
        # Check if new code conflicts with existing courses
        if "code" in data:
            existing = await get_course_by_code(db, data["code"])
            if existing and existing.id != course_id:
                raise HTTPException(status_code=400, detail="Course code already exists")
        
        course_update = CourseUpdate(**data)
        course = await update_course(db, course_id, course_update)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating course: {e}")
        raise HTTPException(status_code=500, detail="Failed to update course")

@app.delete("/api/courses/{course_id}")
async def delete_course_endpoint(course_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a course (soft delete)"""
    success = await delete_course(db, course_id)
    if not success:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted successfully"}

# === SEMESTER MANAGEMENT ENDPOINTS ===

@app.get("/api/semesters")
async def get_semesters_endpoint(
    created_by: int = 1,
    course_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all semesters, optionally filtered by course"""
    try:
        if course_id:
            semesters = await get_semesters_by_course(db, course_id=course_id, created_by=created_by)
        else:
            semesters = await get_semesters(db, created_by=created_by, skip=skip, limit=limit)
        return semesters
    except Exception as e:
        logger.error(f"Error getting semesters: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch semesters")

@app.get("/api/semesters/{semester_id}")
async def get_semester_endpoint(semester_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific semester by ID"""
    semester = await get_semester(db, semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    return semester

@app.get("/api/semesters/{semester_id}/any-status")
async def get_semester_any_status_endpoint(semester_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single semester by ID regardless of active status"""
    semester = await get_semester_any_status(db, semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    return semester

@app.post("/api/semesters")
async def create_semester_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create a new semester"""
    try:
        data = await request.json()
        
        # Check if semester code already exists
        existing = await get_semester_by_code(db, data.get("code"))
        if existing:
            raise HTTPException(status_code=400, detail="Semester code already exists")
        
        semester_data = SemesterCreate(**data)
        semester = await create_semester(db, semester_data)
        return semester
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating semester: {e}")
        raise HTTPException(status_code=500, detail="Failed to create semester")

@app.put("/api/semesters/{semester_id}")
async def update_semester_endpoint(
    semester_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Update a semester"""
    try:
        data = await request.json()
        
        # Check if new code conflicts with existing semesters
        if "code" in data and data["code"]:
            existing = await get_semester_by_code(db, data["code"])
            if existing and existing.id != semester_id:
                raise HTTPException(status_code=400, detail="Semester code already exists")
        
        semester_update = SemesterUpdate(**data)
        semester = await update_semester(db, semester_id, semester_update)
        if not semester:
            raise HTTPException(status_code=404, detail="Semester not found")
        return semester
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating semester: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to update semester: {str(e)}")

@app.delete("/api/semesters/{semester_id}")
async def delete_semester_endpoint(semester_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a semester (soft delete)"""
    success = await delete_semester(db, semester_id)
    if not success:
        raise HTTPException(status_code=404, detail="Semester not found")
    return {"message": "Semester deleted successfully"}

# === GROUP MANAGEMENT ENDPOINTS ===

@app.get("/api/groups")
async def get_groups_endpoint(
    created_by: Optional[int] = None,
    course_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all groups with optional filtering"""
    if course_id:
        groups = await get_groups_by_course(db, course_id, created_by)
    else:
        groups = await get_groups(db, created_by, skip, limit)
    
    # Filter by semester if specified
    if semester_id:
        groups = [g for g in groups if g.semester_id == semester_id]
    
    return groups

@app.get("/api/groups/{group_id}")
async def get_group_endpoint(group_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single group by ID"""
    group = await get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@app.post("/api/groups")
async def create_group_endpoint(group_data: dict, db: AsyncSession = Depends(get_db)):
    """Create a new group"""
    try:
        # Convert dict to Pydantic model
        group_create = GroupCreate(**group_data)
        
        # Check for duplicate group name
        existing_group = await get_group_by_name(db, group_create.name, group_create.created_by)
        if existing_group:
            raise HTTPException(status_code=400, detail="Group with this name already exists")
        
        group = await create_group(db, group_create)
        return group
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        raise HTTPException(status_code=500, detail="Failed to create group")

@app.put("/api/groups/{group_id}")
async def update_group_endpoint(group_id: int, group_data: dict, db: AsyncSession = Depends(get_db)):
    """Update a group"""
    try:
        group_update = GroupUpdate(**group_data)
        group = await update_group(db, group_id, group_update)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return group
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating group: {e}")
        raise HTTPException(status_code=500, detail="Failed to update group")

@app.delete("/api/groups/{group_id}")
async def delete_group_endpoint(group_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a group (soft delete)"""
    success = await delete_group(db, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group deleted successfully"}

# ===== Classroom Management Endpoints =====

@app.get("/api/classrooms", response_model=List[ClassroomResponse])
async def get_classrooms_endpoint(
    course_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all classrooms with optional filtering by course and/or semester"""
    classrooms = await get_classrooms(db, course_id=course_id, semester_id=semester_id, skip=skip, limit=limit)
    return classrooms

@app.get("/api/classrooms/{classroom_id}")
async def get_classroom_endpoint(classroom_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single classroom by ID with its groups"""
    classroom = await get_classroom_with_details(db, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    # Return classroom as dict without lazy loading issues
    return {
        "id": classroom.id,
        "name": classroom.name,
        "teacher_name": classroom.teacher_name,
        "language": classroom.language,
        "course_id": classroom.course_id,
        "semester_id": classroom.semester_id,
        "description": classroom.description,
        "created_by": classroom.created_by,
        "is_active": classroom.is_active,
        "created_at": classroom.created_at,
        "updated_at": classroom.updated_at,
        "course": {
            "id": classroom.course.id,
            "name": classroom.course.name,
            "code": classroom.course.code
        } if classroom.course else None,
        "semester": {
            "id": classroom.semester.id,
            "name": classroom.semester.name,
            "code": classroom.semester.code
        } if classroom.semester else None,
        "groups": [
            {
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "members": g.members
            } for g in classroom.groups
        ] if classroom.groups else []
    }

@app.post("/api/classrooms", response_model=ClassroomResponse)
async def create_classroom_endpoint(classroom_data: dict, db: AsyncSession = Depends(get_db)):
    """Create a new classroom"""
    try:
        # Convert dict to Pydantic model
        classroom_create = ClassroomCreate(**classroom_data)
        
        # TODO: Hardcoded created_by for now, replace with actual user ID from auth
        created_by = classroom_data.get("created_by", 1)
        
        classroom = await create_classroom(db, classroom_create, created_by)
        return classroom
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating classroom: {e}")
        raise HTTPException(status_code=500, detail="Failed to create classroom")

@app.put("/api/classrooms/{classroom_id}")
async def update_classroom_endpoint(classroom_id: int, classroom_data: dict, db: AsyncSession = Depends(get_db)):
    """Update a classroom"""
    try:
        classroom_update = ClassroomUpdate(**classroom_data)
        classroom = await update_classroom(db, classroom_id, classroom_update)
        if not classroom:
            raise HTTPException(status_code=404, detail="Classroom not found")
        return classroom
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating classroom: {e}")
        raise HTTPException(status_code=500, detail="Failed to update classroom")

@app.delete("/api/classrooms/{classroom_id}")
async def delete_classroom_endpoint(classroom_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a classroom (soft delete)"""
    success = await delete_classroom(db, classroom_id)
    if not success:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return {"message": "Classroom deleted successfully"}

# Test endpoint
@app.get("/api/test")
async def test_endpoint():
    return {"message": "Test endpoint works"}

# AI Evaluation endpoint
@app.post("/api/submissions/{submission_id}/ai-evaluate")
async def ai_evaluate_submission(
    submission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """AI evaluation of submission using Ollama with vision support"""
    import tempfile
    import base64
    from pdf2image import convert_from_path
    from io import BytesIO
    
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
                logger.info(f"Created temporary PDF from database: {pdf_file_path}")
            elif submission.pdf_file_path:
                # PDF is stored on filesystem
                pdf_file_path = f"uploads{submission.pdf_file_path}" if not submission.pdf_file_path.startswith('/uploads/') else f".{submission.pdf_file_path}"
                if not os.path.exists(pdf_file_path):
                    raise HTTPException(status_code=404, detail="PDF file not found on filesystem")
            else:
                raise HTTPException(status_code=404, detail="No PDF file found for this submission")
            
            # Extract text from PDF for context
            try:
                pdf_content = pymupdf4llm.to_markdown(pdf_file_path)
                logger.info(f"Extracted PDF content length: {len(pdf_content)}")
            except Exception as e:
                logger.error(f"Error extracting PDF text: {e}")
                pdf_content = ""
            
            # Convert PDF to images for vision model
            image_data = []
            if use_vision:
                try:
                    logger.info("Converting PDF to images for vision model...")
                    images = convert_from_path(pdf_file_path, dpi=150, fmt='png')
                    
                    # Limit to first 10 pages to avoid excessive processing
                    for page_num, img in enumerate(images[:10], 1):
                        buffered = BytesIO()
                        img.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        image_data.append(img_base64)
                        logger.info(f"Converted page {page_num} to image ({len(img_base64)} bytes base64)")
                    
                    logger.info(f"Successfully converted {len(image_data)} PDF pages to images")
                except Exception as e:
                    logger.error(f"Error converting PDF to images: {e}")
                    logger.warning("Falling back to text-only evaluation")
                    image_data = []
                    use_vision = False
        
        finally:
            # Clean up temporary file if created
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                try:
                    os.unlink(temp_pdf_path)
                    logger.info(f"Cleaned up temporary PDF: {temp_pdf_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temporary PDF: {e}")
        
        # Prepare exercise evaluation prompt
        exercises_info = []
        for exercise in assignment.exercises:
            exercises_info.append({
                "id": exercise.id,
                "points": exercise.points,
                "description": exercise.description,
                "evaluation_criteria": exercise.evaluation_criteria
            })
        
        # Use the centralized prompt function from ai_prompts.py
        prompt = get_submission_evaluation_prompt(
            assignment_name=assignment.name,
            assignment_description=assignment.description,
            exercises_info=exercises_info,
            pdf_content=pdf_content,
            use_vision=use_vision and bool(image_data),
            num_pages=len(image_data) if image_data else 0
        )

        # OLD CODE REMOVED - Prompt is now managed in ai_prompts.py
        # This keeps the code clean and prompts centralized
        """You are an expert academic evaluator analyzing a COMPLETE STUDENT SUBMISSION.

{'=' * 80}
ASSIGNMENT INFORMATION
{'=' * 80}
Assignment: {assignment.name}
Description: {assignment.description}

{'=' * 80}
EXERCISES TO EVALUATE (Total: {len(exercises_info)} exercises)
{'=' * 80}
You must evaluate ALL {len(exercises_info)} exercises listed below.
Each exercise may be answered in different sections/pages of the submission.

"""
        
        for i, exercise in enumerate(exercises_info):
            prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXERCISE {i + 1} [ID: {exercise['id']}] - Weight: {exercise['points']} points
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task Description:
{exercise['description']}

Evaluation Criteria:
{exercise['evaluation_criteria']}

"""
        
        submission_context = ""
        if pdf_content:
            # Increase text limit to capture more content
            max_text_length = 30000  # Increased from 10000
            submission_context = f"""
{'=' * 80}
STUDENT SUBMISSION - TEXT CONTENT (First {max_text_length} characters)
{'=' * 80}
{pdf_content[:max_text_length]}
{"..." if len(pdf_content) > max_text_length else ""}
"""
        
        prompt += f"""{vision_note}
{'=' * 80}
CRITICAL EVALUATION INSTRUCTIONS
{'=' * 80}

YOUR TASK:
1. Read through the ENTIRE submission (ALL pages/images provided)
   - SKIP the front page/cover page/index/table of contents
   - Focus on the actual content pages with exercise responses
2. For EACH of the {len(exercises_info)} exercises listed above:
   - Search for the student's response throughout the submission
   - The response may be in ANY section or page - don't assume order
   - Evaluate WHAT THE STUDENT ACTUALLY SUBMITTED (not the requirements)
   - Consider text, diagrams, code snippets, screenshots, tables, charts
   - Ignore table of contents, front pages, and index pages
3. If an exercise is not addressed, still include it with low score (1-2 points)
4. Be specific - cite actual content, page sections, or visual elements you evaluated
5. Use the same language as the submission for comments

{submission_context}

{'=' * 80}
REQUIRED OUTPUT FORMAT - MUST INCLUDE ALL {len(exercises_info)} EXERCISES
{'=' * 80}

Return ONLY valid JSON (no markdown blocks, no explanations, no extra text):

{{
  "exercise_grades": [
    {{
      "exercise_id": {exercises_info[0]['id']},
      "description": "Brief description of what this exercise asked for",
      "points": <number_1_to_10>,
      "comments": "Detailed evaluation: what was good, what was missing, specific observations from submission"
    }},"""
        
        # Add template for remaining exercises
        for i in range(1, len(exercises_info)):
            prompt += f"""
    {{
      "exercise_id": {exercises_info[i]['id']},
      "description": "Brief description of what this exercise asked for",
      "points": <number_1_to_10>,
      "comments": "Detailed evaluation: what was good, what was missing, specific observations from submission"
    }}{"," if i < len(exercises_info) - 1 else ""}"""
        
        prompt += """
  ]
}

GRADING SCALE (1-10 points per exercise):
- 9-10: Exceptional - Exceeds requirements, excellent quality, innovative
- 7-8: Excellent - Fully meets requirements with high quality
- 5-6: Good - Meets most requirements adequately
- 3-4: Adequate - Partially complete, noticeable gaps
- 1-2: Poor - Incomplete, major issues, or not addressed

COMMENTS MUST INCLUDE:
✓ Specific observations from the actual submission
✓ What was done well (strengths)
✓ What is missing or needs improvement (weaknesses)
✓ Reference to specific pages, sections, diagrams, or code if applicable
✓ Constructive feedback for improvement
✓ Same language as submission

RESPOND WITH ONLY THE JSON ARRAY. START WITH {{ and END WITH }}. NO MARKDOWN, NO EXTRA TEXT."""

        # Call Ollama API with vision support
        try:
            # Select model based on whether we have images
            model_to_use = "llava" if (use_vision and image_data) else "llama2"
            logger.info(f"Using AI model: {model_to_use} (vision={'enabled' if use_vision and image_data else 'disabled'})")
            
            if use_vision and image_data:
                # Use chat API for vision model with images
                ollama_response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": model_to_use,
                        "messages": [{
                            "role": "user",
                            "content": prompt,
                            "images": image_data
                        }],
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "num_predict": 2000
                        }
                    },
                    timeout=300  # Longer timeout for vision processing
                )
            else:
                # Use generate API for text-only model
                ollama_response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": model_to_use,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "max_tokens": 2000
                        }
                    },
                    timeout=120
                )
            
            if ollama_response.status_code != 200:
                logger.error(f"Ollama API error: {ollama_response.status_code} - {ollama_response.text}")
                raise HTTPException(status_code=500, detail="AI evaluation service unavailable")
            
            ai_response = ollama_response.json()
            
            # Extract response text (different format for chat vs generate API)
            if use_vision and image_data:
                # Chat API response format
                ai_text = ai_response.get("message", {}).get("content", "")
            else:
                # Generate API response format
                ai_text = ai_response.get("response", "")
            
            logger.info(f"AI response length: {len(ai_text)}")
            logger.info(f"AI response preview: {ai_text[:500]}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            raise HTTPException(status_code=500, detail="Failed to connect to AI evaluation service")
        
        # Parse AI response
        try:
            # Extract JSON from AI response
            json_start = ai_text.find('{')
            json_end = ai_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error(f"No valid JSON found in AI response")
                logger.error(f"Full AI response: {ai_text}")
                raise ValueError("No valid JSON found in AI response")
            
            json_str = ai_text[json_start:json_end]
            logger.info(f"Extracted JSON string: {json_str[:500]}...")
            
            ai_evaluation = json.loads(json_str)
            
            if "exercise_grades" not in ai_evaluation:
                logger.error(f"Invalid AI response format - missing exercise_grades")
                logger.error(f"AI evaluation keys: {ai_evaluation.keys()}")
                raise ValueError("Invalid AI response format")
            
            logger.info(f"Successfully parsed {len(ai_evaluation['exercise_grades'])} exercise grades")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing AI response: {e}")
            logger.error(f"Raw AI response: {ai_text}")
            logger.error(f"JSON start position: {json_start}, JSON end position: {json_end}")
            if json_start != -1 and json_end > 0:
                logger.error(f"Extracted JSON string: {json_str}")
            raise HTTPException(status_code=500, detail=f"Failed to parse AI evaluation results: {str(e)}")
        
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
        logger.error(f"Error in AI evaluation: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"AI evaluation failed: {str(e)}")

# Placeholder for additional endpoints

if __name__ == "__main__":
    import uvicorn
    # When running directly, use app object without reload
    # For reload mode, use: uvicorn db_server:app --reload
    print(f"🚀 Starting Smart Grade AI Backend")
    print(f"   Backend:  {settings.backend_url}")
    print(f"   Frontend: {settings.frontend_url}")
    print(f"   CORS Origins: {len(settings.cors_origins_list)} configured")
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.BACKEND_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
