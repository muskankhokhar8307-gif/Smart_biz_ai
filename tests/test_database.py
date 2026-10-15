import tempfile
import unittest
from pathlib import Path
from datetime import date
from database import DatabaseManager
from models import Product, Customer, Sale


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = DatabaseManager(Path(self.tmp.name) / "test.db")
        self.pid = self.db.add_product(Product("Test item", "Test", "100.00", "40.00", 10, 2))
        self.cid = self.db.add_customer(Customer("Test customer", "Test city"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_sale_reduces_stock_and_records_amount(self):
        sid = self.db.add_sale(Sale(self.pid, self.cid, 2, date.today().isoformat()))
        self.assertGreater(sid, 0)
        self.assertEqual(self.db.get_product(self.pid)["stock"], 8)
        sales = self.db.list_sales(include_cancelled=False)
        self.assertEqual(sales[0]["total_amount"], "200.00")

    def test_sale_rejects_insufficient_stock(self):
        with self.assertRaises(ValueError):
            self.db.add_sale(Sale(self.pid, self.cid, 11, date.today().isoformat()))
        self.assertEqual(self.db.get_product(self.pid)["stock"], 10)

    def test_cancel_sale_restores_stock(self):
        sid = self.db.add_sale(Sale(self.pid, self.cid, 3, date.today().isoformat()))
        self.db.cancel_sale(sid)
        self.assertEqual(self.db.get_product(self.pid)["stock"], 10)
        self.assertEqual(self.db.list_sales()[0]["status"], "cancelled")

    def test_cancel_twice_fails(self):
        sid = self.db.add_sale(Sale(self.pid, self.cid, 1, date.today().isoformat()))
        self.db.cancel_sale(sid)
        with self.assertRaises(ValueError):
            self.db.cancel_sale(sid)

    def test_product_with_sales_cannot_be_deleted(self):
        self.db.add_sale(Sale(self.pid, self.cid, 1, date.today().isoformat()))
        with self.assertRaises(ValueError):
            self.db.delete_product(self.pid)


if __name__ == "__main__":
    unittest.main()
