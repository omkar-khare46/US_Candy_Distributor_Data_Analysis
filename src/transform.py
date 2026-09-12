"""
#transform.py
#Stage 2 of the ETL pipeline: TRANSFORM
 
#Takes the raw DataFrames from extract.py and applies cleaning:
#- dtype fixes (dates, zero-padded zip codes)
#- key validation and dedup
#- a data-quality check on Gross Profit
#- trims us_zips down to only the zips that appear in Sales
 
#Saves cleaned output to data/processed/ as parquet checkpoints.
"""

import logging
import pandas as pd
from pathlib import Path

from extract import extract_all

logging.basicConfig(
    level= logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    )

logger = logging.getLogger(__name__)

# 1. Finds the directory where this specific script file lives
SCRIPT_DIR = Path(__file__).resolve().parent

# 2. Finds the directory one level above the script directory
PROJECT_ROOT = SCRIPT_DIR.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


############### cleaning Sales table ###################### 

def clean_sales(df : pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Ship Date']  = pd.to_datetime(df['Ship Date'])
    
    # Postal Code is a US zip — if pandas read it as int/float, leading
    # zeros (e.g. "02134") are already lost by this point, so we just
    # zero-pad back to 5 digits on the string form.
    
    df["Postal Code"] = df["Postal Code"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5)
 
    df["Product ID"] = df["Product ID"].astype(str).str.strip()
    
    before = len(df)
    
    
    df = df.drop_duplicates(subset="Row ID")
    if len(df) < before:
        logger.warning("Sales: dropped %d duplicate Row ID rows", before - len(df))
 
    # Data-quality check, not a fix: does Gross Profit already equal Sales - Cost?
    expected_gp = df["Sales"] - df["Cost"]
    mismatch = (df["Gross Profit"] - expected_gp).abs() > 0.01
    if mismatch.any():
        logger.warning(
            "Sales: %d rows where Gross Profit != Sales - Cost (kept as-is, flagged only)",
            mismatch.sum(),
        )
 
    logger.info("Sales cleaned: %d rows", len(df))
    return df

def clean_factories(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Factory"] = df["Factory"].astype(str).str.strip()
    return df
 
 
def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Product ID"] = df["Product ID"].astype(str).str.strip()
 
    dupes = df["Product ID"].duplicated().sum()
    if dupes:
        logger.warning("Products: %d duplicate Product ID values found", dupes)
 
    return df
 
 
def clean_targets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Division"] = df["Division"].astype(str).str.strip()
    return df
 
 
def clean_geography(df: pd.DataFrame, sales_zips: set) -> pd.DataFrame:
    df = df.copy()
 
    # parent_zcta is 100% null (confirmed in extraction output) — drop it
    # rather than carry an empty column into the warehouse.
    df = df.drop(columns=["parent_zcta"])
 
    df["zip"] = df["zip"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5)
 
    before = len(df)
    df = df[df["zip"].isin(sales_zips)]
    logger.info("Geography trimmed from %d to %d rows (only zips present in Sales)", before, len(df))
 
    return df
 
 
def transform_all() -> dict[str, pd.DataFrame]:
    raw = extract_all()
 
    sales = clean_sales(raw["sales"])
    factories = clean_factories(raw["factories"])
    products = clean_products(raw["products"])
    targets = clean_targets(raw["targets"])
    geography = clean_geography(raw["us_zips"], sales_zips=set(sales["Postal Code"]))
 
    return {
        "sales": sales,
        "factories": factories,
        "products": products,
        "targets": targets,
        "geography": geography,
    }
 
 
if __name__ == "__main__":
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
 
    tables = transform_all()
    for name, df in tables.items():
        out_path = PROCESSED_DIR / f"{name}_clean.parquet"
        df.to_parquet(out_path, index=False)
        logger.info("Saved '%s' -> %s (%d rows)", name, out_path, len(df))
 
    logger.info("TRANSFORMATION COMPLETE")