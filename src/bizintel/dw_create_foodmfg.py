"""dw_create_foodmfg.py - custom project.

Creates a star schema data warehouse for a food manufacturing
production-monitoring use case using DuckDB.

This applies the same star schema and ETVL concepts used in the
smart sales warehouse example to a different domain: tracking
production runs across manufacturing lines and product batches,
so an engineering team can analyze output volume, defect rates,
and downtime.

Author: Abdelhafidh Mahouel
Date: 2026-07

Process:
    - Create the artifacts/ folder if it does not exist.
    - Connect to (or create) the DuckDB data warehouse.
    - Drop existing tables if they exist.
    - Create dimension tables (lines, products).
    - Create the fact table (production_runs).
    - Log table creation results.

Output:
- artifacts/food_manufacturing.duckdb

Terminal command to run this file from the root project folder:

uv run python -m bizintel.dw_create_foodmfg
"""

# === Section 1. Import dependencies and set up constants ===

from pathlib import Path
from typing import Final

from datafun_toolkit.logger import log_path
import duckdb

from bizintel.utils_logger import LOG, log_header

# === DECLARE CONSTANTS ===

DW_FILE: Final[Path] = Path("artifacts/food_manufacturing.duckdb")


# === Section 2. Define Reusable Functions ===

# === Section 2.1 DEFINE A CREATE DIMENSION LINES FUNCTION ===

# The lines dimension describes which production line ran each batch.


def create_dim_lines(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the production lines dimension table.

    WHY: The lines dimension lets us analyze production output,
    defect rates, and downtime by physical production line and plant.

    Args:
        conn: Open DuckDB connection.

    Returns:
        None
    """
    LOG.info("START create lines dimension table....")

    conn.execute("DROP TABLE IF EXISTS dim_lines")

    LOG.info("CREATE TABLE with typed columns")
    LOG.info("- LineID is the primary key and should be an INTEGER")
    LOG.info("- LineName and Plant are text so we use VARCHAR")
    LOG.info("- CapacityUnitsPerHour should be an INTEGER")

    conn.execute("""
        CREATE TABLE dim_lines (
            LineID                INTEGER PRIMARY KEY,
            LineName              VARCHAR,
            Plant                 VARCHAR,
            CapacityUnitsPerHour  INTEGER
        )
    """)

    LOG.info("  dim_lines created.")


# === Section 2.2 DEFINE A CREATE DIMENSION PRODUCTS FUNCTION ===

# The products dimension describes what food product was produced.


def create_dim_products(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the products dimension table.

    WHY: The product dimension lets us analyze production and
    defect metrics by product category, batch size, and shelf life.

    Args:
        conn: Open DuckDB connection.

    Returns:
        None
    """
    LOG.info("START create products dimension table....")

    conn.execute("DROP TABLE IF EXISTS dim_products")

    LOG.info("CREATE TABLE with typed columns")
    LOG.info("- ProductID is the primary key and should be an INTEGER")
    LOG.info("- ProductName and Category are text so we use VARCHAR")
    LOG.info("- BatchSizeKg should be a DOUBLE column")
    LOG.info("- ShelfLifeDays should be an INTEGER column")

    conn.execute("""
        CREATE TABLE dim_products (
            ProductID      INTEGER PRIMARY KEY,
            ProductName    VARCHAR,
            Category       VARCHAR,
            BatchSizeKg    DOUBLE,
            ShelfLifeDays  INTEGER
        )
    """)

    LOG.info("  dim_products created.")


# === Section 2.3 DEFINE A CREATE FACT PRODUCTION RUNS FUNCTION ===

# A fact table holds the measurable events we want to analyze.
# Each row represents one production run (one batch produced on one
# line, on one date, on one shift).


def create_fact_production_runs(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the production runs fact table.

    WHY: The fact table is the center of the star schema. It holds
    the numeric measures (units produced, defects, downtime) and
    foreign keys that link to each dimension table. The grain of
    this fact table is one production run.

    Args:
        conn: Open DuckDB connection.

    Returns:
        None
    """
    LOG.info("START create production runs fact table....")

    conn.execute("DROP TABLE IF EXISTS fact_production_runs")

    LOG.info("The fact table references the dimension tables")
    LOG.info("   - use a foreign key to dim_lines(LineID)")
    LOG.info("   - use a foreign key to dim_products(ProductID)")

    conn.execute("""
        CREATE TABLE fact_production_runs (
            RunID             INTEGER PRIMARY KEY,
            RunDate           DATE,
            LineID            INTEGER REFERENCES dim_lines(LineID),
            ProductID         INTEGER REFERENCES dim_products(ProductID),
            ShiftName         VARCHAR,
            UnitsProduced     INTEGER,
            DefectUnits       INTEGER,
            DowntimeMinutes   DOUBLE,
            DefectRatePct     DOUBLE
        )
    """)

    LOG.info("  fact_production_runs created.")


# === Section 2.4 DEFINE A DELETE TABLES FUNCTION ===


def delete_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Delete all tables in reverse order of creation.

    Args:
        conn: Open DuckDB connection.

    Returns:
        None
    """
    LOG.info("START delete tables....")
    conn.execute("DROP TABLE IF EXISTS fact_production_runs")
    conn.execute("DROP TABLE IF EXISTS dim_products")
    conn.execute("DROP TABLE IF EXISTS dim_lines")
    LOG.info("  All tables deleted.")


# === Section 2.5 DEFINE A VERIFY FUNCTION ===


def verify_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Log all tables in the warehouse to verify creation.

    Args:
        conn: Open DuckDB connection.

    Returns:
        None
    """
    LOG.info("START verify warehouse schema....")
    tables = conn.execute("SHOW TABLES").fetchall()
    LOG.info(f"  Tables in warehouse: {[t[0] for t in tables]}")


# === MAIN FUNCTION ===


def main() -> None:
    """Main function to create the food manufacturing warehouse schema."""

    log_header(LOG, "BI")

    LOG.info("========================")
    LOG.info("START main()")
    LOG.info("========================")

    log_path(LOG, "Data warehouse:", DW_FILE)

    DW_FILE.parent.mkdir(parents=True, exist_ok=True)

    LOG.info("Connecting to DuckDB data warehouse........")
    conn: duckdb.DuckDBPyConnection = duckdb.connect(str(DW_FILE))

    delete_tables(conn)
    create_dim_lines(conn)
    create_dim_products(conn)
    create_fact_production_runs(conn)
    verify_schema(conn)

    conn.close()

    LOG.info("Workflow 1-CREATE DW (food manufacturing) complete")
    LOG.info("========================")
    LOG.info("Executed successfully!")
    LOG.info("========================")


if __name__ == "__main__":
    main()
