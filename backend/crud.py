"""
CRUD operations for Smart Grade AI
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from database import Assignment, Exercise, SectionExtractionConfig, Submission, Group, Course, Semester, Classroom
from typing import List, Optional, Dict, Any
from datetime import datetime
from repositories.assignment_repository import AssignmentRepository

# Import all domain models from schemas
from schemas import (
    # Exercise models
    ExerciseBase, ExerciseCreate, ExerciseUpdate, ExerciseResponse, ExerciseGrade,
    # Assignment models
    AssignmentBase, AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    # Section config models
    SectionExtractionConfigBase, SectionExtractionConfigCreate,
    SectionExtractionConfigUpdate, SectionExtractionConfigResponse,
    # Group models
    GroupMember,
    GroupBase, GroupCreate, GroupUpdate, GroupResponse,
    # Course models
    CourseBase, CourseCreate, CourseUpdate, CourseResponse,
    # Semester models
    SemesterBase, SemesterCreate, SemesterUpdate, SemesterResponse,
    # Classroom models
    ClassroomBase, ClassroomCreate, ClassroomUpdate, ClassroomResponse,
    # Submission models
    SubmissionBase, SubmissionCreate, SubmissionUpdate, SubmissionResponse,
    SubmissionFile
)

# CRUD Operations for Assignments
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

# CRUD operations for submissions
async def get_submissions(db: AsyncSession, assignment_id: Optional[int] = None, classroom_id: Optional[int] = None, group_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Submission]:
    """Get all submissions with optional filtering"""
    query = select(Submission).options(
        selectinload(Submission.assignment).selectinload(Assignment.exercises),
        selectinload(Submission.classroom).selectinload(Classroom.course),
        selectinload(Submission.classroom).selectinload(Classroom.semester),
        selectinload(Submission.group)
    )
    
    if assignment_id:
        query = query.where(Submission.assignment_id == assignment_id)
    if classroom_id:
        query = query.where(Submission.classroom_id == classroom_id)
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
            selectinload(Submission.assignment).selectinload(Assignment.exercises),
            selectinload(Submission.classroom).selectinload(Classroom.course),
            selectinload(Submission.classroom).selectinload(Classroom.semester),
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
    
    # Get the classroom to inherit course_id and semester_id
    classroom_result = await db.execute(
        select(Classroom).where(Classroom.id == submission.classroom_id)
    )
    classroom = classroom_result.scalar_one_or_none()
    
    if not classroom:
        raise ValueError(f"Classroom with id {submission.classroom_id} not found")
    
    db_submission = Submission(
        assignment_id=submission.assignment_id,
        classroom_id=submission.classroom_id,
        course_id=classroom.course_id,  # Inherit from classroom
        semester_id=classroom.semester_id,  # Inherit from classroom
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

# CRUD operations for groups
async def get_groups(db: AsyncSession, created_by: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Group]:
    """Get all groups, optionally filtered by creator"""
    from sqlalchemy.orm import selectinload
    
    query = select(Group).where(Group.is_active == True)
    
    if created_by:
        query = query.where(Group.created_by == created_by)
    
    # Load related classroom data
    query = query.options(
        selectinload(Group.classroom)
    ).offset(skip).limit(limit).order_by(Group.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_group(db: AsyncSession, group_id: int) -> Optional[Group]:
    """Get a single group by ID"""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Group).options(
            selectinload(Group.classroom)
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
    
    # Get the classroom to inherit course_id and semester_id
    classroom = await db.get(Classroom, group.classroom_id)
    if not classroom:
        raise ValueError(f"Classroom with id {group.classroom_id} not found")
    
    # Convert Pydantic models to dict for JSON storage
    members_dict = []
    if group.members:
        members_dict = [member.model_dump() for member in group.members]
    
    db_group = Group(
        name=group.name,
        description=group.description,
        classroom_id=group.classroom_id,
        course_id=classroom.course_id,  # Inherit from classroom
        semester_id=classroom.semester_id,  # Inherit from classroom
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
        # Check if members are already dictionaries or Pydantic models
        if isinstance(update_data['members'][0], dict):
            # Already dictionaries, no need to convert
            pass
        else:
            # Pydantic models, convert to dictionaries
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
    
    # Load related classroom data
    query = query.options(
        selectinload(Group.classroom)
    ).order_by(Group.name)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_groups_by_classroom(db: AsyncSession, classroom_id: int, created_by: Optional[int] = None) -> List[Group]:
    """Get all groups for a specific classroom"""
    from sqlalchemy.orm import selectinload
    
    query = select(Group).where(Group.classroom_id == classroom_id, Group.is_active == True)
    
    if created_by:
        query = query.where(Group.created_by == created_by)
    
    # Load related classroom data
    query = query.options(
        selectinload(Group.classroom)
    ).order_by(Group.name)
    
    result = await db.execute(query)
    return result.scalars().all()

# === COURSE MODELS AND OPERATIONS ===

# CRUD operations for courses
async def get_courses(db: AsyncSession, created_by: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Course]:
    """Get all courses, optionally filtered by creator"""
    from sqlalchemy.orm import selectinload
    
    query = select(Course).where(Course.is_active == True)
    
    if created_by:
        query = query.where(Course.created_by == created_by)
    
    # Load semesters relationship
    query = query.options(selectinload(Course.semesters)).offset(skip).limit(limit).order_by(Course.name)
    
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
    """Get all courses with their active semesters"""
    # Use selectinload to eagerly load semesters relationship
    query = select(Course).options(selectinload(Course.semesters)).where(Course.is_active == True)
    
    if created_by:
        query = query.where(Course.created_by == created_by)
    
    query = query.offset(skip).limit(limit).order_by(Course.name)
    
    result = await db.execute(query)
    courses = result.scalars().all()
    
    # Filter semesters to only active ones for each course
    for course in courses:
        course.semesters = [semester for semester in course.semesters if semester.is_active]
        # Sort semesters by year desc, then season
        course.semesters.sort(key=lambda s: (s.year, s.season), reverse=True)
    
    return courses

async def get_course_with_semesters(db: AsyncSession, course_id: int) -> Optional[Course]:
    """Get a single course by ID with its active semesters"""
    result = await db.execute(
        select(Course).options(selectinload(Course.semesters)).where(Course.id == course_id, Course.is_active == True)
    )
    course = result.scalar_one_or_none()
    
    if course:
        # Filter semesters to only active ones
        course.semesters = [semester for semester in course.semesters if semester.is_active]
        # Sort semesters by year desc, then season
        course.semesters.sort(key=lambda s: (s.year, s.season), reverse=True)
    
    return course

# ===== Classroom Management =====

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

async def create_assignment(db: AsyncSession, assignment: AssignmentCreate, created_by: int = 1) -> Assignment:
    """Create a new assignment with exercises and associate with classrooms using AssignmentRepository"""
    db_assignment = Assignment(
        name=assignment.name,
        description=assignment.description,
        due_date=assignment.due_date,
        language=assignment.language,
        is_active=assignment.is_active,
        created_by=created_by
    )
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
            assignment=db_assignment,
            description=exercise_data.description,
            evaluation_criteria=exercise_data.evaluation_criteria,
            points=exercise_data.points,
            order=exercise_data.order
        )
        db_assignment.exercises.append(db_exercise)
    repo = AssignmentRepository(db)
    created_assignment = await repo.create(db_assignment)
    return created_assignment
