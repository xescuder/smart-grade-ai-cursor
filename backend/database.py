"""
Database configuration and models for Smart Grade AI
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, LargeBinary, create_engine, text, Table
from sqlalchemy.ext.declarative import declarative_base
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

# Association table for many-to-many relationship between assignments and classrooms
assignment_classroom_association = Table(
    'assignment_classroom',
    Base.metadata,
    Column('assignment_id', Integer, ForeignKey('assignments.id', ondelete='CASCADE'), primary_key=True),
    Column('classroom_id', Integer, ForeignKey('classrooms.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)

class Assignment(Base):
    """Assignment database model - can be assigned to multiple classrooms"""
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime, nullable=False)
    language = Column(String(50), nullable=False)  # Language of assignment (en, es, ca, etc.)
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
    classrooms = relationship("Classroom", secondary=assignment_classroom_association, back_populates="assignments")
    exercises = relationship("Exercise", back_populates="assignment", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")

class SectionExtractionConfig(Base):
    """Configuration for PDF section extraction"""
    __tablename__ = "section_extraction_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Descripció", "Què s'ha de lliurar"
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
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)  # Foreign key to course
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=True)  # Foreign key to semester
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)  # Foreign key to group
    
    # Submission content - simplified to just PDF and comments
    comments = Column(Text, nullable=True)  # Comments/description
    pdf_file_path = Column(String(500), nullable=True)  # Path to uploaded PDF file
    pdf_file_name = Column(String(255), nullable=True)  # Original PDF filename
    # Optional: store PDF bytes directly in DB
    pdf_file_data = Column(LargeBinary, nullable=True)
    pdf_mime_type = Column(String(100), nullable=True)
    pdf_file_size = Column(Integer, nullable=True)
    
    # Status and grading
    status = Column(String(50), nullable=False, default='submitted')  # submitted, graded, returned, late, draft
    total_score = Column(Float, nullable=True)  # Total points earned
    max_score = Column(Float, nullable=True)  # Total points possible (from assignment)
    percentage_score = Column(Float, nullable=True)  # Calculated percentage
    
    # Feedback
    teacher_feedback = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    grade_breakdown = Column(JSON, nullable=True)  # Detailed breakdown by exercise: [{"exercise_id": 1, "score": 20, "feedback": "Good work"}]
    
    # Metadata
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    graded_at = Column(DateTime, nullable=True)
    graded_by = Column(Integer, nullable=True)  # Teacher user ID
    is_late = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    course = relationship("Course")
    semester = relationship("Semester")
    group = relationship("Group")

class Classroom(Base):
    """Classroom database model - links courses and semesters with teacher and language"""
    __tablename__ = "classrooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "CS101 - Fall 2024 - Morning Section"
    teacher_name = Column(String(255), nullable=False)  # Teacher's full name
    language = Column(String(50), nullable=False)  # e.g., "en", "es", "ca", "English", "Spanish", "Catalan"
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)
    
    # Additional information
    description = Column(Text, nullable=True)
    
    # Metadata
    created_by = Column(Integer, nullable=False)  # Teacher user ID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course")
    semester = relationship("Semester")
    groups = relationship("Group", back_populates="classroom", cascade="all, delete-orphan")
    assignments = relationship("Assignment", secondary=assignment_classroom_association, back_populates="classrooms")

class Group(Base):
    """Group database model for student groups"""
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)  # Foreign key to classroom
    
    # Legacy fields for backward compatibility (can be removed later)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)  # Deprecated - use classroom.course_id
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=True)  # Deprecated - use classroom.semester_id
    
    # Group members - JSON array of student info
    members = Column(JSON, nullable=False)  # [{"name": "John", "email": "john@example.com", "student_id": "12345"}]
    
    # Metadata
    created_by = Column(Integer, nullable=False)  # Teacher user ID
    is_active = Column(Boolean, default=True)
    max_members = Column(Integer, nullable=True)  # Optional limit on group size
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    classroom = relationship("Classroom", back_populates="groups")
    course = relationship("Course")  # Legacy
    semester = relationship("Semester")  # Legacy

class Course(Base):
    """Course database model"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Computer Science 101"
    code = Column(String(50), nullable=False, unique=True)  # e.g., "CS101"
    description = Column(Text, nullable=True)
    department = Column(String(255), nullable=True)  # e.g., "Computer Science"
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
    name = Column(String(100), nullable=False)  # e.g., "Fall 2024"
    code = Column(String(20), nullable=False, unique=True)  # e.g., "F24"
    year = Column(Integer, nullable=False)  # e.g., 2024
    season = Column(String(20), nullable=False)  # e.g., "Fall", "Spring", "Summer"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)  # Link to course
    
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
                ADD COLUMN IF NOT EXISTS pdf_file_size integer;
            """
        ))
        await conn.execute(text(
            """
            ALTER TABLE submissions
                ADD COLUMN IF NOT EXISTS pdf_file_data bytea,
                ADD COLUMN IF NOT EXISTS pdf_mime_type varchar(100),
                ADD COLUMN IF NOT EXISTS pdf_file_size integer;
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
        # Create assignment-classroom association table (many-to-many)
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS assignment_classroom (
                assignment_id INTEGER REFERENCES assignments(id) ON DELETE CASCADE,
                classroom_id INTEGER REFERENCES classrooms(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (assignment_id, classroom_id)
            );
            """
        ))
        # Drop old classroom_id column from assignments if it exists (may have data, so be careful)
        # We'll keep it for now for backward compatibility and manual migration
        # await conn.execute(text("ALTER TABLE assignments DROP COLUMN IF EXISTS classroom_id;"))

async def close_db():
    """Close database connections"""
    await async_engine.dispose()
