"""
Users router for user management
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from .auth import User, get_current_user

router = APIRouter()


@router.get("/", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_user)):
    """Get all users (teachers only)"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Mock data - replace with database query
    return [
        User(id=1, username="teacher", email="teacher@example.com", 
             full_name="John Teacher", role="teacher", is_active=True),
        User(id=2, username="student", email="student@example.com", 
             full_name="Jane Student", role="student", is_active=True)
    ]


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int, current_user: User = Depends(get_current_user)):
    """Get user by ID"""
    # Mock data - replace with database query
    if user_id == current_user.id:
        return current_user
    
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Return mock user
    return User(id=user_id, username=f"user{user_id}", email=f"user{user_id}@example.com",
                full_name=f"User {user_id}", role="student", is_active=True)

