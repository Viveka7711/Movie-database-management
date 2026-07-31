import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "university_placement.db"
CSV_FILE = BASE_DIR / "students.csv"
JSON_FILE = BASE_DIR / "placements.json"


def connect_db():
    return sqlite3.connect(DB_FILE)


def create_database():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            year INTEGER,
            email TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS placements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            company TEXT NOT NULL,
            package REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        )
    """)

    conn.commit()
    conn.close()


def import_students():
    conn = connect_db()
    cur = conn.cursor()

    with open(CSV_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cur.execute("""
                INSERT OR REPLACE INTO students
                (student_id, name, department, year, email)
                VALUES (?, ?, ?, ?, ?)
            """, (
                int(row["student_id"]),
                row["name"],
                row["department"],
                int(row["year"]),
                row["email"]
            ))

    conn.commit()
    conn.close()


def import_placements():
    with open(JSON_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    conn = connect_db()
    cur = conn.cursor()

    # Prevent duplicate records when reloading the JSON file.
    cur.execute("DELETE FROM placements")

    for item in data["placements"]:
        cur.execute("""
            INSERT INTO placements
            (student_id, company, package, status)
            VALUES (?, ?, ?, ?)
        """, (
            int(item["student_id"]),
            item["company"],
            float(item["package"]),
            item["status"]
        ))

    conn.commit()
    conn.close()


def load_data():
    try:
        import_students()
        import_placements()
        refresh_table()
        update_dashboard()
        messagebox.showinfo(
            "Data Loaded",
            "Student CSV and placement JSON data were successfully integrated."
        )
    except Exception as e:
        messagebox.showerror("Import Error", str(e))


def get_report(search_text="", placed_only=False):
    conn = connect_db()
    cur = conn.cursor()

    query = """
        SELECT
            s.student_id,
            s.name,
            s.department,
            s.year,
            COALESCE(p.company, 'Not Placed') AS company,
            COALESCE(p.package, 0) AS package,
            COALESCE(p.status, 'Not Placed') AS status
        FROM students s
        LEFT JOIN placements p
            ON s.student_id = p.student_id
    """

    conditions = []
    params = []

    if search_text.strip():
        conditions.append(
            "(s.name LIKE ? OR s.department LIKE ? OR p.company LIKE ?)"
        )
        keyword = "%" + search_text.strip() + "%"
        params.extend([keyword, keyword, keyword])

    if placed_only:
        conditions.append("p.status = 'Placed'")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += """
        ORDER BY
            CASE WHEN p.status = 'Placed' THEN 0 ELSE 1 END,
            p.package DESC,
            s.name ASC
    """

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return rows


def refresh_table():
    for item in student_tree.get_children():
        student_tree.delete(item)

    rows = get_report(search_var.get(), placed_only_var.get())

    for row in rows:
        package_display = f"₹{row[5]:.2f} LPA" if row[6] == "Placed" else "-"
        student_tree.insert(
            "",
            "end",
            values=(row[0], row[1], row[2], row[3], row[4], package_display, row[6])
        )


def search_students():
    refresh_table()


def clear_search():
    search_var.set("")
    placed_only_var.set(False)
    refresh_table()


def show_placed_only():
    placed_only_var.set(True)
    refresh_table()


def update_dashboard():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(DISTINCT student_id)
        FROM placements
        WHERE status = 'Placed'
    """)
    placed_students = cur.fetchone()[0]

    cur.execute("""
        SELECT AVG(package)
        FROM placements
        WHERE status = 'Placed'
    """)
    average_package = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT MAX(package)
        FROM placements
        WHERE status = 'Placed'
    """)
    highest_package = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT company, COUNT(*)
        FROM placements
        WHERE status = 'Placed'
        GROUP BY company
        ORDER BY COUNT(*) DESC, company ASC
        LIMIT 1
    """)
    top_company = cur.fetchone()

    conn.close()

    not_placed = total_students - placed_students
    percentage = (placed_students / total_students * 100) if total_students else 0

    total_students_label.config(text=str(total_students))
    placed_label.config(text=str(placed_students))
    percentage_label.config(text=f"{percentage:.2f}%")
    average_label.config(text=f"₹{average_package:.2f} LPA")
    highest_label.config(text=f"₹{highest_package:.2f} LPA")

    if top_company:
        top_company_label.config(text=f"{top_company[0]} ({top_company[1]})")
    else:
        top_company_label.config(text="No offers")


