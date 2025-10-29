"""
Database configuration and models for Smart Grade AI
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, LargeBinary, create_engine, text, Table, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime
import os

# Import settings for centralized configuration
from core.config import settings

# Create async engine with configuration from settings
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW
)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

# Base class for models
Base = declarative_base()

# Removed assignment_classroom_association table - assignments no longer linked to classrooms

class Assignment(Base):
    """Assignment database model - assignments belong to specific course-semester combinations"""
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime, nullable=False)
    language = Column(String(50), nullable=False)  # Language of assignment (en, es, ca, etc.)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)  # Course assignment belongs to (nullable for backward compatibility)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=True)  # Semester assignment belongs to (nullable for backward compatibility)
    pdf_file_path = Column(String(500), nullable=True)
    pdf_file_name = Column(String(255), nullable=True)
    # Optional: store PDF bytes directly in DB
    pdf_file_data = Column(LargeBinary, nullable=True)
    pdf_mime_type = Column(String(100), nullable=True)
    pdf_file_size = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=False)  # User ID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course")
    semester = relationship("Semester")
    exercises = relationship("Exercise", back_populates="assignment", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")

class SectionExtractionConfig(Base):
    """Configuration for PDF section extraction"""
    __tablename__ = "section_extraction_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Description", "What to deliver"
    markers = Column(Text, nullable=False)  # JSON array of search terms
    description = Column(Text)  # Human readable description
    priority = Column(Integer, default=1)  # Lower number = higher priority
    is_active = Column(Boolean, default=True)
    extraction_strategy = Column(String(50), default='section_to_end')  # 'section_to_end', 'section_limited', 'full_document'
    max_characters = Column(Integer, default=4000)  # Max chars to extract from this section
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Exercise(Base):
    """Exercise database model"""
    __tablename__ = "exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    description = Column(Text)
    evaluation_criteria = Column(Text, nullable=True)  # New field for evaluation criteria
    points = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to assignment
    assignment = relationship("Assignment", back_populates="exercises")

class Submission(Base):
    """Submission database model for student group submissions"""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)  # Foreign key to classroom
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)  # Foreign key to group
    
    # Legacy fields for backward compatibility (can be removed later)
    course_id = Column(Integer, nullable=True)  # Deprecated - use classroom.course_id
    semester_id = Column(Integer, nullable=True)  # Deprecated - use classroom.semester_id
    
    # Submission content - simplified to just PDF and comments
    comments = Column(Text, nullable=True)  # Comments/description
    meeting_notes = Column(Boolean, nullable=False, default=False)  # Meeting notes checkbox
    pdf_file_path = Column(String(500), nullable=True)  # Path to uploaded PDF file
    pdf_file_name = Column(String(255), nullable=True)  # Original PDF filename
    # Optional: store PDF bytes directly in DB
    pdf_file_data = Column(LargeBinary, nullable=True)
    pdf_mime_type = Column(String(100), nullable=True)
    pdf_file_size = Column(Integer, nullable=True)
    
    # Additional PDF files
    private_pdf_data = Column(LargeBinary, nullable=True)  # Private PDF file
    private_pdf_mime_type = Column(String(100), nullable=True)
    private_pdf_size = Column(Integer, nullable=True)
    private_pdf_filename = Column(String(255), nullable=True)
    private_pdf_uploaded_at = Column(DateTime, nullable=True)
    coordinators = Column(Text, nullable=True)  # JSON array of coordinator names
    
    public_pdf_data = Column(LargeBinary, nullable=True)  # Public PDF file
    public_pdf_mime_type = Column(String(100), nullable=True)
    public_pdf_size = Column(Integer, nullable=True)
    public_pdf_filename = Column(String(255), nullable=True)
    public_pdf_uploaded_at = Column(DateTime, nullable=True)
    public_pdf_responsible_students = Column(Text, nullable=True)  # JSON array of coordinator names
    
    # Presence flags (persisted and editable)
    has_submission_pdf = Column(Boolean, nullable=False, default=False)
    has_private_pdf = Column(Boolean, nullable=False, default=False)
    has_public_pdf = Column(Boolean, nullable=False, default=False)
    
    # Hybrid properties for derived attributes
    @hybrid_property
    def has_submission_pdf_derived(self):
        """Derived attribute: True if pdf_file_data exists and is not empty"""
        return bool(self.pdf_file_data and len(self.pdf_file_data) > 0)
    
    @has_submission_pdf_derived.expression
    def has_submission_pdf_derived(cls):
        """SQL expression for the derived attribute"""
        return cls.pdf_file_data.isnot(None) & (cls.pdf_file_data != b'')
    
    @hybrid_property
    def has_private_pdf_derived(self):
        """Derived attribute: True if private_pdf_data exists and is not empty"""
        return bool(self.private_pdf_data and len(self.private_pdf_data) > 0)
    
    @has_private_pdf_derived.expression
    def has_private_pdf_derived(cls):
        """SQL expression for the derived attribute"""
        return cls.private_pdf_data.isnot(None) & (cls.private_pdf_data != b'')
    
    @hybrid_property
    def has_public_pdf_derived(self):
        """Derived attribute: True if public_pdf_data exists and is not empty"""
        return bool(self.public_pdf_data and len(self.public_pdf_data) > 0)
    
    @has_public_pdf_derived.expression
    def has_public_pdf_derived(cls):
        """SQL expression for the derived attribute"""
        return cls.public_pdf_data.isnot(None) & (cls.public_pdf_data != b'')
    
    # Status and grading
    status = Column(String(50), nullable=False, default='submitted')  # submitted, graded, returned, late, draft
    total_score = Column(Float, nullable=True)  # Total points earned
    max_score = Column(Float, nullable=True)  # Total points possible (from assignment)
    percentage_score = Column(Float, nullable=True)  # Calculated percentage
    
    # Feedback
    teacher_feedback = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    grade_breakdown = Column(JSON, nullable=True)  # Detailed breakdown by exercise: [{"exercise_id": 1, "points": 20, "comments": "Good work"}]
    private_report_evaluation = Column(JSON, nullable=True)  # Private report evaluation results
    
    # Metadata
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    graded_at = Column(DateTime, nullable=True)
    graded_by = Column(Integer, nullable=True)  # Teacher user ID
    is_late = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    classroom = relationship("Classroom")
    group = relationship("Group")

class Classroom(Base):
    """Classroom database model - links courses and semesters with teacher and language"""
    __tablename__ = "classrooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "CS101 - Fall 2024 - Morning Section"
    teacher_name = Column(String(255), nullable=False)  # Teacher's full name
    language = Column(String(50), nullable=False)  # e.g., "en", "es", "ca", "English", "Spanish", "Catalan"
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)
    
    # Metadata
    created_by = Column(Integer, nullable=False)  # Teacher user ID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    semester = relationship("Semester")
    groups = relationship("Group", back_populates="classroom", cascade="all, delete-orphan")

class Group(Base):
    """Group database model for student groups"""
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=True)  # Optional nickname like "Mandalorian"
    description = Column(Text, nullable=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)  # Foreign key to classroom
    
    # Group members - JSON array of student info
    members = Column(JSON, nullable=False)  # [{"name": "John", "email": "john@example.com", "student_id": "12345"}]
    
    # Metadata
    created_by = Column(Integer, nullable=False)  # Teacher user ID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    classroom = relationship("Classroom", back_populates="groups")

class Course(Base):
    """Course database model"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Computer Science 101"
    code = Column(String(50), nullable=False, unique=True)  # e.g., "CS101"
    credits = Column(Integer, nullable=True)  # Course credits
    
    # Metadata
    created_by = Column(Integer, nullable=False)  # Teacher user ID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    semesters = relationship("Semester", back_populates="course", cascade="all, delete-orphan")

