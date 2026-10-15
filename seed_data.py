"""Create clearly labelled sample records for demonstrations."""
from datetime import date, timedelta
from decimal import Decimal
import random

from database import DatabaseManager
from models import Product, Customer, Sale

random.seed(42)


def seed(db=None):
    db = db or DatabaseManager()
    if any(db.table_counts().values()):
        print("Database already contains data. No sample records added.")
        return db

    product_rows = [
        ("Wireless Mouse", "Electronics", "799.00", "420.00", 35, 8),
        ("USB-C Cable", "Electronics", "299.00", "100.00", 60, 12),
        ("Notebook", "Stationery", "80.00", "35.00", 100, 20),
        ("Desk Lamp", "Home", "1299.00", "720.00", 18, 5),
        ("Water Bottle", "Lifestyle", "399.00", "180.00", 40, 10),
    ]
    product_ids = []
    for name, cat, price, cost, stock, reorder in product_rows:
        product_ids.append(db.add_product(Product(name, cat, Decimal(price), Decimal(cost), stock, reorder)))

    customer_rows = [
        ("Aarav Sharma", "Ambala", "aarav@example.test"),
        ("Priya Verma", "Chandigarh", "priya@example.test"),
        ("Kabir Singh", "Ludhiana", "kabir@example.test"),
        ("Anaya Gupta", "Patiala", "anaya@example.test"),
        ("Ishaan Mehta", "Delhi", "ishaan@example.test"),
    ]
    customer_ids = [db.add_customer(Customer(*row)) for row in customer_rows]

    today = date.today()
    # Spread sample sales across six months, staying within stock limits.
    for offset in range(150, -1, -3):
        product_index = random.randrange(len(product_ids))
        customer_index = random.randrange(len(customer_ids))
        product = db.get_product(product_ids[product_index])
        qty = random.randint(1, min(2, max(1, int(product["stock"]))))
        try:
            db.add_sale(Sale(product_ids[product_index], customer_ids[customer_index], qty,
                             (today - timedelta(days=offset)).isoformat()))
        except ValueError:
            # Out-of-stock samples are skipped rather than altering stock rules.
            continue

    for category, amount, days_ago, desc in [
        ("Rent", "8000.00", 25, "Sample monthly shop rent"),
        ("Utilities", "1250.00", 18, "Sample electricity bill"),
        ("Marketing", "2200.00", 10, "Sample local promotion"),
        ("Transport", "650.00", 5, "Sample delivery costs"),
    ]:
        db.add_expense(category, amount, today - timedelta(days=days_ago), desc)

    print("Sample data added. These are fictional demonstration records.")
    print(db.table_counts())
    return db


if __name__ == "__main__":
    seed()
