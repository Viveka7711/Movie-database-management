import tkinter as tk
from tkinter import ttk, messagebox
import json
import csv
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent
PRODUCTS_FILE = BASE_DIR / "products.json"
SALES_FILE = BASE_DIR / "sales.csv"
OUTPUT_FILE = BASE_DIR / "total_sales_report.csv"


def load_data():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as file:
        product_data = json.load(file)

    products = pd.DataFrame(product_data["products"])
    sales = pd.read_csv(SALES_FILE)

    sales["quantity"] = pd.to_numeric(sales["quantity"], errors="coerce").fillna(0)

    quantity_summary = (
        sales.groupby("product_id", as_index=False)["quantity"]
        .sum()
        .rename(columns={"quantity": "total_quantity_sold"})
    )

    final_report = products.merge(
        quantity_summary,
        on="product_id",
        how="left"
    )

    final_report["total_quantity_sold"] = (
        final_report["total_quantity_sold"]
        .fillna(0)
        .astype(int)
    )

    final_report["total_sales_value"] = (
        final_report["price"] * final_report["total_quantity_sold"]
    )

    final_report = final_report[
        [
            "product_id",
            "product_name",
            "brand",
            "category",
            "price",
            "total_quantity_sold",
            "total_sales_value"
        ]
    ]

    final_report.to_csv(OUTPUT_FILE, index=False)

    return products, sales, final_report


def refresh_table():
    try:
        products, sales, report = load_data()

        for item in report_tree.get_children():
            report_tree.delete(item)

        for _, row in report.iterrows():
            report_tree.insert(
                "",
                "end",
                values=(
                    row["product_id"],
                    row["product_name"],
                    row["brand"],
                    row["category"],
                    f"₹{row['price']:,.2f}",
                    int(row["total_quantity_sold"]),
                    f"₹{row['total_sales_value']:,.2f}"
                )
            )

        total_products_label.config(text=str(len(products)))
        total_transactions_label.config(text=str(len(sales)))
        total_units_label.config(
            text=str(int(report["total_quantity_sold"].sum()))
        )
        total_value_label.config(
            text=f"₹{report['total_sales_value'].sum():,.0f}"
        )

    except Exception as e:
        messagebox.showerror("Error", str(e))


def save_report():
    try:
        load_data()
        messagebox.showinfo(
            "Report Saved",
            f"The final report was saved as:\n\n{OUTPUT_FILE.name}"
        )
    except Exception as e:
        messagebox.showerror("Error", str(e))


def search_products():
    search_text = search_var.get().strip().lower()

    try:
        _, _, report = load_data()

        if search_text:
            report = report[
                report["product_id"].astype(str).str.lower().str.contains(
                    search_text
                )
                | report["product_name"].astype(str).str.lower().str.contains(
                    search_text
                )
                | report["brand"].astype(str).str.lower().str.contains(
                    search_text
                )
                | report["category"].astype(str).str.lower().str.contains(
                    search_text
                )
            ]

        for item in report_tree.get_children():
            report_tree.delete(item)

        for _, row in report.iterrows():
            report_tree.insert(
                "",
                "end",
                values=(
                    row["product_id"],
                    row["product_name"],
                    row["brand"],
                    row["category"],
                    f"₹{row['price']:,.2f}",
                    int(row["total_quantity_sold"]),
                    f"₹{row['total_sales_value']:,.2f}"
                )
            )

    except Exception as e:
        messagebox.showerror("Search Error", str(e))


def clear_search():
    search_var.set("")
    refresh_table()


def show_product_details(event=None):
    selected = report_tree.selection()

    if not selected:
        return

    values = report_tree.item(selected[0], "values")

    details = (
        f"Product ID: {values[0]}\n"
        f"Product Name: {values[1]}\n"
        f"Brand: {values[2]}\n"
        f"Category: {values[3]}\n"
        f"Price: {values[4]}\n"
        f"Total Quantity Sold: {values[5]}\n"
        f"Total Sales Value: {values[6]}"
    )

    messagebox.showinfo("Product Sales Details", details)


