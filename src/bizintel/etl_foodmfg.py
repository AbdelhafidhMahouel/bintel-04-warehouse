"""etl_foodmfg.py - custom project.

Loads prepared food manufacturing data into the food_manufacturing.duckdb
warehouse created by dw_create_foodmfg.py.

Author: Abdelhafidh Mahouel
Date: 2026-07

Process:
    - Connect to the DuckDB data warehouse.
    - Extract prepared CSV files (lines, products, production runs).
    - Verify row counts before loading.
    - Load data into dimension and fact tables.
    - Verify row counts after loading.

Data Source:
- data/food_data/prepared/production_lines_prepared.csv
- data/food_data/prepared/products_prepared.csv
- data/food_data/prepared/production_runs_prepared.csv

Output:
- artifacts/food_manufacturing.duckdb (populated)

Terminal command to run this file from the root project folder:

uv run python -m bizintel.etl_foodmfg

OBS:
  Run dw_create_foodmfg.py first to (re)create the schema before running this.
"""

# === Section 1. Import dependencies and set up constants ===

from pathlib import Path
from typing import Final

from datafun_toolkit.logger import log_path
import duckdb
import pandas as pd

from bizintel.utils_data import load_data
from bizintel.utils_logger import LOG, log_header

# === DECLARE CONSTANTS ===

DATA_PREPARED: Final[Path] = Path("data/food_data/prepared")

LINES_PREPARED: Final[Path] = DATA_PREPARED / "production_lines_prepared.csv"
PRODUCTS_PREPARED: Final[Path] = DATA_PREPARED / "products_prepared.csv"
RUNS_PREPARED: Final[Path] = DATA_PREPARED / "production_runs_prepared.csv"

DW_FILE: Final[Path] = Path("artifacts/food_manufacturing.duckdb")


# === Section 2. Define Reusable Functions ===

# === Section 2.1 DEFINE A VERIFY ROW COUNT FUNCTION ===


def verify_row_count(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    expected: int,
) -> None:
    """Verify that a table contains the expected number of rows.

    Args:
        conn: Open DuckDB connection.
        table: Table name to check.
        expected: Expected number of rows.

    Returns:
        None
    """
    result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    actual: int = int(result[0]) if result else 0

    if actual == expected:
        LOG.info(f"  PASS: {table} has {actual} rows")
    else:
        LOG.warning(f"  FAIL: {table} expected {expected} rows, got {actual}")


# === Section 2.2 DEFINE A LOAD LINES FUNCTION ===


def load_lines(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    """Load prepared production lines data into dim_lines.

    Args:
        conn: Open DuckDB connection.
        df: Prepared lines DataFrame.

    Returns:
        None
    """
    LOG.info("Loading lines into dim_lines")

    conn.execute("""
        INSERT INTO dim_lines
        SELECT
            LineID,
            LineName,
            Plant,
            CapacityUnitsPerHour
        FROM df
    """)

    LOG.info(f"  Loaded {df.shape[0]} rows into dim_lines")


# === Section 2.3 DEFINE A LOAD PRODUCTS FUNCTION ===


def load_products(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    """Load prepared products data into dim_products.

    Args:
        conn: Open DuckDB connection.
        df: Prepared products DataFrame.

    Returns:
        None
    """
    LOG.info("Loading products into dim_products")

    df = df.copy()
    df["BatchSizeKg"] = pd.to_numeric(df["BatchSizeKg"], errors="coerce")

    conn.execute("""
        INSERT INTO dim_products
        SELECT
            ProductID,
            ProductName,
            Category,
            BatchSizeKg,
            ShelfLifeDays
        FROM df
    """)

    LOG.info(f"  Loaded {df.shape[0]} rows into dim_products")


# === Section 2.4 DEFINE A LOAD PRODUCTION RUNS FUNCTION ===


def load_production_runs(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    """Load prepared production runs data into fact_production_runs.

    WHY: The fact table is loaded last because it references both
    dimension tables via foreign keys.

    Args:
        conn: Open DuckDB connection.
        df: Prepared production runs DataFrame.

    Returns:
        None
    """
    LOG.info("Loading production runs into fact_production_runs")

    df = df.copy()
    df["RunDate"] = pd.to_datetime(df["RunDate"], errors="coerce")
    df["UnitsProduced"] = pd.to_numeric(df["UnitsProduced"], errors="coerce")
    df["DefectUnits"] = pd.to_numeric(df["DefectUnits"], errors="coerce")
    df["DowntimeMinutes"] = pd.to_numeric(df["DowntimeMinutes"], errors="coerce")
    df["DefectRatePct"] = pd.to_numeric(df["DefectRatePct"], errors="coerce")

    conn.execute("""
        INSERT INTO fact_production_runs
        SELECT
            RunID,
            RunDate,
            LineID,
            ProductID,
            ShiftName,
            UnitsProduced,
            DefectUnits,
            DowntimeMinutes,
            DefectRatePct
        FROM df
    """)

    LOG.info(f"  Loaded {df.shape[0]} rows into fact_production_runs")


# === MAIN FUNCTION ===


def main() -> None:
    """Main function to run the food manufacturing ETL load logic."""

    log_header(LOG, "BI")

    LOG.info("========================")
    LOG.info("START main()")
    LOG.info("========================")

    log_path(LOG, "Prepared data:", DATA_PREPARED)
    log_path(LOG, "Data warehouse:", DW_FILE)

    df_lines = load_data(LINES_PREPARED, "lines prepared")
    df_products = load_data(PRODUCTS_PREPARED, "products prepared")
    df_runs = load_data(RUNS_PREPARED, "production runs prepared")

    LOG.info("========================")
    LOG.info("ROW COUNTS BEFORE LOAD")
    LOG.info("========================")
    LOG.info(f"  Lines:           {df_lines.shape[0]} rows")
    LOG.info(f"  Products:        {df_products.shape[0]} rows")
    LOG.info(f"  Production Runs: {df_runs.shape[0]} rows")

    LOG.info("Connecting to DuckDB data warehouse........")
    conn: duckdb.DuckDBPyConnection = duckdb.connect(str(DW_FILE))

    load_lines(conn, df_lines)
    load_products(conn, df_products)
    load_production_runs(conn, df_runs)

    LOG.info("========================")
    LOG.info("ROW COUNTS AFTER LOAD")
    LOG.info("========================")

    verify_row_count(conn, "dim_lines", df_lines.shape[0])
    verify_row_count(conn, "dim_products", df_products.shape[0])
    verify_row_count(conn, "fact_production_runs", df_runs.shape[0])

    conn.close()

    LOG.info("Workflow 2-ETL (food manufacturing) complete")
    LOG.info("========================")
    LOG.info("Executed successfully!")
    LOG.info("========================")


if __name__ == "__main__":
    main()
