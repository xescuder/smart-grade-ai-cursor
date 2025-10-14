#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crud import update_submission
from database import get_db
from pydantic import BaseModel
from typing import List, Optional

class SubmissionUpdate(BaseModel):
    total_score: Optional[float] = None
    teacher_feedback: Optional[str] = None
    graded_by: Optional[int] = None
    status: Optional[str] = None
    grade_breakdown: Optional[List[dict]] = None

async def test_grading():
    """Test the grading functionality"""
    print("Testing grading functionality...")
    
    # Get database session
    async for db in get_db():
        try:
            # Test data
            grade_update = SubmissionUpdate(
                total_score=95.0,
                teacher_feedback="Test feedback",
                graded_by=1,
                status="graded",
                grade_breakdown=[{"exercise_id": 240, "points": 8.5, "comments": "Good work"}]
            )
            
            print(f"Testing with grade_update: {grade_update}")
            
            # Try to update submission
            submission = await update_submission(db, 12, grade_update)
            
            if submission:
                print(f"✅ Success! Updated submission: {submission.id}")
                print(f"   Total score: {submission.total_score}")
                print(f"   Grade breakdown: {submission.grade_breakdown}")
            else:
                print("❌ Failed: submission not found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
        finally:
            break

if __name__ == "__main__":
    asyncio.run(test_grading())