class Semester(Base):
    """Semester database model"""
    __tablename__ = "semesters"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)  # e.g., 2024
    season = Column(String(20), nullable=False)  # e.g., "Fall", "Spring", "Summer"
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)  # Link to course
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Metadata
    created_by = Column(Integer, nullable=False)  # Teacher user ID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course", back_populates="semesters")

class AiSetting(Base):
    """Key-value store for AI configuration (system prompts, etc.)."""
    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Ensure new columns exist (idempotent)
        await conn.execute(text(
            """
            ALTER TABLE assignments
                ADD COLUMN IF NOT EXISTS pdf_file_data bytea,
                ADD COLUMN IF NOT EXISTS pdf_mime_type varchar(100),
                ADD COLUMN IF NOT EXISTS pdf_file_size integer,
                ADD COLUMN IF NOT EXISTS course_id integer,
                ADD COLUMN IF NOT EXISTS semester_id integer,
                ADD COLUMN IF NOT EXISTS description text,
                ADD COLUMN IF NOT EXISTS due_date timestamp,
                ADD COLUMN IF NOT EXISTS pdf_file_path varchar(500),
                ADD COLUMN IF NOT EXISTS pdf_file_name varchar(255);
            """
        ))
        # Add start_date and end_date to semesters if not exists
        await conn.execute(text(
            """
            ALTER TABLE semesters
                ADD COLUMN IF NOT EXISTS start_date date,
                ADD COLUMN IF NOT EXISTS end_date date;
            """
        ))
        # Add foreign key constraints if they don't exist
        await conn.execute(text(
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'assignments_course_id_fkey'
                ) THEN
                    ALTER TABLE assignments 
                    ADD CONSTRAINT assignments_course_id_fkey 
                    FOREIGN KEY (course_id) REFERENCES courses(id);
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'assignments_semester_id_fkey'
                ) THEN
                    ALTER TABLE assignments 
                    ADD CONSTRAINT assignments_semester_id_fkey 
                    FOREIGN KEY (semester_id) REFERENCES semesters(id);
                END IF;
            END $$;
            """
        ))
        await conn.execute(text(
            """
            ALTER TABLE submissions
                ADD COLUMN IF NOT EXISTS pdf_file_data bytea,
                ADD COLUMN IF NOT EXISTS pdf_mime_type varchar(100),
                ADD COLUMN IF NOT EXISTS pdf_file_size integer,
                ADD COLUMN IF NOT EXISTS meeting_notes boolean DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS private_pdf_data bytea,
                ADD COLUMN IF NOT EXISTS private_pdf_mime_type varchar(100),
                ADD COLUMN IF NOT EXISTS private_pdf_size integer,
                ADD COLUMN IF NOT EXISTS private_pdf_filename varchar(255),
                ADD COLUMN IF NOT EXISTS private_pdf_uploaded_at timestamp,
                ADD COLUMN IF NOT EXISTS coordinators text,
                ADD COLUMN IF NOT EXISTS public_pdf_data bytea,
                ADD COLUMN IF NOT EXISTS public_pdf_mime_type varchar(100),
                ADD COLUMN IF NOT EXISTS public_pdf_size integer,
                ADD COLUMN IF NOT EXISTS public_pdf_filename varchar(255),
                ADD COLUMN IF NOT EXISTS public_pdf_uploaded_at timestamp,
                ADD COLUMN IF NOT EXISTS public_pdf_responsible_students text,
                ADD COLUMN IF NOT EXISTS has_submission_pdf boolean DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS has_private_pdf boolean DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS has_public_pdf boolean DEFAULT FALSE;
            """
        ))
        # Create ai_settings table if not exists
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS ai_settings (
                id SERIAL PRIMARY KEY,
                key VARCHAR(100) UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
        ))
        # Create classrooms table and update groups table
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS classrooms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                teacher_name VARCHAR(255) NOT NULL,
                language VARCHAR(50) NOT NULL,
                course_id INTEGER REFERENCES courses(id),
                semester_id INTEGER REFERENCES semesters(id),
                description TEXT,
                created_by INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
        ))
        # Add classroom_id to groups table if not exists
        await conn.execute(text(
            """
            ALTER TABLE groups
                ADD COLUMN IF NOT EXISTS classroom_id INTEGER REFERENCES classrooms(id);
            """
        ))
        # Add language to assignments table if not exists
        await conn.execute(text(
            """
            ALTER TABLE assignments
                ADD COLUMN IF NOT EXISTS language VARCHAR(50) DEFAULT 'en';
            """
        ))
        # Drop assignment_classroom association table if it exists (no longer needed)
        await conn.execute(text("DROP TABLE IF EXISTS assignment_classroom;"))
        # Drop old classroom_id column from assignments if it exists (no longer needed)
        await conn.execute(text("ALTER TABLE assignments DROP COLUMN IF EXISTS classroom_id;"))

async def close_db():
    """Close database connections"""
    await async_engine.dispose()
