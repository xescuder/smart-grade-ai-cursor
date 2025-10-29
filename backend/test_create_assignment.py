#!/usr/bin/env python3
"""
Test script to reproduce the POST /api/assignments/ error
"""
import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.insert(0, '/Users/escuderx/Projects/personal/smart-grade-ai-cursor/backend')

from database import AsyncSessionLocal
from crud import create_assignment, AssignmentCreate
from logging_config import logger

async def test_create_assignment():
    """Test creating an assignment"""
    async with AsyncSessionLocal() as db:
        try:
            # Create assignment data
            assignment_data = AssignmentCreate(
                name="Test Assignment",
                description="Test Description",
                due_date=datetime.now(),
                language="en",
                is_active=True,
                classroom_ids=[],
                exercises=[]
            )

            logger.info(f"Creating assignment with data: {assignment_data.model_dump()}")

            # Try to create
            result = await create_assignment(db, assignment_data, created_by=1)

            logger.success(f"✅ Assignment created successfully: ID={result.id}")
            return result

        except Exception as e:
            logger.error(f"❌ Error creating assignment: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

if __name__ == "__main__":
    asyncio.run(test_create_assignment())

