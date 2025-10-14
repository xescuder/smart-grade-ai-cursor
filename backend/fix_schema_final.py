#!/usr/bin/env python3
"""
Final database schema fix for submissions table
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://smartgrade:@localhost:5432/smartgrade_db")

async def fix_schema():
    """Fix submissions table schema completely"""
    
    # Parse the DATABASE_URL to get connection details
    if "postgresql+asyncpg://" in DATABASE_URL:
        clean_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    else:
        clean_url = DATABASE_URL
    
    print(f"Connecting to database: {clean_url}")
    
    try:
        conn = await asyncpg.connect(clean_url)
        print("Connected to database successfully")
        
        # First, let's see what columns exist in the submissions table
        print("\n=== Current submissions table structure ===")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'submissions' 
            ORDER BY ordinal_position
        """)
        
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Check for old columns that need to be removed
        old_columns = ['group_name', 'group_members', 'description', 'submission_files']
        existing_old_columns = []
        
        for col in columns:
            if col['column_name'] in old_columns:
                existing_old_columns.append(col['column_name'])
        
        if existing_old_columns:
            print(f"\n=== Found old columns to remove: {existing_old_columns} ===")
            
            # Drop the old columns
            for col_name in existing_old_columns:
                try:
                    print(f"Dropping column: {col_name}")
                    await conn.execute(f"ALTER TABLE submissions DROP COLUMN IF EXISTS {col_name}")
                    print(f"  ✓ Successfully dropped column: {col_name}")
                except Exception as e:
                    print(f"  ✗ Error dropping column {col_name}: {e}")
        else:
            print("\n=== No old columns found - schema is clean ===")
        
        # Verify the final structure
        print("\n=== Final submissions table structure ===")
        final_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'submissions' 
            ORDER BY ordinal_position
        """)
        
        for col in final_columns:
            print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        print("\n=== Schema fix completed successfully! ===")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            await conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    asyncio.run(fix_schema())

