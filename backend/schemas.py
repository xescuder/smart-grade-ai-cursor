"""
Domain models (Pydantic schemas) for Smart Grade AI
These represent the API request/response models and business domain entities
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date


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
    points: float
    comments: Optional[str] = None


# ===== ASSIGNMENT MODELS =====

class AssignmentBase(BaseModel):
    name: str
    due_date: Optional[datetime] = None
    language: Optional[str] = "en"  # Language code: en, es, ca, etc. Default to English


class AssignmentCreate(AssignmentBase):
    exercises: List[ExerciseCreate] = []
    course_id: Optional[int] = None
    semester_id: Optional[int] = None


class AssignmentUpdate(AssignmentBase):
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    pdf_file_data: Optional[bytes] = None
    pdf_mime_type: Optional[str] = None
    pdf_file_size: Optional[int] = None
    course_id: Optional[int] = None
    semester_id: Optional[int] = None


class AssignmentResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    due_date: Optional[datetime] = Field(default=None)
    language: Optional[str] = Field(default="en")
    course_id: Optional[int] = Field(default=None)
    semester_id: Optional[int] = Field(default=None)
    pdf_file_path: Optional[str] = Field(default=None)
    pdf_file_name: Optional[str] = Field(default=None)
    created_by: int
    created_at: datetime
    updated_at: datetime
    exercises: List[ExerciseResponse] = Field(default_factory=list)
    # Course can be CourseResponse or dict (to avoid lazy loading semesters)
    course: Optional[Dict[str, Any]] = Field(default=None)
    # Semester can be SemesterResponse or dict (with computed 'name' field for frontend)
    semester: Optional[Dict[str, Any]] = Field(default=None)


# ===== SECTION EXTRACTION CONFIG MODELS =====

class SectionExtractionConfigBase(BaseModel):
    name: str
    markers: str  # JSON string of array
    description: Optional[str] = None
    priority: int = 1
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
    nickname: Optional[str] = None  # Optional nickname like "Mandalorian"
    description: Optional[str] = None
    classroom_id: int  # Required field
    members: Optional[List[GroupMember]] = None


class GroupCreate(GroupBase):
    created_by: int


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None  # Optional nickname like "Mandalorian"
    description: Optional[str] = None
    classroom_id: Optional[int] = None
    course_id: Optional[int] = None
    semester_id: Optional[int] = None
    members: Optional[List[GroupMember]] = None


# ===== COURSE MODELS =====

class CourseBase(BaseModel):
    name: str
    code: str
    credits: Optional[int] = Field(None, ge=0, le=15, description="Course credits (0-15)")


class CourseCreate(CourseBase):
    created_by: int


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    credits: Optional[int] = Field(None, ge=0, le=15, description="Course credits (0-15)")


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
    year: int
    season: str
    course_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SemesterCreate(SemesterBase):
    created_by: int

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


class SemesterUpdate(BaseModel):
    year: Optional[int] = None
    season: Optional[str] = None
    course_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def empty_string_to_none_update(cls, v):
        if v == "" or v is None:
            return None
        return v


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
    semester_id: int


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    teacher_name: Optional[str] = None
    language: Optional[str] = None


class ClassroomResponse(ClassroomBase):
    id: int
    created_by: int
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
    meeting_notes: Optional[bool] = False
    # persisted presence flags
    has_submission_pdf: Optional[bool] = False
    has_private_pdf: Optional[bool] = False
    has_public_pdf: Optional[bool] = False
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
    meeting_notes: Optional[bool] = None
    has_submission_pdf: Optional[bool] = None
    has_private_pdf: Optional[bool] = None
    has_public_pdf: Optional[bool] = None
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
    private_report_evaluation: Optional[dict] = None
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
    private_report_evaluation: Optional[dict] = None
    submitted_at: datetime
    graded_at: Optional[datetime] = None
    graded_by: Optional[int] = None
    is_late: bool = False
    created_at: datetime
    updated_at: datetime
    
    # Derived attributes (computed from PDF data)
    has_submission_pdf_derived: Optional[bool] = None
    has_private_pdf_derived: Optional[bool] = None
    has_public_pdf_derived: Optional[bool] = None

    class Config:
        from_attributes = True

