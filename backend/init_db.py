#!/usr/bin/env python3
"""
Database initialization script
Creates tables and adds sample data
"""

import asyncio
from database import init_db, AsyncSessionLocal, Assignment, Exercise
from datetime import datetime, timedelta

async def create_sample_data():
    """Create sample assignment data"""
    async with AsyncSessionLocal() as db:
        # Create PAC1 assignment
        pac1_assignment = Assignment(
            name="PAC1",
            description="Desxrip",
            due_date=datetime(2026, 12, 20),
            created_by=1,
            is_active=True
        )
        
        db.add(pac1_assignment)
        await db.flush()  # Get the ID
        
        # Add exercises for PAC1
        exercise1 = Exercise(
            assignment_id=pac1_assignment.id,
            description="Primer exercisi",
            points=20,
            order=1
        )
        
        exercise2 = Exercise(
            assignment_id=pac1_assignment.id,
            description="Descripció del segon exercici",
            points=80,
            order=2
        )
        
        db.add(exercise1)
        db.add(exercise2)
        
        await db.commit()
        print("✅ Sample data created: PAC1 assignment with 2 exercises")

async def main():
    """Initialize database and create sample data"""
    print("🔄 Initializing PostgreSQL database...")
    
    # Create tables
    await init_db()
    print("✅ Database tables created")
    
    # Create sample data
    await create_sample_data()
    
    print("🎉 Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(main())
