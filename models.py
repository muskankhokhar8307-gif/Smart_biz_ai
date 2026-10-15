"""Typed domain models and validation helpers for SmartBiz AI."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional


def money(value, field_name="amount") -> Decimal:
    try:
        result = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid number.")
    if not result.is_finite():
        raise ValueError(f"{field_name} must be finite.")
    return result


def positive_int(value, field_name="quantity") -> int:
    try:
        number = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a whole number.")
    if number <= 0 or str(value).strip() not in (str(number), f"+{number}"):
        raise ValueError(f"{field_name} must be a positive whole number.")
    return number


def valid_date(value) -> str:
    if isinstance(value, date):
        return value.isoformat()
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise ValueError("Date must use YYYY-MM-DD format.")


@dataclass
class Product:
    product_name: str
    category: str
    price: Decimal
    unit_cost: Decimal
    stock: int
    reorder_level: int = 5
    product_id: Optional[int] = None

    def __post_init__(self):
        self.product_name = str(self.product_name).strip()
        self.category = str(self.category).strip()
        if not self.product_name or not self.category:
            raise ValueError("Product name and category are required.")
        self.price = money(self.price, "price")
        self.unit_cost = money(self.unit_cost, "unit_cost")
        if self.price < 0 or self.unit_cost < 0:
            raise ValueError("Price and unit cost cannot be negative.")
        self.stock = int(self.stock)
        self.reorder_level = int(self.reorder_level)
        if self.stock < 0 or self.reorder_level < 0:
            raise ValueError("Stock and reorder level cannot be negative.")


@dataclass
class Customer:
    name: str
    city: str = ""
    email: str = ""
    customer_id: Optional[int] = None

    def __post_init__(self):
        self.name = str(self.name).strip()
        self.city = str(self.city or "").strip()
        self.email = str(self.email or "").strip()
        if not self.name:
            raise ValueError("Customer name is required.")


@dataclass
class Sale:
    product_id: int
    customer_id: int
    quantity: int
    sale_date: str
    unit_price: Optional[Decimal] = None
    sale_id: Optional[int] = None

    def __post_init__(self):
        self.product_id = positive_int(self.product_id, "product_id")
        self.customer_id = positive_int(self.customer_id, "customer_id")
        self.quantity = positive_int(self.quantity, "quantity")
        self.sale_date = valid_date(self.sale_date)
        if self.unit_price is not None:
            self.unit_price = money(self.unit_price, "unit_price")
            if self.unit_price < 0:
                raise ValueError("Unit price cannot be negative.")
