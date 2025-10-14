"""
CRUD operations for Smart Grade AI
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from database import Assignment, Exercise, SectionExtractionConfig, Submission, Group, Course, Semester, Classroom
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Pydantic models for API
class ExerciseBase(BaseModel):
    description: str
    evaluation_criteria: Optional[str] = None
    points: int
    order: int = 1

class ExerciseCreate(ExerciseBase):
    pass

class ExerciseUpdate(ExerciseBase):
    pass

class ExerciseResponse(ExerciseBase):
    id: int
    assignment_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AssignmentBase(BaseModel):
    name: str
    description: str
    due_date: datetime
    language: str  # Language code: en, es, ca, etc.
    is_active: bool = True

class AssignmentCreate(AssignmentBase):
    classroom_ids: List[int] = []  # List of classroom IDs to assign this to
    exercises: List[ExerciseCreate] = []

class AssignmentUpdate(AssignmentBase):
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    pdf_file_data: Optional[bytes] = None
    pdf_mime_type: Optional[str] = None
    pdf_file_size: Optional[int] = None

class AssignmentResponse(AssignmentBase):
    id: int
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    # Exclude raw bytes from API response for performance/security
    created_by: int
    created_at: datetime
    updated_at: datetime
    exercises: List[ExerciseResponse] = []

    class Config:
        from_attributes = True

# CRUD Operations for Assignments
async def create_assignment(db: AsyncSession, assignment: AssignmentCreate, created_by: int) -> Assignment:
    """Create a new assignment with exercises and associate with classrooms"""
    db_assignment = Assignment(
        name=assignment.name,
        description=assignment.description,
        due_date=assignment.due_date,
        language=assignment.language,
        is_active=assignment.is_active,
        created_by=created_by
    )
    
    db.add(db_assignment)
    await db.flush()  # Get the assignment ID
    
    # Associate with classrooms
    if assignment.classroom_ids:
        from crud import get_classroom  # Import here to avoid circular import
        for classroom_id in assignment.classroom_ids:
            classroom = await get_classroom(db, classroom_id)
            if classroom:
                db_assignment.classrooms.append(classroom)
    
    # Add exercises
    for exercise_data in assignment.exercises:
        db_exercise = Exercise(
            assignment_id=db_assignment.id,
            description=exercise_data.description,
            evaluation_criteria=exercise_data.evaluation_criteria,
            points=exercise_data.points,
            order=exercise_data.order
        )
        db.add(db_exercise)
    
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment

async def get_assignments(db: AsyncSession) -> List[Assignment]:
    """Get all assignments with their exercises and classrooms"""
    result = await db.execute(
        select(Assignment)
        .options(selectinload(Assignment.exercises))
        .options(selectinload(Assignment.classrooms))
        .order_by(Assignment.created_at.desc())
    )
    return result.scalars().all()

async def get_assignment(db: AsyncSession, assignment_id: int) -> Optional[Assignment]:
    """Get a single assignment by ID with exercises and classrooms"""
    result = await db.execute(
        select(Assignment)
        .options(selectinload(Assignment.exercises))
        .options(selectinload(Assignment.classrooms))
        .where(Assignment.id == assignment_id)
    )
    return result.scalar_one_or_none()

async def update_assignment(db: AsyncSession, assignment_id: int, assignment_update: AssignmentUpdate) -> Optional[Assignment]:
    """Update an assignment"""
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    db_assignment = result.scalar_one_or_none()
    
    if not db_assignment:
        return None
    
    # Update fields
    for field, value in assignment_update.dict(exclude_unset=True).items():
        setattr(db_assignment, field, value)
    
    db_assignment.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment

async def delete_assignment(db: AsyncSession, assignment_id: int) -> bool:
    """Delete an assignment and its exercises"""
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    db_assignment = result.scalar_one_or_none()
    
    if not db_assignment:
        return False
    
    await db.delete(db_assignment)
    await db.commit()
    return True

# CRUD Operations for Exercises
async def get_assignment_exercises(db: AsyncSession, assignment_id: int) -> List[Exercise]:
    """Get all exercises for an assignment"""
    result = await db.execute(
        select(Exercise)
        .where(Exercise.assignment_id == assignment_id)
        .order_by(Exercise.order)
    )
    return result.scalars().all()

async def update_assignment_exercises(db: AsyncSession, assignment_id: int, exercises: List[ExerciseUpdate]) -> List[Exercise]:
    """Replace all exercises for an assignment"""
    # First, delete existing exercises
    await db.execute(delete(Exercise).where(Exercise.assignment_id == assignment_id))
    
    # Add new exercises
    db_exercises = []
    for exercise_data in exercises:
        db_exercise = Exercise(
            assignment_id=assignment_id,
            description=exercise_data.description,
            evaluation_criteria=exercise_data.evaluation_criteria,
            points=exercise_data.points,
            order=exercise_data.order
        )
        db.add(db_exercise)
        db_exercises.append(db_exercise)
    
    await db.commit()
    
    # Refresh to get IDs
    for exercise in db_exercises:
        await db.refresh(exercise)
    
    return db_exercises

async def update_assignment_pdf(db: AsyncSession, assignment_id: int, file_path: str, file_name: str) -> Optional[Assignment]:
    """Update PDF information for an assignment"""
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    db_assignment = result.scalar_one_or_none()
    
    if not db_assignment:
        return None
    
    db_assignment.pdf_file_path = file_path
    db_assignment.pdf_file_name = file_name
    db_assignment.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment

async def update_assignment_pdf_bytes(
    db: AsyncSession,
    assignment_id: int,
    file_bytes: bytes,
    file_name: str,
    mime_type: str = "application/pdf"
) -> Optional[Assignment]:
    """Update assignment to store PDF in DB as bytes (bytea)."""
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    db_assignment = result.scalar_one_or_none()
    if not db_assignment:
        return None
    db_assignment.pdf_file_data = file_bytes
    db_assignment.pdf_file_name = file_name
    db_assignment.pdf_mime_type = mime_type
    db_assignment.pdf_file_size = len(file_bytes) if file_bytes is not None else None
    # Clear path to indicate DB-backed storage
    db_assignment.pdf_file_path = None
    db_assignment.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment

async def remove_assignment_pdf(db: AsyncSession, assignment_id: int) -> Optional[Assignment]:
    """Remove PDF information from an assignment"""
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    db_assignment = result.scalar_one_or_none()
    
    if not db_assignment:
        return None
    
    db_assignment.pdf_file_path = None
    db_assignment.pdf_file_name = None
    db_assignment.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment

# Pydantic models for Section Extraction Configuration
class SectionExtractionConfigBase(BaseModel):
    name: str
    markers: str  # JSON string of array
    description: Optional[str] = None
    priority: int = 1
    is_active: bool = True
    extraction_strategy: str = 'section_to_end'
    max_characters: int = 4000

class SectionExtractionConfigCreate(SectionExtractionConfigBase):
    pass

class SectionExtractionConfigUpdate(SectionExtractionConfigBase):
    pass

class SectionExtractionConfigResponse(SectionExtractionConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# CRUD Operations for Section Extraction Configuration
async def get_section_extraction_configs(db: AsyncSession) -> List[SectionExtractionConfig]:
    """Get all section extraction configurations"""
    result = await db.execute(
        select(SectionExtractionConfig)
        .where(SectionExtractionConfig.is_active == True)
        .order_by(SectionExtractionConfig.priority)
    )
    return result.scalars().all()

async def get_section_extraction_config(db: AsyncSession, config_id: int) -> Optional[SectionExtractionConfig]:
    """Get a single section extraction configuration by ID"""
    result = await db.execute(
        select(SectionExtractionConfig)
        .where(SectionExtractionConfig.id == config_id)
    )
    return result.scalar_one_or_none()

async def create_section_extraction_config(db: AsyncSession, config: SectionExtractionConfigCreate) -> SectionExtractionConfig:
    """Create a new section extraction configuration"""
    db_config = SectionExtractionConfig(
        name=config.name,
        markers=config.markers,
        description=config.description,
        priority=config.priority,
        is_active=config.is_active,
        extraction_strategy=config.extraction_strategy,
        max_characters=config.max_characters
    )
    
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)
    return db_config

async def update_section_extraction_config(db: AsyncSession, config_id: int, config_update: SectionExtractionConfigUpdate) -> Optional[SectionExtractionConfig]:
    """Update a section extraction configuration"""
    result = await db.execute(select(SectionExtractionConfig).where(SectionExtractionConfig.id == config_id))
    db_config = result.scalar_one_or_none()
    
    if not db_config:
        return None
    
    # Update fields
    for field, value in config_update.dict(exclude_unset=True).items():
        setattr(db_config, field, value)
    
    db_config.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_config)
    return db_config

async def delete_section_extraction_config(db: AsyncSession, config_id: int) -> bool:
    """Delete a section extraction configuration"""
    result = await db.execute(select(SectionExtractionConfig).where(SectionExtractionConfig.id == config_id))
    db_config = result.scalar_one_or_none()
    
    if not db_config:
        return False
    
    await db.delete(db_config)
    await db.commit()
    return True

# === SUBMISSION MODELS AND OPERATIONS ===

# Pydantic models for submissions
class StudentInfo(BaseModel):
    name: str
    email: str
    student_id: str

class SubmissionFile(BaseModel):
    name: str
    path: str
    size: int
    content_type: str

class ExerciseGrade(BaseModel):
    exercise_id: int
    score: float
    feedback: Optional[str] = None

class SubmissionBase(BaseModel):
    assignment_id: int
    course_id: Optional[int] = None
    semester_id: Optional[int] = None
    group_id: Optional[int] = None
    comments: Optional[str] = None
    status: str = 'submitted'

class SubmissionCreate(SubmissionBase):
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    pdf_file_data: Optional[bytes] = None
    pdf_mime_type: Optional[str] = None
    pdf_file_size: Optional[int] = None

class SubmissionUpdate(BaseModel):
    course_id: Optional[int] = None
    semester_id: Optional[int] = None
    group_id: Optional[int] = None
    comments: Optional[str] = None
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    pdf_file_data: Optional[bytes] = None
    pdf_mime_type: Optional[str] = None
    pdf_file_size: Optional[int] = None
    status: Optional[str] = None
    total_score: Optional[float] = None
    percentage_score: Optional[float] = None
    teacher_feedback: Optional[str] = None
    grade_breakdown: Optional[List[dict]] = None
    ai_feedback: Optional[str] = None
    graded_by: Optional[int] = None


# CRUD operations for submissions
async def get_submissions(db: AsyncSession, assignment_id: Optional[int] = None, course_id: Optional[int] = None, semester_id: Optional[int] = None, group_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Submission]:
    """Get all submissions with optional filtering"""
    # Use simple query without eager loading to avoid relationship issues
    query = select(Submission)
    
    if assignment_id:
        query = query.where(Submission.assignment_id == assignment_id)
    if course_id:
        query = query.where(Submission.course_id == course_id)
    if semester_id:
        query = query.where(Submission.semester_id == semester_id)
    if group_id:
        query = query.where(Submission.group_id == group_id)
    
    query = query.offset(skip).limit(limit).order_by(Submission.submitted_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_submission(db: AsyncSession, submission_id: int) -> Optional[Submission]:
    """Get a single submission by ID"""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Submission).options(
            selectinload(Submission.assignment),
            selectinload(Submission.course),
            selectinload(Submission.semester),
            selectinload(Submission.group)
        ).where(Submission.id == submission_id)
    )
    return result.scalar_one_or_none()

async def get_submissions_by_assignment(db: AsyncSession, assignment_id: int) -> List[Submission]:
    """Get all submissions for a specific assignment"""
    result = await db.execute(
        select(Submission)
        .where(Submission.assignment_id == assignment_id)
        .order_by(Submission.submitted_at.desc())
    )
    return result.scalars().all()

async def create_submission(db: AsyncSession, submission: SubmissionCreate) -> Submission:
    """Create a new submission"""
    # Calculate max_score from assignment exercises
    assignment_result = await db.execute(
        select(Assignment).where(Assignment.id == submission.assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()
    
    # Get exercises separately to avoid selectinload issues
    if assignment:
        exercises_result = await db.execute(
            select(Exercise).where(Exercise.assignment_id == submission.assignment_id)
        )
        exercises = exercises_result.scalars().all()
        max_score = sum(exercise.points for exercise in exercises) if exercises else 100
    else:
        max_score = 100
    
    db_submission = Submission(
        assignment_id=submission.assignment_id,
        course_id=submission.course_id,
        semester_id=submission.semester_id,
        group_id=submission.group_id,
        comments=submission.comments,
        pdf_file_path=submission.pdf_file_path,
        pdf_file_name=submission.pdf_file_name,
        pdf_file_data=submission.pdf_file_data,
        pdf_mime_type=submission.pdf_mime_type,
        pdf_file_size=submission.pdf_file_size,
        status=submission.status,
        max_score=max_score,
        is_late=assignment.due_date < datetime.now() if assignment else False
    )
    
    db.add(db_submission)
    await db.commit()
    await db.refresh(db_submission)
    # Expunge the object from the session to avoid lazy loading issues
    db.expunge(db_submission)
    return db_submission

async def update_submission(db: AsyncSession, submission_id: int, submission_update: SubmissionUpdate) -> Optional[Submission]:
    """Update a submission"""
    try:
        result = await db.execute(select(Submission).where(Submission.id == submission_id))
        db_submission = result.scalar_one_or_none()
        
        if not db_submission:
            print(f"Submission {submission_id} not found")
            return None
        
        # Update fields
        update_data = submission_update.model_dump(exclude_unset=True)
        print(f"Update data: {update_data}")
        
        # Handle nested models
        if 'grade_breakdown' in update_data and update_data['grade_breakdown']:
            # grade_breakdown is already a list of dicts, keep as is
            pass  # No conversion needed since it's already a list of dicts
        
        # Set graded_at if scoring
        if 'total_score' in update_data or 'grade_breakdown' in update_data:
            update_data['graded_at'] = datetime.now()
            if 'status' not in update_data:
                update_data['status'] = 'graded'
        
        # Calculate percentage if total_score is provided
        if 'total_score' in update_data and db_submission.max_score:
            update_data['percentage_score'] = (update_data['total_score'] / db_submission.max_score) * 100
        
        for field, value in update_data.items():
            print(f"Setting {field} = {value}")
            setattr(db_submission, field, value)
        
        db_submission.updated_at = datetime.now()
        await db.commit()
        await db.refresh(db_submission)
        return db_submission
    except Exception as e:
        print(f"Error in update_submission: {str(e)}")
        await db.rollback()
        raise e

async def delete_submission(db: AsyncSession, submission_id: int) -> bool:
    """Delete a submission"""
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    db_submission = result.scalar_one_or_none()
    
    if not db_submission:
        return False
    
    await db.delete(db_submission)
    await db.commit()
    return True

# === GROUP MODELS AND OPERATIONS ===

# Pydantic models for groups
class GroupMember(BaseModel):
    name: str
    email: str
    student_id: str

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    course_id: Optional[int] = None
    semester_id: Optional[int] = None
    members: Optional[List[GroupMember]] = []
    max_members: Optional[int] = None
    is_active: bool = True

class GroupCreate(GroupBase):
    created_by: int

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    course_id: Optional[int] = None
    semester_id: Optional[int] = None
    members: Optional[List[GroupMember]] = None
    max_members: Optional[int] = None
    is_active: Optional[bool] = None

# CRUD operations for groups
async def get_groups(db: AsyncSession, created_by: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Group]:
    """Get all groups, optionally filtered by creator"""
    from sqlalchemy.orm import selectinload
    
    query = select(Group).where(Group.is_active == True)
    
    if created_by:
        query = query.where(Group.created_by == created_by)
    
    # Load related course and semester data
    query = query.options(
        selectinload(Group.course),
        selectinload(Group.semester)
    ).offset(skip).limit(limit).order_by(Group.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_group(db: AsyncSession, group_id: int) -> Optional[Group]:
    """Get a single group by ID"""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Group).options(
            selectinload(Group.course),
            selectinload(Group.semester)
        ).where(Group.id == group_id, Group.is_active == True)
    )
    return result.scalar_one_or_none()

async def get_group_by_name(db: AsyncSession, name: str, created_by: int) -> Optional[Group]:
    """Get a group by name and creator (to check for duplicates)"""
    result = await db.execute(
        select(Group).where(
            Group.name == name, 
            Group.created_by == created_by,
            Group.is_active == True
        )
    )
    return result.scalar_one_or_none()

async def create_group(db: AsyncSession, group: GroupCreate) -> Group:
    """Create a new group"""
    
    # Convert Pydantic models to dict for JSON storage
    members_dict = [member.model_dump() for member in (group.members or [])]
    
    db_group = Group(
        name=group.name,
        description=group.description,
        course_id=group.course_id,
        semester_id=group.semester_id,
        members=members_dict,
        max_members=group.max_members,
        created_by=group.created_by,
        is_active=group.is_active
    )
    
    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)
    return db_group

async def update_group(db: AsyncSession, group_id: int, group_update: GroupUpdate) -> Optional[Group]:
    """Update a group"""
    result = await db.execute(select(Group).where(Group.id == group_id, Group.is_active == True))
    db_group = result.scalar_one_or_none()
    
    if not db_group:
        return None
    
    # Update fields
    update_data = group_update.model_dump(exclude_unset=True)
    
    # Handle nested models
    if 'members' in update_data and update_data['members'] is not None:
        update_data['members'] = [member.model_dump() for member in update_data['members']]
    
    for field, value in update_data.items():
        setattr(db_group, field, value)
    
    db_group.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_group)
    return db_group

async def delete_group(db: AsyncSession, group_id: int) -> bool:
    """Soft delete a group (set is_active to False)"""
    result = await db.execute(select(Group).where(Group.id == group_id, Group.is_active == True))
    db_group = result.scalar_one_or_none()
    
    if not db_group:
        return False
    
    db_group.is_active = False
    db_group.updated_at = datetime.utcnow()
    await db.commit()
    return True

async def get_groups_by_course(db: AsyncSession, course_id: int, created_by: Optional[int] = None) -> List[Group]:
    """Get all groups for a specific course"""
    from sqlalchemy.orm import selectinload
    
    query = select(Group).where(Group.course_id == course_id, Group.is_active == True)
    
    if created_by:
        query = query.where(Group.created_by == created_by)
    
    # Load related course and semester data
    query = query.options(
        selectinload(Group.course),
        selectinload(Group.semester)
    ).order_by(Group.name)
    
    result = await db.execute(query)
    return result.scalars().all()

# === COURSE MODELS AND OPERATIONS ===

# Pydantic models for courses
class CourseBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    department: Optional[str] = None
    credits: Optional[int] = Field(None, ge=0, le=15, description="Course credits (0-15)")
    is_active: bool = True

class CourseCreate(CourseBase):
    created_by: int

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    credits: Optional[int] = Field(None, ge=0, le=15, description="Course credits (0-15)")
    is_active: Optional[bool] = None

class CourseResponse(CourseBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# CRUD operations for courses
async def get_courses(db: AsyncSession, created_by: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Course]:
    """Get all courses, optionally filtered by creator"""
    query = select(Course).where(Course.is_active == True)
    
    if created_by:
        query = query.where(Course.created_by == created_by)
    
    query = query.offset(skip).limit(limit).order_by(Course.name)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_course(db: AsyncSession, course_id: int) -> Optional[Course]:
    """Get a single course by ID"""
    result = await db.execute(
        select(Course).where(Course.id == course_id, Course.is_active == True)
    )
    return result.scalar_one_or_none()

async def get_course_by_code(db: AsyncSession, code: str) -> Optional[Course]:
    """Get a course by code (to check for duplicates)"""
    result = await db.execute(
        select(Course).where(Course.code == code, Course.is_active == True)
    )
    return result.scalar_one_or_none()

async def create_course(db: AsyncSession, course: CourseCreate) -> Course:
    """Create a new course"""
    
    db_course = Course(
        name=course.name,
        code=course.code,
        description=course.description,
        department=course.department,
        credits=course.credits,
        created_by=course.created_by,
        is_active=course.is_active
    )
    
    db.add(db_course)
    await db.commit()
    await db.refresh(db_course)
    return db_course

async def update_course(db: AsyncSession, course_id: int, course_update: CourseUpdate) -> Optional[Course]:
    """Update a course"""
    result = await db.execute(select(Course).where(Course.id == course_id, Course.is_active == True))
    db_course = result.scalar_one_or_none()
    
    if not db_course:
        return None
    
    # Update fields
    update_data = course_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_course, field, value)
    
    db_course.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_course)
    return db_course

async def delete_course(db: AsyncSession, course_id: int) -> bool:
    """Soft delete a course (set is_active to False)"""
    result = await db.execute(select(Course).where(Course.id == course_id, Course.is_active == True))
    db_course = result.scalar_one_or_none()
    
    if not db_course:
        return False
    
    db_course.is_active = False
    db_course.updated_at = datetime.utcnow()
    await db.commit()
    return True

async def get_courses_by_department(db: AsyncSession, department: str, created_by: Optional[int] = None) -> List[Course]:
    """Get all courses for a specific department"""
    query = select(Course).where(Course.department == department, Course.is_active == True)
    
    if created_by:
        query = query.where(Course.created_by == created_by)
    
    query = query.order_by(Course.name)
    
    result = await db.execute(query)
    return result.scalars().all()

# === SEMESTER MODELS AND OPERATIONS ===

# Pydantic models for semesters
class SemesterBase(BaseModel):
    name: str
    code: str
    year: int
    season: str
    start_date: datetime
    end_date: datetime
    course_id: int
    is_active: bool = True

class SemesterCreate(SemesterBase):
    created_by: int

class SemesterUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    year: Optional[int] = None
    season: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    course_id: Optional[int] = None
    is_active: Optional[bool] = None

class SemesterResponse(SemesterBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Group Response model (defined after Course and Semester models)
class GroupResponse(GroupBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    course: Optional[CourseResponse] = None
    semester: Optional[SemesterResponse] = None

    class Config:
        from_attributes = True

class SubmissionResponse(SubmissionBase):
    id: int
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    pdf_file_size: Optional[int] = None
    pdf_mime_type: Optional[str] = None
    total_score: Optional[float] = None
    max_score: Optional[float] = None
    percentage_score: Optional[float] = None
    teacher_feedback: Optional[str] = None
    ai_feedback: Optional[str] = None
    grade_breakdown: Optional[List[ExerciseGrade]] = []
    submitted_at: datetime
    graded_at: Optional[datetime] = None
    # Relationship data - excluded to avoid lazy loading issues
    # course: Optional[CourseResponse] = None
    # semester: Optional[SemesterResponse] = None
    # group: Optional[GroupResponse] = None
    graded_by: Optional[int] = None
    is_late: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# CRUD operations for semesters
async def get_semesters(db: AsyncSession, created_by: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Semester]:
    """Get all semesters, optionally filtered by creator"""
    query = select(Semester).where(Semester.is_active == True)
    
    if created_by:
        query = query.where(Semester.created_by == created_by)
    
    query = query.offset(skip).limit(limit).order_by(Semester.year.desc(), Semester.season)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_semester(db: AsyncSession, semester_id: int) -> Optional[Semester]:
    """Get a single semester by ID"""
    result = await db.execute(
        select(Semester).where(Semester.id == semester_id, Semester.is_active == True)
    )
    return result.scalar_one_or_none()

async def get_semester_any_status(db: AsyncSession, semester_id: int) -> Optional[Semester]:
    """Get a single semester by ID regardless of active status"""
    result = await db.execute(
        select(Semester).where(Semester.id == semester_id)
    )
    return result.scalar_one_or_none()

async def get_semester_by_code(db: AsyncSession, code: str) -> Optional[Semester]:
    """Get a semester by code (to check for duplicates)"""
    result = await db.execute(
        select(Semester).where(Semester.code == code, Semester.is_active == True)
    )
    return result.scalar_one_or_none()

async def create_semester(db: AsyncSession, semester: SemesterCreate) -> Semester:
    """Create a new semester"""
    
    db_semester = Semester(
        name=semester.name,
        code=semester.code,
        year=semester.year,
        season=semester.season,
        start_date=semester.start_date,
        end_date=semester.end_date,
        course_id=semester.course_id,
        created_by=semester.created_by,
        is_active=semester.is_active
    )
    
    db.add(db_semester)
    await db.commit()
    await db.refresh(db_semester)
    return db_semester

async def update_semester(db: AsyncSession, semester_id: int, semester_update: SemesterUpdate) -> Optional[Semester]:
    """Update a semester"""
    result = await db.execute(select(Semester).where(Semester.id == semester_id))
    db_semester = result.scalar_one_or_none()
    
    if not db_semester:
        return None
    
    # Update fields
    update_data = semester_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_semester, field, value)
    
    db_semester.updated_at = datetime.now()
    await db.commit()
    await db.refresh(db_semester)
    return db_semester

async def delete_semester(db: AsyncSession, semester_id: int) -> bool:
    """Soft delete a semester (set is_active to False)"""
    result = await db.execute(select(Semester).where(Semester.id == semester_id, Semester.is_active == True))
    db_semester = result.scalar_one_or_none()
    
    if not db_semester:
        return False
    
    db_semester.is_active = False
    db_semester.updated_at = datetime.utcnow()
    await db.commit()
    return True

async def get_semesters_by_year(db: AsyncSession, year: int, created_by: Optional[int] = None) -> List[Semester]:
    """Get all semesters for a specific year"""
    query = select(Semester).where(Semester.year == year, Semester.is_active == True)
    
    if created_by:
        query = query.where(Semester.created_by == created_by)
    
    query = query.order_by(Semester.season)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_current_semester(db: AsyncSession, created_by: Optional[int] = None) -> Optional[Semester]:
    """Get the current active semester"""
    from datetime import datetime
    now = datetime.utcnow()
    
    query = select(Semester).where(
        Semester.start_date <= now,
        Semester.end_date >= now,
        Semester.is_active == True
    )
    
    if created_by:
        query = query.where(Semester.created_by == created_by)
    
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_semesters_by_course(db: AsyncSession, course_id: int, created_by: Optional[int] = None) -> List[Semester]:
    """Get all semesters for a specific course"""
    query = select(Semester).where(Semester.course_id == course_id, Semester.is_active == True)
    
    if created_by:
        query = query.where(Semester.created_by == created_by)
    
    query = query.order_by(Semester.year.desc(), Semester.season)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_courses_with_semesters(db: AsyncSession, created_by: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Course]:
    """Get all courses with their semesters"""
    query = select(Course).where(Course.is_active == True)
    
    if created_by:
        query = query.where(Course.created_by == created_by)
    
    query = query.options(selectinload(Course.semesters)).offset(skip).limit(limit).order_by(Course.name)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_course_with_semesters(db: AsyncSession, course_id: int) -> Optional[Course]:
    """Get a single course by ID with its semesters"""
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.semesters))
        .where(Course.id == course_id, Course.is_active == True)
    )
    return result.scalar_one_or_none()

# ===== Classroom Management =====

class ClassroomBase(BaseModel):
    name: str
    teacher_name: str
    language: str  # e.g., "en", "es", "ca", "English", "Spanish", "Catalan"
    course_id: int
    semester_id: int
    description: Optional[str] = None

class ClassroomCreate(ClassroomBase):
    pass

class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    teacher_name: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ClassroomResponse(ClassroomBase):
    id: int
    created_by: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

async def create_classroom(db: AsyncSession, classroom: ClassroomCreate, created_by: int) -> Classroom:
    """Create a new classroom"""
    db_classroom = Classroom(
        name=classroom.name,
        teacher_name=classroom.teacher_name,
        language=classroom.language,
        course_id=classroom.course_id,
        semester_id=classroom.semester_id,
        description=classroom.description,
        created_by=created_by,
        is_active=True
    )
    
    db.add(db_classroom)
    await db.commit()
    await db.refresh(db_classroom)
    return db_classroom

async def get_classrooms(
    db: AsyncSession, 
    course_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Classroom]:
    """Get all classrooms with optional filtering"""
    query = select(Classroom).where(Classroom.is_active == True)
    
    if course_id:
        query = query.where(Classroom.course_id == course_id)
    if semester_id:
        query = query.where(Classroom.semester_id == semester_id)
    
    query = query.order_by(Classroom.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_classroom(db: AsyncSession, classroom_id: int) -> Optional[Classroom]:
    """Get a single classroom by ID"""
    result = await db.execute(
        select(Classroom)
        .options(selectinload(Classroom.groups))
        .where(Classroom.id == classroom_id, Classroom.is_active == True)
    )
    return result.scalar_one_or_none()

async def update_classroom(db: AsyncSession, classroom_id: int, classroom: ClassroomUpdate) -> Optional[Classroom]:
    """Update a classroom"""
    result = await db.execute(
        select(Classroom).where(Classroom.id == classroom_id)
    )
    db_classroom = result.scalar_one_or_none()
    
    if not db_classroom:
        return None
    
    # Update fields if provided
    update_data = classroom.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_classroom, key, value)
    
    db_classroom.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_classroom)
    return db_classroom

async def delete_classroom(db: AsyncSession, classroom_id: int) -> bool:
    """Soft delete a classroom"""
    result = await db.execute(
        select(Classroom).where(Classroom.id == classroom_id)
    )
    db_classroom = result.scalar_one_or_none()
    
    if not db_classroom:
        return False
    
    db_classroom.is_active = False
    db_classroom.updated_at = datetime.utcnow()
    await db.commit()
    return True

async def get_classroom_with_details(db: AsyncSession, classroom_id: int) -> Optional[Classroom]:
    """Get a classroom with course, semester, and groups"""
    result = await db.execute(
        select(Classroom)
        .options(
            selectinload(Classroom.course),
            selectinload(Classroom.semester),
            selectinload(Classroom.groups)
        )
        .where(Classroom.id == classroom_id, Classroom.is_active == True)
    )
    return result.scalar_one_or_none()
