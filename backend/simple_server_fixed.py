#!/usr/bin/env python3
"""
Simple FastAPI server for testing - Fixed version
"""

from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import uuid

app = FastAPI(title="Smart Grade AI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
mock_assignments = [
    {
        "id": 1,
        "name": "Climate Change Essay Assignment",
        "description": "Write a comprehensive essay on climate change impacts and solutions",
        "instructions": "Your essay should demonstrate understanding of scientific concepts and propose realistic solutions...",
        "due_date": "2024-12-01T23:59:59",
        "exercises": [
            {"id": 1, "name": "Introduction", "description": "Write a compelling introduction with thesis statement", "points": 15, "order": 1},
            {"id": 2, "name": "Problem Analysis", "description": "Analyze current climate change impacts", "points": 25, "order": 2},
            {"id": 3, "name": "Scientific Evidence", "description": "Present scientific evidence and data", "points": 25, "order": 3},
            {"id": 4, "name": "Solutions Proposal", "description": "Propose realistic solutions and interventions", "points": 20, "order": 4},
            {"id": 5, "name": "Conclusion", "description": "Summarize key points and call to action", "points": 15, "order": 5}
        ],
        "pdf_file_path": "/uploads/climate-essay-instructions.pdf",
        "pdf_file_name": "climate-essay-instructions.pdf",
        "created_by": 1,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    },
    {
        "id": 2,
        "name": "Mathematics Problem Set",
        "description": "Solve various calculus problems demonstrating integration techniques",
        "instructions": "Show all work and provide clear explanations for each solution step...",
        "due_date": "2024-11-20T23:59:59",
        "exercises": [
            {"id": 6, "name": "Basic Integration", "description": "Solve 5 basic integration problems", "points": 20, "order": 1},
            {"id": 7, "name": "Integration by Parts", "description": "Apply integration by parts technique", "points": 30, "order": 2},
            {"id": 8, "name": "Substitution Method", "description": "Use substitution for complex integrals", "points": 30, "order": 3},
            {"id": 9, "name": "Applied Problems", "description": "Solve real-world application problems", "points": 20, "order": 4}
        ],
        "pdf_file_path": None,
        "pdf_file_name": None,
        "created_by": 1,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
]

@app.get("/")
def root():
    return {"message": "Smart Grade AI API", "status": "active"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/assignments")
def get_assignments():
    return mock_assignments

@app.get("/api/assignments/{assignment_id}")
def get_assignment(assignment_id):
    assignment = next((a for a in mock_assignments if a["id"] == int(assignment_id)), None)
    if not assignment:
        return {"error": "Assignment not found"}
    return assignment

@app.post("/api/assignments")
async def create_assignment(request: Request):
    assignment_data = await request.json()
    new_id = len(mock_assignments) + 1
    
    # Generate exercise IDs
    next_exercise_id = max([ex["id"] for a in mock_assignments for ex in a["exercises"]], default=0) + 1
    for i, exercise in enumerate(assignment_data.get("exercises", [])):
        if "id" not in exercise:
            exercise["id"] = next_exercise_id + i
    
    new_assignment = {
        "id": new_id,
        "name": assignment_data["name"],
        "description": assignment_data["description"],
        "instructions": assignment_data["instructions"],
        "due_date": assignment_data["due_date"],
        "exercises": assignment_data.get("exercises", []),
        "pdf_file_path": None,
        "pdf_file_name": None,
        "created_by": 1,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
    
    mock_assignments.append(new_assignment)
    return new_assignment

@app.put("/api/assignments/{assignment_id}")
async def update_assignment(assignment_id, request: Request):
    assignment_data = await request.json()
    assignment = next((a for a in mock_assignments if a["id"] == int(assignment_id)), None)
    if not assignment:
        return {"error": "Assignment not found"}
    
    # Update assignment fields
    for key, value in assignment_data.items():
        if key in assignment:
            assignment[key] = value
    
    return assignment

@app.delete("/api/assignments/{assignment_id}")
def delete_assignment(assignment_id):
    global mock_assignments
    assignment = next((a for a in mock_assignments if a["id"] == int(assignment_id)), None)
    if not assignment:
        return {"error": "Assignment not found"}
    
    mock_assignments = [a for a in mock_assignments if a["id"] != assignment_id]
    return {"success": True, "message": "Assignment deleted"}

@app.get("/api/assignments/{assignment_id}/exercises")
def get_assignment_exercises(assignment_id):
    assignment = next((a for a in mock_assignments if a["id"] == int(assignment_id)), None)
    if not assignment:
        return {"error": "Assignment not found"}
    
    return sorted(assignment["exercises"], key=lambda x: x["order"])

@app.put("/api/assignments/{assignment_id}/exercises")
async def update_assignment_exercises(assignment_id, request: Request):
    exercises_data = await request.json()
    assignment = next((a for a in mock_assignments if a["id"] == int(assignment_id)), None)
    if not assignment:
        return {"error": "Assignment not found"}
    
    # Validate total points
    total = sum(ex.get("points", 0) for ex in exercises_data)
    if total != 100:
        return {"error": f"Total points must equal 100, got {total}"}
    
    # Generate IDs for new exercises
    next_exercise_id = max([ex["id"] for a in mock_assignments for ex in a["exercises"] if "id" in ex], default=0) + 1
    for i, exercise in enumerate(exercises_data):
        if "id" not in exercise:
            exercise["id"] = next_exercise_id + i
    
    assignment["exercises"] = exercises_data
    return sorted(assignment["exercises"], key=lambda x: x["order"])

@app.post("/api/assignments/{assignment_id}/upload-pdf")
async def upload_assignment_pdf(assignment_id, file: UploadFile = File(...)):
    # Find assignment
    assignment = next((a for a in mock_assignments if a["id"] == int(assignment_id)), None)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Validate file size (max 10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = ".pdf"
    unique_filename = f"assignment_{assignment_id}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update assignment with PDF info
    assignment["pdf_file_path"] = f"/{file_path}"
    assignment["pdf_file_name"] = file.filename
    
    return {
        "success": True,
        "message": "PDF uploaded successfully",
        "file_name": file.filename,
        "file_path": assignment["pdf_file_path"]
    }

@app.delete("/api/assignments/{assignment_id}/pdf")
def delete_assignment_pdf(assignment_id):
    assignment = next((a for a in mock_assignments if a["id"] == int(assignment_id)), None)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if not assignment.get("pdf_file_path"):
        raise HTTPException(status_code=404, detail="No PDF file found for this assignment")
    
    # Remove PDF info from assignment
    assignment["pdf_file_path"] = None
    assignment["pdf_file_name"] = None
    
    return {"success": True, "message": "PDF deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
