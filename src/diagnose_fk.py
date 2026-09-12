"""One-off diagnostic: find which FK values in products/sales don't
exist in their parent dimension tables. Delete after use."""
import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

factories = pd.read_parquet(PROCESSED_DIR / "factories_clean.parquet")
targets = pd.read_parquet(PROCESSED_DIR / "targets_clean.parquet")
products = pd.read_parquet(PROCESSED_DIR / "products_clean.parquet")
geography = pd.read_parquet(PROCESSED_DIR / "geography_clean.parquet")
sales = pd.read_parquet(PROCESSED_DIR / "sales_clean.parquet")

valid_factories = set(factories["Factory"])
valid_divisions = set(targets["Division"])
valid_products = set(products["Product ID"])
valid_zips = set(geography["zip"])

print("Products.Factory not in Factories.Factory:",
      sorted(set(products["Factory"]) - valid_factories))
print("Products.Division not in Targets.Division:",
      sorted(set(products["Division"]) - valid_divisions))
print("Sales.Division not in Targets.Division:",
      sorted(set(sales["Division"]) - valid_divisions))
print("Sales.Product ID not in Products.Product ID:",
      sorted(set(sales["Product ID"]) - valid_products))
print("Sales.Postal Code not in Geography.zip:",
      sorted(set(sales["Postal Code"]) - valid_zips))
