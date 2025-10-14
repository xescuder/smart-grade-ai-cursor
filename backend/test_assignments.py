#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script for assignments API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_assignments_import():
    try:
        from api.routers.assignments import mock_assignments, router
        print("SUCCESS: Successfully imported assignments module")
        print(f"SUCCESS: Found {len(mock_assignments)} mock assignments")
        print("SUCCESS: Router created successfully")
        
        # Test the assignments data
        for i, assignment in enumerate(mock_assignments):
            print(f"Assignment {i+1}: {assignment.name} ({len(assignment.exercises)} exercises)")
            
        return True
    except Exception as e:
        print(f"ERROR: Failed to import assignments: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_import():
    try:
        from core.config import settings
        print("SUCCESS: Successfully imported settings")
        print(f"SUCCESS: CORS origins: {settings.ALLOWED_ORIGINS}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to import settings: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing backend modules...")
    
    config_ok = test_config_import()
    assignments_ok = test_assignments_import()
    
    if config_ok and assignments_ok:
        print("\nSUCCESS: All tests passed! Backend modules are working.")
    else:
        print("\nERROR: Some tests failed. Check the errors above.")
        sys.exit(1)