def show_top_products():
    try:
        _, _, report = load_data()

        top = report.sort_values(
            "total_quantity_sold",
            ascending=False
        ).head(5)

        window = tk.Toplevel(root)
        window.title("Top Selling Products")
        window.geometry("700x450")
        window.configure(bg="#f4f7fb")

        tk.Label(
            window,
            text="TOP SELLING PRODUCTS",
            font=("Arial", 19, "bold"),
            bg="#f4f7fb"
        ).pack(pady=15)

        columns = (
            "Rank",
            "Product",
            "Brand",
            "Quantity Sold"
        )

        tree = ttk.Treeview(
            window,
            columns=columns,
            show="headings"
        )

        for col in columns:
            tree.heading(col, text=col)

        tree.column("Rank", width=70, anchor="center")
        tree.column("Product", width=250)
        tree.column("Brand", width=150)
        tree.column("Quantity Sold", width=130, anchor="center")

        tree.pack(fill="both", expand=True, padx=25, pady=10)

        for rank, (_, row) in enumerate(top.iterrows(), start=1):
            tree.insert(
                "",
                "end",
                values=(
                    rank,
                    row["product_name"],
                    row["brand"],
                    int(row["total_quantity_sold"])
                )
            )

    except Exception as e:
        messagebox.showerror("Error", str(e))


# ---------------- GUI ----------------

root = tk.Tk()
root.title("Mobile Retail Sales Management System")
root.geometry("1150x720")
root.minsize(1000, 650)
root.configure(bg="#eef2f7")

style = ttk.Style()

try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure(
    "Treeview",
    rowheight=32,
    font=("Arial", 10)
)

style.configure(
    "Treeview.Heading",
    font=("Arial", 10, "bold")
)

# Header
header = tk.Frame(root, bg="#17365d", height=95)
header.pack(fill="x")

tk.Label(
    header,
    text="MOBILE RETAIL SALES MANAGEMENT",
    font=("Arial", 23, "bold"),
    fg="white",
    bg="#17365d"
).pack(pady=(20, 3))

tk.Label(
    header,
    text="JSON + CSV + Pandas + Python",
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


total_products_label = create_card(
    dashboard,
    "TOTAL PRODUCTS"
)

total_transactions_label = create_card(
    dashboard,
    "SALES TRANSACTIONS"
)

total_units_label = create_card(
    dashboard,
    "TOTAL UNITS SOLD"
)

total_value_label = create_card(
    dashboard,
    "TOTAL SALES VALUE"
)

# Search bar
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
    width=30
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Search",
    command=search_products
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Clear",
    command=clear_search
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Top Products",
    command=show_top_products
).pack(side="left", padx=8)

ttk.Button(
    search_frame,
    text="Save Report CSV",
    command=save_report
).pack(side="left", padx=5)

ttk.Button(
    search_frame,
    text="Reload Data",
    command=refresh_table
).pack(side="left", padx=5)

# Report table
table_frame = tk.Frame(root, bg="#eef2f7")
table_frame.pack(fill="both", expand=True, padx=25, pady=10)

columns = (
    "Product ID",
    "Product Name",
    "Brand",
    "Category",
    "Price",
    "Quantity Sold",
    "Total Sales Value"
)

report_tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

for col in columns:
    report_tree.heading(col, text=col)

widths = {
    "Product ID": 100,
    "Product Name": 220,
    "Brand": 130,
    "Category": 130,
    "Price": 120,
    "Quantity Sold": 130,
    "Total Sales Value": 160
}

for col, width in widths.items():
    report_tree.column(col, width=width, anchor="center")

scrollbar_y = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=report_tree.yview
)

scrollbar_x = ttk.Scrollbar(
    table_frame,
    orient="horizontal",
    command=report_tree.xview
)

report_tree.configure(
    yscrollcommand=scrollbar_y.set,
    xscrollcommand=scrollbar_x.set
)

report_tree.pack(side="top", fill="both", expand=True)
scrollbar_y.pack(side="right", fill="y")
scrollbar_x.pack(side="bottom", fill="x")

report_tree.bind("<Double-1>", show_product_details)

# Footer
tk.Label(
    root,
    text="Double-click a product to view sales details",
    bg="#eef2f7",
    fg="#64748b",
    font=("Arial", 9)
).pack(pady=(0, 8))

# Start
refresh_table()

root.mainloop()
