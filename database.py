"""SQLite persistence layer. All SQL statements use parameters."""
import os
import sqlite3
from pathlib import Path
from datetime import date
from decimal import Decimal
import logging

from models import Product, Customer, Sale, money, valid_date

LOGGER = logging.getLogger(__name__)
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "database" / "smartbiz.db"


class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = Path(db_path or os.getenv("SMARTBIZ_DB_PATH", str(DEFAULT_DB_PATH)))
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        with self.connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                price TEXT NOT NULL CHECK(CAST(price AS REAL) >= 0),
                unit_cost TEXT NOT NULL DEFAULT '0.00' CHECK(CAST(unit_cost AS REAL) >= 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                reorder_level INTEGER NOT NULL DEFAULT 5 CHECK(reorder_level >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES products(product_id),
                customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
                sale_date TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price TEXT NOT NULL CHECK(CAST(unit_price AS REAL) >= 0),
                unit_cost TEXT NOT NULL CHECK(CAST(unit_cost AS REAL) >= 0),
                total_amount TEXT NOT NULL CHECK(CAST(total_amount AS REAL) >= 0),
                status TEXT NOT NULL DEFAULT 'completed' CHECK(status IN ('completed','cancelled')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS expenses (
                expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                amount TEXT NOT NULL CHECK(CAST(amount AS REAL) >= 0),
                expense_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
            CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id);
            CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
            CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);
            """)

    def add_product(self, product: Product) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """INSERT INTO products(product_name, category, price, unit_cost, stock, reorder_level)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (product.product_name, product.category, str(product.price), str(product.unit_cost),
                 product.stock, product.reorder_level))
            return cur.lastrowid

    def update_product(self, product_id, product: Product):
        with self.connect() as conn:
            cur = conn.execute(
                """UPDATE products SET product_name=?, category=?, price=?, unit_cost=?, stock=?, reorder_level=?
                   WHERE product_id=?""",
                (product.product_name, product.category, str(product.price), str(product.unit_cost),
                 product.stock, product.reorder_level, int(product_id)))
            if cur.rowcount == 0:
                raise ValueError("Product not found.")

    def delete_product(self, product_id):
        with self.connect() as conn:
            try:
                cur = conn.execute("DELETE FROM products WHERE product_id=?", (int(product_id),))
            except sqlite3.IntegrityError as exc:
                raise ValueError("Cannot delete a product with sales history.") from exc
            if cur.rowcount == 0:
                raise ValueError("Product not found.")

    def list_products(self):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM products ORDER BY product_name")]

    def get_product(self, product_id):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM products WHERE product_id=?", (int(product_id),)).fetchone()
            return dict(row) if row else None

    def add_customer(self, customer: Customer) -> int:
        with self.connect() as conn:
            cur = conn.execute("INSERT INTO customers(name, city, email) VALUES (?, ?, ?)",
                               (customer.name, customer.city, customer.email))
            return cur.lastrowid

    def update_customer(self, customer_id, customer: Customer):
        with self.connect() as conn:
            cur = conn.execute("UPDATE customers SET name=?, city=?, email=? WHERE customer_id=?",
                               (customer.name, customer.city, customer.email, int(customer_id)))
            if cur.rowcount == 0:
                raise ValueError("Customer not found.")

    def delete_customer(self, customer_id):
        with self.connect() as conn:
            try:
                cur = conn.execute("DELETE FROM customers WHERE customer_id=?", (int(customer_id),))
            except sqlite3.IntegrityError as exc:
                raise ValueError("Cannot delete a customer with sales history.") from exc
            if cur.rowcount == 0:
                raise ValueError("Customer not found.")

    def list_customers(self):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM customers ORDER BY name")]

    def add_sale(self, sale: Sale) -> int:
        """Record a sale atomically, snapshotting current price and cost and reducing stock."""
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            product = conn.execute("SELECT * FROM products WHERE product_id=?", (sale.product_id,)).fetchone()
            customer = conn.execute("SELECT customer_id FROM customers WHERE customer_id=?",
                                    (sale.customer_id,)).fetchone()
            if not product:
                raise ValueError("Selected product does not exist.")
            if not customer:
                raise ValueError("Selected customer does not exist.")
            if int(product["stock"]) < sale.quantity:
                raise ValueError(f"Insufficient stock. Available: {product['stock']}.")
            unit_price = sale.unit_price if sale.unit_price is not None else money(product["price"])
            unit_cost = money(product["unit_cost"])
            total = (unit_price * sale.quantity).quantize(Decimal("0.01"))
            conn.execute("UPDATE products SET stock=stock-? WHERE product_id=?",
                         (sale.quantity, sale.product_id))
            cur = conn.execute(
                """INSERT INTO sales(product_id, customer_id, sale_date, quantity, unit_price, unit_cost, total_amount)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sale.product_id, sale.customer_id, sale.sale_date, sale.quantity,
                 str(unit_price), str(unit_cost), str(total)))
            return cur.lastrowid

    def cancel_sale(self, sale_id):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM sales WHERE sale_id=?", (int(sale_id),)).fetchone()
            if not row:
                raise ValueError("Sale not found.")
            if row["status"] == "cancelled":
                raise ValueError("Sale is already cancelled.")
            conn.execute("UPDATE sales SET status='cancelled' WHERE sale_id=?", (int(sale_id),))
            conn.execute("UPDATE products SET stock=stock+? WHERE product_id=?",
                         (row["quantity"], row["product_id"]))

    def list_sales(self, start_date=None, end_date=None, include_cancelled=True):
        sql = """SELECT s.*, p.product_name, p.category, c.name AS customer_name
                 FROM sales s JOIN products p ON p.product_id=s.product_id
                 JOIN customers c ON c.customer_id=s.customer_id WHERE 1=1"""
        params = []
        if start_date:
            sql += " AND s.sale_date >= ?"; params.append(valid_date(start_date))
        if end_date:
            sql += " AND s.sale_date <= ?"; params.append(valid_date(end_date))
        if not include_cancelled:
            sql += " AND s.status='completed'"
        sql += " ORDER BY s.sale_date DESC, s.sale_id DESC"
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(sql, params)]

    def add_expense(self, category, amount, expense_date=None, description=""):
        category = str(category).strip()
        description = str(description or "").strip()
        amount = money(amount, "amount")
        if not category:
            raise ValueError("Expense category is required.")
        if amount < 0:
            raise ValueError("Expense amount cannot be negative.")
        expense_date = valid_date(expense_date or date.today())
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO expenses(category, description, amount, expense_date) VALUES (?, ?, ?, ?)",
                (category, description, str(amount), expense_date))
            return cur.lastrowid

    def list_expenses(self, start_date=None, end_date=None):
        sql = "SELECT * FROM expenses WHERE 1=1"
        params = []
        if start_date:
            sql += " AND expense_date >= ?"; params.append(valid_date(start_date))
        if end_date:
            sql += " AND expense_date <= ?"; params.append(valid_date(end_date))
        sql += " ORDER BY expense_date DESC, expense_id DESC"
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(sql, params)]

    def delete_expense(self, expense_id):
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM expenses WHERE expense_id=?", (int(expense_id),))
            if cur.rowcount == 0:
                raise ValueError("Expense not found.")

    def table_counts(self):
        with self.connect() as conn:
            return {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    for table in ("products", "customers", "sales", "expenses")}
