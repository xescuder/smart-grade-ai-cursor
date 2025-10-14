#!/usr/bin/env python3
"""
Migration script to update Group table to use foreign key relationships
with Course and Semester tables instead of string fields.
"""

import asyncio
import asyncpg
from datetime import datetime

# Database connection parameters
DB_URL = "postgresql://smartgrade:@localhost:5432/smartgrade_db"

async def migrate_group_relationships():
    """Migrate Group table to use course_id and semester_id foreign keys"""
    
    print("Starting Group relationships migration...")
    
    # Connect to database
    conn = await asyncpg.connect(DB_URL)
    
    try:
        async with conn.transaction():
            # Step 1: Add new foreign key columns (nullable initially)
            print("Adding course_id and semester_id columns...")
            await conn.execute("""
                ALTER TABLE groups 
                ADD COLUMN course_id INTEGER REFERENCES courses(id),
                ADD COLUMN semester_id INTEGER REFERENCES semesters(id)
            """)
            
            # Step 2: Try to match existing course names to course IDs
            print("Mapping existing course names to course IDs...")
            
            # Get all unique course names from groups
            group_courses = await conn.fetch("""
                SELECT DISTINCT course 
                FROM groups 
                WHERE course IS NOT NULL AND course != ''
            """)
            
            course_mappings = {}
            for row in group_courses:
                course_name = row['course']
                
                # Try to find matching course by name
                matching_course = await conn.fetchrow("""
                    SELECT id FROM courses 
                    WHERE name ILIKE $1 OR code ILIKE $1
                    LIMIT 1
                """, f"%{course_name}%")
                
                if matching_course:
                    course_mappings[course_name] = matching_course['id']
                    print(f"Mapped course '{course_name}' to ID {matching_course['id']}")
                else:
                    print(f"Warning: No matching course found for '{course_name}'")
            
            # Step 3: Try to match existing semester names to semester IDs
            print("Mapping existing semester names to semester IDs...")
            
            # Get all unique semester names from groups
            group_semesters = await conn.fetch("""
                SELECT DISTINCT semester 
                FROM groups 
                WHERE semester IS NOT NULL AND semester != ''
            """)
            
            semester_mappings = {}
            for row in group_semesters:
                semester_name = row['semester']
                
                # Try to find matching semester by name or code
                matching_semester = await conn.fetchrow("""
                    SELECT id FROM semesters 
                    WHERE name ILIKE $1 OR code ILIKE $1
                    LIMIT 1
                """, f"%{semester_name}%")
                
                if matching_semester:
                    semester_mappings[semester_name] = matching_semester['id']
                    print(f"Mapped semester '{semester_name}' to ID {matching_semester['id']}")
                else:
                    print(f"Warning: No matching semester found for '{semester_name}'")
            
            # Step 4: Update groups with mapped IDs
            print("Updating groups with foreign key relationships...")
            
            updated_count = 0
            for course_name, course_id in course_mappings.items():
                result = await conn.execute("""
                    UPDATE groups 
                    SET course_id = $1 
                    WHERE course = $2
                """, course_id, course_name)
                updated_count += int(result.split()[-1])
            
            for semester_name, semester_id in semester_mappings.items():
                result = await conn.execute("""
                    UPDATE groups 
                    SET semester_id = $1 
                    WHERE semester = $2
                """, semester_id, semester_name)
                updated_count += int(result.split()[-1])
            
            print(f"Updated {updated_count} group records with foreign key relationships")
            
            # Step 5: Drop the old string columns
            print("Dropping old course and semester string columns...")
            await conn.execute("""
                ALTER TABLE groups 
                DROP COLUMN IF EXISTS course,
                DROP COLUMN IF EXISTS semester
            """)
            
            print("Migration completed successfully!")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        await conn.close()

async def main():
    """Main function"""
    try:
        await migrate_group_relationships()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

