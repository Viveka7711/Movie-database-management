import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "insurance_claims.db"
CSV_FILE = BASE_DIR / "customers.csv"
XML_FILE = BASE_DIR / "claims.xml"


def connect_db():
    return sqlite3.connect(DB_FILE)


def create_database():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            policy_number TEXT,
            policy_type TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            claim_type TEXT,
            amount REAL,
            claim_date TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


def import_customers():
    conn = connect_db()
    cur = conn.cursor()

    with open(CSV_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cur.execute("""
                INSERT OR REPLACE INTO customers
                (customer_id, name, age, policy_number, policy_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["customer_id"],
                row["name"],
                int(row["age"]),
                row["policy_number"],
                row["policy_type"]
            ))

    conn.commit()
    conn.close()


def import_claims():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM claims")

    for claim in root.findall("claim"):
        claim_id = claim.findtext("claim_id", "")
        customer_id = claim.findtext("customer_id", "")
        claim_type = claim.findtext("claim_type", "")
        amount = float(claim.findtext("amount", "0"))
        claim_date = claim.findtext("date", "")
        status = claim.findtext("status", "")

        cur.execute("""
            INSERT OR REPLACE INTO claims
            (claim_id, customer_id, claim_type, amount, claim_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            claim_id,
            customer_id,
            claim_type,
            amount,
            claim_date,
            status
        ))

    conn.commit()
    conn.close()


def load_data(show_message=True):
    try:
        import_customers()
        import_claims()
        refresh_table()
        update_dashboard()

        if show_message:
            messagebox.showinfo(
                "Data Loaded",
                "Customer CSV and claim XML data were successfully integrated."
            )
    except Exception as e:
        messagebox.showerror("Import Error", str(e))


def get_report(search_text="", incomplete_only=False, complete_only=False):
    conn = connect_db()
    cur = conn.cursor()

    query = """
        SELECT
            c.claim_id,
            c.customer_id,
            COALESCE(cu.name, 'Not Found') AS customer_name,
            COALESCE(cu.policy_number, '-') AS policy_number,
            COALESCE(cu.policy_type, '-') AS policy_type,
            c.claim_type,
            c.amount,
            c.claim_date,
            c.status,
            CASE
                WHEN cu.customer_id IS NULL THEN 'Incomplete'
                ELSE 'Complete'
            END AS claim_status
        FROM claims c
        LEFT JOIN customers cu
            ON c.customer_id = cu.customer_id
    """

    conditions = []
    params = []

    if search_text.strip():
        conditions.append("""
            (
                c.claim_id LIKE ?
                OR c.customer_id LIKE ?
                OR cu.name LIKE ?
                OR c.claim_type LIKE ?
            )
        """)
        keyword = "%" + search_text.strip() + "%"
        params.extend([keyword, keyword, keyword, keyword])

    if incomplete_only:
        conditions.append("cu.customer_id IS NULL")

    if complete_only:
        conditions.append("cu.customer_id IS NOT NULL")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY c.claim_id"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return rows


def refresh_table():
    for item in claim_tree.get_children():
        claim_tree.delete(item)

    rows = get_report(
        search_var.get(),
        incomplete_only_var.get(),
        complete_only_var.get()
    )

    for row in rows:
        display_row = list(row)
        display_row[6] = f"₹{row[6]:,.2f}"
        claim_tree.insert("", "end", values=display_row)


def update_dashboard():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM claims")
    total_claims = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM claims c
        INNER JOIN customers cu
        ON c.customer_id = cu.customer_id
    """)
    complete_claims = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM claims c
        LEFT JOIN customers cu
        ON c.customer_id = cu.customer_id
        WHERE cu.customer_id IS NULL
    """)
    incomplete_claims = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM claims")
    total_amount = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(c.amount), 0)
        FROM claims c
        LEFT JOIN customers cu
        ON c.customer_id = cu.customer_id
        WHERE cu.customer_id IS NULL
    """)
    incomplete_amount = cur.fetchone()[0]

    conn.close()

    completion_rate = (
        complete_claims / total_claims * 100
        if total_claims else 0
    )

    total_claims_label.config(text=str(total_claims))
    complete_label.config(text=str(complete_claims))
    incomplete_label.config(text=str(incomplete_claims))
    rate_label.config(text=f"{completion_rate:.2f}%")
    total_amount_label.config(text=f"₹{total_amount:,.0f}")
    incomplete_amount_label.config(text=f"₹{incomplete_amount:,.0f}")


def search_claims():
    refresh_table()


def clear_search():
    search_var.set("")
    incomplete_only_var.set(False)
    complete_only_var.set(False)
    refresh_table()


def show_incomplete_only():
    complete_only_var.set(False)
    incomplete_only_var.set(True)
    refresh_table()


def show_complete_only():
    incomplete_only_var.set(False)
    complete_only_var.set(True)
    refresh_table()


def show_selected_claim(event=None):
    selected = claim_tree.selection()

    if not selected:
        return

    values = claim_tree.item(selected[0], "values")

    details = (
        f"Claim ID: {values[0]}\n"
        f"Customer ID: {values[1]}\n"
        f"Customer Name: {values[2]}\n"
        f"Policy Number: {values[3]}\n"
        f"Policy Type: {values[4]}\n"
        f"Claim Type: {values[5]}\n"
        f"Amount: {values[6]}\n"
        f"Claim Date: {values[7]}\n"
        f"Claim Status: {values[8]}\n"
        f"Data Status: {values[9]}"
    )

    messagebox.showinfo("Claim Details", details)


def show_incomplete_report():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.claim_id,
            c.customer_id,
            c.claim_type,
            c.amount,
            c.claim_date,
            c.status
        FROM claims c
        LEFT JOIN customers cu
            ON c.customer_id = cu.customer_id
        WHERE cu.customer_id IS NULL
        ORDER BY c.claim_id
    """)

    rows = cur.fetchall()
    conn.close()

    window = tk.Toplevel(root)
    window.title("Incomplete Claims Report")
    window.geometry("850x500")
    window.configure(bg="#f4f7fb")

    tk.Label(
        window,
        text="INCOMPLETE CLAIMS REPORT",
        font=("Arial", 20, "bold"),
        bg="#f4f7fb"
    ).pack(pady=15)

    if not rows:
        tk.Label(
            window,
            text="No incomplete claims found.",
            font=("Arial", 13),
            bg="#f4f7fb"
        ).pack(pady=30)
        return

    total_incomplete = sum(row[3] for row in rows)

    tk.Label(
        window,
        text=f"Incomplete Claims: {len(rows)}    |    "
             f"Total Amount: ₹{total_incomplete:,.2f}",
        font=("Arial", 11, "bold"),
        bg="#f4f7fb"
    ).pack(pady=(0, 10))

    columns = (
        "Claim ID",
        "Customer ID",
        "Claim Type",
        "Amount",
        "Date",
        "Claim Status"
    )

    tree = ttk.Treeview(
        window,
        columns=columns,
        show="headings"
    )

    for col in columns:
        tree.heading(col, text=col)

    tree.column("Claim ID", width=100, anchor="center")
    tree.column("Customer ID", width=120, anchor="center")
    tree.column("Claim Type", width=220)
    tree.column("Amount", width=130, anchor="center")
    tree.column("Date", width=120, anchor="center")
    tree.column("Claim Status", width=120, anchor="center")

    tree.pack(fill="both", expand=True, padx=25, pady=10)

    for row in rows:
        tree.insert(
            "",
            "end",
            values=(
                row[0],
                row[1],
                row[2],
                f"₹{row[3]:,.2f}",
                row[4],
                row[5]
            )
        )


