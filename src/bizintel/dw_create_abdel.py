"""dw_create_abdel.py - custom version.

Creates a star schema data warehouse using DuckDB, extended with
additional derived columns for customers, products, and sales.

This project combines SQL and Python - two key skills for BI development.
It demonstrates recreating an empty star schema data warehouse.
After calling this, call the etl_abdel.py script to load data into the warehouse.

Author: Abdelhafidh Mahouel
Date: 2026-07

Development: This script is intended for development and testing purposes.
  - It drops and recreates the warehouse tables to ensure a clean slate for testing and development.
  - This approach is suitable for development but should be used with caution in production environments.
  - Once a data warehouse is in production, we should use migrations and careful incremental updates.

Process:
    - Create the artifacts/ folder if it does not exist.
    - Connect to (or create) the DuckDB data warehouse.
    - Drop existing tables if they exist.
    - Create dimension tables (customers, products) with additional columns.
    - Create the fact table (sales) with additional columns.
    - Log table creation results.

Additional columns added:
    - dim_customers.customer_tenure_years (DOUBLE)
    - dim_products.price_tier (VARCHAR)
    - fact_sales.sale_year (INTEGER)
    - fact_sales.sale_quarter (VARCHAR)

Output:
- artifacts/smart_sales.duckdb

Terminal command to run this file from the root project folder:

uv run python -m bizintel.dw_create_abdel

OBS:
  This is my custom copy of dw_create_case.py, modified for my own project.
"""

# === Section 1. Import dependencies and set up constants ===


# === IMPORTS (USE uv to CREATE YOUR ENVIRONMENT) ===

from pathlib import Path
from typing import Final

from datafun_toolkit.logger import log_path
import duckdb  # Verify duckdb is in pyproject.toml dependencies

from bizintel.utils_logger import LOG, log_header

# === DECLARE CONSTANTS ===

# Path to the DuckDB data warehouse file.
# DuckDB stores the entire warehouse in one file.
DW_FILE: Final[Path] = Path("artifacts/smart_sales.duckdb")


# === Section 2. Define Reusable Functions ===

# === Section 2.1 DEFINE A CREATE DIMENSION CUSTOMERS FUNCTION ===

# A dimension table holds descriptive attributes about a business entity.
# The customers dimension describes who made each purchase.


