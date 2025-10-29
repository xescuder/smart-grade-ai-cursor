#!/usr/bin/env python3
"""
Test script to verify Coordinator score calculation
"""

import json

def test_coordinator_calculation():
    """Test the coordinator score calculation with your example"""
    
    # Your example: Private Report 7.5, Public Report 6.5
    ai_feedback = {
        "public_report": {
            "points": 6.5,
            "comments": "Good public report"
        },
        "private_report": {
            "points": 7.5,
            "comments": "Excellent private report"
        }
    }
    
    # Convert to JSON string (as stored in database)
    ai_feedback_str = json.dumps(ai_feedback)
    
    # Calculate coordinator score using the same logic as Excel service
    try:
        feedback_data = json.loads(ai_feedback_str)
        
        # Get original scores (0-10 scale) directly from AI feedback
        public_report = feedback_data.get('public_report', {})
        public_score = public_report.get('points', 0)
        
        private_report = feedback_data.get('private_report', {})
        private_score = private_report.get('points', 0)
        
        print(f"Public Report Score: {public_score}")
        print(f"Private Report Score: {private_score}")
        
        # Calculate average and normalize from 0-10 to 0-1 scale
        if public_score > 0 or private_score > 0:
            average_score = (public_score + private_score) / 2
            normalized_score = average_score / 10  # Normalize from 0-10 to 0-1 scale
            coordinator_score = round(normalized_score, 2)
            
            print(f"Average Score: {average_score}")
            print(f"Normalized Score: {normalized_score}")
            print(f"Final Coordinator Score: {coordinator_score}")
            
            # Expected calculation
            expected_average = (7.5 + 6.5) / 2
            expected_normalized = expected_average / 10
            print(f"\nExpected Average: {expected_average}")
            print(f"Expected Normalized: {expected_normalized}")
            print(f"Expected Coordinator Score: {round(expected_normalized, 2)}")
            
            if coordinator_score == round(expected_normalized, 2):
                print("✅ Calculation is CORRECT!")
            else:
                print("❌ Calculation is INCORRECT!")
                
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_coordinator_calculation()
