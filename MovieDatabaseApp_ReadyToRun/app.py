import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "movie_database.db"
XML_FILE = BASE_DIR / "movies.xml"
CSV_FILE = BASE_DIR / "ratings.csv"


def connect_db():
    return sqlite3.connect(DB_FILE)


def create_database():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            genre TEXT,
            year INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            viewer TEXT NOT NULL,
            rating REAL NOT NULL,
            FOREIGN KEY(movie_id) REFERENCES movies(id)
        )
    """)

    conn.commit()
    conn.close()


def import_xml_movies():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    conn = connect_db()
    cur = conn.cursor()

    for movie in root.findall("movie"):
        movie_id = int(movie.findtext("id"))
        title = movie.findtext("title", "")
        genre = movie.findtext("genre", "")
        year = int(movie.findtext("year", "0"))

        cur.execute("""
            INSERT OR REPLACE INTO movies (id, title, genre, year)
            VALUES (?, ?, ?, ?)
        """, (movie_id, title, genre, year))

    conn.commit()
    conn.close()


def import_csv_ratings():
    conn = connect_db()
    cur = conn.cursor()

    # Prevent duplicate imports when the application is restarted.
    cur.execute("DELETE FROM ratings")

    with open(CSV_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            movie_id = int(row["movie_id"])
            viewer = row["viewer"]
            rating = float(row["rating"])

            cur.execute("""
                INSERT INTO ratings (movie_id, viewer, rating)
                VALUES (?, ?, ?)
            """, (movie_id, viewer, rating))

    conn.commit()
    conn.close()


def load_data():
    try:
        import_xml_movies()
        import_csv_ratings()
        refresh_table()
        update_dashboard()
    except Exception as e:
        messagebox.showerror("Import Error", str(e))


def get_movie_report(search_text=""):
    conn = connect_db()
    cur = conn.cursor()

    query = """
        SELECT
            m.id,
            m.title,
            m.genre,
            m.year,
            ROUND(COALESCE(AVG(r.rating), 0), 2) AS average_rating,
            COUNT(r.id) AS total_ratings
        FROM movies m
        LEFT JOIN ratings r ON m.id = r.movie_id
    """

    params = ()

    if search_text.strip():
        query += " WHERE m.title LIKE ? OR m.genre LIKE ? "
        keyword = "%" + search_text.strip() + "%"
        params = (keyword, keyword)

    query += """
        GROUP BY m.id, m.title, m.genre, m.year
        ORDER BY average_rating DESC, m.title ASC
    """

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return rows


def refresh_table():
    for item in movie_tree.get_children():
        movie_tree.delete(item)

    rows = get_movie_report(search_var.get())

    for row in rows:
        movie_tree.insert("", "end", values=row)


def search_movies():
    refresh_table()


def clear_search():
    search_var.set("")
    refresh_table()


def update_dashboard():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM movies")
    total_movies = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM ratings")
    total_ratings = cur.fetchone()[0]

    cur.execute("""
        SELECT m.title, ROUND(AVG(r.rating), 2)
        FROM movies m
        JOIN ratings r ON m.id = r.movie_id
        GROUP BY m.id
        ORDER BY AVG(r.rating) DESC
        LIMIT 1
    """)
    top_movie = cur.fetchone()

    cur.execute("SELECT ROUND(AVG(rating), 2) FROM ratings")
    overall_average = cur.fetchone()[0] or 0

    conn.close()

    total_movies_label.config(text=str(total_movies))
    total_ratings_label.config(text=str(total_ratings))
    average_label.config(text=str(overall_average))

    if top_movie:
        top_movie_label.config(text=f"{top_movie[0]} ({top_movie[1]}/5)")
    else:
        top_movie_label.config(text="No ratings")


def add_rating():
    movie_id = movie_id_entry.get().strip()
    viewer = viewer_entry.get().strip()
    rating = rating_var.get().strip()

    if not movie_id or not viewer or not rating:
        messagebox.showwarning("Missing Data", "Please fill all fields.")
        return

    try:
        movie_id = int(movie_id)
        rating = float(rating)

        if rating < 1 or rating > 5:
            raise ValueError

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT title FROM movies WHERE id = ?", (movie_id,))
        movie = cur.fetchone()

        if not movie:
            conn.close()
            messagebox.showerror("Invalid Movie", "Movie ID does not exist.")
            return

        cur.execute("""
            INSERT INTO ratings (movie_id, viewer, rating)
            VALUES (?, ?, ?)
        """, (movie_id, viewer, rating))

        conn.commit()
        conn.close()

        viewer_entry.delete(0, tk.END)
        movie_id_entry.delete(0, tk.END)
        rating_var.set("")

        refresh_table()
        update_dashboard()

        messagebox.showinfo("Success", f"Rating added for {movie[0]}.")

    except ValueError:
        messagebox.showerror(
            "Invalid Rating",
            "Movie ID must be an integer and rating must be between 1 and 5."
        )


def show_selected_movie(event=None):
    selected = movie_tree.selection()

    if not selected:
        return

    values = movie_tree.item(selected[0], "values")

    details = (
        f"Movie ID: {values[0]}\n"
        f"Title: {values[1]}\n"
        f"Genre: {values[2]}\n"
        f"Year: {values[3]}\n"
        f"Average Rating: {values[4]}/5\n"
        f"Number of Ratings: {values[5]}"
    )

    messagebox.showinfo("Movie Details", details)


def create_database_view():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            m.title,
            r.viewer,
            r.rating
        FROM ratings r
        JOIN movies m ON r.movie_id = m.id
        ORDER BY m.title, r.rating DESC
    """)

    rows = cur.fetchall()
    conn.close()

    for item in rating_tree.get_children():
        rating_tree.delete(item)

    for row in rows:
        rating_tree.insert("", "end", values=row)