def create_dim_customers(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the customers dimension table.

    WHY: Dimension tables hold the descriptive context for our facts.
    The customer dimension lets us analyze sales by region,
    join date, tenure, and other customer attributes.

    Args:
        conn: Open DuckDB connection.

    Returns:
        None
    """
    LOG.info("START create customers dimension table....")

    LOG.info("DROP the table if it already exists so we can recreate it cleanly")
    LOG.info("- Use SQL command: DROP TABLE IF EXISTS dim_customers")
    LOG.info("- Use conn.execute() to run the SQL command")

    conn.execute("DROP TABLE IF EXISTS dim_customers")

    LOG.info("CREATE TABLE with typed columns")
    LOG.info("- Every table should have one primary key column")
    LOG.info("- Look at the data to decide suitable column types")
    LOG.info("- CustomerID is the primary key and should be an INTEGER")
    LOG.info("- Name is text so we use VARCHAR (variable number of characters)")
    LOG.info("- Region is text so we use VARCHAR (variable number of characters)")
    LOG.info("- JoinDate should be a DATE column")
    LOG.info("- customer_tenure_years is my additional column (DOUBLE)")
    LOG.info("  - computed as years since JoinDate, filled in during ETL")

    conn.execute("""
        CREATE TABLE dim_customers (
            CustomerID            INTEGER PRIMARY KEY,
            Name                  VARCHAR,
            Region                VARCHAR,
            JoinDate              DATE,
            customer_tenure_years DOUBLE
        )
    """)

    LOG.info("  dim_customers created.")


# === Section 2.2 DEFINE A CREATE DIMENSION PRODUCTS FUNCTION ===

# The products dimension describes what was purchased.


def create_dim_products(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the products dimension table.

    WHY: The product dimension lets us analyze sales by category,
    price range, price tier, and product name.

    Args:
        conn: Open DuckDB connection.

    Returns:
        None
    """
    LOG.info("START create products dimension table....")

    LOG.info("DROP the table if it already exists so we can recreate it cleanly")
    LOG.info("- Use SQL command: DROP TABLE IF EXISTS dim_products")
    LOG.info("- Use conn.execute() to run the SQL command")

    conn.execute("DROP TABLE IF EXISTS dim_products")

    LOG.info("CREATE TABLE with typed columns")
    LOG.info("- Every table should have one primary key column")
    LOG.info("- Look at the data to decide suitable column types")
    LOG.info("- ProductID is the primary key and should be an INTEGER")
    LOG.info("- ProductName is text so we use VARCHAR (variable number of characters)")
    LOG.info("- Category is text so we use VARCHAR (variable number of characters)")
    LOG.info("- UnitPrice should be a DOUBLE column")
    LOG.info("- price_tier is my additional column (VARCHAR)")
    LOG.info("  - Low/Medium/High bucket computed from UnitPrice during ETL")

    conn.execute("""
        CREATE TABLE dim_products (
            ProductID    INTEGER PRIMARY KEY,
            ProductName  VARCHAR,
            Category     VARCHAR,
            UnitPrice    DOUBLE,
            price_tier   VARCHAR
        )
    """)

    LOG.info("  dim_products created.")


# === Section 2.3 DEFINE A CREATE FACT SALES FUNCTION ===

# A fact table holds the measurable events we want to analyze.
# Each row in the fact table is one transaction.
# Foreign keys link each sale to its customer and product dimensions.


def create_fact_sales(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the sales fact table.

    WHY: The fact table is the center of a star schema.
    It holds the numeric measures (SaleAmount) and foreign keys
    that link to each dimension table, plus derived time columns
    (sale_year, sale_quarter) for easier time-based analysis.

    Args:
        conn: Open DuckDB connection.

    Returns:
        None
    """
    LOG.info("START create sales fact table....")

    LOG.info("DROP the table if it already exists so we can recreate it cleanly")
    LOG.info("- Use SQL command: DROP TABLE IF EXISTS fact_sales")
    LOG.info("- Use conn.execute() to run the SQL command")

    conn.execute("DROP TABLE IF EXISTS fact_sales")

    LOG.info("The fact table references the dimension tables")
    LOG.info("   - use a foreign key to dim_customers(CustomerID)")
    LOG.info("   - use a foreign key to dim_products(ProductID)")

    LOG.info("   - the REFERENCES keyword ensures referential integrity")
    LOG.info("   - every sale must link to a valid customer and product")
    LOG.info("- sale_year and sale_quarter are my additional columns")
    LOG.info("  - both computed from SaleDate during ETL")

    conn.execute("""
        CREATE TABLE fact_sales (
            TransactionID  INTEGER PRIMARY KEY,
            SaleDate       DATE,
            CustomerID     INTEGER REFERENCES dim_customers(CustomerID),
            ProductID      INTEGER REFERENCES dim_products(ProductID),
            StoreID        INTEGER,
            CampaignID     INTEGER,
            SaleAmount     DOUBLE,
            sale_year      INTEGER,
            sale_quarter   VARCHAR
        )
    """)

    LOG.info("  fact_sales created.")


# === Section 2.4 DEFINE A DELETE TABLES FUNCTION ===


def delete_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Delete all tables in reverse order of creation.

    WHY: Ensures a clean slate before creating schema objects.

    Args:
        conn: Open DuckDB connection.

    Returns:
        None
    """
    LOG.info("START delete tables....")

    LOG.info("- Dropping fact_sales table if it exists")
    conn.execute("DROP TABLE IF EXISTS fact_sales")

    LOG.info("- Dropping dim_products table if it exists")
    conn.execute("DROP TABLE IF EXISTS dim_products")

    LOG.info("- Dropping dim_customers table if it exists")
    conn.execute("DROP TABLE IF EXISTS dim_customers")

    LOG.info("  All tables deleted.")


# === Section 2.5 DEFINE A VERIFY FUNCTION ===


def verify_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Log all tables in the warehouse to verify creation.

    WHY: Always verify after creating schema objects.
    A table that fails silently is harder to debug later.

    Args:
        conn: Open DuckDB connection.

    Returns:
        None
    """
    LOG.info("START verify warehouse schema....")

    LOG.info("SHOW TABLES returns a list of all tables in the database")
    LOG.info("- Calling .fetchall() on the result of SHOW TABLES")
    LOG.info("- Gets the result - we can store it in a variable named 'tables'")
    tables = conn.execute("SHOW TABLES").fetchall()

    LOG.info("  - Retrieved tables from the warehouse.")
    LOG.info(" - tables has a tuple for each table in the warehouse")
    LOG.info(" - the first tuple element (at the 0 index) is the table name")
    LOG.info(f"  Tables in warehouse: {[t[0] for t in tables]}")


# === MAIN FUNCTION ===


def main() -> None:
    """Main function to create the data warehouse schema."""

    log_header(LOG, "BI")

    LOG.info("========================")
    LOG.info("START main()")
    LOG.info("========================")

    log_path(LOG, "Data warehouse:", DW_FILE)

    LOG.info("Create the artifacts/ folder if it does not exist")
    DW_FILE.parent.mkdir(parents=True, exist_ok=True)

    LOG.info("Connect to DuckDB - creates the file if it does not exist")
    LOG.info("Connecting to DuckDB data warehouse........")
    conn: duckdb.DuckDBPyConnection = duckdb.connect(str(DW_FILE))

    LOG.info("Created conn: a DuckDB connection object")
    LOG.info("CALL a function to delete tables in reverse order of creation")
    delete_tables(conn)

    LOG.info("CALL a function to create dim_customers........")
    LOG.info("PASS IN conn: the DuckDB connection object")
    create_dim_customers(conn)

    LOG.info("CALL a function to create dim_products........")
    LOG.info("PASS IN conn: the DuckDB connection object")
    create_dim_products(conn)

    LOG.info("CALL a function to create fact_sales........")
    LOG.info("PASS IN conn: the DuckDB connection object")
    create_fact_sales(conn)

    LOG.info("CALL a function to verify the schema........")
    LOG.info("PASS IN conn: the DuckDB connection object")
    verify_schema(conn)

    # Close the connection when done
    conn.close()

    LOG.info("Workflow 1-CREATE DW complete")
    LOG.info("========================")
    LOG.info("Executed successfully!")
    LOG.info("========================")


# === CONDITIONAL EXECUTION GUARD ===

if __name__ == "__main__":
    main()
