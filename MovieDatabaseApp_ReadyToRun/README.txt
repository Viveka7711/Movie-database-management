MOVIE DATABASE MANAGEMENT SYSTEM

Requirements:
- Python 3.x
- Tkinter (normally included with standard Python)
- No external packages are required.

Files:
1. app.py          -> Main application
2. movies.xml      -> Movie information
3. ratings.csv     -> Viewer ratings
4. movie_database.db -> Created automatically by the application

How to run:
1. Keep all files in the same folder.
2. Open a terminal/command prompt in that folder.
3. Run:
       python app.py

Features:
- Imports movie details from XML.
- Imports viewer ratings from CSV.
- Stores data in SQLite.
- Calculates average rating for every movie.
- Sorts movies by average rating.
- Searches movies by title or genre.
- Displays viewer ratings.
- Allows adding new viewer ratings.
- Shows dashboard statistics.

For a 10-mark explanation:
XML -> Movie dataset
CSV -> Ratings dataset
Python -> Reads and combines the datasets
SQLite -> Database storage
SQL AVG() -> Average rating
ORDER BY -> Sorts report by rating
Tkinter -> Graphical user interface
