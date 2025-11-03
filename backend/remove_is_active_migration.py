"""
Migration script to remove is_active columns from all tables.
Run this script to drop the is_active columns from the database.

Usage:
    python remove_is_active_migration.py
"""

import asyncio
from sqlalchemy import text
from database import async_engine


async def remove_is_active_columns():
    """Remove is_active columns from all tables"""
    async with async_engine.begin() as conn:
        tables_to_update = [
            "assignments",
            "section_extraction_configs",
            "groups",
            "courses",
            "semesters",
            "classrooms"
        ]
        
        for table in tables_to_update:
            try:
                # Drop the is_active column if it exists
                await conn.execute(text(
                    f"""
                    ALTER TABLE {table} 
                    DROP COLUMN IF EXISTS is_active;
                    """
                ))
                print(f"✓ Removed is_active column from {table}")
            except Exception as e:
                print(f"✗ Error removing is_active from {table}: {e}")
        
        print("\n✓ Migration complete!")


if __name__ == "__main__":
    print("Removing is_active columns from all tables...")
    asyncio.run(remove_is_active_columns())

