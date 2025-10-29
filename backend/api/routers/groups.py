"""
Group management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import tempfile
import os

from database import get_db
from crud import (
    get_groups,
    get_group,
    create_group,
    update_group,
    delete_group,
    get_groups_by_classroom,
    GroupCreate,
    GroupUpdate,
    GroupResponse,
)
from services.groups_importer import import_students_csv_with_mapping

router = APIRouter()

# Error messages
GROUP_NOT_FOUND = "Group not found"


@router.get("/", response_model=List[dict])
async def list_groups(
    created_by: Optional[int] = Query(None),
    classroom_id: Optional[int] = Query(None),
    course_id: Optional[int] = Query(None),
    semester_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get groups with optional filters.

    Note: Filtering by classroom_id/course_id/semester_id is applied in-memory for now
    to avoid adding multiple DB functions. This is acceptable for small datasets and
    can be optimized later if needed.
    """
    groups = await get_groups(db, created_by, skip, limit)

    if classroom_id is not None:
        groups = [g for g in groups if getattr(g, "classroom_id", None) == classroom_id]
    if course_id is not None:
        groups = [g for g in groups if getattr(g, "course_id", None) == course_id]
    if semester_id is not None:
        groups = [g for g in groups if getattr(g, "semester_id", None) == semester_id]

    # Convert to dict and add relationship data
    result = []
    for group in groups:
        group_dict = {
            "id": group.id,
            "name": group.name,
            "nickname": group.nickname,
            "description": group.description,
            "classroom_id": group.classroom_id,
            "course_id": group.course_id,
            "semester_id": group.semester_id,
            "members": group.members,
            "is_active": group.is_active,
            "created_by": group.created_by,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            # Add classroom relationship data
            "classroom": {
                "id": group.classroom.id,
                "name": group.classroom.name,
                "teacher_name": group.classroom.teacher_name,
                "language": group.classroom.language
            } if group.classroom else None
        }
        result.append(group_dict)

    return result


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group_by_id(
    group_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific group by ID"""
    group = await get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail=GROUP_NOT_FOUND)
    return group


@router.post("/", response_model=GroupResponse)
async def create_new_group(
    group: GroupCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new group"""
    db_group = await create_group(db, group)
    return db_group


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group_by_id(
    group_id: int,
    group: GroupUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a group"""
    db_group = await get_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail=GROUP_NOT_FOUND)
    updated = await update_group(db, group_id, group)
    return updated


@router.delete("/{group_id}")
async def delete_group_by_id(
    group_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a group"""
    group = await get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail=GROUP_NOT_FOUND)
    await delete_group(db, group_id)
    return {"message": "Group deleted successfully"}


@router.post("/import-csv/{classroom_id}")
async def import_groups_from_csv(
    classroom_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Import groups and students from a CSV file for a specific classroom"""
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    # Create temporary file to store uploaded content
    content = await file.read()
    temp_file_path = tempfile.mktemp(suffix='.csv')
    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(content)
    
    try:
        # Import students from CSV using the groups importer
        students_data = import_students_csv_with_mapping(temp_file_path)
        
        if not students_data:
            raise HTTPException(status_code=400, detail="No valid student data found in CSV file")
        
        # Remove existing groups for this classroom before importing new ones
        existing_groups = await get_groups_by_classroom(db, classroom_id)
        for group in existing_groups:
            await delete_group(db, group.id)
        
        # Group students by group name
        groups_dict = {}
        for student in students_data:
            group_name = student.get('group', '')
            if group_name not in groups_dict:
                groups_dict[group_name] = []
            groups_dict[group_name].append(student)
        
        created_groups = []
        
        # Create groups and add students
        for group_name, students in groups_dict.items():
            if not group_name.strip():
                continue
                
            # Convert students to the expected format
            group_members = []
            for student in students:
                group_members.append({
                    "name": student.get('name', ''),
                    "email": student.get('email', ''),
                    "student_id": student.get('login', '')
                })
            
            # Create group data
            group_data = GroupCreate(
                name=group_name,
                description=f"Imported from CSV - {len(students)} students",
                classroom_id=classroom_id,
                members=group_members,
                created_by=1  # Default user ID
            )
            
            # Create the group
            created_group = await create_group(db, group_data)
            created_groups.append(created_group)
        
        return {
            "message": f"Successfully imported {len(created_groups)} groups with {len(students_data)} students",
            "groups_created": len(created_groups),
            "students_imported": len(students_data),
            "groups": created_groups
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing CSV: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


