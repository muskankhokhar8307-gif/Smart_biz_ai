"""Business metrics built from the database's recorded facts."""
from decimal import Decimal
import pandas as pd
import numpy as np


def _decimal_sum(series):
    return sum((Decimal(str(v)) for v in series), Decimal("0.00"))


def sales_dataframe(db, start_date=None, end_date=None):
    rows = db.list_sales(start_date, end_date, include_cancelled=False)
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=[
            "sale_id", "product_id", "customer_id", "sale_date", "quantity",
            "unit_price", "unit_cost", "total_amount", "status", "product_name",
            "category", "customer_name", "revenue", "cogs", "gross_profit", "month"
        ])
    for col in ("unit_price", "unit_cost", "total_amount"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(int)
    df["revenue"] = df["total_amount"]
    df["cogs"] = df["unit_cost"] * df["quantity"]
    df["gross_profit"] = df["revenue"] - df["cogs"]
    df["month"] = pd.to_datetime(df["sale_date"], errors="coerce").dt.to_period("M").astype(str)
    return df


def expense_dataframe(db, start_date=None, end_date=None):
    df = pd.DataFrame(db.list_expenses(start_date, end_date))
    if df.empty:
        return pd.DataFrame(columns=["expense_id", "category", "description", "amount", "expense_date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    return df


def business_kpis(db, start_date=None, end_date=None):
    sales = sales_dataframe(db, start_date, end_date)
    expenses = expense_dataframe(db, start_date, end_date)
    revenue = float(sales["revenue"].sum()) if not sales.empty else 0.0
    cogs = float(sales["cogs"].sum()) if not sales.empty else 0.0
    expense_total = float(expenses["amount"].sum()) if not expenses.empty else 0.0
    products = db.list_products()
    return {
        "revenue": round(revenue, 2),
        "orders": int(len(sales)),
        "units_sold": int(sales["quantity"].sum()) if not sales.empty else 0,
        "products": len(products),
        "customers": len(db.list_customers()),
        "expenses": round(expense_total, 2),
        "cogs": round(cogs, 2),
        "gross_profit": round(revenue - cogs, 2),
        "net_profit_estimate": round(revenue - cogs - expense_total, 2),
        "low_stock": sum(1 for p in products if int(p["stock"]) <= int(p["reorder_level"])),
    }


def monthly_sales(db, start_date=None, end_date=None):
    df = sales_dataframe(db, start_date, end_date)
    if df.empty:
        return pd.DataFrame(columns=["month", "revenue", "orders", "gross_profit"])
    return (df.groupby("month", as_index=False)
            .agg(revenue=("revenue", "sum"), orders=("sale_id", "count"),
                 gross_profit=("gross_profit", "sum"))
            .sort_values("month"))


def category_performance(db, start_date=None, end_date=None):
    df = sales_dataframe(db, start_date, end_date)
    if df.empty:
        return pd.DataFrame(columns=["category", "revenue", "gross_profit", "quantity"])
    return (df.groupby("category", as_index=False)
            .agg(revenue=("revenue", "sum"), gross_profit=("gross_profit", "sum"),
                 quantity=("quantity", "sum"))
            .sort_values("revenue", ascending=False))


def product_performance(db, start_date=None, end_date=None):
    df = sales_dataframe(db, start_date, end_date)
    if df.empty:
        return pd.DataFrame(columns=["product_name", "revenue", "quantity", "gross_profit"])
    return (df.groupby("product_name", as_index=False)
            .agg(revenue=("revenue", "sum"), quantity=("quantity", "sum"),
                 gross_profit=("gross_profit", "sum"))
            .sort_values("revenue", ascending=False))


def inventory_dataframe(db):
    products = pd.DataFrame(db.list_products())
    if products.empty:
        return pd.DataFrame(columns=["product_id", "product_name", "category", "price", "unit_cost", "stock", "reorder_level"])
    for col in ("price", "unit_cost"):
        products[col] = pd.to_numeric(products[col], errors="coerce").fillna(0.0)
    products["needs_restock"] = products["stock"] <= products["reorder_level"]
    return products


def simple_sales_diagnostics(db):
    monthly = monthly_sales(db)
    if len(monthly) < 2:
        return {"status": "insufficient_data", "message": "At least two months with sales are needed to compare monthly revenue."}
    previous, current = float(monthly.iloc[-2]["revenue"]), float(monthly.iloc[-1]["revenue"])
    change = current - previous
    pct = (change / previous * 100) if previous else None
    return {
        "status": "ok", "previous_month": monthly.iloc[-2]["month"],
        "current_month": monthly.iloc[-1]["month"], "previous_revenue": round(previous, 2),
        "current_revenue": round(current, 2), "change": round(change, 2),
        "change_percent": round(pct, 2) if pct is not None else None,
        "direction": "increased" if change > 0 else "decreased" if change < 0 else "stayed flat",
    }
