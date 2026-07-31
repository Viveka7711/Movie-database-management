# Railway Ticket Reservation System

A Python GUI application that integrates passenger details from CSV with train schedules from JSON, stores both datasets in SQLite, verifies train numbers, and generates a final passenger reservation report.

## Technologies

- Python 3
- Tkinter
- SQLite
- CSV
- JSON

No external packages are required.

## Files

- `app.py` - Main Python application code
- `passengers.csv` - Passenger input dataset
- `trains.json` - Train schedule input dataset
- `railway_reservation.db` - SQLite database created automatically
- `run_app.bat` - Windows launcher

## How to Run

Double-click `run_app.bat`

OR run:

```bash
python app.py
```

## Features

- Import passenger data from CSV
- Import train schedules from JSON
- Store data in SQLite
- Verify passenger train numbers
- Identify valid and invalid reservations
- Generate final passenger reservation report
- Search passenger, train number or train name
- Filter valid/invalid reservations
- Show train-wise passenger summary
- Add new passenger reservation
- Double-click a passenger to view details

## Database Tables

### passengers
- passenger_id
- name
- age
- gender
- train_number
- seat

### trains
- train_number
- train_name
- source
- destination
- departure
- arrival

## Question Mapping

Passenger details -> CSV  
Train schedules -> JSON  
Integration -> Python + SQLite JOIN  
Train verification -> LEFT JOIN / train number matching  
Final report -> Integrated GUI table and summary
