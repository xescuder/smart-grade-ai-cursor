#!/usr/bin/env python3
"""
Test script for Excel grade summary generation
"""

import json
from datetime import datetime
from services.excel_grade_service import ExcelGradeService

def test_excel_generation():
    """Test Excel generation with sample data"""
    
    # Sample assignment data
    assignment = {
        'id': 1,
        'name': 'Test Assignment - Data Structures',
        'description': 'Implementation of basic data structures in Python',
        'due_date': datetime(2024, 1, 15, 23, 59),
        'language': 'catalan',
        'exercises': [
            {
                'id': 1,
                'description': 'Implement a Stack class with push, pop, and peek methods',
                'points': 30,
                'evaluation_criteria': 'Correct implementation, error handling, documentation',
                'order': 1
            },
            {
                'id': 2,
                'description': 'Implement a Queue class with enqueue and dequeue methods',
                'points': 25,
                'evaluation_criteria': 'Correct implementation, time complexity analysis',
                'order': 2
            },
            {
                'id': 3,
                'description': 'Implement a Binary Search Tree with insert and search methods',
                'points': 45,
                'evaluation_criteria': 'Correct implementation, recursive approach, test cases',
                'order': 3
            }
        ]
    }
    
    # Sample classroom data
    classroom = {
        'id': 1,
        'name': 'CS101 - Data Structures',
        'teacher_name': 'Dr. Smith',
        'language': 'catalan'
    }
    
    # Sample submissions data
    submissions = [
        {
            'id': 1,
            'assignment_id': 1,
            'classroom_id': 1,
            'group_id': 1,
            'status': 'graded',
            'total_score': 8.5,
            'max_score': 10.0,
            'percentage_score': 85.0,
            'teacher_feedback': 'Excellent work! All implementations are correct and well-documented.',
            'ai_feedback': json.dumps({
                'public_report': {
                    'points': 8.0,
                    'comments': 'Informe ben estructurat amb explicacions detallades'
                },
                'private_report': {
                    'coordinators': [{'name': 'Alice', 'points': 9.0, 'comments': 'Excel·lent coordinació'}],
                    'members': [{'name': 'Bob', 'points': 8.5, 'comments': 'Bon treball individual'}]
                }
            }),
            'grade_breakdown': [
                {'exercise_id': 1, 'points': 9.0, 'comments': 'Perfect implementation'},
                {'exercise_id': 2, 'points': 8.5, 'comments': 'Good implementation, minor issues'},
                {'exercise_id': 3, 'points': 8.0, 'comments': 'Correct but could be more efficient'}
            ],
            'submitted_at': datetime(2024, 1, 14, 20, 30),
            'graded_at': datetime(2024, 1, 16, 10, 15),
            'coordinators': json.dumps(['Alice Johnson']),
            'public_pdf_responsible_students': json.dumps(['Alice Johnson', 'Bob Smith']),
            'private_pdf_data': b'fake_pdf_data',
            'public_pdf_data': b'fake_pdf_data',
            'group': {
                'id': 1,
                'name': 'Team Alpha',
                'description': 'Advanced programming team',
                'members': [
                    {'name': 'Alice Johnson', 'email': 'alice@university.edu'},
                    {'name': 'Bob Smith', 'email': 'bob@university.edu'},
                    {'name': 'Charlie Brown', 'email': 'charlie@university.edu'}
                ]
            },
            'classroom': classroom
        },
        {
            'id': 2,
            'assignment_id': 1,
            'classroom_id': 1,
            'group_id': 2,
            'status': 'graded',
            'total_score': 7.2,
            'max_score': 10.0,
            'percentage_score': 72.0,
            'teacher_feedback': 'Good work overall, but some implementations need improvement.',
            'ai_feedback': json.dumps({
                'public_report': {
                    'points': 7.5,
                    'comments': 'Informe acceptable però manquen alguns detalls'
                }
            }),
            'grade_breakdown': [
                {'exercise_id': 1, 'points': 8.0, 'comments': 'Good implementation'},
                {'exercise_id': 2, 'points': 7.0, 'comments': 'Some issues with edge cases'},
                {'exercise_id': 3, 'points': 6.5, 'comments': 'Basic implementation, needs improvement'}
            ],
            'submitted_at': datetime(2024, 1, 15, 18, 45),
            'graded_at': datetime(2024, 1, 16, 14, 20),
            'coordinators': json.dumps(['David Wilson']),
            'public_pdf_responsible_students': json.dumps(['David Wilson']),
            'private_pdf_data': None,
            'public_pdf_data': b'fake_pdf_data',
            'group': {
                'id': 2,
                'name': 'Team Beta',
                'description': 'Intermediate programming team',
                'members': [
                    {'name': 'David Wilson', 'email': 'david@university.edu'},
                    {'name': 'Eva Garcia', 'email': 'eva@university.edu'}
                ]
            },
            'classroom': classroom
        }
    ]
    
    # Generate Excel file
    excel_service = ExcelGradeService()
    excel_bytes = excel_service.generate_assignment_grade_summary(
        assignment, 
        submissions, 
        classroom
    )
    
    # Save to file for inspection
    filename = f"test_grades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    with open(filename, 'wb') as f:
        f.write(excel_bytes)
    
    print(f"✅ Excel file generated successfully: {filename}")
    print(f"📊 File size: {len(excel_bytes)} bytes")
    print(f"📋 Assignment: {assignment['name']}")
    print(f"👥 Groups: {len(submissions)}")
    print(f"📝 Exercises: {len(assignment['exercises'])}")
    
    return filename

if __name__ == "__main__":
    test_excel_generation()