def show_summary():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            claim_type,
            COUNT(*),
            COALESCE(SUM(amount), 0),
            COALESCE(AVG(amount), 0)
        FROM claims
        GROUP BY claim_type
        ORDER BY COUNT(*) DESC
    """)
    claim_type_rows = cur.fetchall()

    cur.execute("""
        SELECT
            status,
            COUNT(*),
            COALESCE(SUM(amount), 0)
        FROM claims
        GROUP BY status
        ORDER BY COUNT(*) DESC
    """)
    status_rows = cur.fetchall()

    conn.close()

    window = tk.Toplevel(root)
    window.title("Insurance Claim Summary")
    window.geometry("900x650")
    window.configure(bg="#f4f7fb")

    tk.Label(
        window,
        text="INSURANCE CLAIM SUMMARY",
        font=("Arial", 20, "bold"),
        bg="#f4f7fb"
    ).pack(pady=15)

    tk.Label(
        window,
        text="Claim Type Summary",
        font=("Arial", 13, "bold"),
        bg="#f4f7fb"
    ).pack(anchor="w", padx=25)

    columns = (
        "Claim Type",
        "Claims",
        "Total Amount",
        "Average Amount"
    )

    type_tree = ttk.Treeview(
        window,
        columns=columns,
        show="headings",
        height=8
    )

    for col in columns:
        type_tree.heading(col, text=col)

    type_tree.column("Claim Type", width=300)
    type_tree.column("Claims", width=100, anchor="center")
    type_tree.column("Total Amount", width=160, anchor="center")
    type_tree.column("Average Amount", width=160, anchor="center")

    type_tree.pack(fill="x", padx=25, pady=10)

    for row in claim_type_rows:
        type_tree.insert(
            "",
            "end",
            values=(
                row[0],
                row[1],
                f"₹{row[2]:,.2f}",
                f"₹{row[3]:,.2f}"
            )
        )

    tk.Label(
        window,
        text="Claim Status Summary",
        font=("Arial", 13, "bold"),
        bg="#f4f7fb"
    ).pack(anchor="w", padx=25, pady=(15, 0))

    status_columns = ("Status", "Claims", "Total Amount")

    status_tree = ttk.Treeview(
        window,
        columns=status_columns,
        show="headings",
        height=6
    )

    for col in status_columns:
        status_tree.heading(col, text=col)

    status_tree.column("Status", width=250)
    status_tree.column("Claims", width=150, anchor="center")
    status_tree.column("Total Amount", width=200, anchor="center")

    status_tree.pack(fill="x", padx=25, pady=10)

    for row in status_rows:
        status_tree.insert(
            "",
            "end",
            values=(row[0], row[1], f"₹{row[2]:,.2f}")
        )


def add_claim():
    claim_id = claim_id_entry.get().strip()
    customer_id = customer_id_entry.get().strip()
    claim_type = claim_type_entry.get().strip()
    amount = amount_entry.get().strip()
    claim_date = date_entry.get().strip()
    status = status_var.get().strip()

    if not all([
        claim_id,
        customer_id,
        claim_type,
        amount,
        claim_date,
        status
    ]):
        messagebox.showwarning(
            "Missing Data",
            "Please fill all claim fields."
        )
        return

    try:
        amount = float(amount)

        if amount <= 0:
            raise ValueError

        conn = connect_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT name FROM customers WHERE customer_id = ?",
            (customer_id,)
        )
        customer = cur.fetchone()

        cur.execute("""
            INSERT OR REPLACE INTO claims
            (claim_id, customer_id, claim_type, amount, claim_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            claim_id,
            customer_id,
            claim_type,
            amount,
            claim_date,
            status
        ))

        conn.commit()
        conn.close()

        for entry in (
            claim_id_entry,
            customer_id_entry,
            claim_type_entry,
            amount_entry,
            date_entry
        ):
            entry.delete(0, tk.END)

        status_var.set("Pending")

        refresh_table()
        update_dashboard()

        if customer:
            messagebox.showinfo(
                "Claim Added",
                f"Claim added successfully.\n\n"
                f"Customer: {customer[0]}\n"
                f"Status: Complete"
            )
        else:
            messagebox.showwarning(
                "Incomplete Claim",
                f"Claim added, but customer ID {customer_id} "
                f"was not found.\n\n"
                f"Data Status: Incomplete"
            )

    except ValueError:
        messagebox.showerror(
            "Invalid Amount",
            "Claim amount must be a positive number."
        )


