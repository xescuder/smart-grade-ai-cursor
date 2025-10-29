#!/usr/bin/env python3
"""
Debug script to examine actual AI feedback data from database
"""

import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import get_db

async def debug_ai_feedback():
    """Debug the actual AI feedback data"""
    async for db in get_db():
        try:
            # Get submissions with AI feedback
            result = await db.execute(
                text("SELECT id, group_id, ai_feedback FROM submissions WHERE ai_feedback IS NOT NULL AND ai_feedback != '' LIMIT 5")
            )
            submissions = result.fetchall()
            
            print(f"Found {len(submissions)} submissions with AI feedback:")
            
            for submission in submissions:
                submission_id, group_id, ai_feedback = submission
                print(f"\n--- Submission {submission_id} (Group {group_id}) ---")
                
                try:
                    feedback_data = json.loads(ai_feedback)
                    
                    print(f"Full AI feedback structure:")
                    print(json.dumps(feedback_data, indent=2))
                    
                    # Check public report
                    public_report = feedback_data.get('public_report', {})
                    public_score = public_report.get('points', 'N/A')
                    print(f"Public Report Score: {public_score} (type: {type(public_score)})")
                    
                    # Check private report
                    private_report = feedback_data.get('private_report', {})
                    private_score = private_report.get('points', 'N/A')
                    print(f"Private Report Score: {private_score} (type: {type(private_score)})")
                    
                    # Calculate what the coordinator score should be
                    if isinstance(public_score, (int, float)) and isinstance(private_score, (int, float)):
                        average = (public_score + private_score) / 2
                        normalized = average / 10
                        print(f"Expected Coordinator Score: {round(normalized, 2)}")
                    else:
                        print("Cannot calculate - scores are not numeric")
                        
                except json.JSONDecodeError as e:
                    print(f"JSON Error: {e}")
                    print(f"Raw AI feedback: {ai_feedback[:200]}...")
                    
        except Exception as e:
            print(f"Database error: {e}")
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(debug_ai_feedback())
