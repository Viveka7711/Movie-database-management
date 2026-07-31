# Mobile Retail Sales Management System

A Python GUI application that combines product details from JSON with sales transactions from CSV, calculates total quantity sold for each product, and saves the final results into a new CSV file.

## Technologies

- Python 3
- Tkinter
- Pandas
- JSON
- CSV

## Install Pandas

If Pandas is not installed, run:

`pip install pandas`

## Files

- `app.py` - Main Python application code
- `products.json` - Mobile product details
- `sales.csv` - Sales transactions
- `total_sales_report.csv` - Generated output report
- `run_app.bat` - Windows launcher

## How to Run

Double-click:

`run_app.bat`

OR run:

`python app.py`

## Output

The application automatically creates:

`total_sales_report.csv`

The output contains:

- product_id
- product_name
- brand
- category
- price
- total_quantity_sold
- total_sales_value

## Main Operation

Sales quantities are grouped by product ID:

`sales.groupby("product_id")["quantity"].sum()`

The grouped sales data is merged with product details:

`products.merge(quantity_summary, on="product_id", how="left")`

Finally the result is saved:

`final_report.to_csv("total_sales_report.csv", index=False)`

## Features

- JSON product data loading
- CSV sales data loading
- Dataset integration
- Total quantity calculation
- Total sales value calculation
- Search products
- Top-selling products report
- GUI dashboard
- Automatic output CSV generation

## Question Mapping

Product details -> JSON
Sales transactions -> CSV
Combine datasets -> Pandas merge
Total quantity sold -> groupby + sum
Save results -> total_sales_report.csv
