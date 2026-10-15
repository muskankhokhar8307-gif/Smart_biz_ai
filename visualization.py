"""Reusable Matplotlib chart functions."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path


def monthly_revenue_chart(monthly_df):
    fig, ax = plt.subplots(figsize=(9, 4))
    if monthly_df.empty:
        ax.text(0.5, 0.5, "No sales data yet", ha="center", va="center")
        ax.set_axis_off()
    else:
        ax.plot(monthly_df["month"], monthly_df["revenue"], marker="o")
        ax.set_title("Monthly Revenue")
        ax.set_xlabel("Month")
        ax.set_ylabel("Revenue (₹)")
        ax.tick_params(axis="x", rotation=35)
        ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


def category_revenue_chart(category_df):
    fig, ax = plt.subplots(figsize=(8, 4))
    if category_df.empty:
        ax.text(0.5, 0.5, "No category sales data yet", ha="center", va="center")
        ax.set_axis_off()
    else:
        ax.bar(category_df["category"], category_df["revenue"])
        ax.set_title("Revenue by Category")
        ax.set_ylabel("Revenue (₹)")
        ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return fig


def expense_category_chart(expense_df):
    fig, ax = plt.subplots(figsize=(8, 4))
    if expense_df.empty:
        ax.text(0.5, 0.5, "No expense data yet", ha="center", va="center")
        ax.set_axis_off()
    else:
        grouped = expense_df.groupby("category", as_index=False)["amount"].sum()
        ax.bar(grouped["category"], grouped["amount"])
        ax.set_title("Expenses by Category")
        ax.set_ylabel("Expense amount (₹)")
        ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return fig
