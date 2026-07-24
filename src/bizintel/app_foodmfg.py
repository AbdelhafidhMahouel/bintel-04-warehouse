"""app_foodmfg.py - custom project.

Queries the food_manufacturing.duckdb warehouse (built by
dw_create_foodmfg.py and populated by etl_foodmfg.py) to produce
engineering-relevant production insights: output volume by line,
defect rate by product category, and downtime by shift.

Author: Abdelhafidh Mahouel
Date: 2026-07

Process:
    - Connect to the populated DuckDB warehouse.
    - Query total units produced by production line.
    - Query average defect rate by product category.
    - Query total downtime minutes by shift.
    - Persist chart images and a summary CSV to artifacts/.
    - Log a summary of findings for engineering review.

Data Source:
- artifacts/food_manufacturing.duckdb (built by dw_create_foodmfg.py
  and etl_foodmfg.py)

Output:
- artifacts/food_charts/units_by_line.png
- artifacts/food_charts/defect_rate_by_category.png
- artifacts/food_charts/downtime_by_shift.png
- artifacts/food_insights_summary.csv

Terminal command to run this file from the root project folder:

uv run python -m bizintel.app_foodmfg
"""

# === Section 1. Import dependencies and set up constants ===

from pathlib import Path
from typing import Final

from datafun_toolkit.logger import log_path
import duckdb
import matplotlib.pyplot as plt
import pandas as pd

from bizintel.utils_logger import LOG, log_header
from bizintel.utils_viz import plot_bar

# === DECLARE CONSTANTS ===

DW_FILE: Final[Path] = Path("artifacts/food_manufacturing.duckdb")
CHARTS_DIR: Final[Path] = Path("artifacts/food_charts")
SUMMARY_CSV: Final[Path] = Path("artifacts/food_insights_summary.csv")


# === Section 2. Define Reusable Functions ===

# === Section 2.1 DEFINE A UNITS BY LINE FUNCTION ===


