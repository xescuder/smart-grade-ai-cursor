"""
Assignments router for assignment management with exercises
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io
import csv
import json
from datetime import datetime

from ai_prompts import get_exercise_extraction_prompt
from core.config import settings
from services.google_ai_service import GoogleAIService
from services.excel_grade_service import ExcelGradeService
from crud import (
    get_assignments as crud_get_assignments,
    get_assignment as crud_get_assignment,
    update_assignment as crud_update_assignment,
    delete_assignment as crud_delete_assignment,
    get_assignment_exercises as crud_get_assignment_exercises,
    update_assignment_exercises as crud_update_assignment_exercises,
    get_assignments_by_semester as crud_get_assignments_by_semester,
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


@router.get("/by-semester/{semester_id}", response_model=List[AssignmentResponse])
async def get_assignments_by_semester(
    semester_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all assignments for a specific semester"""
    assignments = await crud_get_assignments_by_semester(db, semester_id=semester_id)
    return assignments


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
        google_ai_service = GoogleAIService(api_key=settings.GOOGLE_API_KEY)
        
        result = await google_ai_service.analyse_pdf(
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


@router.get("/{assignment_id}/export-excel")
async def export_assignment_grades_excel(
    assignment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Export assignment grades as Excel file with comprehensive summary"""
    
    # Get assignment with exercises
    assignment = await crud_get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Get assignment exercises
    exercises = await crud_get_assignment_exercises(db, assignment_id)
    
    # Get submissions for this assignment with relationships loaded
    from database import Submission
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.group), selectinload(Submission.classroom))
        .where(Submission.assignment_id == assignment_id)
    )
    submissions = result.scalars().all()
    
    if not submissions:
        raise HTTPException(status_code=404, detail="No submissions found for this assignment")
    
    try:
        # Convert to dict format for Excel service
        assignment_dict = {
            'id': assignment.id,
            'name': assignment.name,
            'description': assignment.description or '',
            'due_date': assignment.due_date,
            'language': assignment.language or 'English',
            'exercises': [
                {
                    'id': ex.id,
                    'description': ex.description or '',
                    'points': ex.points,
                    'evaluation_criteria': ex.evaluation_criteria or '',
                    'order': ex.order
                } for ex in exercises
            ]
        }
        
        # Convert submissions to dict format
        submissions_dict = []
        for submission in submissions:
            try:
                submission_dict = {
                    'id': submission.id,
                    'assignment_id': submission.assignment_id,
                    'classroom_id': submission.classroom_id,
                    'group_id': submission.group_id,
                    'status': submission.status,
                    'total_score': submission.total_score,
                    'max_score': submission.max_score,
                    'percentage_score': submission.percentage_score,
                    'teacher_feedback': submission.teacher_feedback or '',
                    'ai_feedback': submission.ai_feedback or '',
                    'grade_breakdown': submission.grade_breakdown,
                    'submitted_at': submission.submitted_at,
                    'graded_at': submission.graded_at,
                    'coordinators': submission.coordinators or '',
                    'public_pdf_responsible_students': submission.public_pdf_responsible_students or '',
                    'group': {
                        'id': submission.group.id,
                        'name': submission.group.name,
                        'description': submission.group.description or '',
                        'members': submission.group.members or []
                    } if submission.group else None,
                    'classroom': {
                        'id': submission.classroom.id,
                        'name': submission.classroom.name,
                        'teacher_name': submission.classroom.teacher_name,
                        'language': submission.classroom.language or 'English'
                    } if submission.classroom else None
                }
                submissions_dict.append(submission_dict)
            except Exception as e:
                print(f"Error processing submission {submission.id}: {str(e)}")
                # Skip this submission and continue
                continue
        
        # Get classroom info from first submission
        classroom_info = submissions_dict[0].get('classroom') if submissions_dict else None
        
        # Generate Excel file
        try:
            excel_service = ExcelGradeService()
            excel_bytes = excel_service.generate_assignment_grade_summary(
                assignment_dict, 
                submissions_dict, 
                classroom_info
            )
        except Exception as e:
            print(f"Excel generation error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Excel generation failed: {str(e)}"
            )
        
        # Create filename
        assignment_name = assignment.name.replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{assignment_name}_grades_{timestamp}.xlsx"
        
        # Return Excel file as streaming response
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Excel export failed: {str(e)}"
        )


@router.get("/{assignment_id}/export-csv")
async def export_assignment_grades_csv(
    assignment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Export assignment grades as CSV with group-focused format"""
    
    # Get assignment with exercises
    assignment = await crud_get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Get assignment exercises
    exercises = await crud_get_assignment_exercises(db, assignment_id)
    
    # Get submissions for this assignment
    from crud import get_submissions_by_assignment
    submissions = await get_submissions_by_assignment(db, assignment_id)
    
    if not submissions:
        raise HTTPException(status_code=404, detail="No submissions found for this assignment")
    
    try:
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Create headers
        headers = ['Group']
        
        # Add exercise score columns
        for i, exercise in enumerate(exercises, 1):
            headers.append(f'Exercise {i} score')
        
        headers.extend([
            'Minutes (delivered)',
            'Public report score', 
            'Private report score',
            'Group comments',
            'Coordinator comments'
        ])
        
        writer.writerow(headers)
        
        # Process each submission
        for submission in submissions:
            row = []
            
            # Group name
            group_name = "No Group"
            if submission.group:
                group_name = submission.group.name
            row.append(group_name)
            
            # Exercise scores
            grade_breakdown = submission.grade_breakdown or []
            for exercise in exercises:
                # Find grade for this exercise
                exercise_grade = next(
                    (grade for grade in grade_breakdown if grade.get('exercise_id') == exercise.id),
                    None
                )
                
                if exercise_grade:
                    score = exercise_grade.get('score', exercise_grade.get('points', 0))
                else:
                    score = 0
                
                row.append(score)
            
            # Minutes delivered (Yes/No based on submission status)
            minutes_delivered = "Yes" if submission.status in ['graded', 'submitted'] else "No"
            row.append(minutes_delivered)
            
            # Public report score
            public_report_score = ""
            coordinator_comments = []
            
            ai_feedback = submission.ai_feedback or ""
            if ai_feedback:
                try:
                    feedback_data = json.loads(ai_feedback)
                    public_report = feedback_data.get('public_report', {})
                    public_report_score = public_report.get('points', '')
                    
                    # Add public report comments to coordinator comments
                    public_comments = public_report.get('comments', '')
                    if public_comments:
                        coordinator_comments.append(f"Public report: {public_comments}")
                        
                except (json.JSONDecodeError, TypeError):
                    pass
            
            row.append(public_report_score)
            
            # Private report score
            private_report_score = ""
            if ai_feedback:
                try:
                    feedback_data = json.loads(ai_feedback)
                    private_report = feedback_data.get('private_report', {})
                    
                    # Extract coordinator scores from private report
                    coordinators = private_report.get('coordinators', [])
                    if coordinators:
                        # Take average of coordinator scores
                        coord_scores = [float(coord.get('points', 0)) for coord in coordinators if coord.get('points')]
                        if coord_scores:
                            private_report_score = round(sum(coord_scores) / len(coord_scores), 2)
                    
                    # Add private report comments to coordinator comments
                    for coord in coordinators:
                        coord_comments = coord.get('comments', '')
                        if coord_comments:
                            coordinator_comments.append(f"Private report ({coord.get('name', 'Coordinator')}): {coord_comments}")
                            
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
            
            row.append(private_report_score)
            
            # Group comments (join all exercise comments)
            group_comments = []
            for exercise in exercises:
                exercise_grade = next(
                    (grade for grade in grade_breakdown if grade.get('exercise_id') == exercise.id),
                    None
                )
                
                if exercise_grade:
                    comments = exercise_grade.get('feedback', exercise_grade.get('comments', ''))
                    if comments:
                        group_comments.append(f"Exercise {exercises.index(exercise) + 1}: {comments}")
            
            group_comments_str = '\n'.join(group_comments)
            row.append(group_comments_str)
            
            # Coordinator comments (join public and private report comments)
            coordinator_comments_str = '\n'.join(coordinator_comments)
            row.append(coordinator_comments_str)
            
            writer.writerow(row)
        
        # Prepare CSV response
        csv_content = output.getvalue()
        output.close()
        
        # Create filename
        assignment_name = assignment.name.replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{assignment_name}_group_grades_{timestamp}.csv"
        
        # Return CSV file as streaming response
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CSV export failed: {str(e)}"
        )
