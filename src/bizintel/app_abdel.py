"""app_abdel.py - custom version.

An extended version of the raw data exploration example that adds
customer revenue concentration analysis and persists chart images
and derived tables as reusable artifacts, instead of only displaying
transient chart windows.

Author: Abdelhafidh Mahouel
Date: 2026-07

Process:
    - Load raw CSV data files.
    - Visualize sales by region and product category.
    - Identify the top N customers by total sales.
    - Compute what share of total revenue those top customers represent
      (a customer revenue concentration / Pareto-style analysis).
    - Persist chart images and the top-customers table to artifacts/
      so results survive after the script exits, not just while
      the chart windows are open.
    - Log a summary of findings.

Data Source:
- data/raw/customers_data.csv
- data/raw/products_data.csv
- data/raw/sales_data.csv

Output:
- artifacts/charts/sales_by_region.png
- artifacts/charts/sales_by_category.png
- artifacts/charts/top_customers.png
- artifacts/top_customers.csv

Terminal command to run this file from the root project folder:

uv run python -m bizintel.app_abdel

OBS:
  This is my custom copy of app_case.py, modified for my own project.
"""

# === Section 1. Import dependencies and set up constants ===

# === DECLARE IMPORTS (bring in free code from elsewhere) ===

from pathlib import Path
from typing import Final

from datafun_toolkit.logger import log_path
import matplotlib.pyplot as plt
import pandas as pd

from bizintel.utils_data import (
    load_data,
)
from bizintel.utils_logger import LOG, log_header
from bizintel.utils_viz import plot_bar

# === DECLARE GLOBAL CONSTANTS AND CONFIGURATION ===

# Raw data folder path (relative to the root project folder).
DATA_RAW: Final[Path] = Path("data/raw")

# The three raw data files for the smart sales project.
CUSTOMERS_FILE: Final[Path] = DATA_RAW / "customers_data.csv"
PRODUCTS_FILE: Final[Path] = DATA_RAW / "products_data.csv"
SALES_FILE: Final[Path] = DATA_RAW / "sales_data.csv"

# Output folders for persisted artifacts.
ARTIFACTS_DIR: Final[Path] = Path("artifacts")
CHARTS_DIR: Final[Path] = ARTIFACTS_DIR / "charts"
TOP_CUSTOMERS_CSV: Final[Path] = ARTIFACTS_DIR / "top_customers.csv"

# How many top customers to analyze.
TOP_N_CUSTOMERS: Final[int] = 5


# === Section 2. Define Reusable Functions ===

# === Section 2.1 DEFINE A SALES BY REGION FUNCTION ===


