import unittest
from models import Product, Customer, Sale


class ModelTests(unittest.TestCase):
    def test_negative_price_rejected(self):
        with self.assertRaises(ValueError):
            Product("Item", "General", "-1", "0", 1)

    def test_blank_customer_rejected(self):
        with self.assertRaises(ValueError):
            Customer(" ")

    def test_invalid_date_rejected(self):
        with self.assertRaises(ValueError):
            Sale(1, 1, 1, "12/10/2026")


if __name__ == "__main__":
    unittest.main()
