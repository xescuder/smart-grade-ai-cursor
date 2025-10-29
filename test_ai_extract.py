#!/usr/bin/env python3
"""
Test script to verify AI extract functionality with PDF data from database
"""

import asyncio
import tempfile
import os
from database import AsyncSessionLocal, Assignment
from sqlalchemy import select
from crud import get_assignment

async def test_ai_extract_logic():
    """Test the AI extract logic with assignment 17"""
    
    async with AsyncSessionLocal() as db:
        # Get assignment using the same function as the AI extract endpoint
        assignment: Assignment = await get_assignment(db, 17)
        
        if not assignment:
            print("❌ Assignment not found")
            return
        
        print(f"✅ Assignment found: {assignment.name}")
        
        # Check if PDF exists in either storage method (same logic as AI extract)
        pdf_file_data = getattr(assignment, "pdf_file_data", None)
        pdf_file_path = assignment.pdf_file_path
        
        print(f"📄 PDF file data present: {pdf_file_data is not None}")
        print(f"📄 PDF file data size: {len(pdf_file_data) if pdf_file_data else 0} bytes")
        print(f"📄 PDF file path: {pdf_file_path}")
        print(f"📄 PDF file name: {assignment.pdf_file_name}")
        
        if not pdf_file_data and not pdf_file_path:
            print("❌ No PDF file found for this assignment")
            return
        
        print("✅ PDF found!")
        
        # Test the temporary file creation logic
        temp_path = None
        if pdf_file_data:
            try:
                # Create temporary file from database bytes (same logic as AI extract)
                fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix=f"assignment_{assignment.id}_")
                with os.fdopen(fd, "wb") as tmp:
                    tmp.write(pdf_file_data)
                file_path = temp_path
                print(f"✅ Created temporary PDF file: {file_path}")
                print(f"📁 File size: {os.path.getsize(file_path)} bytes")
                
                # Verify the file is a valid PDF
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    if header == b'%PDF':
                        print("✅ File is a valid PDF")
                    else:
                        print(f"❌ File is not a valid PDF (header: {header})")
                
            except Exception as e:
                print(f"❌ Error creating temporary file: {e}")
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                return
        else:
            print("📁 Using filesystem path (not tested)")
        
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"🧹 Cleaned up temporary file: {temp_path}")
            except Exception as e:
                print(f"⚠️ Failed to clean up temporary file {temp_path}: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_extract_logic())