def sales_by_region(
    df_customers: pd.DataFrame,
    df_sales: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate total sales amount by customer region.

    Args:
        df_customers: Customers DataFrame with CustomerID and Region columns.
        df_sales: Sales DataFrame with CustomerID and SaleAmount columns.

    Returns:
        DataFrame with Region and SaleAmount columns, sorted by SaleAmount.
    """
    LOG.info("Aggregating sales by region")

    df_sales = df_sales.copy()
    df_sales["SaleAmount"] = pd.to_numeric(df_sales["SaleAmount"], errors="coerce")

    df_merged: pd.DataFrame = df_sales.merge(
        df_customers[["CustomerID", "Region"]],
        on="CustomerID",
        how="left",
    )

    df_merged["Region"] = df_merged["Region"].str.strip().str.title()

    grouped: pd.Series = pd.Series(df_merged.groupby("Region")["SaleAmount"].sum())

    df_region: pd.DataFrame = grouped.reset_index().sort_values(
        "SaleAmount", ascending=False
    )

    top_region: str = str(df_region.iloc[0]["Region"])
    top_sales: float = float(df_region.iloc[0]["SaleAmount"])
    LOG.info(f"  Top region: {top_region} (${top_sales:,.2f})")

    return df_region


# === Section 2.2 DEFINE A SALES BY CATEGORY FUNCTION ===


def sales_by_category(
    df_products: pd.DataFrame,
    df_sales: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate total sales amount by product category.

    Args:
        df_products: Products DataFrame with ProductID and Category columns.
        df_sales: Sales DataFrame with ProductID and SaleAmount columns.

    Returns:
        DataFrame with Category and SaleAmount columns, sorted by SaleAmount.
    """
    LOG.info("Aggregating sales by product category")

    df_sales = df_sales.copy()
    df_sales["SaleAmount"] = pd.to_numeric(df_sales["SaleAmount"], errors="coerce")

    df_merged: pd.DataFrame = df_sales.merge(
        df_products[["ProductID", "Category"]],
        on="ProductID",
        how="left",
    )

    grouped: pd.Series = pd.Series(df_merged.groupby("Category")["SaleAmount"].sum())

    df_category: pd.DataFrame = grouped.reset_index().sort_values(
        "SaleAmount", ascending=False
    )

    top_category: str = str(df_category.iloc[0]["Category"])
    top_sales: float = float(df_category.iloc[0]["SaleAmount"])
    LOG.info(f"  Top category: {top_category} (${top_sales:,.2f})")

    return df_category


# === Section 2.3 DEFINE A TOP CUSTOMERS FUNCTION (MY MODIFICATION) ===

# WHY: Knowing which regions and categories drive revenue is useful,
# but BI analysts also need to know how concentrated revenue is
# among individual customers. If a small number of customers account
# for a large share of revenue, that's a retention risk worth flagging
# to the business. This is a lightweight version of a Pareto (80/20)
# analysis, a standard technique in customer analytics.


def top_customers_by_revenue(
    df_customers: pd.DataFrame,
    df_sales: pd.DataFrame,
    top_n: int = TOP_N_CUSTOMERS,
) -> tuple[pd.DataFrame, float]:
    """Identify the top N customers by total sales and their revenue share.

    WHY: Understanding revenue concentration helps the business assess
    dependency risk. If the top few customers represent a large
    percentage of total revenue, losing even one could meaningfully
    affect the business.

    Args:
        df_customers: Customers DataFrame with CustomerID and Name columns.
        df_sales: Sales DataFrame with CustomerID and SaleAmount columns.
        top_n: Number of top customers to return.

    Returns:
        A tuple of:
            - DataFrame with Name and SaleAmount columns for the top N
              customers, sorted by SaleAmount descending.
            - The percentage of total revenue those top N customers
              represent, as a float (e.g. 12.5 means 12.5%).
    """
    LOG.info(f"Aggregating sales by customer (top {top_n})")

    df_sales = df_sales.copy()
    df_sales["SaleAmount"] = pd.to_numeric(df_sales["SaleAmount"], errors="coerce")

    df_merged: pd.DataFrame = df_sales.merge(
        df_customers[["CustomerID", "Name"]],
        on="CustomerID",
        how="left",
    )

    grouped: pd.Series = pd.Series(df_merged.groupby("Name")["SaleAmount"].sum())

    df_all_customers: pd.DataFrame = grouped.reset_index().sort_values(
        "SaleAmount", ascending=False
    )

    total_revenue: float = float(df_all_customers["SaleAmount"].sum())

    df_top: pd.DataFrame = df_all_customers.head(top_n).reset_index(drop=True)
    top_n_revenue: float = float(df_top["SaleAmount"].sum())

    revenue_share_pct: float = (
        (top_n_revenue / total_revenue * 100) if total_revenue else 0.0
    )

    top_name: str = str(df_top.iloc[0]["Name"])
    top_sales: float = float(df_top.iloc[0]["SaleAmount"])
    LOG.info(f"  Top customer: {top_name} (${top_sales:,.2f})")
    LOG.info(
        f"  Top {top_n} customers represent {revenue_share_pct:.1f}% "
        f"of total revenue (${top_n_revenue:,.2f} of ${total_revenue:,.2f})"
    )

    return df_top, revenue_share_pct


# === Section 2.4 DEFINE A PERSIST CHART FUNCTION (MY MODIFICATION) ===

# WHY: The example project only displays charts in pop-up windows,
# which disappear once closed. A professional BI workflow should
# save chart images as artifacts so they can be reused in reports,
# shared with stakeholders, or embedded in documentation without
# needing to rerun the script.


def save_current_figure(filename: str) -> None:
    """Save the most recently created matplotlib figure to artifacts/charts/.

    WHY: Persisting chart images turns a one-time visual into a
    reusable artifact for reports and documentation.

    Args:
        filename: Name of the PNG file to save (e.g. "sales_by_region.png").

    Returns:
        None
    """
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path: Path = CHARTS_DIR / filename
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    LOG.info(f"  Saved chart: {output_path}")


# === Section 2.5 DEFINE A SUMMARIZE FUNCTION ===


def summarize(
    df_customers: pd.DataFrame,
    df_products: pd.DataFrame,
    df_sales: pd.DataFrame,
    revenue_share_pct: float,
    top_n: int,
) -> None:
    """Log a brief summary of all three datasets and the concentration finding.

    Args:
        df_customers: Customers DataFrame.
        df_products: Products DataFrame.
        df_sales: Sales DataFrame.
        revenue_share_pct: Percentage of total revenue held by the top N customers.
        top_n: Number of top customers used in the concentration analysis.

    Returns:
        None
    """
    LOG.info("========================")
    LOG.info("SUMMARY")
    LOG.info("========================")

    cust_rows: int = df_customers.shape[0]
    cust_cols: int = df_customers.shape[1]
    prod_rows: int = df_products.shape[0]
    prod_cols: int = df_products.shape[1]
    sale_rows: int = df_sales.shape[0]
    sale_cols: int = df_sales.shape[1]

    LOG.info(f"Customers:  {cust_rows} rows, {cust_cols} columns")
    LOG.info(f"Products:   {prod_rows} rows, {prod_cols} columns")
    LOG.info(f"Sales:      {sale_rows} rows, {sale_cols} columns")

    LOG.info("========================")
    LOG.info("ANALYST NOTES:")
    LOG.info(
        f"The top {top_n} customers account for {revenue_share_pct:.1f}% "
        "of total revenue."
    )
    LOG.info(
        "This concentration level should inform retention priorities: "
        "the higher this percentage, the more revenue risk is tied to "
        "a small number of accounts."
    )
    LOG.info("========================")


# === DEFINE THE MAIN FUNCTION (WHERE THE MAGIC HAPPENS) ===


def main() -> None:
    """Main function to run the extended BI logic.
    This is where the main logic starts when this script is run.
    """

    log_header(LOG, "BI")

    LOG.info("========================")
    LOG.info("START main()")
    LOG.info("========================")

    log_path(LOG, "Raw data: ", DATA_RAW)
    log_path(LOG, "Customers:", CUSTOMERS_FILE)
    log_path(LOG, "Products: ", PRODUCTS_FILE)
    log_path(LOG, "Sales:    ", SALES_FILE)

    LOG.info("CALL a function to load each dataset.............")
    df_customers = load_data(CUSTOMERS_FILE, "customers")
    df_products = load_data(PRODUCTS_FILE, "products")
    df_sales = load_data(SALES_FILE, "sales")

    LOG.info("CALL a function to get sales by region........")
    df_region = sales_by_region(df_customers, df_sales)

    LOG.info("CALL a function to plot sales by region........")
    plot_bar(
        df=df_region,
        x="Region",
        y="SaleAmount",
        title="Total Sales by Region",
        xlabel="Region",
        ylabel="Total Sales Amount ($)",
        palette="Blues_d",
    )
    save_current_figure("sales_by_region.png")

    LOG.info("CALL a function to get sales by product category........")
    df_category = sales_by_category(df_products, df_sales)

    LOG.info("CALL a function to plot sales by product category........")
    plot_bar(
        df=df_category,
        x="Category",
        y="SaleAmount",
        title="Total Sales by Product Category",
        xlabel="Category",
        ylabel="Total Sales Amount ($)",
        palette="Greens_d",
    )
    save_current_figure("sales_by_category.png")

    LOG.info("CALL a function to get top customers by revenue........")
    df_top_customers, revenue_share_pct = top_customers_by_revenue(
        df_customers, df_sales, top_n=TOP_N_CUSTOMERS
    )

    LOG.info("CALL a function to plot top customers........")
    plot_bar(
        df=df_top_customers,
        x="Name",
        y="SaleAmount",
        title=f"Top {TOP_N_CUSTOMERS} Customers by Total Sales",
        xlabel="Customer",
        ylabel="Total Sales Amount ($)",
        palette="Oranges_d",
    )
    save_current_figure("top_customers.png")

    LOG.info("CALL a function to persist the top customers table........")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    df_top_customers.to_csv(TOP_CUSTOMERS_CSV, index=False)
    LOG.info(f"  Saved table: {TOP_CUSTOMERS_CSV}")

    LOG.info("CALL a function to summarize the datasets........")
    summarize(
        df_customers,
        df_products,
        df_sales,
        revenue_share_pct=revenue_share_pct,
        top_n=TOP_N_CUSTOMERS,
    )

    LOG.info("CALL a function to show charts........")
    plt.show()

    LOG.info("Workflow complete")
    LOG.info("CLOSE chart windows to continue.")
    LOG.info("Terminate this process with CTRL+c as needed.")
    LOG.info("========================")
    LOG.info("Executed successfully!")
    LOG.info("========================")


# === CONDITIONAL EXECUTION GUARD ===

if __name__ == "__main__":
    main()
