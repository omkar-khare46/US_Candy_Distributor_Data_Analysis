"""
extract.py
Stage 1 of the ETL pipeline: EXTRACT

Reads all raw CSVs into DataFrames and profiles them
(shape, dtypes, null counts, a few sample rows) so we know
exactly what we're dealing with before any cleaning happens.

No transformation logic belongs in this file.
"""
import sys
from pathlib import Path
import os
import logging
import pandas as pd

########################################### Logging Setup ###################
LOG_DIR = "logs"

os.makedirs(LOG_DIR, exist_ok= True)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s",
              )
logger = logging.getLogger(__name__)

#################################### Config Setup ##############################

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

FILES = {
    "sales": "Candy_Sales.csv",
    "factories": "Candy_Factories.csv",
    "products": "Candy_Products.csv",
    "targets": "Candy_Targets.csv",
    "us_zips": "uszips.csv",
}
###################
class ExtractionError(Exception):
     """Raised when a raw file can't be read or is empty."""

def extract_table(name: str, filename: str) -> pd.DataFrame:

## Read a single raw CSV into a DataFrame and log a profile of it.
### Raises:
###        ExtractionError: if the file is missing, empty, or fails to parse.

    

    path = RAW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Raw file not found {name} : {path}")

    
    try:
         df = pd.read_csv(path)

    except pd.errors.EmptyDataError as e:
        raise ExtractionError(f"{path} is empty") from e
    except pd.errors.ParserError as e:
        raise ExtractionError(f"{path} could not be parsed as CSV: {e}") from e
    except UnicodeDecodeError as e:
        raise ExtractionError(f"{path} has an encoding issue: {e}") from e
    if df.empty:
        raise ExtractionError(f"{path} loaded but contains 0 rows")

    logger.info("Loaded '%s' from %s: %d rows x %d columns", name, path, *df.shape)
    
    logger.debug("'%s' dtypes:\n%s", name, df.dtypes)
 
    null_counts = df.isnull().sum()
    nulls_present = null_counts[null_counts > 0]
    if not nulls_present.empty:
        logger.warning("'%s' has null values:\n%s", name, nulls_present)
    else:
        logger.info("'%s' has no null values", name)
 
    return df


def extract_all() -> dict[str, pd.DataFrame]:
    tables = {}
    for name, filename in FILES.items():
        tables[name] = extract_table(name, filename)
    return tables


if __name__ == "__main__":
    tables = extract_all()

    logger.info("EXTRACTION COMPLETE — %d tables loaded", len(tables))