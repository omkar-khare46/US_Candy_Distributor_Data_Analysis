"""
load_mysql.py
Stage 3 of the ETL pipeline: LOAD (MySQL version)

Same logic as load.py, but targets a local MySQL server instead of
SQLite. Reads the cleaned parquet files from data/processed/, renames
columns to match sql/schema_mysql.sql, and inserts them in FK-safe
order: dimensions first, fact table last.

Requires: pip install mysql-connector-python sqlalchemy
"""

import logging

import mysql.connector
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema_mysql.sql"

# --- fill these in for your local MySQL install ---
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "your_password_here"
MYSQL_DATABASE = "candy_warehouse"
# ----------------------------------------------------

COLUMN_MAPS = {
    "factories": {
        "Factory": "factory_name",
        "Latitude": "latitude",
        "Longitude": "longitude",
    },
    "targets": {
        "Division": "division",
        "Target": "target",
    },
    "products": {
        "Product ID": "product_id",
        "Product Name": "product_name",
        "Division": "division",
        "Factory": "factory_name",
        "Unit Price": "unit_price",
        "Unit Cost": "unit_cost",
    },
    "geography": {
        "zip": "zip", "lat": "lat", "lng": "lng", "city": "city",
        "state_id": "state_id", "state_name": "state_name", "zcta": "zcta",
        "population": "population", "density": "density",
        "county_fips": "county_fips", "county_name": "county_name",
        "county_weights": "county_weights", "county_names_all": "county_names_all",
        "county_fips_all": "county_fips_all", "imprecise": "imprecise",
        "military": "military", "timezone": "timezone",
    },
    "sales": {
        "Row ID": "row_id",
        "Order ID": "order_id",
        "Order Date": "order_date",
        "Ship Date": "ship_date",
        "Ship Mode": "ship_mode",
        "Customer ID": "customer_id",
        "Country/Region": "country_region",
        "City": "city",
        "State/Province": "state_province",
        "Postal Code": "postal_code",
        "Division": "division",
        "Region": "region",
        "Product ID": "product_id",
        "Sales": "sales",
        "Units": "units",
        "Gross Profit": "gross_profit",
        "Cost": "cost",
    },
}

LOAD_ORDER = ["factories", "targets", "products", "geography", "sales"]

TABLE_NAMES = {
    "factories": "dim_factories",
    "targets": "dim_targets",
    "products": "dim_products",
    "geography": "dim_geography",
    "sales": "fact_sales",
}


def create_schema() -> None:
    # mysql.connector, not sqlalchemy, for this step — running a multi-
    # statement .sql script (CREATE DATABASE, DROP TABLE x5, CREATE TABLE
    # x5, CREATE INDEX x4) needs multi=True, which sqlalchemy's execute
    # doesn't support directly for MySQL.
    conn = mysql.connector.connect(
        host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD,
    )
    cursor = conn.cursor()
    schema_sql = SCHEMA_PATH.read_text()

    for _ in cursor.execute(schema_sql, multi=True):
        pass

    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Schema created from %s", SCHEMA_PATH)


def prepare_table(name: str) -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED_DIR / f"{name}_clean.parquet")

    col_map = COLUMN_MAPS[name]
    df = df[list(col_map.keys())].rename(columns=col_map)

    # MySQL's DATE type accepts Python date/datetime objects directly via
    # SQLAlchemy — no ISO-string conversion needed here (unlike the SQLite
    # version, which has to stringify dates itself).
    return df


def load_all() -> None:
    create_schema()

    engine = create_engine(
        f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"
    )

    for name in LOAD_ORDER:
        df = prepare_table(name)
        table = TABLE_NAMES[name]
        df.to_sql(table, engine, if_exists="append", index=False)
        logger.info("Loaded %d rows into '%s'", len(df), table)

    engine.dispose()


if __name__ == "__main__":
    load_all()
    logger.info("LOAD COMPLETE — warehouse in MySQL database '%s'", MYSQL_DATABASE)
