"""
Assignment Repository
Handles all database operations related to assignments
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database import Assignment, Exercise
from logging_config import logger


class AssignmentRepository:
    """Repository for Assignment database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, assignment_id: int) -> Optional[Assignment]:
        """
        Get an assignment by ID with all related data loaded

        Args:
            assignment_id: The assignment ID

        Returns:
            Assignment object with exercises and classrooms loaded, or None if not found
        """
        result = await self.db.execute(
            select(Assignment)
            .options(selectinload(Assignment.exercises))
            .options(selectinload(Assignment.classrooms))
            .where(Assignment.id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Assignment]:
        """
        Get all assignments with related data

        Returns:
            List of all assignments
        """
        result = await self.db.execute(
            select(Assignment)
            .options(selectinload(Assignment.exercises))
            .options(selectinload(Assignment.classrooms))
        )
        return result.scalars().all()

    async def create(self, assignment: Assignment) -> Assignment:
        """
        Create a new assignment

        Args:
            assignment: Assignment object to create

        Returns:
            Created assignment with ID
        """
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment

    async def update(self, assignment: Assignment) -> Assignment:
        """
        Update an existing assignment

        Args:
            assignment: Assignment object to update

        Returns:
            Updated assignment
        """
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment

    async def delete(self, assignment: Assignment) -> None:
        """
        Delete an assignment

        Args:
            assignment: Assignment object to delete
        """
        await self.db.delete(assignment)
        await self.db.commit()

    async def replace_exercises(
        self,
        assignment_id: int,
        exercises_data: List[dict]
    ) -> List[Exercise]:
        """
        Replace all exercises for an assignment with new ones

        Args:
            assignment_id: The assignment ID
            exercises_data: List of dicts containing exercise data

        Returns:
            List of created Exercise objects
        """
        # Get assignment
        assignment = await self.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")

        # Delete existing exercises
        for exercise in assignment.exercises:
            await self.db.delete(exercise)
        await self.db.commit()

        # Create new exercises
        created_exercises = []
        for exercise_data in exercises_data:
            new_exercise = Exercise(
                assignment_id=assignment_id,
                description=exercise_data["description"],
                points=exercise_data["points"],
                order=exercise_data["order"],
                evaluation_criteria=exercise_data.get("evaluation_criteria", "")
            )
            self.db.add(new_exercise)
            created_exercises.append(new_exercise)

        await self.db.commit()

        # Refresh to get IDs
        for exercise in created_exercises:
            await self.db.refresh(exercise)

        logger.info(f"✅ Replaced exercises for assignment {assignment_id}: {len(created_exercises)} exercises created")

        return created_exercises

    async def get_pdf_data(self, assignment_id: int) -> Optional[bytes]:
        """
        Get PDF bytes data for an assignment

        Args:
            assignment_id: The assignment ID

        Returns:
            PDF file data as bytes, or None if not found
        """
        assignment = await self.get_by_id(assignment_id)
        if not assignment:
            return None

        return getattr(assignment, "pdf_file_data", None)
"""
Repository layer for database operations
"""
from .assignment_repository import AssignmentRepository

__all__ = ["AssignmentRepository"]
