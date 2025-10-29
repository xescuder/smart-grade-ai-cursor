#!/usr/bin/env python3
"""
Test script for CSV group grades export
"""

import json
from datetime import datetime

def test_csv_generation():
    """Test CSV generation with sample data"""
    
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
                'description': 'Implement a Stack class',
                'points': 30,
                'evaluation_criteria': 'Correct implementation, error handling',
                'order': 1
            },
            {
                'id': 2,
                'description': 'Implement a Queue class',
                'points': 25,
                'evaluation_criteria': 'Correct implementation, time complexity',
                'order': 2
            },
            {
                'id': 3,
                'description': 'Implement a Binary Search Tree',
                'points': 45,
                'evaluation_criteria': 'Correct implementation, recursive approach',
                'order': 3
            }
        ]
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
            'teacher_feedback': 'Excellent work!',
            'ai_feedback': json.dumps({
                'public_report': {
                    'points': 8.0,
                    'comments': 'Informe ben estructurat amb explicacions detallades'
                },
                'private_report': {
                    'coordinators': [
                        {'name': 'Alice', 'points': 9.0, 'comments': 'Excel·lent coordinació i lideratge'}
                    ],
                    'members': [
                        {'name': 'Bob', 'points': 8.5, 'comments': 'Bon treball individual'}
                    ]
                }
            }),
            'grade_breakdown': [
                {'exercise_id': 1, 'points': 9.0, 'comments': 'Perfect implementation with error handling'},
                {'exercise_id': 2, 'points': 8.5, 'comments': 'Good implementation, minor edge case issues'},
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
            }
        },
        {
            'id': 2,
            'assignment_id': 1,
            'classroom_id': 1,
            'group_id': 2,
            'status': 'submitted',
            'total_score': 7.2,
            'max_score': 10.0,
            'percentage_score': 72.0,
            'teacher_feedback': 'Good work overall, needs improvement',
            'ai_feedback': json.dumps({
                'public_report': {
                    'points': 7.5,
                    'comments': 'Informe acceptable però manquen alguns detalls importants'
                }
            }),
            'grade_breakdown': [
                {'exercise_id': 1, 'points': 8.0, 'comments': 'Good implementation'},
                {'exercise_id': 2, 'points': 7.0, 'comments': 'Some issues with edge cases'},
                {'exercise_id': 3, 'points': 6.5, 'comments': 'Basic implementation, needs improvement'}
            ],
            'submitted_at': datetime(2024, 1, 15, 18, 45),
            'graded_at': None,
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
            }
        }
    ]
    
    # Simulate CSV generation logic
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Create headers
    headers = ['Group']
    
    # Add exercise score columns
    for i, exercise in enumerate(assignment['exercises'], 1):
        headers.append(f'Exercise {i} score')
    
    headers.extend([
        'Minutes (delivered)',
        'Public report score', 
        'Private report score',
        'Group comments',
        'Coordinator comments'
    ])
    
    writer.writerow(headers)
    
    # Process each submission
    for submission in submissions:
        row = []
        
        # Group name
        group_name = submission['group']['name']
        row.append(group_name)
        
        # Exercise scores
        grade_breakdown = submission['grade_breakdown']
        for exercise in assignment['exercises']:
            # Find grade for this exercise
            exercise_grade = next(
                (grade for grade in grade_breakdown if grade.get('exercise_id') == exercise['id']),
                None
            )
            
            if exercise_grade:
                score = exercise_grade.get('score', exercise_grade.get('points', 0))
            else:
                score = 0
            
            row.append(score)
        
        # Minutes delivered (Yes/No based on submission status)
        minutes_delivered = "Yes" if submission['status'] in ['graded', 'submitted'] else "No"
        row.append(minutes_delivered)
        
        # Public report score
        public_report_score = ""
        coordinator_comments = []
        
        ai_feedback = submission['ai_feedback']
        if ai_feedback:
            try:
                feedback_data = json.loads(ai_feedback)
                public_report = feedback_data.get('public_report', {})
                public_report_score = public_report.get('points', '')
                
                # Add public report comments to coordinator comments
                public_comments = public_report.get('comments', '')
                if public_comments:
                    coordinator_comments.append(f"Public report: {public_comments}")
                    
            except (json.JSONDecodeError, TypeError):
                pass
        
        row.append(public_report_score)
        
        # Private report score
        private_report_score = ""
        if ai_feedback:
            try:
                feedback_data = json.loads(ai_feedback)
                private_report = feedback_data.get('private_report', {})
                
                # Extract coordinator scores from private report
                coordinators = private_report.get('coordinators', [])
                if coordinators:
                    # Take average of coordinator scores
                    coord_scores = [float(coord.get('points', 0)) for coord in coordinators if coord.get('points')]
                    if coord_scores:
                        private_report_score = round(sum(coord_scores) / len(coord_scores), 2)
                
                # Add private report comments to coordinator comments
                for coord in coordinators:
                    coord_comments = coord.get('comments', '')
                    if coord_comments:
                        coordinator_comments.append(f"Private report ({coord.get('name', 'Coordinator')}): {coord_comments}")
                        
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        
        row.append(private_report_score)
        
        # Group comments (join all exercise comments)
        group_comments = []
        for i, exercise in enumerate(assignment['exercises'], 1):
            exercise_grade = next(
                (grade for grade in grade_breakdown if grade.get('exercise_id') == exercise['id']),
                None
            )
            
            if exercise_grade:
                comments = exercise_grade.get('feedback', exercise_grade.get('comments', ''))
                if comments:
                    group_comments.append(f"Exercise {i}: {comments}")
        
        group_comments_str = '\n'.join(group_comments)
        row.append(group_comments_str)
        
        # Coordinator comments (join public and private report comments)
        coordinator_comments_str = '\n'.join(coordinator_comments)
        row.append(coordinator_comments_str)
        
        writer.writerow(row)
    
    # Get CSV content
    csv_content = output.getvalue()
    output.close()
    
    # Save to file for inspection
    filename = f"test_group_grades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    print(f"✅ CSV file generated successfully: {filename}")
    print(f"📊 File size: {len(csv_content)} bytes")
    print(f"📋 Assignment: {assignment['name']}")
    print(f"👥 Groups: {len(submissions)}")
    print(f"📝 Exercises: {len(assignment['exercises'])}")
    print("\n📄 CSV Preview:")
    print(csv_content[:500] + "..." if len(csv_content) > 500 else csv_content)
    
    return filename

if __name__ == "__main__":
    test_csv_generation()
