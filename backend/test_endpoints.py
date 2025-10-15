#!/usr/bin/env python3
"""
Minimal test server to debug course/semester endpoints
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test Course/Semester Endpoints")

@app.get("/")
async def root():
    return {"message": "Test server is running"}

@app.get("/api/test-courses")
async def test_courses():
    return {"message": "Course test endpoint works!", "status": "success"}

@app.get("/api/courses")
async def get_courses():
    return {"message": "courses endpoint works", "courses": []}

@app.post("/api/courses")
async def create_course():
    return {"message": "course created", "id": 1}

@app.get("/api/semesters")
async def get_semesters():
    return {"message": "semesters endpoint works", "semesters": []}

@app.post("/api/semesters")
async def create_semester():
    return {"message": "semester created", "id": 1}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)