def show_rating_window():
    window = tk.Toplevel(root)
    window.title("Viewer Ratings")
    window.geometry("650x450")
    window.configure(bg="#f5f7fb")

    tk.Label(
        window,
        text="VIEWER RATINGS",
        font=("Arial", 18, "bold"),
        bg="#f5f7fb"
    ).pack(pady=15)

    global rating_tree

    columns = ("Movie", "Viewer", "Rating")
    rating_tree = ttk.Treeview(window, columns=columns, show="headings")

    for col in columns:
        rating_tree.heading(col, text=col)

    rating_tree.column("Movie", width=300)
    rating_tree.column("Viewer", width=180)
    rating_tree.column("Rating", width=100)

    rating_tree.pack(fill="both", expand=True, padx=20, pady=10)

    create_database_view()


def show_top_movies():
    refresh_table()
    messagebox.showinfo(
        "Report",
        "The movie report is sorted from highest to lowest average rating."
    )


# -------------------- GUI --------------------

root = tk.Tk()
root.title("Movie Database Management System")
root.geometry("1100x700")
root.minsize(950, 600)
root.configure(bg="#eef2f7")

style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure(
    "Treeview",
    rowheight=30,
    font=("Arial", 10)
)

style.configure(
    "Treeview.Heading",
    font=("Arial", 10, "bold")
)

# Header
header = tk.Frame(root, bg="#172554", height=85)
header.pack(fill="x")

tk.Label(
    header,
    text="MOVIE DATABASE MANAGEMENT SYSTEM",
    font=("Arial", 23, "bold"),
    fg="white",
    bg="#172554"
).pack(pady=(18, 2))

tk.Label(
    header,
    text="XML + CSV + SQLite + Python",
    font=("Arial", 10),
    fg="white",
    bg="#172554"
).pack()

# Dashboard
dashboard = tk.Frame(root, bg="#eef2f7")
dashboard.pack(fill="x", padx=20, pady=15)

