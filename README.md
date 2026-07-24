# bintel-04-warehouse

[![Workflow Guide](https://img.shields.io/badge/Pro--Guide-pro--analytics--02-green)](https://denisecase.github.io/pro-analytics-02/workflow-b-apply-example-project/)
[![Python 3.14](https://img.shields.io/badge/python-3.14%2B-blue?logo=python)](./pyproject.toml)
[![MIT](https://img.shields.io/badge/license-see%20LICENSE-yellow.svg)](./LICENSE)

> Professional Python project: building and populating star schema data warehouses using ETVL,
> applied to both a smart sales example and a custom food manufacturing project.

## Project Description

This project focuses on designing star schema data warehouses
and loading prepared data into them using the ETVL process:
Extract from prepared CSV files, Transform for the warehouse schema,
Verify row counts and integrity, then Load into DuckDB.

We work with cleaned smart sales data containing
customers, products, and sales records.

We learn to:

- create a DuckDB data warehouse programmatically
- extract and transform prepared CSV data for the warehouse schema
- verify tables are populated correctly before and after loading
- query the warehouse to confirm data integrity

## Custom Work in This Repo

Beyond the instructor's example, this repo includes two custom additions:

- **`app_abdel.py`** - extends the raw-data exploration example with a
  customer revenue concentration analysis (top 5 customers and their
  share of total revenue), and persists chart images and a results
  table to `artifacts/` instead of only showing temporary chart windows.
- **`dw_create_foodmfg.py` / `etl_foodmfg.py` / `app_foodmfg.py`** - a
  completely separate star schema data warehouse applying the same
  ETVL concepts to a food manufacturing production-monitoring problem:
  tracking production runs across manufacturing lines and food products
  to analyze output volume, defect rates, and downtime by shift.

## Use Your Prepared Data

After running the example,
copy over your data/prepared/ files to use in this project.

## VS Code and DuckDB Files

We've added a new extension to
[**.vscode/extensions.json**](.vscode/extensions.json) to interact with DuckDB.
Accept the recommended extensions and you should get it. If not:

- Open the **Extensions left-side tab** in VS Code.
- Search for: DuckDB
- Install the extension published by **chuckjonas**.

In this project, we create and populate a dw file in the new **artifacts/** folder.
To explore the new DuckDB, open the new **DuckDB left-side tab** in VS Code
and select **smart_sales**.

![Explore DuckDB](docs/images/fig_duckdb_tab.png)

The extension is configured in [**.vscode/settings.json**](.vscode/settings.json).
Change this `settings.json` file to reflect any changes you make, e.g. a new database name.

## Working Files

You'll work with these areas:

- **.vscode/extensions.json** - see the additional "chuckjonas.duckdb" extension
- **.vscode/settings.json** - configure the project DuckDB file (if changes needed)
- **artifacts/** - generated data warehouse file
- **data/prepared** - paste your prepared CSV files (e.g., customers, products, sales)
- **docs/** - provides project narrative and documentation
- **src/bizintel/** - run the examples; copy and paste to your own versions to modify
- **pyproject.toml** - update authorship & links
- **zensical.toml** - update authorship & links

## Instructions (pro-analytics-02)

Follow the
[step-by-step workflow guide](https://denisecase.github.io/pro-analytics-02/workflow-b-apply-example-project/)
to complete:

1. Phase 1. **Start & Run**
2. Phase 2. **Change Authorship**
3. Phase 3. **Read & Understand**
4. Phase 4. **Modify**
5. Phase 5. **Apply**

## Challenges

Challenges are expected.
Sometimes instructions may not quite match your operating system.
When issues occur, share screenshots, error messages, and details about what you tried.
Working through issues is part of implementing professional projects.

## Success

After completing Phase 1. **Start & Run**,
you'll have your own GitHub project,
and running the example module will print out:

```shell
========================
Executed successfully!
========================
```

A new file `project.log` will appear in the root project folder.

## Command Reference

<details>
<summary>Show command reference</summary>

### In a machine terminal (open in your `Repos` folder)

After you get a copy of this repo in your own GitHub account,
open a machine terminal in your `Repos` folder:

```shell
# Replace username with YOUR GitHub username.
git clone https://github.com/AbdelhafidhMahouel/bintel-04-warehouse

cd bintel-04-warehouse
code .
```

### In a VS Code terminal

These are listed for convenience.
For best results, follow the detailed instructions in
[pro-analytics-02 guide](https://denisecase.github.io/pro-analytics-02/).

```shell
uv self update
uv python pin 3.14
uv lock --upgrade
uv sync --extra dev --extra docs --upgrade

uvx pre-commit install
uvx pre-commit autoupdate

git add -A
uvx pre-commit run --all-files
# repeat if changes were made
uvx pre-commit run --all-files

# verify the environment (.venv/)
uv run python -m bizintel.app_case

# Workflow 1: build an empty data warehouse in artifacts/
uv run python -m bizintel.dw_create_case

# Workflow 3: etl (extract-transform-load) prepared data into dw
uv run python -m bizintel.etl_case

# My custom smart sales warehouse (with added columns: customer_tenure_years,
# price_tier, sale_year, sale_quarter)
uv run python -m bizintel.dw_create_abdel
uv run python -m bizintel.etl_abdel

# My technical modification: adds customer revenue concentration analysis
# and persists charts/tables to artifacts/
uv run python -m bizintel.app_abdel

# My custom Phase 5 project: food manufacturing production warehouse
uv run python -m bizintel.dw_create_foodmfg
uv run python -m bizintel.etl_foodmfg
uv run python -m bizintel.app_foodmfg

# run common chores
uv run ruff format .
uv run ruff check . --fix
uv run python -m pyright
uv run python -m pytest
uv run python -m zensical build

# save progress
git add -A
git commit -m "update"
git push -u origin main
```

</details>

## Notes

- Use the **UP ARROW** and **DOWN ARROW** in the terminal to scroll through past commands.
- Use `CTRL+f` to find (and replace) text within a file.
- You do not need to add to or modify `tests/`. They are provided for example only.
- Many files are silent helpers. Explore as you like, but nothing is required.
- You do NOT need to understand everything; understanding builds naturally over time.

## Troubleshooting >>>

If you see something like this in your terminal: `>>>` or `...`
You accidentally started Python interactive mode.
It happens.
Press `Ctrl+c` (both keys together) or `Ctrl+Z` then `Enter` on Windows.

## Troubleshooting "File Used By Another Process"

If you try to run Python that interacts with the DuckDB file and get an error that a
file is being used by another process, just
click the **DuckDB left-side tab**, right-click your database and select **Detach Database**.

## Workflow 1. Verified Output (Example Warehouse)

```shell
| INFO | BI | START verify warehouse schema....
| INFO | BI | SHOW TABLES returns a list of all tables in the database
| INFO | BI |   Tables in warehouse: ['dim_customers', 'dim_products', 'fact_sales']
| INFO | BI | Workflow 1-CREATE DW complete
| INFO | BI | ========================
| INFO | BI | Executed successfully!
| INFO | BI | ========================
```

## Workflow 2. Verified Output (Example Warehouse)

```shell
| INFO | BI | ========================
| INFO | BI | ROW COUNTS AFTER LOAD
| INFO | BI | ========================
| INFO | BI |   PASS: dim_customers has 200 rows
| INFO | BI |   PASS: dim_products has 100 rows
| INFO | BI |   PASS: fact_sales has 2392 rows
| INFO | BI | Workflow 2-ETL complete
| INFO | BI | ========================
| INFO | BI | Executed successfully!
```

## Workflow 3. Verified Output (Food Manufacturing Warehouse - Phase 5)

```shell
| INFO | BI |   Highest-volume line: Line A - Mixing (808,286 units)
| INFO | BI |   Highest average defect rate: Frozen (3.27%)
| INFO | BI |   Highest total downtime shift: Night (29,854 min)
| INFO | BI | Workflow complete
| INFO | BI | ========================
| INFO | BI | Executed successfully!
| INFO | BI | ========================
```

## Findings and Visuals

### Smart Sales Warehouse (Example + My Modification)

![Total Sales by Region](./docs/images/Figure_1.png)

![Total Sales by Product Category](./docs/images/Figure_2.png)

My technical modification (`app_abdel.py`) added a top-5 customer
revenue concentration analysis. Jessica Mora is the top customer at
$260,450.52, and the top 5 customers together represent 21.1% of
total revenue ($802,722.78 of $3,803,615.11).

![Top 5 Customers by Total Sales](./docs/images/top_customers.png)

### Food Manufacturing Warehouse (Phase 5 Custom Project)

Applying the same star schema and ETVL concepts to a food
manufacturing production-monitoring problem, I found:

- **Line A - Mixing** is the highest-volume production line
  (808,286 units produced)
- **Frozen** products have the highest average defect rate (3.27%)
- **Night shift** has the highest total downtime (29,854 minutes)

![Total Units Produced by Line](./docs/images/units_by_line.png)

![Average Defect Rate by Product Category](./docs/images/defect_rate_by_category.png)

![Total Downtime Minutes by Shift](./docs/images/downtime_by_shift.png)

## Project Documentation

Additional project instructions, terms, and notes:

[docs/index.md](docs/index.md)

## Citation

[CITATION.cff](./CITATION.cff)

## License

[MIT](./LICENSE)
