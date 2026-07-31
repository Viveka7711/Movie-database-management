import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "railway_reservation.db"
CSV_FILE = BASE_DIR / "passengers.csv"
JSON_FILE = BASE_DIR / "trains.json"


def connect_db():
    return sqlite3.connect(DB_FILE)


def create_database():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS passengers (
            passenger_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            train_number TEXT NOT NULL,
            seat TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS trains (
            train_number TEXT PRIMARY KEY,
            train_name TEXT NOT NULL,
            source TEXT,
            destination TEXT,
            departure TEXT,
            arrival TEXT
        )
    """)

    conn.commit()
    conn.close()


def import_passengers():
    conn = connect_db()
    cur = conn.cursor()

    with open(CSV_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cur.execute("""
                INSERT OR REPLACE INTO passengers
                (passenger_id, name, age, gender, train_number, seat)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                row["passenger_id"],
                row["name"],
                int(row["age"]),
                row["gender"],
                row["train_number"],
                row["seat"]
            ))

    conn.commit()
    conn.close()


def import_trains():
    with open(JSON_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM trains")

    for train in data["trains"]:
        cur.execute("""
            INSERT OR REPLACE INTO trains
            (train_number, train_name, source, destination, departure, arrival)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(train["train_number"]),
            train["train_name"],
            train["source"],
            train["destination"],
            train["departure"],
            train["arrival"]
        ))

    conn.commit()
    conn.close()


def load_data(show_message=True):
    try:
        import_passengers()
        import_trains()
        refresh_table()
        update_dashboard()

        if show_message:
            messagebox.showinfo(
                "Data Loaded",
                "Passenger CSV and train JSON data were successfully integrated."
            )
    except Exception as e:
        messagebox.showerror("Import Error", str(e))


def get_report(search_text="", valid_only=False, invalid_only=False):
    conn = connect_db()
    cur = conn.cursor()

    query = """
        SELECT
            p.passenger_id,
            p.name,
            p.age,
            p.gender,
            p.train_number,
            COALESCE(t.train_name, 'Not Found') AS train_name,
            COALESCE(t.source, '-') AS source,
            COALESCE(t.destination, '-') AS destination,
            COALESCE(t.departure, '-') AS departure,
            COALESCE(t.arrival, '-') AS arrival,
            p.seat,
            CASE
                WHEN t.train_number IS NOT NULL THEN 'Valid'
                ELSE 'Invalid Train'
            END AS status
        FROM passengers p
        LEFT JOIN trains t
            ON p.train_number = t.train_number
    """

    conditions = []
    params = []

    if search_text.strip():
        conditions.append("""
            (
                p.name LIKE ?
                OR p.passenger_id LIKE ?
                OR p.train_number LIKE ?
                OR t.train_name LIKE ?
            )
        """)
        keyword = "%" + search_text.strip() + "%"
        params.extend([keyword, keyword, keyword, keyword])

    if valid_only:
        conditions.append("t.train_number IS NOT NULL")

    if invalid_only:
        conditions.append("t.train_number IS NULL")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY p.passenger_id"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return rows


def refresh_table():
    for item in passenger_tree.get_children():
        passenger_tree.delete(item)

    rows = get_report(
        search_var.get(),
        valid_only_var.get(),
        invalid_only_var.get()
    )

    for row in rows:
        passenger_tree.insert("", "end", values=row)


def update_dashboard():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM passengers")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM passengers p
        INNER JOIN trains t
        ON p.train_number = t.train_number
    """)
    valid = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM passengers p
        LEFT JOIN trains t
        ON p.train_number = t.train_number
        WHERE t.train_number IS NULL
    """)
    invalid = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM trains")
    total_trains = cur.fetchone()[0]

    conn.close()

    verification_rate = (valid / total * 100) if total else 0

    total_label.config(text=str(total))
    valid_label.config(text=str(valid))
    invalid_label.config(text=str(invalid))
    rate_label.config(text=f"{verification_rate:.2f}%")
    trains_label.config(text=str(total_trains))


def search_passengers():
    refresh_table()


def clear_search():
    search_var.set("")
    valid_only_var.set(False)
    invalid_only_var.set(False)
    refresh_table()


def show_valid_only():
    invalid_only_var.set(False)
    valid_only_var.set(True)
    refresh_table()


def show_invalid_only():
    valid_only_var.set(False)
    invalid_only_var.set(True)
    refresh_table()


def show_selected_passenger(event=None):
    selected = passenger_tree.selection()

    if not selected:
        return

    values = passenger_tree.item(selected[0], "values")

    details = (
        f"Passenger ID: {values[0]}\n"
        f"Name: {values[1]}\n"
        f"Age: {values[2]}\n"
        f"Gender: {values[3]}\n"
        f"Train Number: {values[4]}\n"
        f"Train Name: {values[5]}\n"
        f"Route: {values[6]} → {values[7]}\n"
        f"Departure: {values[8]}\n"
        f"Arrival: {values[9]}\n"
        f"Seat: {values[10]}\n"
        f"Verification: {values[11]}"
    )

    messagebox.showinfo("Passenger Reservation Details", details)


def show_summary():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            t.train_number,
            t.train_name,
            t.source,
            t.destination,
            COUNT(p.passenger_id)
        FROM trains t
        LEFT JOIN passengers p
            ON t.train_number = p.train_number
        GROUP BY t.train_number
        ORDER BY COUNT(p.passenger_id) DESC
    """)
    train_rows = cur.fetchall()

    cur.execute("""
        SELECT
            t.train_number,
            t.train_name,
            COUNT(p.passenger_id)
        FROM trains t
        LEFT JOIN passengers p
            ON t.train_number = p.train_number
        GROUP BY t.train_number
        ORDER BY COUNT(p.passenger_id) DESC
        LIMIT 1
    """)
    top_train = cur.fetchone()

    conn.close()

    window = tk.Toplevel(root)
    window.title("Passenger Reservation Summary")
    window.geometry("850x550")
    window.configure(bg="#f4f7fb")

    tk.Label(
        window,
        text="FINAL PASSENGER RESERVATION REPORT",
        font=("Arial", 18, "bold"),
        bg="#f4f7fb"
    ).pack(pady=15)

    if top_train:
        tk.Label(
            window,
            text=f"Most Reserved Train: {top_train[1]} ({top_train[0]}) - "
                 f"{top_train[2]} passengers",
            font=("Arial", 11, "bold"),
            bg="#f4f7fb"
        ).pack(pady=(0, 10))

    columns = (
        "Train Number",
        "Train Name",
        "Source",
        "Destination",
        "Passengers"
    )

    tree = ttk.Treeview(
        window,
        columns=columns,
        show="headings"
    )

    for col in columns:
        tree.heading(col, text=col)

    tree.column("Train Number", width=110, anchor="center")
    tree.column("Train Name", width=230)
    tree.column("Source", width=130)
    tree.column("Destination", width=130)
    tree.column("Passengers", width=100, anchor="center")

    tree.pack(fill="both", expand=True, padx=25, pady=10)

    for row in train_rows:
        tree.insert("", "end", values=row)