def card(parent, title):
    frame = tk.Frame(parent, bg="white", bd=1, relief="solid")
    frame.pack(side="left", fill="both", expand=True, padx=5)
    tk.Label(
        frame, text=title, font=("Arial", 10, "bold"),
        bg="white", fg="#475569"
    ).pack(pady=(12, 2))
    value = tk.Label(
        frame, text="0", font=("Arial", 20, "bold"),
        bg="white", fg="#172554"
    )
    value.pack(pady=(0, 12))
    return value

total_movies_label = card(dashboard, "TOTAL MOVIES")
total_ratings_label = card(dashboard, "TOTAL RATINGS")
average_label = card(dashboard, "PLATFORM AVERAGE")
top_movie_label = card(dashboard, "TOP RATED MOVIE")

# Search
search_frame = tk.Frame(root, bg="#eef2f7")
search_frame.pack(fill="x", padx=25, pady=5)

tk.Label(
    search_frame,
    text="Search:",
    font=("Arial", 11, "bold"),
    bg="#eef2f7"
).pack(side="left", padx=(0, 8))

search_var = tk.StringVar()

search_entry = ttk.Entry(
    search_frame,
    textvariable=search_var,
    width=35
)
search_entry.pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Search",
    command=search_movies
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Clear",
    command=clear_search
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Top Rated Report",
    command=show_top_movies
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Viewer Ratings",
    command=show_rating_window
).pack(side="left", padx=5)

# Movie table
table_frame = tk.Frame(root, bg="#eef2f7")
table_frame.pack(fill="both", expand=True, padx=25, pady=10)

columns = (
    "ID",
    "Title",
    "Genre",
    "Year",
    "Average Rating",
    "Ratings Count"
)

movie_tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

for col in columns:
    movie_tree.heading(col, text=col)

movie_tree.column("ID", width=60, anchor="center")
movie_tree.column("Title", width=250)
movie_tree.column("Genre", width=140)
movie_tree.column("Year", width=80, anchor="center")
movie_tree.column("Average Rating", width=130, anchor="center")
movie_tree.column("Ratings Count", width=120, anchor="center")

scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=movie_tree.yview
)

movie_tree.configure(yscrollcommand=scrollbar.set)

movie_tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

movie_tree.bind("<Double-1>", show_selected_movie)

# Add rating section
add_frame = tk.LabelFrame(
    root,
    text="Add Viewer Rating",
    font=("Arial", 11, "bold"),
    bg="#eef2f7",
    padx=10,
    pady=10
)
add_frame.pack(fill="x", padx=25, pady=(0, 15))

tk.Label(add_frame, text="Movie ID", bg="#eef2f7").pack(side="left", padx=5)
movie_id_entry = ttk.Entry(add_frame, width=10)
movie_id_entry.pack(side="left", padx=5)

tk.Label(add_frame, text="Viewer", bg="#eef2f7").pack(side="left", padx=5)
viewer_entry = ttk.Entry(add_frame, width=20)
viewer_entry.pack(side="left", padx=5)

tk.Label(add_frame, text="Rating (1-5)", bg="#eef2f7").pack(side="left", padx=5)
rating_var = tk.StringVar()
rating_entry = ttk.Entry(add_frame, textvariable=rating_var, width=10)
rating_entry.pack(side="left", padx=5)

ttk.Button(
    add_frame,
    text="Add Rating",
    command=add_rating
).pack(side="left", padx=10)

ttk.Button(
    add_frame,
    text="Reload XML + CSV",
    command=load_data
).pack(side="left", padx=5)

# Footer
tk.Label(
    root,
    text="Double-click a movie to view details",
    bg="#eef2f7",
    fg="#64748b",
    font=("Arial", 9)
).pack(pady=(0, 8))

# Start application
try:
    create_database()
    load_data()
except Exception as e:
    messagebox.showerror(
        "Startup Error",
        "Could not load the application data.\n\n" + str(e)
    )

root.mainloop()
