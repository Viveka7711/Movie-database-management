# University Placement Management System

A Python GUI application for integrating student details from CSV and placement information from JSON, storing the integrated data in SQLite, identifying placed students, and generating placement summaries.

## Technologies

- Python 3
- Tkinter
- SQLite
- CSV
- JSON

No external Python packages are required.

## Files

- `app.py` - Main GUI application
- `students.csv` - Student details
- `placements.json` - Placement information
- `university_placement.db` - SQLite database created automatically
- `run_app.bat` - Windows launcher

## How to Run

### Option 1
Double-click:

`run_app.bat`

### Option 2
Open Command Prompt in this folder and run:

`python app.py`

## Features

- Integrates CSV and JSON datasets
- Stores data in SQLite
- Identifies students who received placement offers
- Shows placed and not-placed students
- Calculates placement percentage
- Calculates average package
- Finds highest package
- Shows top recruiting company
- Generates company-wise placement summary
- Generates department-wise placement summary
- Searches students
- Adds or updates placement offers

## Database Tables

### students
- student_id
- name
- department
- year
- email

### placements
- id
- student_id
- company
- package
- status

## Question Mapping

Student details -> CSV  
Placement details -> JSON  
Integration -> Python + SQLite JOIN  
Placed students -> status = 'Placed'  
Placement summary -> SQL aggregation and GUI report