def show_summary():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT company, COUNT(*), ROUND(AVG(package), 2)
        FROM placements
        WHERE status = 'Placed'
        GROUP BY company
        ORDER BY COUNT(*) DESC, company ASC
    """)
    company_rows = cur.fetchall()

    cur.execute("""
        SELECT
            s.department,
            COUNT(DISTINCT s.student_id) AS total,
            COUNT(DISTINCT CASE WHEN p.status = 'Placed'
                                THEN s.student_id END) AS placed
        FROM students s
        LEFT JOIN placements p ON s.student_id = p.student_id
        GROUP BY s.department
        ORDER BY s.department
    """)
    department_rows = cur.fetchall()

    conn.close()

    window = tk.Toplevel(root)
    window.title("Placement Summary")
    window.geometry("850x600")
    window.configure(bg="#f4f7fb")

    tk.Label(
        window,
        text="PLACEMENT SUMMARY",
        font=("Arial", 20, "bold"),
        bg="#f4f7fb"
    ).pack(pady=15)

    tk.Label(
        window,
        text="Company-wise Offers",
        font=("Arial", 13, "bold"),
        bg="#f4f7fb"
    ).pack(anchor="w", padx=25)

    company_tree = ttk.Treeview(
        window,
        columns=("Company", "Offers", "Average Package"),
        show="headings",
        height=8
    )

    for col in ("Company", "Offers", "Average Package"):
        company_tree.heading(col, text=col)

    company_tree.column("Company", width=300)
    company_tree.column("Offers", width=120, anchor="center")
    company_tree.column("Average Package", width=180, anchor="center")

    company_tree.pack(fill="x", padx=25, pady=8)

    for row in company_rows:
        company_tree.insert(
            "",
            "end",
            values=(row[0], row[1], f"₹{row[2]:.2f} LPA")
        )

    tk.Label(
        window,
        text="Department-wise Placement",
        font=("Arial", 13, "bold"),
        bg="#f4f7fb"
    ).pack(anchor="w", padx=25, pady=(15, 0))

    dept_tree = ttk.Treeview(
        window,
        columns=("Department", "Total Students", "Placed", "Percentage"),
        show="headings",
        height=8
    )

    for col in ("Department", "Total Students", "Placed", "Percentage"):
        dept_tree.heading(col, text=col)

    dept_tree.column("Department", width=180)
    dept_tree.column("Total Students", width=150, anchor="center")
    dept_tree.column("Placed", width=120, anchor="center")
    dept_tree.column("Percentage", width=140, anchor="center")

    dept_tree.pack(fill="x", padx=25, pady=8)

    for department, total, placed in department_rows:
        percent = placed / total * 100 if total else 0
        dept_tree.insert(
            "",
            "end",
            values=(department, total, placed, f"{percent:.2f}%")
        )


def show_selected_student(event=None):
    selected = student_tree.selection()

    if not selected:
        return

    values = student_tree.item(selected[0], "values")

    details = (
        f"Student ID: {values[0]}\n"
        f"Name: {values[1]}\n"
        f"Department: {values[2]}\n"
        f"Year: {values[3]}\n"
        f"Company: {values[4]}\n"
        f"Package: {values[5]}\n"
        f"Status: {values[6]}"
    )

    messagebox.showinfo("Student Details", details)


def add_placement():
    student_id = placement_id_entry.get().strip()
    company = company_entry.get().strip()
    package = package_entry.get().strip()

    if not student_id or not company or not package:
        messagebox.showwarning(
            "Missing Data",
            "Please enter Student ID, Company and Package."
        )
        return

    try:
        student_id = int(student_id)
        package = float(package)

        if package <= 0:
            raise ValueError

        conn = connect_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT name FROM students WHERE student_id = ?",
            (student_id,)
        )
        student = cur.fetchone()

        if not student:
            conn.close()
            messagebox.showerror(
                "Invalid Student",
                "Student ID does not exist."
            )
            return

        cur.execute(
            "DELETE FROM placements WHERE student_id = ?",
            (student_id,)
        )

        cur.execute("""
            INSERT INTO placements
            (student_id, company, package, status)
            VALUES (?, ?, ?, 'Placed')
        """, (student_id, company, package))

        conn.commit()
        conn.close()

        placement_id_entry.delete(0, tk.END)
        company_entry.delete(0, tk.END)
        package_entry.delete(0, tk.END)

        refresh_table()
        update_dashboard()

        messagebox.showinfo(
            "Success",
            f"Placement added for {student[0]}."
        )

    except ValueError:
        messagebox.showerror(
            "Invalid Input",
            "Student ID must be an integer and package must be a positive number."
        )


# -------------------- GUI --------------------

root = tk.Tk()
root.title("University Placement Management System")
root.geometry("1150x750")
root.minsize(1000, 650)
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
header = tk.Frame(root, bg="#17365d", height=90)
header.pack(fill="x")

tk.Label(
    header,
    text="UNIVERSITY PLACEMENT MANAGEMENT SYSTEM",
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


def create_card(parent, title):
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


total_students_label = create_card(dashboard, "TOTAL STUDENTS")
placed_label = create_card(dashboard, "STUDENTS PLACED")
percentage_label = create_card(dashboard, "PLACEMENT PERCENTAGE")
average_label = create_card(dashboard, "AVERAGE PACKAGE")
highest_label = create_card(dashboard, "HIGHEST PACKAGE")
top_company_label = create_card(dashboard, "TOP COMPANY")

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
    width=30
)
search_entry.pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Search",
    command=search_students
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Clear",
    command=clear_search
).pack(side="left", padx=5)

placed_only_var = tk.BooleanVar(value=False)

ttk.Checkbutton(
    search_frame,
    text="Placed Students Only",
    variable=placed_only_var,
    command=refresh_table
).pack(side="left", padx=10)

ttk.Button(
    search_frame,
    text="Placement Summary",
    command=show_summary
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Reload CSV + JSON",
    command=load_data
).pack(side="left", padx=5)

# Main table
table_frame = tk.Frame(root, bg="#eef2f7")
table_frame.pack(fill="both", expand=True, padx=25, pady=10)

columns = (
    "Student ID",
    "Name",
    "Department",
    "Year",
    "Company",
    "Package",
    "Status"
)

student_tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

for col in columns:
    student_tree.heading(col, text=col)

student_tree.column("Student ID", width=80, anchor="center")
student_tree.column("Name", width=190)
student_tree.column("Department", width=120)
student_tree.column("Year", width=70, anchor="center")
student_tree.column("Company", width=170)
student_tree.column("Package", width=120, anchor="center")
student_tree.column("Status", width=110, anchor="center")

scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=student_tree.yview
)

student_tree.configure(yscrollcommand=scrollbar.set)

student_tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

student_tree.bind("<Double-1>", show_selected_student)

# Add placement section
add_frame = tk.LabelFrame(
    root,
    text="Add / Update Placement Offer",
    font=("Arial", 11, "bold"),
    bg="#eef2f7",
    padx=10,
    pady=10
)
add_frame.pack(fill="x", padx=25, pady=(0, 10))

tk.Label(
    add_frame,
    text="Student ID",
    bg="#eef2f7"
).pack(side="left", padx=5)

placement_id_entry = ttk.Entry(add_frame, width=10)
placement_id_entry.pack(side="left", padx=5)

tk.Label(
    add_frame,
    text="Company",
    bg="#eef2f7"
).pack(side="left", padx=5)

company_entry = ttk.Entry(add_frame, width=20)
company_entry.pack(side="left", padx=5)

tk.Label(
    add_frame,
    text="Package (LPA)",
    bg="#eef2f7"
).pack(side="left", padx=5)

package_entry = ttk.Entry(add_frame, width=12)
package_entry.pack(side="left", padx=5)

ttk.Button(
    add_frame,
    text="Add Placement",
    command=add_placement
).pack(side="left", padx=10)

# Footer
tk.Label(
    root,
    text="Double-click a student to view placement details",
    bg="#eef2f7",
    fg="#64748b",
    font=("Arial", 9)
).pack(pady=(0, 8))

# Start
try:
    create_database()
    import_students()
    import_placements()
    refresh_table()
    update_dashboard()
except Exception as e:
    messagebox.showerror(
        "Startup Error",
        "Could not load the application data.\n\n" + str(e)
    )

root.mainloop()
