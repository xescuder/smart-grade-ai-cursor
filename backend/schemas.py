"""
Domain models (Pydantic schemas) for Smart Grade AI
These represent the API request/response models and business domain entities
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ===== EXERCISE MODELS =====

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


class ExerciseGrade(BaseModel):
    exercise_id: int
    score: float
    feedback: Optional[str] = None


# ===== ASSIGNMENT MODELS =====

class AssignmentBase(BaseModel):
    name: str
    description: str
    due_date: datetime
    language: Optional[str] = "en"  # Language code: en, es, ca, etc. Default to English
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
    classroom_ids: List[int] = []  # Add classroom IDs to response
    exercises: List[ExerciseResponse] = []

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to extract classroom IDs from relationship"""
        data = {
            'id': obj.id,
            'name': obj.name,
            'description': obj.description,
            'due_date': obj.due_date,
            'language': obj.language,
            'is_active': obj.is_active,
            'pdf_file_path': obj.pdf_file_path,
            'pdf_file_name': obj.pdf_file_name,
            'created_by': obj.created_by,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
            'classroom_ids': [c.id for c in obj.classrooms] if hasattr(obj, 'classrooms') and obj.classrooms else []
        }
        return cls(**data)


# ===== SECTION EXTRACTION CONFIG MODELS =====

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


# ===== STUDENT AND GROUP MODELS =====

class GroupMember(BaseModel):
    """Legacy group member model - consider using Student instead"""
    name: str
    email_address: str
    student_id: str


# Temporarily commented out to debug email validation issue
# class Student(BaseModel):
#     """Pydantic model for a student in a group with email validation"""
#     name: str
#     email_address: str  # Email validation using str for now
#     login: str
#     group_id: Optional[int] = None  # Reference to group ID
#
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "name": "John Doe",
#                 "email_address": "john.doe@university.edu",
#                 "login": "jdoe",
#                 "group_id": 1
#             }
#         }


# Temporarily commented out to debug email validation issue
# class StudentInfo(BaseModel):
#     """Student information for submissions"""
#     name: str
#     email_address: str
#     student_id: str


# ===== GROUP MODELS =====

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    classroom_id: int  # Required field
    course_id: Optional[int] = None
    semester_id: Optional[int] = None
    members: Optional[List[GroupMember]] = None
    max_members: Optional[int] = None
    is_active: bool = True


class GroupCreate(GroupBase):
    created_by: int


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    classroom_id: Optional[int] = None
    course_id: Optional[int] = None
    semester_id: Optional[int] = None
    members: Optional[List[GroupMember]] = None
    max_members: Optional[int] = None
    is_active: Optional[bool] = None


# ===== COURSE MODELS =====

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
    semesters: List["SemesterResponse"] = []

    class Config:
        from_attributes = True


# ===== SEMESTER MODELS =====

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== CLASSROOM MODELS =====

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


# ===== SUBMISSION MODELS =====

class SubmissionFile(BaseModel):
    name: str
    path: str
    size: int
    content_type: str


class SubmissionBase(BaseModel):
    assignment_id: int
    classroom_id: int  # Required field
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


# ===== RESPONSE MODELS (defined after dependencies) =====

class GroupResponse(GroupBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    # Allow legacy rows where classroom_id may be NULL
    classroom_id: Optional[int] = None

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
    graded_by: Optional[int] = None
    is_late: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

