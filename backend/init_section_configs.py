#!/usr/bin/env python3
"""
Initialize default section extraction configurations
"""

import asyncio
import json
from database import get_db, init_db, SectionExtractionConfig
from crud import create_section_extraction_config, SectionExtractionConfigCreate

async def create_default_section_configs():
    """Create default section extraction configurations"""
    
    # Initialize database
    await init_db()
    
    # Get database session
    async for db in get_db():
        print("🔧 Creating default section extraction configurations...")
        
        # Default configurations
        configs = [
            {
                "name": "Què s'ha de lliurar",
                "markers": json.dumps([
                    "què s'ha de lliurar",
                    "que s'ha de lliurar", 
                    "qué s'ha de lliurar",
                    "deliverables",
                    "entregables"
                ]),
                "description": "Main deliverables section - what students need to submit",
                "priority": 1,
                "extraction_strategy": "section_to_end",
                "max_characters": 6000
            },
            {
                "name": "Descripció",
                "markers": json.dumps([
                    "descripció",
                    "descripcion", 
                    "description",
                    "descripció de la pac",
                    "descripcio de la pac",
                    "pac 1 consisteix",
                    "consisteix en"
                ]),
                "description": "Assignment description section with exercise details",
                "priority": 2,
                "extraction_strategy": "section_limited",
                "max_characters": 8000
            },
            {
                "name": "General Exercise Markers",
                "markers": json.dumps([
                    "exercici",
                    "ejercicio",
                    "exercise",
                    "activitat",
                    "actividades",
                    "activities",
                    "tasca",
                    "tarea",
                    "task"
                ]),
                "description": "General exercise and activity markers",
                "priority": 3,
                "extraction_strategy": "section_limited",
                "max_characters": 4000
            },
            {
                "name": "Assignment Structure",
                "markers": json.dumps([
                    "pac consisteix",
                    "assignació consisteix",
                    "consta de",
                    "exercicis:",
                    "ejercicios:",
                    "práctica",
                    "pràctica",
                    "practice"
                ]),
                "description": "Assignment structure and organization markers",
                "priority": 4,
                "extraction_strategy": "section_limited",
                "max_characters": 3000
            }
        ]
        
        for config_data in configs:
            try:
                config = SectionExtractionConfigCreate(**config_data)
                created_config = await create_section_extraction_config(db, config)
                print(f"✅ Created: {created_config.name} (ID: {created_config.id})")
            except Exception as e:
                print(f"❌ Failed to create {config_data['name']}: {e}")
        
        print(f"✅ Section extraction configurations initialized!")
        break

async def main():
    """Main function"""
    try:
        await create_default_section_configs()
        print("🎉 Default section extraction configurations created successfully!")
    except Exception as e:
        print(f"❌ Error initializing section configurations: {e}")

if __name__ == "__main__":
    asyncio.run(main())

