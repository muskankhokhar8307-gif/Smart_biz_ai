"""Data import/export and cleaning helpers."""
from pathlib import Path
import pandas as pd


def read_csv(path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    return pd.read_csv(path)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy; does not modify the caller's frame."""
    result = df.copy()
    result.columns = [str(c).strip() for c in result.columns]
    result = result.drop_duplicates()
    for col in result.select_dtypes(include=["object"]).columns:
        result[col] = result[col].map(lambda x: x.strip() if isinstance(x, str) else x)
    return result


def import_products_csv(db, path):
    df = clean_dataframe(read_csv(path))
    required = {"product_name", "category", "price", "unit_cost", "stock"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError("Products CSV missing columns: " + ", ".join(sorted(missing)))
    imported, errors = 0, []
    from models import Product
    for idx, row in df.iterrows():
        try:
            product = Product(
                product_name=row["product_name"], category=row["category"],
                price=row["price"], unit_cost=row.get("unit_cost", 0),
                stock=int(row["stock"]), reorder_level=int(row.get("reorder_level", 5)))
            db.add_product(product)
            imported += 1
        except Exception as exc:
            errors.append(f"CSV row {idx + 2}: {exc}")
    return {"imported": imported, "errors": errors}


def import_customers_csv(db, path):
    df = clean_dataframe(read_csv(path))
    required = {"name"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError("Customers CSV missing columns: " + ", ".join(sorted(missing)))
    imported, errors = 0, []
    from models import Customer
    for idx, row in df.iterrows():
        try:
            db.add_customer(Customer(row["name"], row.get("city", ""), row.get("email", "")))
            imported += 1
        except Exception as exc:
            errors.append(f"CSV row {idx + 2}: {exc}")
    return {"imported": imported, "errors": errors}


def dataframe_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")