def add_passenger():
    passenger_id = id_entry.get().strip()
    name = name_entry.get().strip()
    age = age_entry.get().strip()
    gender = gender_var.get().strip()
    train_number = train_entry.get().strip()
    seat = seat_entry.get().strip()

    if not all([passenger_id, name, age, gender, train_number, seat]):
        messagebox.showwarning(
            "Missing Data",
            "Please fill all passenger fields."
        )
        return

    try:
        age = int(age)

        if age <= 0:
            raise ValueError

        conn = connect_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT train_name FROM trains WHERE train_number = ?",
            (train_number,)
        )
        train = cur.fetchone()

        cur.execute("""
            INSERT OR REPLACE INTO passengers
            (passenger_id, name, age, gender, train_number, seat)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            passenger_id,
            name,
            age,
            gender,
            train_number,
            seat
        ))

        conn.commit()
        conn.close()

        for entry in (
            id_entry,
            name_entry,
            age_entry,
            train_entry,
            seat_entry
        ):
            entry.delete(0, tk.END)

        gender_var.set("")

        refresh_table()
        update_dashboard()

        if train:
            messagebox.showinfo(
                "Reservation Added",
                f"Reservation added successfully.\n\n"
                f"Train: {train[0]}\n"
                f"Train Number: {train_number}\n"
                f"Status: Valid"
            )
        else:
            messagebox.showwarning(
                "Reservation Added",
                f"Passenger added, but train number {train_number} "
                f"was not found in the train schedule.\n\n"
                f"Status: Invalid Train"
            )

    except ValueError:
        messagebox.showerror(
            "Invalid Age",
            "Age must be a positive integer."
        )


# ---------------- GUI ----------------

root = tk.Tk()
root.title("Railway Ticket Reservation System")
root.geometry("1250x760")
root.minsize(1050, 650)
root.configure(bg="#eef2f7")

style = ttk.Style()

try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure(
    "Treeview",
    rowheight=30,
    font=("Arial", 9)
)

style.configure(
    "Treeview.Heading",
    font=("Arial", 9, "bold")
)

# Header
header = tk.Frame(root, bg="#17365d", height=90)
header.pack(fill="x")

tk.Label(
    header,
    text="RAILWAY TICKET RESERVATION SYSTEM",
    font=("Arial", 23, "bold"),
    fg="white",
    bg="#17365d"
).pack(pady=(18, 2))

tk.Label(
    header,
    text="CSV + JSON + SQLite + Python",
    font=("Arial", 10),
    fg="white",
    bg="#17365d"
).pack()

# Dashboard
dashboard = tk.Frame(root, bg="#eef2f7")
dashboard.pack(fill="x", padx=20, pady=15)


def card(parent, title):
    frame = tk.Frame(parent, bg="white", bd=1, relief="solid")
    frame.pack(side="left", fill="both", expand=True, padx=5)

    tk.Label(
        frame,
        text=title,
        font=("Arial", 9, "bold"),
        bg="white",
        fg="#475569"
    ).pack(pady=(10, 2))

    value = tk.Label(
        frame,
        text="0",
        font=("Arial", 18, "bold"),
        bg="white",
        fg="#17365d"
    )
    value.pack(pady=(0, 10))

    return value


total_label = card(dashboard, "TOTAL PASSENGERS")
valid_label = card(dashboard, "VALID RESERVATIONS")
invalid_label = card(dashboard, "INVALID TRAIN NUMBERS")
rate_label = card(dashboard, "VERIFICATION RATE")
trains_label = card(dashboard, "AVAILABLE TRAINS")

# Search / filters
search_frame = tk.Frame(root, bg="#eef2f7")
search_frame.pack(fill="x", padx=25, pady=5)

tk.Label(
    search_frame,
    text="Search:",
    font=("Arial", 11, "bold"),
    bg="#eef2f7"
).pack(side="left", padx=(0, 8))

search_var = tk.StringVar()

ttk.Entry(
    search_frame,
    textvariable=search_var,
    width=28
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Search",
    command=search_passengers
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Clear",
    command=clear_search
).pack(side="left", padx=5)

valid_only_var = tk.BooleanVar(value=False)
invalid_only_var = tk.BooleanVar(value=False)

ttk.Checkbutton(
    search_frame,
    text="Valid Only",
    variable=valid_only_var,
    command=lambda: (
        invalid_only_var.set(False),
        refresh_table()
    )
).pack(side="left", padx=8)

ttk.Checkbutton(
    search_frame,
    text="Invalid Only",
    variable=invalid_only_var,
    command=lambda: (
        valid_only_var.set(False),
        refresh_table()
    )
).pack(side="left", padx=8)

ttk.Button(
    search_frame,
    text="Final Report",
    command=show_summary
).pack(side="left", padx=8)

ttk.Button(
    search_frame,
    text="Reload CSV + JSON",
    command=lambda: load_data(True)
).pack(side="left", padx=5)

# Passenger table
table_frame = tk.Frame(root, bg="#eef2f7")
table_frame.pack(fill="both", expand=True, padx=25, pady=10)

columns = (
    "Passenger ID",
    "Name",
    "Age",
    "Gender",
    "Train No.",
    "Train Name",
    "Source",
    "Destination",
    "Departure",
    "Arrival",
    "Seat",
    "Status"
)

passenger_tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

for col in columns:
    passenger_tree.heading(col, text=col)

widths = {
    "Passenger ID": 90,
    "Name": 150,
    "Age": 55,
    "Gender": 65,
    "Train No.": 80,
    "Train Name": 180,
    "Source": 100,
    "Destination": 110,
    "Departure": 75,
    "Arrival": 75,
    "Seat": 75,
    "Status": 100
}

for col, width in widths.items():
    passenger_tree.column(col, width=width, anchor="center")

scrollbar_y = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=passenger_tree.yview
)

scrollbar_x = ttk.Scrollbar(
    table_frame,
    orient="horizontal",
    command=passenger_tree.xview
)

passenger_tree.configure(
    yscrollcommand=scrollbar_y.set,
    xscrollcommand=scrollbar_x.set
)

passenger_tree.pack(side="top", fill="both", expand=True)
scrollbar_y.pack(side="right", fill="y")
scrollbar_x.pack(side="bottom", fill="x")

passenger_tree.bind("<Double-1>", show_selected_passenger)

# Add passenger section
add_frame = tk.LabelFrame(
    root,
    text="Add Passenger Reservation",
    font=("Arial", 11, "bold"),
    bg="#eef2f7",
    padx=8,
    pady=8
)
add_frame.pack(fill="x", padx=25, pady=(0, 10))

tk.Label(add_frame, text="ID", bg="#eef2f7").pack(side="left", padx=3)
id_entry = ttk.Entry(add_frame, width=10)
id_entry.pack(side="left", padx=3)

tk.Label(add_frame, text="Name", bg="#eef2f7").pack(side="left", padx=3)
name_entry = ttk.Entry(add_frame, width=17)
name_entry.pack(side="left", padx=3)

tk.Label(add_frame, text="Age", bg="#eef2f7").pack(side="left", padx=3)
age_entry = ttk.Entry(add_frame, width=6)
age_entry.pack(side="left", padx=3)

tk.Label(add_frame, text="Gender", bg="#eef2f7").pack(side="left", padx=3)
gender_var = tk.StringVar()

gender_combo = ttk.Combobox(
    add_frame,
    textvariable=gender_var,
    values=["M", "F", "Other"],
    width=8,
    state="readonly"
)
gender_combo.pack(side="left", padx=3)

tk.Label(add_frame, text="Train No.", bg="#eef2f7").pack(side="left", padx=3)
train_entry = ttk.Entry(add_frame, width=10)
train_entry.pack(side="left", padx=3)

tk.Label(add_frame, text="Seat", bg="#eef2f7").pack(side="left", padx=3)
seat_entry = ttk.Entry(add_frame, width=10)
seat_entry.pack(side="left", padx=3)

ttk.Button(
    add_frame,
    text="Add Reservation",
    command=add_passenger
).pack(side="left", padx=10)

# Footer
tk.Label(
    root,
    text="Double-click a passenger to view complete reservation details",
    bg="#eef2f7",
    fg="#64748b",
    font=("Arial", 9)
).pack(pady=(0, 8))

# Start application
try:
    create_database()
    import_passengers()
    import_trains()
    refresh_table()
    update_dashboard()
except Exception as e:
    messagebox.showerror(
        "Startup Error",
        "Could not load the application data.\n\n" + str(e)
    )

root.mainloop()
