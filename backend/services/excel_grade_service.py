"""
Excel Grade Summary Service

This service generates comprehensive Excel grade summaries for assignments,
including exercise breakdowns, group information, and detailed analytics.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
import io


class ExcelGradeService:
    """Service for generating Excel grade summaries"""
    
    def __init__(self):
        self.workbook = None
        self.worksheet = None
        
    def generate_assignment_grade_summary(
        self, 
        assignment: Dict[str, Any], 
        submissions: List[Dict[str, Any]],
        classroom: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generate a comprehensive Excel grade summary for an assignment
        
        Args:
            assignment: Assignment data with exercises
            submissions: List of submission data with grades
            classroom: Optional classroom information
            
        Returns:
            Excel file as bytes
        """
        # Create workbook and worksheets
        self.workbook = Workbook()
        
        # First tab: Group grades summary
        self.worksheet = self.workbook.active
        self.worksheet.title = f"Group Grades - {assignment.get('name', 'Assignment')}"
        
        # Generate the group summary
        self._create_header_section(assignment, classroom)
        self._create_exercise_summary_section(assignment)
        self._create_group_grades_section(assignment, submissions)
        self._create_statistics_section(submissions)
        self._create_public_report_section(submissions)
        self._create_private_report_section(submissions)
        
        # Auto-adjust column widths for first tab
        self._auto_adjust_columns()
        
        # Second tab: Student details
        self._create_student_details_tab(assignment, submissions)
        
        # Save to bytes
        excel_buffer = io.BytesIO()
        self.workbook.save(excel_buffer)
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
    
    def _create_header_section(self, assignment: Dict[str, Any], classroom: Optional[Dict[str, Any]]):
        """Create assignment and classroom information header"""
        row = 1
        
        # Assignment title
        self.worksheet[f'A{row}'] = "ASSIGNMENT GRADE SUMMARY"
        self.worksheet[f'A{row}'].font = Font(size=16, bold=True)
        self.worksheet[f'A{row}'].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        self.worksheet[f'A{row}'].font = Font(size=16, bold=True, color="FFFFFF")
        self.worksheet.merge_cells(f'A{row}:F{row}')
        row += 2
        
        # Assignment details
        self.worksheet[f'A{row}'] = "Assignment:"
        self.worksheet[f'B{row}'] = assignment.get('name', 'N/A')
        self.worksheet[f'A{row}'].font = Font(bold=True)
        row += 1
        
        self.worksheet[f'A{row}'] = "Description:"
        self.worksheet[f'B{row}'] = assignment.get('description', 'N/A')
        self.worksheet[f'A{row}'].font = Font(bold=True)
        row += 1
        
        self.worksheet[f'A{row}'] = "Due Date:"
        due_date = assignment.get('due_date')
        if due_date:
            if isinstance(due_date, str):
                self.worksheet[f'B{row}'] = due_date
            else:
                self.worksheet[f'B{row}'] = due_date.strftime('%Y-%m-%d %H:%M')
        else:
            self.worksheet[f'B{row}'] = 'N/A'
        self.worksheet[f'A{row}'].font = Font(bold=True)
        row += 1
        
        # Classroom details if available
        if classroom:
            self.worksheet[f'A{row}'] = "Classroom:"
            self.worksheet[f'B{row}'] = classroom.get('name', 'N/A')
            self.worksheet[f'A{row}'].font = Font(bold=True)
            row += 1
            
            self.worksheet[f'A{row}'] = "Teacher:"
            self.worksheet[f'B{row}'] = classroom.get('teacher_name', 'N/A')
            self.worksheet[f'A{row}'].font = Font(bold=True)
            row += 1
            
            self.worksheet[f'A{row}'] = "Language:"
            self.worksheet[f'B{row}'] = classroom.get('language', 'N/A')
            self.worksheet[f'A{row}'].font = Font(bold=True)
            row += 1
        
        # Generated timestamp
        self.worksheet[f'A{row}'] = "Generated:"
        self.worksheet[f'B{row}'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.worksheet[f'A{row}'].font = Font(bold=True)
        row += 3
    
    def _create_exercise_summary_section(self, assignment: Dict[str, Any]):
        """Create exercise summary section"""
        exercises = assignment.get('exercises', [])
        if not exercises:
            return
            
        row = self._get_next_row()
        
        # Section header
        self.worksheet[f'A{row}'] = "EXERCISE SUMMARY"
        self.worksheet[f'A{row}'].font = Font(size=14, bold=True)
        self.worksheet[f'A{row}'].fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        self.worksheet.merge_cells(f'A{row}:E{row}')
        row += 2
        
        # Exercise headers
        headers = ['Exercise', 'Description', 'Weight', 'Criteria']
        for col, header in enumerate(headers, 1):
            cell = self.worksheet.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        row += 1
        
        # Exercise data
        for i, exercise in enumerate(exercises, 1):
            self.worksheet[f'A{row}'] = f"Exercise {i}"
            self.worksheet[f'B{row}'] = exercise.get('description', 'N/A')
            
            # Extract weight from points field (assuming it's stored as percentage)
            weight = exercise.get('points', 0)
            if isinstance(weight, (int, float)):
                self.worksheet[f'C{row}'] = f"{weight}%"
            else:
                self.worksheet[f'C{row}'] = str(weight)
            
            criteria = exercise.get('evaluation_criteria', 'N/A')
            self.worksheet[f'D{row}'] = criteria
            
            row += 1
        
        row += 2
        self._set_next_row(row)
    
    def _create_group_grades_section(self, assignment: Dict[str, Any], submissions: List[Dict[str, Any]]):
        """Create detailed group grades section"""
        exercises = assignment.get('exercises', [])
        if not exercises or not submissions:
            return
            
        row = self._get_next_row()
        
        # Section header
        self.worksheet[f'A{row}'] = "GROUP GRADES"
        self.worksheet[f'A{row}'].font = Font(size=14, bold=True)
        self.worksheet[f'A{row}'].fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        
        # Calculate columns needed
        num_exercises = len(exercises)
        total_cols = 2 + (num_exercises * 2) + 3  # Group + (Points + Comments) * exercises + Total + Percentage + Status
        self.worksheet.merge_cells(f'A{row}:{get_column_letter(total_cols)}{row}')
        row += 2
        
        # Create headers
        headers = ['Group Name']
        
        # Exercise headers
        for exercise in exercises:
            headers.extend([f"Ex{exercise.get('order', exercises.index(exercise) + 1)} Points", f"Ex{exercise.get('order', exercises.index(exercise) + 1)} Comments"])
        
        headers.extend(['Total Score', 'Percentage', 'Status', 'Teacher Feedback'])
        
        # Write headers
        for col, header in enumerate(headers, 1):
            cell = self.worksheet.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        row += 1
        
        # Write submission data
        for submission in submissions:
            col = 1
            
            # Group name
            group_name = "No Group"
            if submission.get('group'):
                group_name = submission['group'].get('name', f"Group {submission.get('group_id', 'N/A')}")
            self.worksheet.cell(row=row, column=col, value=group_name)
            col += 1
            
            # Exercise grades
            grade_breakdown = submission.get('grade_breakdown') or []
            total_weighted_score = 0
            max_possible_score = 0
            
            for exercise in exercises:
                # Find grade for this exercise
                exercise_grade = next(
                    (grade for grade in grade_breakdown if grade.get('exercise_id') == exercise['id']),
                    None
                )
                
                if exercise_grade:
                    points = exercise_grade.get('score', exercise_grade.get('points', 0))
                    comments = exercise_grade.get('feedback', exercise_grade.get('comments', ''))
                else:
                    points = 0
                    comments = ''
                
                # Points
                self.worksheet.cell(row=row, column=col, value=points)
                col += 1
                
                # Comments
                self.worksheet.cell(row=row, column=col, value=comments)
                col += 1
                
                # Calculate weighted score
                exercise_weight = exercise.get('points', 0)
                if isinstance(exercise_weight, (int, float)):
                    weighted_points = points * exercise_weight / 10
                    total_weighted_score += weighted_points
                    max_possible_score += exercise_weight
            
            # Total score
            if max_possible_score > 0:
                final_score = (total_weighted_score / max_possible_score) * 10
            else:
                final_score = 0
            
            self.worksheet.cell(row=row, column=col, value=round(final_score, 2))
            col += 1
            
            # Percentage
            percentage = submission.get('percentage_score', 0)
            self.worksheet.cell(row=row, column=col, value=f"{percentage:.1f}%" if percentage else "0%")
            col += 1
            
            # Status
            status = submission.get('status', 'submitted')
            self.worksheet.cell(row=row, column=col, value=status.title())
            col += 1
            
            # Teacher feedback
            feedback = submission.get('teacher_feedback', '')
            self.worksheet.cell(row=row, column=col, value=feedback)
            
            row += 1
        
        row += 2
        self._set_next_row(row)
    
    def _create_statistics_section(self, submissions: List[Dict[str, Any]]):
        """Create statistics section"""
        if not submissions:
            return
            
        row = self._get_next_row()
        
        # Section header
        self.worksheet[f'A{row}'] = "STATISTICS"
        self.worksheet[f'A{row}'].font = Font(size=14, bold=True)
        self.worksheet[f'A{row}'].fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        self.worksheet.merge_cells(f'A{row}:D{row}')
        row += 2
        
        # Calculate statistics
        scores = [sub.get('total_score', 0) for sub in submissions if sub.get('total_score') is not None]
        percentages = [sub.get('percentage_score', 0) for sub in submissions if sub.get('percentage_score') is not None]
        
        stats = [
            ("Total Submissions", len(submissions)),
            ("Graded Submissions", len(scores)),
            ("Average Score", f"{sum(scores) / len(scores):.2f}" if scores else "N/A"),
            ("Average Percentage", f"{sum(percentages) / len(percentages):.1f}%" if percentages else "N/A"),
            ("Highest Score", f"{max(scores):.2f}" if scores else "N/A"),
            ("Lowest Score", f"{min(scores):.2f}" if scores else "N/A"),
        ]
        
        for stat_name, stat_value in stats:
            self.worksheet[f'A{row}'] = stat_name + ":"
            self.worksheet[f'B{row}'] = stat_value
            self.worksheet[f'A{row}'].font = Font(bold=True)
            row += 1
        
        row += 2
        self._set_next_row(row)
    
    def _create_public_report_section(self, submissions: List[Dict[str, Any]]):
        """Create public report grades section"""
        row = self._get_next_row()
        
        # Section header
        self.worksheet[f'A{row}'] = "PUBLIC REPORT GRADES"
        self.worksheet[f'A{row}'].font = Font(size=14, bold=True)
        self.worksheet[f'A{row}'].fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        self.worksheet.merge_cells(f'A{row}:E{row}')
        row += 2
        
        # Headers
        headers = ['Group Name', 'Public Report Points', 'Comments', 'Responsible Students']
        for col, header in enumerate(headers, 1):
            cell = self.worksheet.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        row += 1
        
        # Data
        for submission in submissions:
            col = 1
            
            # Group name
            group_name = "No Group"
            if submission.get('group'):
                group_name = submission['group'].get('name', f"Group {submission.get('group_id', 'N/A')}")
            self.worksheet.cell(row=row, column=col, value=group_name)
            col += 1
            
            # Extract public report data from ai_feedback
            ai_feedback = submission.get('ai_feedback', '')
            public_report_points = ""
            public_report_comments = ""
            
            if ai_feedback:
                try:
                    feedback_data = json.loads(ai_feedback)
                    public_report = feedback_data.get('public_report', {})
                    public_report_points = public_report.get('points', '')
                    public_report_comments = public_report.get('comments', '')
                except (json.JSONDecodeError, TypeError):
                    pass
            
            self.worksheet.cell(row=row, column=col, value=public_report_points)
            col += 1
            
            self.worksheet.cell(row=row, column=col, value=public_report_comments)
            col += 1
            
            # Responsible students
            responsible_students = submission.get('public_pdf_responsible_students', '')
            if responsible_students:
                try:
                    students = json.loads(responsible_students)
                    if isinstance(students, list):
                        responsible_students = ', '.join(students)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            self.worksheet.cell(row=row, column=col, value=responsible_students)
            
            row += 1
        
        row += 2
        self._set_next_row(row)
    
    def _create_private_report_section(self, submissions: List[Dict[str, Any]]):
        """Create private report grades section"""
        row = self._get_next_row()
        
        # Section header
        self.worksheet[f'A{row}'] = "PRIVATE REPORT GRADES"
        self.worksheet[f'A{row}'].font = Font(size=14, bold=True)
        self.worksheet[f'A{row}'].fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        self.worksheet.merge_cells(f'A{row}:D{row}')
        row += 2
        
        # Headers
        headers = ['Group Name', 'Coordinators', 'Has Private Report', 'AI Evaluation']
        for col, header in enumerate(headers, 1):
            cell = self.worksheet.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        row += 1
        
        # Data
        for submission in submissions:
            col = 1
            
            # Group name
            group_name = "No Group"
            if submission.get('group'):
                group_name = submission['group'].get('name', f"Group {submission.get('group_id', 'N/A')}")
            self.worksheet.cell(row=row, column=col, value=group_name)
            col += 1
            
            # Coordinators
            coordinators = submission.get('coordinators', '')
            if coordinators:
                try:
                    coord_list = json.loads(coordinators)
                    if isinstance(coord_list, list):
                        coordinators = ', '.join(coord_list)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            self.worksheet.cell(row=row, column=col, value=coordinators)
            col += 1
            
            # Has private report
            has_private = "Yes" if submission.get('private_pdf_data') else "No"
            self.worksheet.cell(row=row, column=col, value=has_private)
            col += 1
            
            # AI evaluation status
            ai_feedback = submission.get('ai_feedback', '')
            ai_evaluation = "No"
            if ai_feedback:
                try:
                    feedback_data = json.loads(ai_feedback)
                    if feedback_data.get('private_report'):
                        ai_evaluation = "Yes"
                except (json.JSONDecodeError, TypeError):
                    pass
            
            self.worksheet.cell(row=row, column=col, value=ai_evaluation)
            
            row += 1
        
        self._set_next_row(row + 2)
    
    def generate_classroom_assignment_grades(
        self, 
        assignment: Dict[str, Any], 
        submissions: List[Dict[str, Any]],
        classroom: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generate a simplified Excel grade summary for classroom/assignment with specific columns:
        - Group
        - Exercise Name Score (one column per exercise)
        - Meeting notes (Yes/No, Sí/No for catalan)
        - Public report score
        - Private report score
        - Group comments (joined from all exercises)
        - Coordinator comments (joined from private and public reports)
        
        Args:
            assignment: Assignment data with exercises
            submissions: List of submission data with grades
            classroom: Optional classroom information
            
        Returns:
            Excel file as bytes
        """
        # Create workbook and worksheet
        self.workbook = Workbook()
        self.worksheet = self.workbook.active
        self.worksheet.title = f"Grades - {assignment.get('name', 'Assignment')}"
        
        # Generate the simplified summary
        self._create_simplified_grades_section(assignment, submissions, classroom)
        
        # Auto-adjust column widths
        self._auto_adjust_columns()
        
        # Save to bytes
        excel_buffer = io.BytesIO()
        self.workbook.save(excel_buffer)
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
    
    def _create_simplified_grades_section(self, assignment: Dict[str, Any], submissions: List[Dict[str, Any]], classroom: Optional[Dict[str, Any]]):
        """Create simplified grades section with specific columns"""
        exercises = assignment.get('exercises', [])
        if not submissions:
            return
            
        row = 1
        
        # Determine language for meeting notes
        language = classroom.get('language', 'en').lower() if classroom else 'en'
        meeting_notes_yes = "Sí" if language == 'ca' else "Yes"
        meeting_notes_no = "No" if language == 'ca' else "No"
        
        # Create headers
        headers = ['Group']
        
        # Add exercise score columns
        for exercise in exercises:
            exercise_name = exercise.get('description', f"Exercise {exercise.get('order', exercises.index(exercise) + 1)}")
            headers.append(f"{exercise_name} Score")
        
        headers.extend([
            'Meeting notes',
            'Public report score',
            'Private report score',
            'Coordinator',
            'Group comments',
            'Coordinator comments'
        ])
        
        # Write headers
        for col, header in enumerate(headers, 1):
            cell = self.worksheet.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        row += 1
        
        # Write submission data
        for submission in submissions:
            col = 1
            
            # Group name
            group_name = "No Group"
            if submission.get('group'):
                group_name = submission['group'].get('name', f"Group {submission.get('group_id', 'N/A')}")
            self.worksheet.cell(row=row, column=col, value=group_name)
            col += 1
            
            # Exercise scores
            grade_breakdown = submission.get('grade_breakdown') or []
            
            for exercise in exercises:
                # Find grade for this exercise
                exercise_grade = next(
                    (grade for grade in grade_breakdown if grade.get('exercise_id') == exercise['id']),
                    None
                )
                
                if exercise_grade:
                    # Convert score to 0-100 scale if needed
                    score = exercise_grade.get('score', exercise_grade.get('points', 0))
                    if isinstance(score, (int, float)) and score <= 10:
                        score = score * 10  # Convert from 0-10 to 0-100 scale
                    self.worksheet.cell(row=row, column=col, value=score)
                else:
                    self.worksheet.cell(row=row, column=col, value=0)
                col += 1
            
            # Meeting notes
            meeting_notes_value = submission.get('meeting_notes', False)
            self.worksheet.cell(row=row, column=col, value=meeting_notes_yes if meeting_notes_value else meeting_notes_no)
            col += 1
            
            # Public report score
            public_report_score = ""
            ai_feedback = submission.get('ai_feedback', '')
            if ai_feedback:
                try:
                    feedback_data = json.loads(ai_feedback)
                    public_report = feedback_data.get('public_report', {})
                    score = public_report.get('points', '')
                    if score:
                        # Convert to 0-100 scale if needed
                        if isinstance(score, (int, float)) and score <= 10:
                            score = score * 10
                        public_report_score = score
                except (json.JSONDecodeError, TypeError):
                    pass
            
            self.worksheet.cell(row=row, column=col, value=public_report_score)
            col += 1
            
            # Private report score
            private_report_score = ""
            if ai_feedback:
                try:
                    feedback_data = json.loads(ai_feedback)
                    private_report = feedback_data.get('private_report', {})
                    score = private_report.get('points', '')
                    if score:
                        # Convert to 0-100 scale if needed
                        if isinstance(score, (int, float)) and score <= 10:
                            score = score * 10
                        private_report_score = score
                except (json.JSONDecodeError, TypeError):
                    pass
            
            self.worksheet.cell(row=row, column=col, value=private_report_score)
            col += 1
            
            # Coordinator score (normalized average of Private Report and Public Report scores)
            coordinator_score = ""
            if ai_feedback:
                try:
                    feedback_data = json.loads(ai_feedback)
                    
                    # Get original scores (0-10 scale) directly from AI feedback
                    public_report = feedback_data.get('public_report', {})
                    public_score = public_report.get('points', 0)
                    
                    private_report = feedback_data.get('private_report', {})
                    private_score = private_report.get('points', 0)
                    
                    # Handle cases where scores might be missing or "N/A"
                    if isinstance(public_score, str) and public_score.lower() == 'n/a':
                        public_score = 0
                    if isinstance(private_score, str) and private_score.lower() == 'n/a':
                        private_score = 0
                    
                    # Calculate average and normalize from 0-10 to 0-1 scale
                    if isinstance(public_score, (int, float)) and isinstance(private_score, (int, float)):
                        # Always calculate average between both reports (missing reports = 0)
                        average_score = (public_score + private_score) / 2
                        normalized_score = average_score / 10  # Normalize from 0-10 to 0-1 scale
                        coordinator_score = round(normalized_score, 2)
                    else:
                        coordinator_score = 1.0  # Default for non-coordinators
                except (json.JSONDecodeError, TypeError, ValueError):
                    coordinator_score = 1.0  # Default for non-coordinators
            
            self.worksheet.cell(row=row, column=col, value=coordinator_score)
            col += 1
            
            # Group comments (join all exercise comments)
            group_comments = []
            for exercise_grade in grade_breakdown:
                comments = exercise_grade.get('feedback', exercise_grade.get('comments', ''))
                if comments:
                    group_comments.append(comments)
            
            group_comments_text = '\n'.join(group_comments) if group_comments else ''
            self.worksheet.cell(row=row, column=col, value=group_comments_text)
            col += 1
            
            # Coordinator comments (join private and public report comments)
            coordinator_comments = []
            
            # Private report comments
            if ai_feedback:
                try:
                    feedback_data = json.loads(ai_feedback)
                    private_report = feedback_data.get('private_report', {})
                    private_comments = private_report.get('comments', '')
                    if private_comments:
                        coordinator_comments.append(f"Private: {private_comments}")
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Public report comments
            if ai_feedback:
                try:
                    feedback_data = json.loads(ai_feedback)
                    public_report = feedback_data.get('public_report', {})
                    public_comments = public_report.get('comments', '')
                    if public_comments:
                        coordinator_comments.append(f"Public: {public_comments}")
                except (json.JSONDecodeError, TypeError):
                    pass
            
            coordinator_comments_text = '\n'.join(coordinator_comments) if coordinator_comments else ''
            self.worksheet.cell(row=row, column=col, value=coordinator_comments_text)
            
            row += 1
    
    def _auto_adjust_columns(self):
        """Auto-adjust column widths for better readability"""
        for column in self.worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
            self.worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def _create_student_details_tab(self, assignment: Dict[str, Any], submissions: List[Dict[str, Any]]):
        """Create a second tab with detailed student grades"""
        # Create new worksheet
        student_worksheet = self.workbook.create_sheet(title=f"Student Details - {assignment.get('name', 'Assignment')}")
        
        # Store reference to current worksheet
        original_worksheet = self.worksheet
        self.worksheet = student_worksheet
        
        # Reset row tracking
        self._current_row = 1
        
        # Create header
        self._create_student_header_section(assignment)
        
        # Create student details table
        self._create_student_details_table(assignment, submissions)
        
        # Auto-adjust columns
        self._auto_adjust_columns()
        
        # Restore original worksheet reference
        self.worksheet = original_worksheet
    
    def _create_student_header_section(self, assignment: Dict[str, Any]):
        """Create header for student details tab"""
        row = 1
        
        # Title
        self.worksheet[f'A{row}'] = "STUDENT DETAILED GRADES"
        self.worksheet[f'A{row}'].font = Font(size=16, bold=True)
        self.worksheet[f'A{row}'].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        self.worksheet[f'A{row}'].font = Font(size=16, bold=True, color="FFFFFF")
        self.worksheet.merge_cells(f'A{row}:H{row}')
        row += 2
        
        # Assignment info
        self.worksheet[f'A{row}'] = "Assignment:"
        self.worksheet[f'B{row}'] = assignment.get('name', 'N/A')
        self.worksheet[f'A{row}'].font = Font(bold=True)
        row += 1
        
        self.worksheet[f'A{row}'] = "Description:"
        self.worksheet[f'B{row}'] = assignment.get('description', 'N/A')
        self.worksheet[f'A{row}'].font = Font(bold=True)
        row += 2
        
        self._current_row = row
    
    def _create_student_details_table(self, assignment: Dict[str, Any], submissions: List[Dict[str, Any]]):
        """Create the student details table"""
        exercises = assignment.get('exercises', [])
        row = self._get_next_row()
        
        # Create headers
        headers = ['Group', 'Student Name', 'Coordinator']
        
        # Add exercise headers
        for exercise in exercises:
            headers.append(f"Exercise {exercise.get('order', exercises.index(exercise) + 1)}")
        
        headers.extend(['Meeting Notes', 'Public Report', 'Private Report'])
        
        # Write headers
        for col, header in enumerate(headers, 1):
            cell = self.worksheet.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        row += 1
        
        # Process each submission and extract student details
        for submission in submissions:
            group = submission.get('group')
            if not group or not group.get('members'):
                continue
                
            # Get group grade breakdown
            grade_breakdown = submission.get('grade_breakdown') or []
            
            # Get coordination info
            coordinators = []
            try:
                if submission.get('coordinators'):
                    coordinators = json.loads(submission['coordinators']) if isinstance(submission['coordinators'], str) else submission['coordinators']
            except:
                coordinators = []
            
            # Process each student in the group
            for member in group.get('members', []):
                student_name = member.get('name', 'Unknown Student') if isinstance(member, dict) else str(member)
                
                # Group name
                self.worksheet.cell(row=row, column=1, value=group.get('name', 'No Group'))
                
                # Student name
                self.worksheet.cell(row=row, column=2, value=student_name)
                
                # Coordinator score (check if student is coordinator)
                coordinator_score = self._calculate_student_coordinator_score(student_name, coordinators, submission)
                self.worksheet.cell(row=row, column=3, value=coordinator_score)
                
                # Exercise grades (same for all students in group)
                col = 4
                for exercise in exercises:
                    exercise_grade = next(
                        (grade for grade in grade_breakdown if grade.get('exercise_id') == exercise['id']),
                        None
                    )
                    
                    if exercise_grade:
                        points = exercise_grade.get('score', exercise_grade.get('points', 0))
                    else:
                        points = 0
                    
                    self.worksheet.cell(row=row, column=col, value=points)
                    col += 1
                
                # Meeting notes (empty)
                self.worksheet.cell(row=row, column=col, value="")
                col += 1
                
                # Public report (empty)
                self.worksheet.cell(row=row, column=col, value="")
                col += 1
                
                # Private report score
                private_score = self._calculate_private_report_score(submission)
                self.worksheet.cell(row=row, column=col, value=private_score)
                
                row += 1
        
        self._current_row = row
    
    def _calculate_coordinator_score(self, submission: Dict[str, Any]) -> float:
        """Calculate coordinator score based on whether student is coordinator"""
        # For group-level submissions, we need to determine if this applies to coordinators
        # This method is used in the simplified grades section where we don't have individual student info
        # Return the average score normalized to 0-1 scale
        ai_feedback = submission.get('ai_feedback', '')
        if not ai_feedback:
            return 1.0  # Default score for non-coordinators
        
        try:
            feedback_data = json.loads(ai_feedback)
            
            # Get Public Report score
            public_report = feedback_data.get('public_report', {})
            public_score = public_report.get('points', 0)
            
            # Get Private Report score
            private_report = feedback_data.get('private_report', {})
            private_score = private_report.get('points', 0)
            
            # Calculate average and normalize from 0-10 to 0-1 scale
            if public_score > 0 or private_score > 0:
                average_score = (public_score + private_score) / 2
                normalized_score = average_score / 10  # Normalize from 0-10 to 0-1
                return round(normalized_score, 2)
            else:
                return 1.0  # Default score for non-coordinators
                
        except (json.JSONDecodeError, TypeError, ValueError):
            return 1.0  # Default score for non-coordinators
    
    def _calculate_student_coordinator_score(self, student_name: str, coordinators: list, submission: Dict[str, Any]) -> float:
        """Calculate coordinator score for a specific student"""
        # Check if student is a coordinator
        is_coordinator = any(coord.lower() == student_name.lower() for coord in coordinators)
        
        if not is_coordinator:
            return 1.0  # Non-coordinators get 1.0
        
        # Student is a coordinator - calculate score from reports
        ai_feedback = submission.get('ai_feedback', '')
        if not ai_feedback:
            return 1.0  # Default score if no feedback
        
        try:
            feedback_data = json.loads(ai_feedback)
            
            # Get Public Report score
            public_report = feedback_data.get('public_report', {})
            public_score = public_report.get('points', 0)
            
            # Get Private Report score
            private_report = feedback_data.get('private_report', {})
            private_score = private_report.get('points', 0)
            
            # Handle cases where scores might be missing or "N/A"
            if isinstance(public_score, str) and public_score.lower() == 'n/a':
                public_score = 0
            if isinstance(private_score, str) and private_score.lower() == 'n/a':
                private_score = 0
            
            # Calculate average and normalize from 0-10 to 0-1 scale
            if isinstance(public_score, (int, float)) and isinstance(private_score, (int, float)):
                # Always calculate average between both reports (missing reports = 0)
                average_score = (public_score + private_score) / 2
                normalized_score = average_score / 10  # Normalize from 0-10 to 0-1
                return round(normalized_score, 2)
            else:
                return 1.0  # Default score if scores are not numeric
                
        except (json.JSONDecodeError, TypeError, ValueError):
            return 1.0  # Default score on error
    
    def _calculate_coordination_score(self, submission: Dict[str, Any]) -> float:
        """Calculate coordination score for a student (legacy method - now uses coordinator score)"""
        return self._calculate_coordinator_score(submission)
    
    def _calculate_private_report_score(self, submission: Dict[str, Any]) -> float:
        """Calculate private report score for a student"""
        # Check if submission has private report data
        if submission.get('private_pdf_data'):
            # If private report exists, could implement scoring logic here
            # For now, return placeholder value
            return 0.0
        else:
            # No private report submitted
            return 0.0
    
    def _get_next_row(self) -> int:
        """Get the next available row"""
        if not hasattr(self, '_current_row'):
            self._current_row = 1
        return self._current_row
    
    def _set_next_row(self, row: int):
        """Set the next available row"""
        self._current_row = row
