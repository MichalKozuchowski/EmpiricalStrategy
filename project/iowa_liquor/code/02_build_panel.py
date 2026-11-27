"""
02_build_panel.py: turn ~22M store-order rows (2018-2025) into analysis panels with DuckDB (never loads all rows in pandas).

Steps (each streams to Parquet, so memory stays small; DuckDB spills to disk if needed):
  1. orders.parquet            typed, slim copy of every order line (bottles > 0)
  2. item_month.parquet        product (item_no) x month, statewide: bottles, liters, dollars, posted price, # prices, # stores
  3. county_item_month.parquet county x product x month (for county markets / heterogeneity)
  4. items.parquet             one row per item: its (most common) category, vendor, name, size, pack
  5. categories.csv            every category with items / bottles / dollars (to hand-code nests + tariff exposure)

Price facts behind this design (docs/data_notes.md): the state charges every store the same price (0.03% exceptions),
the portal blanks cost/retail -> price = dollars / bottles, and retail = 1.5 x cost -> cost = price / 1.5.

Run:  uv run --with duckdb --with pandas --with pyarrow python code/02_build_panel.py
"""
import os
import duckdb

DATA_DIR = os.environ.get("IOWA_DATA_DIR", os.path.expanduser("~/mgt634_data/iowa_liquor"))
RAW, BUILD = os.path.join(DATA_DIR, "raw"), os.path.join(DATA_DIR, "build")
os.makedirs(BUILD, exist_ok=True)
YEARS = range(2018, 2026)
P = lambda name: os.path.join(BUILD, name).replace("\\", "/")

con = duckdb.connect()
con.execute("SET memory_limit='4GB'; SET threads=4; SET preserve_insertion_order=false;")
con.execute(f"SET temp_directory='{P('duckdb_tmp')}'")
q = lambda sql: con.execute(sql).df()
files = ", ".join(f"'{RAW}/{y}/*.csv'".replace("\\", "/") for y in YEARS if os.path.isdir(os.path.join(RAW, str(y))))

# ---- 1. slim typed orders ----
if not os.path.exists(P("orders.parquet")):
    con.execute(f"""
        COPY (
          SELECT CAST(ordered_on AS DATE) AS day, store_no, county_name, category_name, vendor_name, item_no, im_desc,
                 TRY_CAST(bottle_volume_ml AS DOUBLE) AS ml, TRY_CAST(pack AS DOUBLE) AS pack,
                 TRY_CAST(sales_bottles AS DOUBLE) AS bottles, TRY_CAST(sales_dollars AS DOUBLE) AS dollars,
                 TRY_CAST(sales_liters AS DOUBLE) AS liters
          -- DISTINCT removes exact duplicate rows: the 2025 file repeats ~518k lines in Jul-Oct 2025
          -- (every Aug 2025 line appears twice). Before Jul 2025 invoice_id is unique per line, so exact
          -- duplicates cannot be real orders; after Sep 2025 invoice_id is per order, but identical lines are still dups.
          FROM (SELECT DISTINCT * FROM read_csv_auto([{files}], header=true, all_varchar=true, union_by_name=true))
          WHERE TRY_CAST(sales_bottles AS DOUBLE) > 0 AND TRY_CAST(sales_dollars AS DOUBLE) > 0
        ) TO '{P("orders.parquet")}' (FORMAT parquet)""")
con.execute(f"CREATE OR REPLACE VIEW orders AS SELECT *, date_trunc('month', day) AS month, ROUND(dollars / bottles, 2) AS unit_price FROM '{P('orders.parquet')}'")
print(q("""SELECT year(day) AS year, COUNT(*) AS rows, COUNT(DISTINCT item_no) AS items, COUNT(DISTINCT store_no) AS stores,
                  ROUND(SUM(bottles)/1e6, 1) AS m_bottles, ROUND(SUM(liters)/1e6, 1) AS m_liters, ROUND(SUM(dollars)/1e6, 1) AS m_dollars
           FROM orders GROUP BY 1 ORDER BY 1""").to_string(index=False))

# ---- 2. item x month (posted price = the price with the most bottles that month) ----
con.execute(f"""
    COPY (
      WITH ip AS (SELECT item_no, month, unit_price, SUM(bottles) AS b, SUM(dollars) AS d, SUM(liters) AS l,
                         COUNT(*) AS n_orders FROM orders GROUP BY 1, 2, 3)
      SELECT item_no, month, SUM(b) AS bottles, SUM(l) AS liters, SUM(d) AS dollars,
             SUM(d) / SUM(b) AS price_mean, arg_max(unit_price, b) AS price_posted, COUNT(*) AS n_prices,
             SUM(n_orders) AS n_orders
      FROM ip GROUP BY 1, 2
    ) TO '{P("item_month.parquet")}' (FORMAT parquet)""")
con.execute(f"""
    COPY (SELECT o.item_no, o.month, COUNT(DISTINCT store_no) AS n_stores FROM orders o GROUP BY 1, 2)
    TO '{P("item_month_stores.parquet")}' (FORMAT parquet)""")

# ---- 3. county x item x month ----
con.execute(f"""
    COPY (SELECT county_name, item_no, month, SUM(bottles) AS bottles, SUM(liters) AS liters, SUM(dollars) AS dollars
          FROM orders GROUP BY 1, 2, 3) TO '{P("county_item_month.parquet")}' (FORMAT parquet)""")

# ---- 4. item attributes (most common value by bottles; count how many categories an item ever had) ----
con.execute(f"""
    COPY (
      WITH a AS (SELECT item_no, category_name, vendor_name, im_desc, ml, pack, SUM(bottles) AS b FROM orders GROUP BY ALL)
      SELECT item_no, arg_max(category_name, b) AS category_name, arg_max(vendor_name, b) AS vendor_name,
             arg_max(im_desc, b) AS im_desc, arg_max(ml, b) AS ml, arg_max(pack, b) AS pack,
             COUNT(DISTINCT category_name) AS n_categories, SUM(b) AS total_bottles
      FROM a GROUP BY 1
    ) TO '{P("items.parquet")}' (FORMAT parquet)""")

# ---- 5. categories ----
q("""SELECT category_name, COUNT(DISTINCT item_no) AS items, ROUND(SUM(bottles)) AS bottles, ROUND(SUM(dollars)) AS dollars
     FROM orders GROUP BY 1 ORDER BY bottles DESC""").to_csv(P("categories.csv"), index=False)

for f in ["item_month", "county_item_month", "items"]:
    print(f, q(f"SELECT COUNT(*) AS rows FROM '{P(f + '.parquet')}'").iloc[0, 0])
print("Saved to", BUILD)