# ---------------- GUI ----------------

root = tk.Tk()
root.title("Insurance Claim Processing System")
root.geometry("1250x780")
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
    text="INSURANCE CLAIM PROCESSING SYSTEM",
    font=("Arial", 23, "bold"),
    fg="white",
    bg="#17365d"
).pack(pady=(18, 2))

tk.Label(
    header,
    text="CSV + XML + SQLite + Python",
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


total_claims_label = create_card(dashboard, "TOTAL CLAIMS")
complete_label = create_card(dashboard, "COMPLETE CLAIMS")
incomplete_label = create_card(dashboard, "INCOMPLETE CLAIMS")
rate_label = create_card(dashboard, "COMPLETION RATE")
total_amount_label = create_card(dashboard, "TOTAL CLAIM AMOUNT")
incomplete_amount_label = create_card(dashboard, "INCOMPLETE AMOUNT")

# Search/filter bar
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
    command=search_claims
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Clear",
    command=clear_search
).pack(side="left", padx=5)

incomplete_only_var = tk.BooleanVar(value=False)
complete_only_var = tk.BooleanVar(value=False)

ttk.Checkbutton(
    search_frame,
    text="Incomplete Only",
    variable=incomplete_only_var,
    command=lambda: (
        complete_only_var.set(False),
        refresh_table()
    )
).pack(side="left", padx=8)