def units_by_line(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Query total units produced by production line.

    WHY: Engineering leads need to know which lines are producing
    the most volume to plan capacity, staffing, and maintenance windows.

    Args:
        conn: Open DuckDB connection.

    Returns:
        DataFrame with LineName and UnitsProduced columns,
        sorted descending.
    """
    LOG.info("Querying total units produced by line")

    df: pd.DataFrame = conn.execute("""
        SELECT
            l.LineName AS LineName,
            SUM(f.UnitsProduced) AS UnitsProduced
        FROM fact_production_runs f
        JOIN dim_lines l ON f.LineID = l.LineID
        GROUP BY l.LineName
        ORDER BY UnitsProduced DESC
    """).df()

    top_line: str = str(df.iloc[0]["LineName"])
    top_units: int = int(df.iloc[0]["UnitsProduced"])
    LOG.info(f"  Highest-volume line: {top_line} ({top_units:,} units)")

    return df


# === Section 2.2 DEFINE A DEFECT RATE BY CATEGORY FUNCTION ===


def defect_rate_by_category(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Query average defect rate percentage by product category.

    WHY: Quality control needs to know which product categories have
    the highest defect rates so root-cause investigation can be
    prioritized where it matters most.

    Args:
        conn: Open DuckDB connection.

    Returns:
        DataFrame with Category and AvgDefectRatePct columns,
        sorted descending.
    """
    LOG.info("Querying average defect rate by product category")

    df: pd.DataFrame = conn.execute("""
        SELECT
            p.Category AS Category,
            ROUND(AVG(f.DefectRatePct), 2) AS AvgDefectRatePct
        FROM fact_production_runs f
        JOIN dim_products p ON f.ProductID = p.ProductID
        GROUP BY p.Category
        ORDER BY AvgDefectRatePct DESC
    """).df()

    worst_cat: str = str(df.iloc[0]["Category"])
    worst_rate: float = float(df.iloc[0]["AvgDefectRatePct"])
    LOG.info(f"  Highest average defect rate: {worst_cat} ({worst_rate}%)")

    return df


# === Section 2.3 DEFINE A DOWNTIME BY SHIFT FUNCTION ===


def downtime_by_shift(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Query total downtime minutes by shift.

    WHY: Operations needs to know whether downtime is concentrated
    in a particular shift, which could point to staffing, training,
    or handoff issues between shifts.

    Args:
        conn: Open DuckDB connection.

    Returns:
        DataFrame with ShiftName and TotalDowntimeMinutes columns,
        sorted descending.
    """
    LOG.info("Querying total downtime minutes by shift")

    df: pd.DataFrame = conn.execute("""
        SELECT
            ShiftName,
            SUM(DowntimeMinutes) AS TotalDowntimeMinutes
        FROM fact_production_runs
        GROUP BY ShiftName
        ORDER BY TotalDowntimeMinutes DESC
    """).df()

    worst_shift: str = str(df.iloc[0]["ShiftName"])
    worst_minutes: float = float(df.iloc[0]["TotalDowntimeMinutes"])
    LOG.info(
        f"  Highest total downtime shift: {worst_shift} ({worst_minutes:,.0f} min)"
    )

    return df


# === Section 2.4 DEFINE A PERSIST CHART FUNCTION ===


def save_current_figure(filename: str) -> None:
    """Save the most recently created matplotlib figure to artifacts/food_charts/.

    Args:
        filename: Name of the PNG file to save.

    Returns:
        None
    """
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path: Path = CHARTS_DIR / filename
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    LOG.info(f"  Saved chart: {output_path}")


# === MAIN FUNCTION ===


def main() -> None:
    """Main function to run the food manufacturing analysis."""

    log_header(LOG, "BI")

    LOG.info("========================")
    LOG.info("START main()")
    LOG.info("========================")

    log_path(LOG, "Data warehouse:", DW_FILE)

    LOG.info("Connecting to DuckDB data warehouse........")
    conn: duckdb.DuckDBPyConnection = duckdb.connect(str(DW_FILE), read_only=True)

    LOG.info("CALL a function to get units produced by line........")
    df_units = units_by_line(conn)

    LOG.info("CALL a function to plot units by line........")
    plot_bar(
        df=df_units,
        x="LineName",
        y="UnitsProduced",
        title="Total Units Produced by Line",
        xlabel="Production Line",
        ylabel="Units Produced",
        palette="Blues_d",
    )
    save_current_figure("units_by_line.png")

    LOG.info("CALL a function to get defect rate by category........")
    df_defects = defect_rate_by_category(conn)

    LOG.info("CALL a function to plot defect rate by category........")
    plot_bar(
        df=df_defects,
        x="Category",
        y="AvgDefectRatePct",
        title="Average Defect Rate by Product Category",
        xlabel="Category",
        ylabel="Average Defect Rate (%)",
        palette="Reds_d",
    )
    save_current_figure("defect_rate_by_category.png")

    LOG.info("CALL a function to get downtime by shift........")
    df_downtime = downtime_by_shift(conn)

    LOG.info("CALL a function to plot downtime by shift........")
    plot_bar(
        df=df_downtime,
        x="ShiftName",
        y="TotalDowntimeMinutes",
        title="Total Downtime Minutes by Shift",
        xlabel="Shift",
        ylabel="Total Downtime (minutes)",
        palette="Oranges_d",
    )
    save_current_figure("downtime_by_shift.png")

    LOG.info("CALL a function to persist a combined insights summary........")
    summary_rows = [
        {
            "Metric": "Highest-volume line",
            "Value": str(df_units.iloc[0]["LineName"]),
            "Detail": f"{int(df_units.iloc[0]['UnitsProduced']):,} units",
        },
        {
            "Metric": "Highest avg defect rate category",
            "Value": str(df_defects.iloc[0]["Category"]),
            "Detail": f"{df_defects.iloc[0]['AvgDefectRatePct']}%",
        },
        {
            "Metric": "Highest downtime shift",
            "Value": str(df_downtime.iloc[0]["ShiftName"]),
            "Detail": f"{df_downtime.iloc[0]['TotalDowntimeMinutes']:,.0f} minutes",
        },
    ]
    df_summary = pd.DataFrame(summary_rows)
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_summary.to_csv(SUMMARY_CSV, index=False)
    LOG.info(f"  Saved summary: {SUMMARY_CSV}")

    conn.close()

    LOG.info("CALL a function to show charts........")
    plt.show()

    LOG.info("Workflow complete")
    LOG.info("CLOSE chart windows to continue.")
    LOG.info("========================")
    LOG.info("Executed successfully!")
    LOG.info("========================")


if __name__ == "__main__":
    main()
