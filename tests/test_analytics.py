import tempfile
import unittest
from pathlib import Path
from datetime import date
from database import DatabaseManager
from models import Product, Customer, Sale
from analytics import business_kpis
from forecasting import forecast_next_month


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = DatabaseManager(Path(self.tmp.name) / "test.db")
        self.pid = self.db.add_product(Product("Item", "General", "100", "60", 100, 5))
        self.cid = self.db.add_customer(Customer("Customer"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_kpis(self):
        self.db.add_sale(Sale(self.pid, self.cid, 2, date.today().isoformat()))
        self.db.add_expense("Rent", "10.00", date.today().isoformat())
        kpis = business_kpis(self.db)
        self.assertEqual(kpis["revenue"], 200.0)
        self.assertEqual(kpis["cogs"], 120.0)
        self.assertEqual(kpis["gross_profit"], 80.0)
        self.assertEqual(kpis["expenses"], 10.0)
        self.assertEqual(kpis["net_profit_estimate"], 70.0)

    def test_forecast_requires_history(self):
        result = forecast_next_month(self.db)
        self.assertEqual(result["status"], "insufficient_data")


if __name__ == "__main__":
    unittest.main()
