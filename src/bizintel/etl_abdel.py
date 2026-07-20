"""etl_abdel.py - custom version.

Loads prepared data into the data warehouse, computing additional
derived columns for customers, products, and sales along the way.
We call this ETL (Extract, Transform, Load).

Before this, call the dw_create_abdel.py script to create the empty data warehouse.

Author: Abdelhafidh Mahouel
Date: 2026-07

Process:
    - Connect to the DuckDB data warehouse.
    - Extract prepared CSV files.
    - Transform data to match the warehouse schema, including new derived columns:
        - customer_tenure_years (dim_customers)
        - price_tier (dim_products)
        - sale_year, sale_quarter (fact_sales)
    - Verify row counts before loading.
    - Load data into dimension and fact tables.
    - Verify row counts after loading.

Data Source:
- data/prepared/customers_data_prepared.csv
- data/prepared/products_data_prepared.csv
- data/prepared/sales_data_prepared.csv

Output:
- artifacts/smart_sales.duckdb (populated)

Terminal command to run this file from the root project folder:

uv run python -m bizintel.etl_abdel

OBS:
  This is my custom copy of etl_case.py, modified for my own project.
  Run dw_create_abdel.py first to (re)create the schema before running this.
"""

# === Section 1. Import dependencies and set up constants ===

# === IMPORTS ===

from pathlib import Path
from typing import Final

from datafun_toolkit.logger import log_path
import duckdb
import pandas as pd

from bizintel.utils_data import load_data
from bizintel.utils_logger import LOG, log_header

# === DECLARE CONSTANTS ===

# Prepared data folder path.
DATA_PREPARED: Final[Path] = Path("data/prepared")

# Prepared input files.
CUSTOMERS_PREPARED: Final[Path] = DATA_PREPARED / "customers_data_prepared.csv"
PRODUCTS_PREPARED: Final[Path] = DATA_PREPARED / "products_data_prepared.csv"
SALES_PREPARED: Final[Path] = DATA_PREPARED / "sales_data_prepared.csv"

# Path to the DuckDB data warehouse file.
DW_FILE: Final[Path] = Path("artifacts/smart_sales.duckdb")

# Price tier thresholds for dim_products.price_tier
# Based on the actual UnitPrice range in this dataset (~$13.51-$976.44)
PRICE_TIER_LOW_MAX: Final[float] = 335.0
PRICE_TIER_MEDIUM_MAX: Final[float] = 667.0


# === Section 2. Define Reusable Functions ===

# === Section 2.1 DEFINE A VERIFY ROW COUNT FUNCTION ===


def verify_row_count(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    expected: int,
) -> None:
    """Verify that a table contains the expected number of rows.

    WHY: Row count verification is the simplest and most important
    check after loading data. If the counts do not match,
    something went wrong in the load step.

    Args:
        conn: Open DuckDB connection.
        table: Table name to check.
        expected: Expected number of rows.

    Returns:
        None
    """
    # COUNT(*) returns the number of rows in the table
    result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    actual: int = int(result[0]) if result else 0

    if actual == expected:
        LOG.info(f"  PASS: {table} has {actual} rows")
    else:
        LOG.warning(f"  FAIL: {table} expected {expected} rows, got {actual}")


# === Section 2.2 DEFINE A LOAD CUSTOMERS FUNCTION ===


def load_customers(
    conn: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
) -> None:
    """Load prepared customers data into dim_customers.

    WHY: We load dimension tables before the fact table
    because the fact table has foreign keys that reference them.

    Adds my additional column:
        - customer_tenure_years: years since JoinDate, computed as of today.

    Args:
        conn: Open DuckDB connection.
        df: Prepared customers DataFrame.

    Returns:
        None
    """
    LOG.info("Loading customers into dim_customers")

    df = df.copy()

    # Convert JoinDate to datetime so DuckDB stores it as DATE
    df["JoinDate"] = pd.to_datetime(df["JoinDate"], errors="coerce")

    # My additional column: customer_tenure_years
    # Computed as the number of years between JoinDate and today
    today = pd.Timestamp.now()
    df["customer_tenure_years"] = (today - df["JoinDate"]).dt.days / 365.25

    # INSERT INTO ... SELECT ... FROM df inserts all rows at once
    # DuckDB can read pandas DataFrames directly
    conn.execute("""
        INSERT INTO dim_customers
        SELECT
            CustomerID,
            Name,
            Region,
            JoinDate,
            customer_tenure_years
        FROM df
    """)

    LOG.info(f"  Loaded {df.shape[0]} rows into dim_customers")


# === Section 2.3 DEFINE A LOAD PRODUCTS FUNCTION ===


