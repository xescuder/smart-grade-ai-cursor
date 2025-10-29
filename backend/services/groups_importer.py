import csv
from typing import List, Dict, Any


def import_students_csv_with_mapping(file_path: str) -> List[Dict[str, str]]:
    """
    Imports student data from a CSV file using a column position map.
    It handles empty 'Grup' cells by carrying the value from the previous row.

    Args:
        file_path: The path to the CSV file.

    Returns:
        A list of dictionaries, where each dictionary represents a student.
    """

    # Define the mapping of data fields to their 0-based column indices.
    # Based on your image:
    # A (Grup) -> 0, B (Nom estudiant) -> 1, C (Login) -> 2, D (Email) -> 3
    COLUMN_MAP = {
        "group": 0,
        "name": 1,
        "login": 2,
        "email": 3
    }

    students_list: List[Dict[str, str]] = []
    current_group: str = ""

    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
            # Try semicolon delimiter first, then fall back to comma
            sample = csvfile.read(1024)
            csvfile.seek(0)
            
            if ';' in sample and sample.count(';') > sample.count(','):
                reader = csv.reader(csvfile, delimiter=';')
            else:
                reader = csv.reader(csvfile, delimiter=',')

            # Skip the header row (assuming row 1 in the image is the header)
            try:
                next(reader)
            except StopIteration:
                print("The CSV file is empty.")
                return students_list

            # Process data rows
            for row in reader:
                # Skip empty rows or rows with only semicolons
                if not row or all(cell.strip() == '' or cell.strip() == ';' for cell in row):
                    continue
                
                # Ensure the row has enough columns based on your map
                if len(row) <= max(COLUMN_MAP.values()):
                    print(f"Skipping row with missing data: {row}")
                    continue

                # Access data using the COLUMN_MAP
                group_cell = row[COLUMN_MAP["group"]].strip()
                name = row[COLUMN_MAP["name"]].strip()
                login = row[COLUMN_MAP["login"]].strip()
                email = row[COLUMN_MAP["email"]].strip()

                # Clean up the data - remove extra semicolons and malformed content
                group_cell = group_cell.split(';')[0].strip() if group_cell else ""
                name = name.split(';')[0].strip() if name else ""
                login = login.split(';')[0].strip() if login else ""
                email = email.split(';')[0].strip() if email else ""

                # Skip rows that look like headers or summary rows
                if any(keyword in group_cell.lower() for keyword in ['grups', 'alumnes', 'mitjana', 'total']):
                    continue

                # --- Core logic to handle empty group cell or numeric-only group cell ---
                # Check if group_cell is empty, contains only semicolons, or is only a number
                is_empty_or_semicolon = not group_cell or group_cell.strip() == '' or group_cell.strip() == ';'
                is_only_number = group_cell.strip().isdigit() if group_cell.strip() else False
                
                if group_cell and not is_empty_or_semicolon and not is_only_number:
                    # If the group cell is not empty, not just semicolons, and not only a number, update the current_group
                    current_group = group_cell

                # Skip rows that don't have essential student info
                if not name and not login and not email:
                    continue
                if not current_group:
                    continue  # Skip until a valid group is found

                # Skip if the name looks like a summary or header
                if any(keyword in name.lower() for keyword in ['total', 'mitjana', 'grups', 'alumnes']):
                    continue

                # Create the student dictionary
                student: Dict[str, str] = {
                    "group": current_group,
                    "name": name,
                    "login": login,
                    "email": email
                }
                print(f"Adding student: {student}")
                students_list.append(student)

        return students_list

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []


