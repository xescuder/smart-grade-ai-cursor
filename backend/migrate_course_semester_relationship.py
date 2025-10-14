#!/usr/bin/env python3
"""
Migration script to add course-semester relationship
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from database import DATABASE_URL

async def migrate_course_semester_relationship():
    """Add course_id column to semesters table and establish relationships"""
    
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if course_id column already exists
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'semesters' AND column_name = 'course_id'
            """))
            
            if result.fetchone():
                print("✅ course_id column already exists in semesters table")
            else:
                print("🔄 Adding course_id column to semesters table...")
                
                # Add course_id column (nullable initially)
                await session.execute(text("""
                    ALTER TABLE semesters 
                    ADD COLUMN course_id INTEGER
                """))
                
                # Add foreign key constraint
                await session.execute(text("""
                    ALTER TABLE semesters 
                    ADD CONSTRAINT fk_semesters_course_id 
                    FOREIGN KEY (course_id) REFERENCES courses(id)
                """))
                
                print("✅ Added course_id column and foreign key constraint")
            
            # Check if we have any existing semesters
            result = await session.execute(text("SELECT COUNT(*) FROM semesters"))
            semester_count = result.scalar()
            
            if semester_count > 0:
                print(f"🔄 Found {semester_count} existing semesters")
                
                # Check if we have any existing courses
                result = await session.execute(text("SELECT COUNT(*) FROM courses"))
                course_count = result.scalar()
                
                if course_count > 0:
                    # Get the first course to assign to existing semesters
                    result = await session.execute(text("SELECT id FROM courses LIMIT 1"))
                    first_course_id = result.scalar()
                    
                    print(f"🔄 Assigning existing semesters to course ID {first_course_id}")
                    
                    # Update existing semesters to reference the first course
                    await session.execute(text("""
                        UPDATE semesters 
                        SET course_id = :course_id 
                        WHERE course_id IS NULL
                    """), {"course_id": first_course_id})
                    
                    print("✅ Updated existing semesters with course reference")
                else:
                    print("⚠️  No courses found. Existing semesters will have NULL course_id")
            
            # Make course_id NOT NULL after updating existing data
            print("🔄 Making course_id NOT NULL...")
            await session.execute(text("""
                ALTER TABLE semesters 
                ALTER COLUMN course_id SET NOT NULL
            """))
            
            await session.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Migration failed: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate_course_semester_relationship())