def load_products(
    conn: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
) -> None:
    """Load prepared products data into dim_products.

    Adds my additional column:
        - price_tier: Low/Medium/High bucket computed from UnitPrice.

    Args:
        conn: Open DuckDB connection.
        df: Prepared products DataFrame.

    Returns:
        None
    """
    LOG.info("Loading products into dim_products")

    df = df.copy()
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")

    # My additional column: price_tier
    # Buckets UnitPrice into Low / Medium / High
    def price_tier(price: float) -> str:
        if pd.isna(price):
            return "Unknown"
        if price < PRICE_TIER_LOW_MAX:
            return "Low"
        elif price < PRICE_TIER_MEDIUM_MAX:
            return "Medium"
        else:
            return "High"

    df["price_tier"] = df["UnitPrice"].apply(price_tier)

    conn.execute("""
        INSERT INTO dim_products
        SELECT
            ProductID,
            ProductName,
            Category,
            UnitPrice,
            price_tier
        FROM df
    """)

    LOG.info(f"  Loaded {df.shape[0]} rows into dim_products")


# === Section 2.4 DEFINE A LOAD SALES FUNCTION ===


def load_sales(
    conn: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
) -> None:
    """Load prepared sales data into fact_sales.

    WHY: The fact table is loaded last because it references
    both dimension tables via foreign keys.
    Loading it first would fail referential integrity checks.

    Adds my additional columns:
        - sale_year: calendar year extracted from SaleDate.
        - sale_quarter: quarter (Q1-Q4) extracted from SaleDate.

    Args:
        conn: Open DuckDB connection.
        df: Prepared sales DataFrame.

    Returns:
        None
    """
    LOG.info("Loading sales into fact_sales")

    df = df.copy()
    df["SaleDate"] = pd.to_datetime(df["SaleDate"], errors="coerce")
    df["SaleAmount"] = pd.to_numeric(df["SaleAmount"], errors="coerce")

    # My additional columns: sale_year and sale_quarter
    # Both derived from SaleDate to make time-based analysis easier
    df["sale_year"] = df["SaleDate"].dt.year
    df["sale_quarter"] = "Q" + df["SaleDate"].dt.quarter.astype("Int64").astype(str)

    conn.execute("""
        INSERT INTO fact_sales
        SELECT
            TransactionID,
            SaleDate,
            CustomerID,
            ProductID,
            StoreID,
            CampaignID,
            SaleAmount,
            sale_year,
            sale_quarter
        FROM df
    """)

    LOG.info(f"  Loaded {df.shape[0]} rows into fact_sales")


# === MAIN FUNCTION ===


def main() -> None:
    """Main function to run the ETL load logic."""

    log_header(LOG, "BI")

    LOG.info("========================")
    LOG.info("START main()")
    LOG.info("========================")

    log_path(LOG, "Prepared data:", DATA_PREPARED)
    log_path(LOG, "Data warehouse:", DW_FILE)

    LOG.info("CALL a function to load each prepared dataset.............")
    df_customers = load_data(CUSTOMERS_PREPARED, "customers prepared")
    df_products = load_data(PRODUCTS_PREPARED, "products prepared")
    df_sales = load_data(SALES_PREPARED, "sales prepared")

    # Log expected row counts before loading
    LOG.info("========================")
    LOG.info("ROW COUNTS BEFORE LOAD")
    LOG.info("========================")
    LOG.info(f"  Customers: {df_customers.shape[0]} rows")
    LOG.info(f"  Products:  {df_products.shape[0]} rows")
    LOG.info(f"  Sales:     {df_sales.shape[0]} rows")

    # Connect to the DuckDB data warehouse
    LOG.info("Connecting to DuckDB data warehouse........")
    conn: duckdb.DuckDBPyConnection = duckdb.connect(str(DW_FILE))

    # Load dimension tables first, then the fact table
    LOG.info("CALL a function to load customers........")
    load_customers(conn, df_customers)

    LOG.info("CALL a function to load products........")
    load_products(conn, df_products)

    LOG.info("CALL a function to load sales........")
    load_sales(conn, df_sales)

    # Verify row counts after loading
    LOG.info("========================")
    LOG.info("ROW COUNTS AFTER LOAD")
    LOG.info("========================")

    LOG.info("CALL a function to verify row counts........")
    verify_row_count(conn, "dim_customers", df_customers.shape[0])
    verify_row_count(conn, "dim_products", df_products.shape[0])
    verify_row_count(conn, "fact_sales", df_sales.shape[0])

    # Close the connection when done
    conn.close()

    LOG.info("Workflow 2-ETL complete")
    LOG.info("========================")
    LOG.info("Executed successfully!")
    LOG.info("========================")


# === CONDITIONAL EXECUTION GUARD ===

if __name__ == "__main__":
    main()
