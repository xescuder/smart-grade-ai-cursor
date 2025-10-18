#!/usr/bin/env python3
"""
Database initialization script
Creates tables and adds sample data
"""

import asyncio
from database import init_db, AsyncSessionLocal, Assignment, Exercise, Course, Semester, Classroom
from datetime import datetime, timedelta

async def create_sample_data():
    """Create sample data including courses, semesters, classrooms, assignments, and exercises"""
    async with AsyncSessionLocal() as db:
        # Create sample courses
        course1 = Course(
            name="Programació Web",
            code="PW",
            description="Curs de programació web amb HTML, CSS i JavaScript",
            department="Informàtica",
            credits=6,
            created_by=1,
            is_active=True
        )
        
        course2 = Course(
            name="Desenvolupament d'Aplicacions",
            code="DA",
            description="Curs de desenvolupament d'aplicacions mòbils i web",
            department="Informàtica",
            credits=6,
            created_by=1,
            is_active=True
        )
        
        db.add(course1)
        db.add(course2)
        await db.flush()  # Get the IDs
        
        # Create sample semesters
        semester1 = Semester(
            name="Tardor 2025",
            code="T2025",
            year=2025,
            season="Fall",
            start_date=datetime(2025, 9, 1),
            end_date=datetime(2025, 12, 20),
            course_id=course1.id,
            created_by=1,
            is_active=True
        )
        
        semester2 = Semester(
            name="Primavera 2026",
            code="P2026",
            year=2026,
            season="Spring",
            start_date=datetime(2026, 2, 1),
            end_date=datetime(2026, 6, 15),
            course_id=course2.id,
            created_by=1,
            is_active=True
        )
        
        db.add(semester1)
        db.add(semester2)
        await db.flush()  # Get the IDs
        
        # Create sample classrooms
        classroom1 = Classroom(
            name="Tardor 2025 - Aula català",
            teacher_name="Xavier Escudero",
            language="ca",
            course_id=course1.id,
            semester_id=semester1.id,
            description="Aula de programació web en català",
            created_by=1,
            is_active=True
        )
        
        classroom2 = Classroom(
            name="Primavera 2026 - Aula castellà",
            teacher_name="María García",
            language="es",
            course_id=course2.id,
            semester_id=semester2.id,
            description="Aula de desenvolupament d'aplicacions en castellà",
            created_by=1,
            is_active=True
        )
        
        db.add(classroom1)
        db.add(classroom2)
        await db.flush()  # Get the IDs
        
        # Create PAC1 assignment
        pac1_assignment = Assignment(
            name="PAC1",
            description="Primera Pràctica d'Avaluació Continuada",
            due_date=datetime(2026, 12, 20),
            language="ca",
            created_by=1,
            is_active=True
        )
        
        db.add(pac1_assignment)
        await db.flush()  # Get the ID
        
        # Add exercises for PAC1
        exercise1 = Exercise(
            assignment_id=pac1_assignment.id,
            description="Primer exercisi",
            points=20,
            order=1
        )
        
        exercise2 = Exercise(
            assignment_id=pac1_assignment.id,
            description="Descripció del segon exercici",
            points=80,
            order=2
        )
        
        db.add(exercise1)
        db.add(exercise2)
        
        await db.commit()
        print("✅ Sample data created:")
        print(f"   - 2 courses: {course1.name}, {course2.name}")
        print(f"   - 2 semesters: {semester1.name}, {semester2.name}")
        print(f"   - 2 classrooms: {classroom1.name}, {classroom2.name}")
        print(f"   - 1 assignment: {pac1_assignment.name} with 2 exercises")

async def main():
    """Initialize database and create sample data"""
    print("🔄 Initializing PostgreSQL database...")
    
    # Create tables
    await init_db()
    print("✅ Database tables created")
    
    # Create sample data
    await create_sample_data()
    
    print("🎉 Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(main())
