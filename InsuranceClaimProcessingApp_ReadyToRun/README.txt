# Insurance Claim Processing System

A Python GUI application for integrating customer details from CSV with insurance claim information from XML, storing the integrated datasets in SQLite, identifying claims without matching customer information, and generating an incomplete-claims report.

## Technologies

- Python 3
- Tkinter
- SQLite
- CSV
- XML

No external Python packages are required.

## Files

- `app.py` - Main Python application code
- `customers.csv` - Customer details
- `claims.xml` - Insurance claim information
- `insurance_claims.db` - SQLite database created automatically
- `run_app.bat` - Windows launcher

## How to Run

Double-click:

`run_app.bat`

OR open Command Prompt in this folder and run:

`python app.py`

## Features

- Import customer data from CSV
- Import claim data from XML
- Store data in SQLite
- Merge customer and claim information
- Identify claims without matching customers
- Generate incomplete claims report
- Search claims
- Filter complete/incomplete claims
- Display claim summary
- Calculate total claim amount
- Calculate incomplete claim amount
- Add or update claims
- Double-click a claim to view details

## Database Tables

### customers
- customer_id
- name
- age
- policy_number
- policy_type

### claims
- claim_id
- customer_id
- claim_type
- amount
- claim_date
- status

## Question Mapping

Customer details -> CSV
Claim information -> XML
Dataset integration -> Python + SQLite LEFT JOIN
Missing customer identification -> LEFT JOIN with NULL check
Incomplete claim report -> GUI report
