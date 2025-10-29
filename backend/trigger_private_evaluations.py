#!/usr/bin/env python3
"""
Script to trigger private report evaluation for submissions that are missing it
"""

import asyncio
import json
import requests
from sqlalchemy import text
from database import get_db

async def trigger_private_report_evaluations():
    """Trigger private report evaluation for submissions that need it"""
    async for db in get_db():
        try:
            # Get submissions that have private PDFs but no private report evaluation
            result = await db.execute(
                text('''
                    SELECT s.id, s.group_id, s.has_private_pdf, s.private_pdf_filename,
                           g.name as group_name, s.ai_feedback
                    FROM submissions s
                    LEFT JOIN groups g ON s.group_id = g.id
                    WHERE s.has_private_pdf = true 
                    AND (g.name LIKE '%GRUP 1%' OR s.group_id = 26 OR s.group_id = 27)
                    ORDER BY s.id DESC
                ''')
            )
            submissions = result.fetchall()
            
            print(f'Triggering private report evaluation for {len(submissions)} submissions...')
            
            for submission in submissions:
                sub_id, group_id, has_private, private_filename, group_name, ai_feedback = submission
                print(f'\n--- Processing Submission {sub_id} (Group: {group_name}, ID: {group_id}) ---')
                
                # Check if private report evaluation already exists
                if ai_feedback:
                    try:
                        feedback_data = json.loads(ai_feedback)
                        has_private_eval = 'private_report' in feedback_data
                        if has_private_eval:
                            print(f'✅ SKIP: Private report evaluation already exists')
                            continue
                    except json.JSONDecodeError:
                        pass
                
                print(f'🔄 TRIGGERING: Private report evaluation for submission {sub_id}')
                
                # Call the API endpoint
                try:
                    response = requests.post(
                        f'http://localhost:8000/api/v1/submissions/{sub_id}/ai-evaluate-private-report',
                        timeout=60  # Give it time to process
                    )
                    
                    if response.status_code == 200:
                        result_data = response.json()
                        print(f'✅ SUCCESS: Private report evaluation completed')
                        print(f'Result: {json.dumps(result_data, indent=2)}')
                    else:
                        print(f'❌ ERROR: API call failed with status {response.status_code}')
                        print(f'Response: {response.text}')
                        
                except requests.exceptions.RequestException as e:
                    print(f'❌ ERROR: Request failed: {e}')
                except Exception as e:
                    print(f'❌ ERROR: Unexpected error: {e}')
                    
        except Exception as e:
            print(f'Database error: {e}')
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(trigger_private_report_evaluations())
