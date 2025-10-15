"""
Grading router for AI-powered grading operations
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .auth import User, get_current_user
from database import get_db

router = APIRouter()


class GradeRequest(BaseModel):
    submission_id: int
    use_ai: bool = True
    manual_grade: Optional[float] = None
    manual_feedback: Optional[str] = None


class GradeResponse(BaseModel):
    submission_id: int
    grade: float
    feedback: str
    confidence_score: float
    grading_criteria: dict
    graded_by: str  # 'ai' or 'manual'


class GradingJob(BaseModel):
    id: int
    submission_ids: List[int]
    status: str  # 'pending', 'processing', 'completed', 'failed'
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: List[GradeResponse] = []


# Mock grading jobs
mock_grading_jobs = []


async def ai_grade_submission(submission_id: int) -> GradeResponse:
    """
    AI grading function - mock implementation
    In production, this would integrate with OpenAI, Anthropic, or other AI services
    """
    # Mock AI grading logic
    # In production, this would send the submission to an AI model
    mock_grade = 85.5  # Mock grade
    mock_feedback = """
    Good effort on this assignment! Your introduction clearly states the topic and thesis. 
    The body paragraphs provide relevant examples and evidence. 
    Consider strengthening the conclusion and checking for minor grammatical errors.
    
    Strengths:
    - Clear thesis statement
    - Good use of examples
    - Logical flow
    
    Areas for improvement:
    - Conclusion could be more impactful
    - Minor grammar issues throughout
    """
    
    # Update the submission with grade
    # submission.grade = mock_grade
    # submission.feedback = mock_feedback
    # submission.graded_at = datetime.now()
    # submission.status = "graded"

    return GradeResponse(
        submission_id=submission_id,
        grade=mock_grade,
        feedback=mock_feedback,
        confidence_score=0.87,
        grading_criteria={
            "content": 88,
            "organization": 85,
            "grammar": 83
        },
        graded_by="ai"
    )


def process_grading_job(job_id: int):
    """Background task to process grading job"""
    job = next((j for j in mock_grading_jobs if j.id == job_id), None)
    if not job:
        return
    
    job.status = "processing"
    
    try:
        # Process each submission
        for submission_id in job.submission_ids:
            # In production, this would be an async call to AI service
            grade_result = ai_grade_submission(submission_id)
            job.results.append(grade_result)
        
        job.status = "completed"
        job.completed_at = datetime.now()
    except Exception as e:
        job.status = "failed"
        print(f"Grading job {job_id} failed: {e}")


@router.post("/grade", response_model=GradeResponse)
async def grade_submission(
    grade_request: GradeRequest,
    current_user: User = Depends(get_current_user)
):
    """Grade a single submission"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can grade submissions")
    
    if grade_request.use_ai:
        # Use AI grading
        return await ai_grade_submission(grade_request.submission_id)
    else:
        # Manual grading
        # submission = next((s for s in mock_submissions if s.id == grade_request.submission_id), None)
        # if not submission:
        #     raise HTTPException(status_code=404, detail="Submission not found")

        # submission.grade = grade_request.manual_grade
        # submission.feedback = grade_request.manual_feedback
        # submission.graded_at = datetime.now()
        # submission.graded_by = current_user.id
        # submission.status = "graded"

        return GradeResponse(
            submission_id=grade_request.submission_id,
            grade=grade_request.manual_grade,
            feedback=grade_request.manual_feedback,
            confidence_score=1.0,
            grading_criteria={},
            graded_by="manual"
        )


@router.post("/batch-grade", response_model=GradingJob)
async def batch_grade_submissions(
    submission_ids: List[int],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Start batch grading job"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can grade submissions")
    
    job = GradingJob(
        id=len(mock_grading_jobs) + 1,
        submission_ids=submission_ids,
        status="pending",
        created_at=datetime.now()
    )
    
    mock_grading_jobs.append(job)
    
    # Start background task
    background_tasks.add_task(process_grading_job, job.id)
    
    return job


@router.get("/jobs", response_model=List[GradingJob])
async def get_grading_jobs(current_user: User = Depends(get_current_user)):
    """Get grading jobs"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view grading jobs")
    
    return mock_grading_jobs


@router.get("/jobs/{job_id}", response_model=GradingJob)
async def get_grading_job(
    job_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get grading job by ID"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view grading jobs")
    
    job = next((j for j in mock_grading_jobs if j.id == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Grading job not found")
    
    return job