ttk.Checkbutton(
    search_frame,
    text="Complete Only",
    variable=complete_only_var,
    command=lambda: (
        incomplete_only_var.set(False),
        refresh_table()
    )
).pack(side="left", padx=8)

ttk.Button(
    search_frame,
    text="Incomplete Report",
    command=show_incomplete_report
).pack(side="left", padx=8)

ttk.Button(
    search_frame,
    text="Summary",
    command=show_summary
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Reload CSV + XML",
    command=lambda: load_data(True)
).pack(side="left", padx=5)

# Main table
table_frame = tk.Frame(root, bg="#eef2f7")
table_frame.pack(fill="both", expand=True, padx=25, pady=10)

columns = (
    "Claim ID",
    "Customer ID",
    "Customer Name",
    "Policy No.",
    "Policy Type",
    "Claim Type",
    "Amount",
    "Date",
    "Status",
    "Data Status"
)

claim_tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

for col in columns:
    claim_tree.heading(col, text=col)

widths = {
    "Claim ID": 80,
    "Customer ID": 90,
    "Customer Name": 150,
    "Policy No.": 100,
    "Policy Type": 100,
    "Claim Type": 170,
    "Amount": 110,
    "Date": 100,
    "Status": 100,
    "Data Status": 110
}

for col, width in widths.items():
    claim_tree.column(col, width=width, anchor="center")

scrollbar_y = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=claim_tree.yview
)

scrollbar_x = ttk.Scrollbar(
    table_frame,
    orient="horizontal",
    command=claim_tree.xview
)

claim_tree.configure(
    yscrollcommand=scrollbar_y.set,
    xscrollcommand=scrollbar_x.set
)

claim_tree.pack(side="top", fill="both", expand=True)
scrollbar_y.pack(side="right", fill="y")
scrollbar_x.pack(side="bottom", fill="x")

claim_tree.bind("<Double-1>", show_selected_claim)

# Add claim section
add_frame = tk.LabelFrame(
    root,
    text="Add / Update Insurance Claim",
    font=("Arial", 11, "bold"),
    bg="#eef2f7",
    padx=8,
    pady=8
)
add_frame.pack(fill="x", padx=25, pady=(0, 10))

tk.Label(add_frame, text="Claim ID", bg="#eef2f7").pack(side="left", padx=3)
claim_id_entry = ttk.Entry(add_frame, width=10)
claim_id_entry.pack(side="left", padx=3)

tk.Label(add_frame, text="Customer ID", bg="#eef2f7").pack(side="left", padx=3)
customer_id_entry = ttk.Entry(add_frame, width=11)
customer_id_entry.pack(side="left", padx=3)

tk.Label(add_frame, text="Claim Type", bg="#eef2f7").pack(side="left", padx=3)
claim_type_entry = ttk.Entry(add_frame, width=18)
claim_type_entry.pack(side="left", padx=3)

tk.Label(add_frame, text="Amount", bg="#eef2f7").pack(side="left", padx=3)
amount_entry = ttk.Entry(add_frame, width=11)
amount_entry.pack(side="left", padx=3)

tk.Label(add_frame, text="Date", bg="#eef2f7").pack(side="left", padx=3)
date_entry = ttk.Entry(add_frame, width=12)
date_entry.pack(side="left", padx=3)

tk.Label(add_frame, text="Status", bg="#eef2f7").pack(side="left", padx=3)
status_var = tk.StringVar(value="Pending")

status_combo = ttk.Combobox(
    add_frame,
    textvariable=status_var,
    values=["Pending", "Approved", "Rejected"],
    width=10,
    state="readonly"
)
status_combo.pack(side="left", padx=3)

ttk.Button(
    add_frame,
    text="Add Claim",
    command=add_claim
).pack(side="left", padx=10)

# Footer
tk.Label(
    root,
    text="Double-click a claim to view complete claim details",
    bg="#eef2f7",
    fg="#64748b",
    font=("Arial", 9)
).pack(pady=(0, 8))

# Start
try:
    create_database()
    import_customers()
    import_claims()
    refresh_table()
    update_dashboard()
except Exception as e:
    messagebox.showerror(
        "Startup Error",
        "Could not load the application data.\n\n" + str(e)
    )

root.mainloop()
