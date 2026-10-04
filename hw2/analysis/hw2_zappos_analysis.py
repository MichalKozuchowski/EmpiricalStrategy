# %% [markdown]
# # MGT 634 HW2: Zappos product, review and sales data (2012-2013)
# Team: Michal Kozuchowski, Laila Lapins, Nick Giamalis, Raymond Chang, Sean Weller
#
# **How to run (Yale cluster, JupyterLab):** upload this notebook to your home folder, then
# Kernel > Restart Kernel and Run All Cells. It reads the five course files in
# `~/esai_2026/data/zappos/`, never changes them, and saves charts to `~/hw2_output/figures/`.
# The first run turns the 2.6 GB `POS.dta` into a compact Parquet copy in `~/hw2_cache/`
# (about 2 minutes); every later run starts from that copy.
#
# **How the work is organised:** one section per assignment question. Big sales queries
# (13.5 million rows) run in DuckDB SQL directly on the Parquet file, so only small summary
# tables are loaded into pandas (Class 7: pandas struggles above ~10M rows). Every merge prints
# its row count before and after and how many rows matched (Class 4/7 merge rules).

# %% Setup: packages, file locations, chart style
import hashlib
import os
import site
import subprocess
import sys
import time
from pathlib import Path


def need(package, pip_name=None):
    """Import a package; if it is missing, install it for this user first (cluster has no uv)."""
    try:
        return __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "-q", pip_name or package])
        sys.path.insert(0, site.getusersitepackages())     # make the new install visible
        return __import__(package)


for pkg in ["duckdb", "pyarrow", "statsmodels"]:
    need(pkg)

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import statsmodels.formula.api as smf
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

# ---- Where are the files? (cluster course folder, or the local copy of the repo) ----
CLUSTER_DATA = Path("~/esai_2026/data/zappos").expanduser()
if CLUSTER_DATA.exists():
    DATA = CLUSTER_DATA                                   # read-only course folder
    CACHE = Path("~/hw2_cache").expanduser()               # our compact copy of POS
    FIG = Path("~/hw2_output/figures").expanduser()
else:                                                      # local run: repo/data/zappos
    repo = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "data" / "zappos").exists())
    DATA = CACHE = repo / "data" / "zappos"
    FIG = repo / "hw2" / "figures"
CACHE.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
POS_DTA, POS_PQ = DATA / "POS.dta", CACHE / "pos.parquet"
print("Data folder:", DATA, "| charts go to:", FIG)

# ---- Chart style: NYT "Upshot" look (colors, light grid, bold left title) ----
DARK_GREEN, SAGE, CREAM, SALMON, DARK_RED = "#636e4f", "#a3ae8d", "#fbebb7", "#d1725c", "#993f2a"
INK, GREY, LIGHT = "#121212", "#737373", "#eeeeee"
for folder in [Path.home() / "fonts", *[p / "fonts" for p in Path.cwd().parents]]:
    for f in folder.glob("LibreFranklin-*.ttf"):             # use the Upshot font if it is around
        font_manager.fontManager.addfont(str(f))
plt.rcParams.update({
    "font.family": ["Libre Franklin", "DejaVu Sans"], "font.size": 9.5,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.edgecolor": "#999999", "axes.labelcolor": "#666666", "axes.grid": True,
    "axes.axisbelow": True, "grid.color": LIGHT, "grid.linewidth": 0.75,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "xtick.color": "#666666", "ytick.color": "#666666", "ytick.left": False,
    "axes.prop_cycle": matplotlib.cycler(color=[DARK_GREEN, SALMON, SAGE, DARK_RED, "#c9a227"]),
    "legend.frameon": False, "figure.dpi": 100, "savefig.dpi": 200, "savefig.bbox": "tight",
    "figure.facecolor": "white",
})
if "text.parse_math" in plt.rcParams:
    plt.rcParams["text.parse_math"] = False                # show "$" as a dollar sign, not math


def finish(fig, ax, name, title, subtitle=None, note=None):
    """Title (the finding) + grey subtitle (what is plotted) + source note, then save as PNG."""
    ax.set_title(title, pad=22 if subtitle else 8)
    if subtitle:
        ax.text(0, 1.015, subtitle, transform=ax.transAxes, color=GREY, fontsize=9, va="bottom")
    # put the source line just below the lowest element (axis label or legend), so they never overlap
    renderer = fig.canvas.get_renderer()
    bottom = min(a.get_tightbbox(renderer).transformed(fig.transFigure.inverted()).y0 for a in fig.axes)
    fig.text(0.01, bottom - 0.015, "Source: Zappos POS, reviews and product data, Jul 2012-Aug 2013."
             + (" " + note if note else ""), color=GREY, fontsize=7.5, ha="left", va="top")
    fig.savefig(FIG / f"{name}.png")
    if "agg" not in matplotlib.get_backend().lower():      # show inline in Jupyter
        plt.show()
    plt.close(fig)


money = FuncFormatter(lambda x, _: f"${x:,.0f}")
millions = FuncFormatter(lambda x, _: f"{x / 1e6:,.1f}M" if x else "0")

# ---- Fingerprint the raw files so we can prove at the end that nothing changed them ----
RAW = [DATA / f for f in ["brand_list.dta", "stock_chars.dta", "categories.csv", "reviews.csv", "POS.dta"]]
RAW = [f for f in RAW if f.exists()]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


raw_hash = {f.name: sha256(f) for f in RAW}
print("Raw files fingerprinted:", ", ".join(raw_hash))

# %% [markdown]
# ## Step 0: load the files and check what one row means
# * `POS.dta` is 2.6 GB (13.5M rows). We read it once in 1-million-row pieces and save a
#   compressed Parquet copy (309 MB). The raw file is only read. The `timestamp` column is
#   dropped: it is stored as a 32-bit float, too coarse to be accurate to the minute; the separate
#   date/time columns are exact.
# * The four small files are read directly.

# %% Step 0a: build the compact POS copy (only if it does not exist yet)
if not POS_PQ.exists():
    start, writer, n = time.time(), None, 0
    with pd.read_stata(POS_DTA, iterator=True, chunksize=1_000_000) as reader:
        for chunk in reader:
            table = pa.Table.from_pandas(chunk.drop(columns=["timestamp"]), preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(POS_PQ, table.schema, compression="zstd")
            writer.write_table(table.cast(writer.schema))
            n += len(chunk)
    writer.close()
    print(f"Converted {n:,} rows in {time.time() - start:.0f}s")
print(f"POS copy: {POS_PQ} ({POS_PQ.stat().st_size / 1e6:.0f} MB)")

# %% Step 0b: load the small files and check each one's level (what one row is)
brand_list = pd.read_stata(DATA / "brand_list.dta")
stock = pd.read_stata(DATA / "stock_chars.dta")
categories = pd.read_csv(DATA / "categories.csv")
reviews = pd.read_csv(DATA / "reviews.csv")

con = duckdb.connect()                                     # DuckDB: SQL on files, in memory
con.execute(f"CREATE VIEW pos_raw AS SELECT * FROM read_parquet('{POS_PQ.as_posix()}', file_row_number = true)")
sql = lambda q: con.sql(q).df()                            # run SQL, return a pandas table

levels = pd.DataFrame([
    ("POS.dta", int(sql("SELECT count(*) FROM pos_raw").iloc[0, 0]), "one unit sold (no quantity column)"),
    ("brand_list.dta", len(brand_list), f"one sku (unique: {brand_list['sku'].is_unique})"),
    ("categories.csv", len(categories), f"one sku (unique: {categories['sku'].is_unique})"),
    ("stock_chars.dta", len(stock),
     f"one sku x color (style_id); {stock['sku'].nunique():,} skus, pair unique: "
     f"{not stock.duplicated(['sku', 'style_id']).any()}"),
    ("reviews.csv", len(reviews),
     f"one sku x month; {reviews['sku'].nunique():,} skus x {reviews[['year', 'month']].drop_duplicates().shape[0]} months"),
], columns=["file", "rows", "one row ="])
print(levels.to_string(index=False))

# %% [markdown]
# ## Step 0c: data checks on all 13.5M sales rows, and the cleaning decisions
# * Prices, discounts and the sale flag are checked against each other on every row.
# * `date_*` is the purchase time (the Stata day number `mdy` matches it on every row);
#   `sdate_*` is a second time stamp 2-3 hours later (a processing time or a time-zone shift),
#   so we use `date_*`.
# * Exact duplicate rows can only occur inside the same order number, and only ~8,500 orders
#   have more than one row, so we look for duplicates there instead of comparing all 13.5M rows.
#   The comparison uses every column: rows can share an order number, product and time yet
#   ship to different addresses, and those are real sales, not duplicates.

# %% Step 0c: checks
checks = sql("""
    SELECT count(*)                                                    AS rows,
           sum(CASE WHEN price <= 0 THEN 1 ELSE 0 END)                 AS price_le_0,
           sum(CASE WHEN price > msrp + 0.005 THEN 1 ELSE 0 END)       AS price_above_msrp,
           sum(CASE WHEN abs(msrp - price - discount) > 0.01 THEN 1 ELSE 0 END) AS discount_mismatch,
           sum(CASE WHEN (sale = 1) <> (discount > 0.005) THEN 1 ELSE 0 END)    AS sale_flag_mismatch,
           sum(CASE WHEN mdy <> date_diff('day', DATE '1960-01-01',
                 make_date(date_y, date_m, date_d)) THEN 1 ELSE 0 END) AS mdy_not_date,
           sum(CASE WHEN state IS NULL OR trim(state) = '' THEN 1 ELSE 0 END) AS blank_state
    FROM pos_raw""")
print(checks.T.rename(columns={0: "rows"}).to_string())

# Exact duplicates: compare full rows, but only inside orders that have more than one row
all_cols = ", ".join(f"p.{c}" for c in sql("DESCRIBE pos_raw")["column_name"] if c != "file_row_number")
dup_rows = sql(f"""
    WITH multi AS (SELECT trans_id FROM pos_raw GROUP BY trans_id HAVING count(*) > 1),
         ranked AS (SELECT p.file_row_number, row_number() OVER (
                        PARTITION BY {all_cols} ORDER BY p.file_row_number) AS copy_no
                    FROM pos_raw p JOIN multi USING (trans_id))
    SELECT file_row_number FROM ranked WHERE copy_no > 1""")
print(f"\nExact duplicate rows (second copies) to drop: {len(dup_rows)}")
con.register("dup_rows", dup_rows)

# Clean sales view: drop duplicate copies, build proper date/time fields, flag real US states.
# Note: 13 codes are not US states (PR, VI, GU, MP, AS, FM, PW, MH; military AA, AE, AP; DC is
# kept as a state-equivalent). They stay in national totals but not in state/region analyses.
NON_STATES = ("PR", "VI", "GU", "MP", "AS", "FM", "PW", "MH", "AA", "AE", "AP", "")
con.execute(f"""
    CREATE OR REPLACE VIEW pos AS
    SELECT state, zipcode, brand AS pos_brand, sku, styleid, trans_id, item,
           price, msrp, discount, percent_off, sale,
           make_timestamp(date_y, date_m, date_d, date_h, date_min, date_s) AS ts,
           make_date(date_y, date_m, date_d) AS day,
           date_h AS hour,
           state NOT IN {NON_STATES} AS us_state
    FROM pos_raw
    WHERE file_row_number NOT IN (SELECT file_row_number FROM dup_rows)""")
clean_n = int(sql("SELECT count(*) FROM pos").iloc[0, 0])
print(f"Rows: raw {int(checks['rows'][0]):,} -> after dropping duplicates {clean_n:,}")

# %% [markdown]
# ## Q1. Product and brand landscape (brand_list.dta + POS.dta)

# %% Q1a: how many brands, and the top 10 by number of SKUs offered
assert brand_list["sku"].is_unique, "brand_list must have one row per sku before merging"
pos_brands = sql("SELECT count(DISTINCT pos_brand) AS n, count(DISTINCT sku) AS skus FROM pos")
print(f"Distinct brand names in POS (incl. sub-lines such as 'Nike Kids'): {pos_brands['n'][0]}")
print(f"Distinct brands in brand_list (parent brands): {brand_list['brand'].nunique()}")
print(f"SKUs: {pos_brands['skus'][0]:,} sold in POS; {len(brand_list):,} in brand_list")

top_skus = brand_list["brand"].value_counts().head(10)
print("\nTop 10 brands by SKUs offered:\n" + top_skus.to_string())

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.barh(top_skus.index[::-1], top_skus.values[::-1], color=DARK_GREEN, height=0.65)
for y, v in enumerate(top_skus.values[::-1]):
    ax.text(v + 15, y, f"{v:,}", va="center", fontsize=8.5, color=INK)
ax.grid(axis="y", visible=False)
ax.set_xlabel("Number of SKUs (products) offered")
finish(fig, ax, "q1_top10_brands_skus", "Athletic brands offer the most products",
       f"Top 10 of {brand_list['brand'].nunique()} brands by number of SKUs, brand_list.dta")

# %% Q1b: merge brand_list onto the sales data and judge how well it works
con.register("brand_list", brand_list)
merge1 = sql("""
    SELECT count(*)                                              AS rows_after,
           sum(CASE WHEN b.sku IS NOT NULL THEN 1 ELSE 0 END)    AS matched_rows,
           count(DISTINCT p.sku)                                 AS skus,
           count(DISTINCT CASE WHEN b.sku IS NOT NULL THEN p.sku END) AS matched_skus,
           sum(CASE WHEN p.pos_brand = b.brand THEN 1 ELSE 0 END) AS same_name_rows
    FROM pos p LEFT JOIN brand_list b USING (sku)""")
m = merge1.iloc[0]
print(f"Rows before merge: {clean_n:,} | after: {int(m.rows_after):,} "
      f"({'OK, unchanged' if m.rows_after == clean_n else 'FLAG: row count changed'})")
print(f"Rows matched: {m.matched_rows / m.rows_after:.2%} | SKUs matched: "
      f"{int(m.matched_skus):,} of {int(m.skus):,}")
print(f"POS brand name = brand_list name on {m.same_name_rows / m.rows_after:.1%} of rows")

# Where the names differ, what is going on?
diff_names = sql("""
    SELECT p.pos_brand, b.brand AS list_brand, count(*) AS units
    FROM pos p JOIN brand_list b USING (sku)
    WHERE p.pos_brand <> b.brand GROUP BY 1, 2 ORDER BY units DESC""")
print(f"\n{diff_names['pos_brand'].nunique()} POS brand names roll up into "
      f"{diff_names['list_brand'].nunique()} parent brands. Largest:")
print(diff_names.head(12).to_string(index=False))
# Does any POS brand name map to more than one parent? (would signal a real conflict)
conflicts = sql("""SELECT p.pos_brand, count(DISTINCT b.brand) AS parents
                   FROM pos p JOIN brand_list b USING (sku) GROUP BY 1 HAVING parents > 1 ORDER BY 1""")
print(f"\nPOS brand names linked to more than one parent brand: {len(conflicts)}")
if len(conflicts):
    print(conflicts.to_string(index=False))

# Sales view with the parent brand attached (used from here on)
con.execute("""CREATE OR REPLACE VIEW pos_b AS
               SELECT p.*, b.brand FROM pos p LEFT JOIN brand_list b USING (sku)""")


# %% [markdown]
# ## Q2. Product characteristics (stock_chars.dta, brand_list.dta, POS.dta)

# %% Q2a: can stock_chars and brand_list be merged into POS? (keys and match rates)
# brand_list: one row per sku -> merges on sku (done in Q1, 100% of rows match).
# stock_chars: one row per sku x COLOR (style_id). POS also records the color (styleid), so the
# right key is sku + styleid. Merging on sku alone would copy each sale once per color.
assert not stock.duplicated(["sku", "style_id"]).any(), "stock_chars must be unique by sku + style_id"
con.register("stock_keys", stock[["sku", "style_id"]])
con.register("stock_skus", stock[["sku"]].drop_duplicates())
keys = sql("""
    SELECT avg(CASE WHEN k.sku IS NOT NULL THEN 1 ELSE 0 END)  AS match_sku_and_color,
           avg(CASE WHEN s.sku IS NOT NULL THEN 1 ELSE 0 END)  AS match_sku_only
    FROM pos p
    LEFT JOIN stock_keys k ON p.sku = k.sku AND p.styleid = k.style_id
    LEFT JOIN stock_skus s ON p.sku = s.sku""")
print(f"Share of sales rows with characteristics: by sku + color {keys.iloc[0, 0]:.1%}, "
      f"by sku only {keys.iloc[0, 1]:.1%}")
print(f"A merge on sku alone would multiply rows: stock_chars has "
      f"{len(stock) / stock['sku'].nunique():.2f} colors per sku on average")
within = stock.groupby("sku").agg(genders=("gender", "nunique"), prices=("orig_price", "nunique"))
print(f"SKUs whose colors disagree on gender: {(within.genders > 1).sum()}, "
      f"on list price: {(within.prices > 1).sum()}")

# %% Q2b: which features are complete enough to use?
missing = (stock.drop(columns=["sku", "style_id"]).isna().mean() * 100).sort_values()
print("Share of product-color rows missing each feature (%):")
print(missing.round(1).to_string())

fig, ax = plt.subplots(figsize=(7, 7))
colors = [DARK_GREEN if v < 10 else (SAGE if v < 50 else SALMON) for v in missing.values]
ax.barh(missing.index[::-1], 100 - missing.values[::-1], color=colors[::-1], height=0.7)
ax.set_xlim(0, 100)
ax.set_xlabel("% of product-colors with the feature filled in")
ax.grid(axis="y", visible=False)
finish(fig, ax, "q2_feature_completeness", "Only a handful of product features are reliably filled in",
       "Completeness of each stock_chars.dta column (117,493 product-colors); green = over 90% complete")

# %% Q2c: pick 3 features and merge them onto the sales data
# Chosen: gender (100% complete, required), occasion (98%) and materials (93%): the most
# complete features that describe who the shoe is for, what it is for and what it is made of.
# Small categories are grouped so every group has enough products to compare.
GENDER = {"Women": "Women", "Men": "Men", "Girls": "Kids", "Boys": "Kids", "Unisex": "Unisex"}
OCCASION = {"Casual": "Casual", "Athletic": "Athletic", "Action Sports": "Athletic", "Outdoor": "Outdoor",
            "Dress": "Dress", "Wedding": "Dress", "Prom & Homecoming": "Dress", "Evening & Cocktail": "Dress",
            "Little Black Dress": "Dress", "Office & Career": "Work", "Work & Duty": "Work"}
MATERIAL = {**{m: "Leather" for m in ["Leather", "Full-grain leather", "Patent Leather", "Nubuck",
                                      "Nappa", "Hair Calf"]},
            "Suede": "Suede",
            **{m: "Synthetic" for m in ["Synthetic", "Faux Leather", "Microfiber", "EVA", "Rubber"]},
            **{m: "Fabric" for m in ["Mesh", "Canvas", "Nylon", "Satin", "Lace", "Cotton", "Polyester",
                                     "Wool", "Felt", "Linen", "Fleece", "Neoprene", "Terry", "Jute"]}}

feat = stock[["sku", "style_id"]].copy()
for new, old, mapping in [("gender", "gender", GENDER), ("occasion", "occasion", OCCASION),
                          ("material", "materials", MATERIAL)]:
    raw_values = stock[old].astype(object)                   # category -> plain text (missing stays missing)
    feat[new] = raw_values.map(mapping)
    feat.loc[raw_values.notna() & feat[new].isna(), new] = "Other"   # rare values -> "Other"
print("Feature groups (product-colors):")
for c in ["gender", "occasion", "material"]:
    print(f"  {c}: {feat[c].value_counts(dropna=False).to_dict()}")

# Fallback for sales whose color is not in stock_chars: the product's most common value
by_sku = feat[["sku"]].drop_duplicates().set_index("sku")
for c in ["gender", "occasion", "material"]:
    top = (feat.dropna(subset=[c]).groupby(["sku", c]).size().rename("n").reset_index()
           .sort_values(["sku", "n"], ascending=[True, False]).drop_duplicates("sku"))
    by_sku[c] = top.set_index("sku")[c]
by_sku = by_sku.reset_index()
assert by_sku["sku"].is_unique
con.register("feat", feat)
con.register("feat_sku", by_sku)
con.execute("""
    CREATE OR REPLACE VIEW pos_f AS
    SELECT p.*,
           coalesce(f.gender, g.gender)     AS gender,
           coalesce(f.occasion, g.occasion) AS occasion,
           coalesce(f.material, g.material) AS material,
           f.sku IS NOT NULL                AS color_match
    FROM pos_b p
    LEFT JOIN feat f     ON p.sku = f.sku AND p.styleid = f.style_id
    LEFT JOIN feat_sku g ON p.sku = g.sku""")
m2 = sql("""SELECT count(*) AS rows_after, avg(color_match::INT) AS by_color,
                   avg((gender IS NOT NULL)::INT) AS gender, avg((occasion IS NOT NULL)::INT) AS occasion,
                   avg((material IS NOT NULL)::INT) AS material FROM pos_f""").iloc[0]
print(f"\nRows before merge: {clean_n:,} | after: {int(m2.rows_after):,} "
      f"({'OK, unchanged' if m2.rows_after == clean_n else 'FLAG: row count changed'})")
print(f"Matched on sku + color: {m2.by_color:.1%}; filled after product-level fallback: "
      f"gender {m2.gender:.1%}, occasion {m2.occasion:.1%}, material {m2.material:.1%}")

# %% Q2d: list price (msrp) vs price paid, per unit sold
stats = sql("""
    SELECT 'msrp (list price)' AS measure, avg(msrp) AS mean, median(msrp) AS median,
           stddev(msrp) AS sd, min(msrp) AS min, max(msrp) AS max FROM pos
    UNION ALL
    SELECT 'price paid', avg(price), median(price), stddev(price), min(price), max(price) FROM pos""")
print(stats.round(2).to_string(index=False))

# Distribution: share of units in log-spaced price bins (counted in SQL, 40 bins from $8 to $3,200)
edges = np.geomspace(8, 3200, 41)
step = np.log(edges[1] / edges[0])
hist = sql(f"""
    SELECT 'msrp' AS which, floor(ln(msrp / 8) / {step}) AS bin, count(*) AS n FROM pos GROUP BY 1, 2
    UNION ALL
    SELECT 'price', floor(ln(price / 8) / {step}), count(*) FROM pos GROUP BY 1, 2""")
fig, ax = plt.subplots(figsize=(7.5, 4.2))
for which, color, lab in [("msrp", SAGE, "List price (msrp)"), ("price", DARK_GREEN, "Price paid")]:
    h = hist[hist["which"] == which].set_index("bin")["n"].reindex(range(40), fill_value=0)
    ax.stairs(h.values / h.sum() * 100, edges, fill=(which == "msrp"), color=color, linewidth=2, label=lab)
ymax = ax.get_ylim()[1]
for v, lab, side in [(stats.loc[1, "median"], "median paid", "right"), (stats.loc[0, "median"], "median list", "left")]:
    ax.axvline(v, color=GREY, linewidth=0.8, linestyle=":")
    ax.text(v, ymax * 0.97, f" {lab} ${v:,.0f} ", color=GREY, fontsize=8, va="top", ha=side)
ax.set_xscale("log")
ax.set_xticks([10, 25, 50, 100, 200, 500, 1000, 3000])
ax.xaxis.set_major_formatter(money)
ax.set_xlabel("Price per unit (log scale)")
ax.set_ylabel("% of units sold")
ax.legend(loc="center right")
finish(fig, ax, "q2_price_distribution", "Most shoes sell for $40-$150; discounts shift prices only slightly",
       f"Distribution of list price and price paid across {clean_n / 1e6:.1f}M units sold")

# %% Q2e: discounts across gender groups (one chart)
disc = sql("""
    SELECT gender,
           count(*) AS units,
           avg(sale) AS share_discounted,
           avg(percent_off) AS avg_pct_off_all,
           avg(CASE WHEN sale = 1 THEN percent_off END) AS avg_pct_off_when_discounted,
           avg(CASE WHEN percent_off = 0 THEN 1.0 ELSE 0 END)                         AS b0,
           avg(CASE WHEN percent_off > 0 AND percent_off < 20 THEN 1.0 ELSE 0 END)     AS b1,
           avg(CASE WHEN percent_off >= 20 AND percent_off < 40 THEN 1.0 ELSE 0 END)   AS b2,
           avg(CASE WHEN percent_off >= 40 THEN 1.0 ELSE 0 END)                        AS b3
    FROM pos_f WHERE gender IS NOT NULL GROUP BY 1 ORDER BY share_discounted""")
print(disc.round(3).to_string(index=False))

fig, ax = plt.subplots(figsize=(7.5, 3.6))
buckets = [("b0", "Full price", "#e3e3e3"), ("b1", "Under 20% off", CREAM),
           ("b2", "20-39% off", SALMON), ("b3", "40%+ off", DARK_RED)]
left = np.zeros(len(disc))
for col, lab, color in buckets:
    ax.barh(disc["gender"], disc[col] * 100, left=left, color=color, label=lab, height=0.62)
    for y, (l, w) in enumerate(zip(left, disc[col] * 100)):
        if w >= 4:
            ax.text(l + w / 2, y, f"{w:.0f}%", ha="center", va="center", fontsize=8,
                    color="white" if col in ("b2", "b3") else INK)
    left += disc[col].values * 100
ax.set_xlim(0, 100)
ax.set_xlabel("% of units sold")
ax.grid(False)
ax.legend(ncol=4, loc="upper left", bbox_to_anchor=(0, -0.16), fontsize=8.5)
finish(fig, ax, "q2_discounts_by_gender", "Women's shoes are discounted most often and most deeply",
       "Units sold by discount depth, by gender of the product", note="Kids = Girls + Boys.")

# %% Q2f: brands with the highest average list price (msrp), and what they sell
# Average over the brand's products (one value per sku = its median msrp), brands with 20+ SKUs
# sold, so one or two luxury items cannot top the list on their own.
brand_msrp = sql("""
    WITH sku AS (SELECT sku, any_value(brand) AS brand, median(msrp) AS msrp, count(*) AS units,
                        mode(gender) AS gender, mode(occasion) AS occasion, mode(material) AS material
                 FROM pos_f GROUP BY sku)
    SELECT brand, count(*) AS skus, avg(msrp) AS avg_msrp, sum(units) AS units,
           mode(gender) AS main_gender, avg((gender = 'Women')::INT) AS share_women,
           mode(occasion) AS main_occasion, mode(material) AS main_material
    FROM sku GROUP BY brand ORDER BY avg_msrp DESC""")
print("Top 5 brands by average msrp (brands with 20+ SKUs):")
print(brand_msrp[brand_msrp["skus"] >= 20].head(5).round(2).to_string(index=False))
print("\nFor reference, top 5 with no minimum (tiny brands can top it):")
print(brand_msrp.head(5).round(2).to_string(index=False))


# %% [markdown]
# ## Q3. Customer reviews over time (reviews.csv)
# **Key fact about this file:** `rev_cnt` is a running total. It never goes down, and in 82% of
# product-months it does not change. So `overall`, `comfort` and `look` are averages over all
# reviews a product has received so far, not that month's reviews. Blank rows are products
# that had no review yet. We therefore measure two things each month: products that *have*
# reviews (running total), and products that got a *new* review that month. New reviews'
# average rating is recovered from the change in the totals:
# new stars = count_t x avg_t - count_(t-1) x avg_(t-1).

# %% Q3a: products with reviews each month
rv = reviews.sort_values(["sku", "year", "month"]).copy()
rv["month_start"] = pd.to_datetime(dict(year=rv["year"], month=rv["month"], day=1))
assert not rv.duplicated(["sku", "month_start"]).any(), "reviews must be one row per sku-month"
grp = rv.groupby("sku")
rv["prev_cnt"] = grp["rev_cnt"].shift().fillna(0)               # 0 before the first review
rv["stars"] = rv["rev_cnt"] * rv["overall"]                       # total stars to date
rv["prev_stars"] = grp["stars"].shift().fillna(0)
rv["new_reviews"] = rv["rev_cnt"].fillna(0) - rv["prev_cnt"]
assert (rv["new_reviews"] >= -1e-9).all(), "rev_cnt should never fall"
first_month = rv["month_start"].min()

monthly = rv.groupby("month_start").agg(
    products_with_reviews=("rev_cnt", "count"),                  # running total (non-blank rows)
    products_new_review=("new_reviews", lambda x: int((x > 0).sum())),
    new_reviews=("new_reviews", "sum"),
    avg_overall_to_date=("overall", "mean"),
)
new = rv[(rv["new_reviews"] > 0) & (rv["month_start"] > first_month)]
monthly["avg_overall_new"] = ((new["stars"] - new["prev_stars"]).groupby(new["month_start"]).sum()
                              / new.groupby("month_start")["new_reviews"].sum())
monthly.loc[first_month, ["products_new_review", "new_reviews"]] = np.nan   # July 2012 holds all past reviews
print(monthly.round(3).to_string())

fig, ax = plt.subplots(figsize=(7.5, 4))
ax.plot(monthly.index, monthly["products_with_reviews"], color=DARK_GREEN, linewidth=2.5, marker="o", ms=4)
ax.plot(monthly.index, monthly["products_new_review"], color=SALMON, linewidth=2.5, marker="o", ms=4)
ax.text(monthly.index[-1], monthly["products_with_reviews"].iloc[-1], "  Have any review\n  (running total)",
        color=DARK_GREEN, va="center", fontsize=9, fontweight="bold")
ax.text(monthly.index[-1], 2500, "  Got a new review\n  that month",
        color=SALMON, va="center", fontsize=9, fontweight="bold")
ax.set_ylim(0, None)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.set_ylabel("Number of products (SKUs)")
finish(fig, ax, "q3_products_with_reviews", "Reviewed products level off at 21,242 and new reviews dry up after January 2013",
       "Unique products with reviews, by month", note="Aug 2013 is a partial month.")

# %% Q3b: which rating dimension scores highest? (all product-months with a rating)
dims = rv[["overall", "comfort", "look"]].agg(["mean", "median", "count"]).T
print(dims.round(3).to_string())
print(f"Highest-scoring dimension: {dims['mean'].idxmax()}")

# %% Q3c: number of reviews vs overall rating (one point per product, latest month)
latest = rv.dropna(subset=["rev_cnt"]).drop_duplicates("sku", keep="last")
fit = smf.ols("overall ~ np.log(rev_cnt)", latest).fit(cov_type="HC1")    # robust SEs (Class 8)
slope, se = fit.params.iloc[1], fit.bse.iloc[1]
print(f"Products: {len(latest):,} | overall = {fit.params.iloc[0]:.2f} + {slope:.3f} x ln(reviews) "
      f"(SE {se:.3f}, R2 {fit.rsquared:.3f})")
latest["count_bin"] = pd.qcut(np.log(latest["rev_cnt"]), 15, duplicates="drop")
binned = latest.groupby("count_bin", observed=True).agg(x=("rev_cnt", "median"), y=("overall", "mean"),
                                                         sd=("overall", "std"))
print(binned.round(3).to_string())

fig, ax = plt.subplots(figsize=(7.5, 4.4))
jitter = np.random.default_rng(0).uniform(-0.03, 0.03, len(latest))
ax.scatter(latest["rev_cnt"] * np.exp(jitter), latest["overall"], s=4, color=SAGE, alpha=0.25, linewidths=0)
ax.plot(binned["x"], binned["y"], "o", color=DARK_GREEN, ms=6, label="Average within bin (binscatter)")
xs = np.geomspace(1, latest["rev_cnt"].max(), 50)
ax.plot(xs, fit.params.iloc[0] + slope * np.log(xs), color=SALMON, linewidth=2,
        label=f"Fitted line: +{slope * np.log(2):.2f} stars per doubling of reviews")
ax.set_xscale("log")
ax.set_xticks([1, 3, 10, 30, 100, 300, 1000, 3000])
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.set_xlabel("Number of reviews (log scale)")
ax.set_ylabel("Overall rating (1-5 stars)")
ax.legend(loc="lower right", fontsize=8.5)
finish(fig, ax, "q3_reviews_vs_rating", "Products with more reviews have slightly higher, far more stable ratings",
       f"One dot per product ({len(latest):,}), latest month; ratings of rarely reviewed products scatter widely")

# %% Q3d: is the average rating rising or falling over time?
trend_new = smf.ols("avg_overall_new ~ t", monthly.dropna(subset=["avg_overall_new"])
                    .assign(t=lambda d: np.arange(len(d)))).fit(cov_type="HC1")
print(f"New reviews' average rating changes by {trend_new.params['t']:+.4f} stars per month "
      f"(SE {trend_new.bse['t']:.4f})")
fig, ax = plt.subplots(figsize=(7.5, 4))
ax.plot(monthly.index, monthly["avg_overall_to_date"], color=DARK_GREEN, linewidth=2.5, marker="o", ms=4)
ax.plot(monthly.index, monthly["avg_overall_new"], color=SALMON, linewidth=2.5, marker="o", ms=4)
ax.text(monthly.index[-1], monthly["avg_overall_to_date"].iloc[-1], "  All reviews to date\n  (product average)",
        color=DARK_GREEN, va="center", fontsize=9, fontweight="bold")
ax.text(monthly.index[-1], monthly["avg_overall_new"].iloc[-1], "  Reviews written\n  that month",
        color=SALMON, va="center", fontsize=9, fontweight="bold")
ax.set_ylim(3.8, 4.6)
ax.set_ylabel("Average overall rating (stars)")
finish(fig, ax, "q3_rating_trend", "Ratings are flat; the running average only dips as newly reviewed products join",
       "Average overall rating by month", note="New-review averages start Aug 2012.")

# %% [markdown]
# ## Q4. Product ratings and characteristics (reviews.csv + stock_chars.dta)
# Reviews are one row per product per month; characteristics are per product-color, but reviews
# have no color. We therefore merge the product-level version of the 3 features built in Q2
# (each product's most common gender / occasion / material) on sku, many-to-one.

# %% Q4a: merge and match rate
print(f"Before merge: reviews {rv.shape}, product features {by_sku.shape}")
rv_f = rv.merge(by_sku, on="sku", how="left", validate="many_to_one", indicator=True)
print(f"After merge:  {rv_f.shape} ({'OK, rows unchanged' if len(rv_f) == len(rv) else 'FLAG: rows changed'})")
print(rv_f["_merge"].value_counts().to_string())
rated = rv_f["rev_cnt"].notna()
print(f"Review records matched to the 3 characteristics: {(rv_f['_merge'] == 'both').mean():.1%} of all rows, "
      f"{(rv_f.loc[rated, '_merge'] == 'both').mean():.1%} of rows with a rating; "
      f"products matched: {rv_f.loc[rv_f['_merge'] == 'both', 'sku'].nunique():,} of {rv_f['sku'].nunique():,}")
for c in ["gender", "occasion", "material"]:
    print(f"  {c} filled on {rv_f.loc[rated, c].notna().mean():.1%} of rated rows")

# %% Q4b: ratings by the 3 characteristics (one value per product: its latest rating)
prod = rv_f[rated].drop_duplicates("sku", keep="last")
fig, axes = plt.subplots(1, 3, figsize=(10, 3.8), sharex=True)
for ax, c in zip(axes, ["gender", "occasion", "material"]):
    g = prod.groupby(c)[["overall", "comfort", "look"]].agg(["mean", "sem", "count"])
    g = g[g[("overall", "count")] >= 30].sort_values(("overall", "mean"))
    print(f"\n{c}:\n" + g.round(3).to_string())
    y = np.arange(len(g))
    for dim, color, off in [("overall", DARK_GREEN, 0.18), ("comfort", SAGE, 0), ("look", SALMON, -0.18)]:
        ax.errorbar(g[(dim, "mean")], y + off, xerr=1.96 * g[(dim, "sem")], fmt="o", color=color, ms=4.5,
                    elinewidth=1, label=dim.capitalize())
    ax.set_yticks(y)
    ax.set_yticklabels([f"{i} ({n:,})" for i, n in zip(g.index, g[("overall", "count")])], fontsize=8.5)
    ax.set_title(c.capitalize(), fontsize=10.5)
    ax.grid(axis="y", visible=False)
fig.subplots_adjust(wspace=0.85, top=0.78, bottom=0.2)               # room for the row labels
axes[0].legend(loc="upper left", bbox_to_anchor=(-0.6, -0.2), ncol=3, fontsize=8.5)
axes[1].set_xlabel("Average rating (stars), 95% confidence interval")
fig.suptitle("Women's, dress and synthetic shoes rate lowest, mostly on comfort",
             x=0.01, ha="left", fontweight="bold", fontsize=12, y=0.99)
fig.text(0.01, 0.9, "Latest average rating per product; number of products in brackets", color=GREY, fontsize=9)
fig.text(0.01, -0.06, "Source: Zappos reviews and product data, Jul 2012-Aug 2013.", color=GREY, fontsize=7.5)
fig.savefig(FIG / "q4_ratings_by_features.png")
if "agg" not in matplotlib.get_backend().lower():
    plt.show()
plt.close(fig)

# %% [markdown]
# ## Q5. Transaction patterns (POS.dta + reviews.csv)

# %% Q5a: how many transactions, over what period?
span = sql("""SELECT count(*) AS units, count(DISTINCT trans_id) AS order_ids, min(ts) AS first_sale,
                     max(ts) AS last_sale, count(DISTINCT day) AS days FROM pos""").iloc[0]
print(f"Transactions (units sold): {span.units:,} | distinct order ids: {span.order_ids:,}")
print(f"From {span.first_sale} to {span.last_sale} ({span.days} days with sales)")

# %% Q5b: top 15 states by transactions
REGION = {**{s: "Northeast" for s in "CT ME MA NH RI VT NJ NY PA".split()},
          **{s: "Midwest" for s in "IL IN MI OH WI IA KS MN MO NE ND SD".split()},
          **{s: "South" for s in "DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX".split()},
          **{s: "West" for s in "AZ CO ID MT NV NM UT WY AK CA HI OR WA".split()}}   # US Census regions
by_state = sql("""SELECT state, count(*) AS units, sum(price) AS revenue, avg(price) AS avg_price,
                         avg(msrp) AS avg_msrp, avg(sale) AS share_discounted
                  FROM pos WHERE us_state GROUP BY state ORDER BY units DESC""")
by_state["region"] = by_state["state"].map(REGION)
assert by_state["region"].notna().all() and len(by_state) == 51, "expected 50 states + DC"
outside = clean_n - by_state["units"].sum()
print(f"Units outside the 50 states + DC (territories, military mail, blank): {outside:,} ({outside / clean_n:.2%})")
top15 = by_state.head(15)
print(top15.round(2).to_string(index=False))

fig, ax = plt.subplots(figsize=(7, 4.8))
ax.barh(top15["state"][::-1], top15["units"][::-1], color=DARK_GREEN, height=0.65)
for y, v in enumerate(top15["units"][::-1]):
    ax.text(v, y, f" {v / 1e6:.2f}M ({v / clean_n:.0%})", va="center", fontsize=8.5)
ax.xaxis.set_major_formatter(millions)
ax.set_xlabel("Units sold")
ax.grid(axis="y", visible=False)
finish(fig, ax, "q5_top15_states", f"California and New York alone buy {top15['units'].iloc[:2].sum() / clean_n:.0%} of all shoes",
       "Top 15 states by number of transactions (units sold)")

# %% Q5c: average transaction price by state (tile map: one square per state)
TILES = {"AK": (0, 0), "ME": (11, 0), "VT": (10, 1), "NH": (11, 1),
         "WA": (1, 2), "ID": (2, 2), "MT": (3, 2), "ND": (4, 2), "MN": (5, 2), "IL": (6, 2), "WI": (7, 2),
         "MI": (8, 2), "NY": (9, 2), "RI": (10, 2), "MA": (11, 2),
         "OR": (1, 3), "NV": (2, 3), "WY": (3, 3), "SD": (4, 3), "IA": (5, 3), "IN": (6, 3), "OH": (7, 3),
         "PA": (8, 3), "NJ": (9, 3), "CT": (10, 3),
         "CA": (1, 4), "UT": (2, 4), "CO": (3, 4), "NE": (4, 4), "MO": (5, 4), "KY": (6, 4), "WV": (7, 4),
         "VA": (8, 4), "MD": (9, 4), "DE": (10, 4),
         "AZ": (2, 5), "NM": (3, 5), "KS": (4, 5), "AR": (5, 5), "TN": (6, 5), "NC": (7, 5), "SC": (8, 5),
         "DC": (9, 5), "OK": (4, 6), "LA": (5, 6), "MS": (6, 6), "AL": (7, 6), "GA": (8, 6),
         "HI": (0, 7), "TX": (4, 7), "FL": (9, 7)}
national = sql("SELECT avg(price) FROM pos WHERE us_state").iloc[0, 0]
print(f"National average price paid: ${national:.2f}")
print("Highest:\n" + by_state.nlargest(5, "avg_price")[["state", "avg_price", "units"]].round(2).to_string(index=False))
print("Lowest:\n" + by_state.nsmallest(5, "avg_price")[["state", "avg_price", "units"]].round(2).to_string(index=False))

cmap = matplotlib.colors.LinearSegmentedColormap.from_list("upshot", [DARK_RED, SALMON, "#f7f7f2", SAGE, DARK_GREEN])
spread = max(abs(by_state["avg_price"] - national))
norm = matplotlib.colors.TwoSlopeNorm(vcenter=national, vmin=national - spread, vmax=national + spread)
fig, ax = plt.subplots(figsize=(8.5, 5.4))
for _, r in by_state.iterrows():
    col, row = TILES[r["state"]]
    color = cmap(norm(r["avg_price"]))
    ax.add_patch(plt.Rectangle((col, -row), 0.94, 0.94, color=color))
    dark = abs(r["avg_price"] - national) > spread * 0.55
    ax.text(col + 0.47, -row + 0.6, r["state"], ha="center", va="center", fontsize=9, fontweight="bold",
            color="white" if dark else INK)
    ax.text(col + 0.47, -row + 0.3, f"${r['avg_price']:.0f}", ha="center", va="center", fontsize=7.5,
            color="white" if dark else INK)
ax.set_xlim(-0.1, 12)
ax.set_ylim(-7.1, 1)
ax.set_aspect("equal")
ax.axis("off")
sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04, pad=0.02, aspect=40)
cb.set_label(f"Average price paid per unit (national average ${national:.0f})", color=GREY)
cb.outline.set_visible(False)
finish(fig, ax, "q5_avg_price_by_state_map", "Prices paid vary little by state: Florida pays least, DC most",
       "Average price paid per unit, by state")

# %% Q5d: share of discounted transactions by US Census region
region = sql("""SELECT state, count(*) AS units, sum(sale) AS discounted, avg(percent_off) AS pct_off
                FROM pos WHERE us_state GROUP BY state""")
region["region"] = region["state"].map(REGION)
reg = region.groupby("region").agg(units=("units", "sum"), discounted=("discounted", "sum"))
reg["share_discounted"] = reg["discounted"] / reg["units"]
reg = reg.sort_values("share_discounted")
print(reg.round(4).to_string())

fig, ax = plt.subplots(figsize=(7, 3.2))
ax.barh(reg.index, reg["share_discounted"] * 100, color=[SAGE] * 3 + [DARK_GREEN], height=0.6)
for y, v in enumerate(reg["share_discounted"] * 100):
    ax.text(v, y, f" {v:.1f}%", va="center", fontsize=9)
ax.set_xlim(0, 40)
ax.set_xlabel("% of units sold at a discount")
ax.grid(axis="y", visible=False)
finish(fig, ax, "q5_discount_share_by_region", "Discount use is almost identical across US regions",
       "Share of transactions with discount > 0, by US Census region")

# %% Q5e: price tiers and ratings (one value per product)
# Tier = the product's list price (median msrp in POS), so a temporary discount does not move a
# product between tiers. Rating = the product's latest average rating.
sku_price = sql("SELECT sku, median(msrp) AS list_price, count(*) AS units FROM pos GROUP BY sku")
tiers = sku_price.merge(rv[rated].drop_duplicates("sku", keep="last")[["sku", "overall", "comfort", "look", "rev_cnt"]],
                        on="sku", how="left", validate="one_to_one")
tiers["tier"] = pd.cut(tiers["list_price"], [0, 50, 100, 200, np.inf], right=False,
                       labels=["Under $50", "$50-$100", "$100-$200", "$200+"])
tier_tab = tiers.groupby("tier", observed=True).agg(
    products=("sku", "size"), share_reviewed=("overall", lambda x: x.notna().mean()),
    overall=("overall", "mean"), overall_sem=("overall", "sem"),
    comfort=("comfort", "mean"), look=("look", "mean"), units=("units", "sum"))
print(tier_tab.round(3).to_string())

fig, ax = plt.subplots(figsize=(7.5, 3.8))
y = np.arange(len(tier_tab))
for dim, color, off in [("overall", DARK_GREEN, 0.2), ("comfort", SAGE, 0), ("look", SALMON, -0.2)]:
    ax.plot(tier_tab[dim], y + off, "o", color=color, ms=7, label=dim.capitalize())
ax.errorbar(tier_tab["overall"], y + 0.2, xerr=1.96 * tier_tab["overall_sem"], fmt="none", color=DARK_GREEN)
ax.set_yticks(y)
ax.set_yticklabels([f"{t}\n{p:,} products, {s:.0%} reviewed" for t, p, s in
                    zip(tier_tab.index, tier_tab["products"], tier_tab["share_reviewed"])], fontsize=8.5)
ax.set_xlabel("Average rating (stars)")
ax.grid(axis="y", visible=False)
ax.legend(loc="upper left", bbox_to_anchor=(0, -0.18), ncol=3, fontsize=8.5)
finish(fig, ax, "q5_ratings_by_price_tier", "Ratings do not simply rise with price: $50-$100 shoes rate lowest",
       "Average latest rating per product, by list-price tier (95% CI on overall)")


# %% [markdown]
# ## Q5f. How could we test whether ratings drive sales?
# **The problem:** comparing sales of high- and low-rated products does not show that ratings
# *cause* sales. (1) *Reverse causality*: products that sell more collect more reviews.
# (2) *Omitted variables* (Class 8): brand, quality, price, style and advertising drive both
# ratings and sales, so they sit in the error term and bias a simple regression.
#
# **The design, step by step (shown below on a product x month panel):**
# 1. Naive regression: this month's sales on *last month's* rating (using last month's rating
#    rules out sales this month changing the rating).
# 2. Add controls and fixed effects for what we observe: month (seasonality, partial months),
#    gender, occasion, list price, number of reviews.
# 3. **Product fixed effects**: compare the *same* product in months when its rating was higher
#    vs lower. Everything fixed about a product (brand, quality, style) drops out. Estimated with
#    the within (demeaning) estimator from Class 8, standard errors clustered by product.
#
# **Stronger designs if we had more data:** Zappos displays ratings rounded to the nearest half
# star, so products just above vs just below a rounding cutoff (e.g. 4.24 vs 4.26 stars) are
# nearly identical but *look* different to shoppers: a regression discontinuity, as in Luca's
# Yelp study. A randomized experiment that changes which reviews are shown first would be
# cleanest of all.

# %% Q5f: product x month panel and three regressions
pm = sql("""SELECT sku, year(day) AS year, month(day) AS month, count(*) AS units
            FROM pos GROUP BY ALL""")
panel = rv.merge(pm, on=["sku", "year", "month"], how="left", validate="one_to_one")
print(f"Panel: {rv.shape} -> {panel.shape} after adding monthly units (rows must not change)")
panel["units"] = panel["units"].fillna(0)                          # no sales that month = 0 units
panel = panel.merge(by_sku, on="sku", how="left", validate="many_to_one")
panel = panel.merge(sku_price[["sku", "list_price"]], on="sku", how="left", validate="many_to_one")
g = panel.groupby("sku")
panel["rating_lag"] = g["overall"].shift()                          # last month's rating
panel["log_reviews_lag"] = np.log1p(g["rev_cnt"].shift())
panel["log_units"] = np.log1p(panel["units"])                        # log(1 + units): ~ % change
panel["ym"] = panel["month_start"].dt.strftime("%Y-%m")
est = panel.dropna(subset=["rating_lag", "gender", "occasion", "list_price"]).copy()
print(f"Estimation sample: {len(est):,} product-months, {est['sku'].nunique():,} products")


def demean_two_ways(df, cols, a, b, rounds=100):
    """Within estimator with two sets of fixed effects: repeatedly subtract product and month
    averages until both are zero (Class 8 'demeaning', applied to product and month at once)."""
    out = df[cols].astype(float)
    for _ in range(rounds):
        out = out - out.groupby(df[a]).transform("mean")
        out = out - out.groupby(df[b]).transform("mean")
        if out.groupby(df[a]).mean().abs().to_numpy().max() < 1e-9:
            break
    return out


models = {}
models["(1) Naive"] = smf.ols("log_units ~ rating_lag", est).fit(
    cov_type="cluster", cov_kwds={"groups": est["sku"]})
models["(2) + controls & month FE"] = smf.ols(
    "log_units ~ rating_lag + log_reviews_lag + np.log(list_price) + C(gender) + C(occasion) + C(ym)", est).fit(
    cov_type="cluster", cov_kwds={"groups": est["sku"]})
dm = demean_two_ways(est, ["log_units", "rating_lag", "log_reviews_lag"], "sku", "ym")
fe = smf.ols("log_units ~ rating_lag + log_reviews_lag - 1", dm).fit(
    cov_type="cluster", cov_kwds={"groups": est["sku"]})
# degrees-of-freedom correction for the absorbed fixed effects (as in Class 8, slide 27)
n_fe = est["sku"].nunique() + est["ym"].nunique() - 1
dof = np.sqrt((len(est) - 2) / (len(est) - 2 - n_fe))
models["(3) Product FE + month FE"] = fe

rows = []
for name, f in models.items():
    b, se = f.params["rating_lag"], f.bse["rating_lag"] * (dof if "Product FE" in name else 1)
    rows.append({"model": name, "effect of +1 star": b, "SE": se, "95% low": b - 1.96 * se,
                 "95% high": b + 1.96 * se, "N": int(f.nobs)})
reg_table = pd.DataFrame(rows).set_index("model")
print("\nOutcome: log(1 + units sold this month); coefficient on last month's rating (SE clustered by product)")
print(reg_table.round(3).to_string())
print("Read as: +1 star -> about 100 x coefficient % more units (approximately, for small values).")
within_sd = (est["rating_lag"] - est.groupby("sku")["rating_lag"].transform("mean")).std()
print(f"How much does a product's rating move over time? Within-product SD = {within_sd:.3f} stars "
      f"(vs {est['rating_lag'].std():.3f} across products)")

# %% [markdown]
# ## Q6. Sales by brand (POS.dta merged with brand_list.dta on sku, done in Q1)

# %% Q6a: top 10 brands by units sold, and revenue by brand
brand_sales = sql("""SELECT brand, count(*) AS units, sum(price) AS revenue, avg(price) AS avg_price,
                            avg(sale) AS share_discounted, count(DISTINCT sku) AS skus
                     FROM pos_b GROUP BY brand ORDER BY units DESC""")
total_rev = brand_sales["revenue"].sum()
brand_sales["revenue_share"] = brand_sales["revenue"] / total_rev
brand_sales["revenue_rank"] = brand_sales["revenue"].rank(ascending=False).astype(int)
print(f"Total revenue: ${total_rev / 1e6:,.1f}M from {len(brand_sales)} brands")
print(brand_sales.head(10).round(3).to_string(index=False))

top10u = brand_sales.head(10)
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.barh(top10u["brand"][::-1], top10u["units"][::-1], color=DARK_GREEN, height=0.65)
for y, (v, r) in enumerate(zip(top10u["units"][::-1], top10u["revenue_rank"][::-1])):
    ax.text(v, y, f" {v / 1e6:.2f}M  (revenue rank #{r})", va="center", fontsize=8.5)
ax.xaxis.set_major_formatter(millions)
ax.set_xlabel("Units sold")
ax.grid(axis="y", visible=False)
finish(fig, ax, "q6_top10_brands_units", f"{top10u['brand'].iloc[0]} and {top10u['brand'].iloc[1]} sell the most pairs",
       "Top 10 brands by units sold (brand_list parent brands)")

# %% Q6b: revenue by brand (top 15) and how concentrated sales are
top15r = brand_sales.sort_values("revenue", ascending=False).head(15)
cum = brand_sales.sort_values("revenue", ascending=False)["revenue_share"].cumsum().to_numpy()
n80 = int(np.searchsorted(cum, 0.80) + 1)
print(top15r[["brand", "revenue", "revenue_share", "units", "avg_price"]].round(3).to_string(index=False))
print(f"Top 10 brands: {cum[9]:.1%} of revenue | top 50: {cum[49]:.1%} | brands needed for 80%: {n80} of {len(cum)}")

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
ax.barh(top15r["brand"][::-1], top15r["revenue"][::-1], color=DARK_GREEN, height=0.65)
for y, (v, s) in enumerate(zip(top15r["revenue"][::-1], top15r["revenue_share"][::-1])):
    ax.text(v, y, f" ${v / 1e6:.0f}M ({s:.1%})", va="center", fontsize=8.5)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x / 1e6:,.0f}M"))
ax.set_xlabel("Revenue (sum of prices paid)")
ax.grid(axis="y", visible=False)
ax.set_title("Top 15 brands by revenue", fontsize=10.5)
ax2.plot(np.arange(1, len(cum) + 1), cum * 100, color=DARK_GREEN, linewidth=2.5)
ax2.axhline(80, color=GREY, linewidth=0.8, linestyle=":")
ax2.axvline(n80, color=GREY, linewidth=0.8, linestyle=":")
ax2.text(n80, 45, f"  {n80} of {len(cum)} brands\n  make 80% of revenue", color=INK, fontsize=8.5)
ax2.set_xlabel("Brands, ranked by revenue")
ax2.set_ylabel("Cumulative % of revenue")
ax2.set_ylim(0, 101)
ax2.set_title("A long tail of brands", fontsize=10.5)
fig.suptitle(f"The top 10 brands bring in {cum[9]:.0%} of revenue, but it takes {n80} brands to reach 80%",
             x=0.01, ha="left",
             fontweight="bold", fontsize=12, y=1.02)
fig.text(0.01, -0.03, f"Source: Zappos POS, Jul 2012-Aug 2013. Revenue = sum of prices paid "
         f"(${total_rev / 1e6:,.0f}M in total).", color=GREY, fontsize=7.5)
fig.savefig(FIG / "q6_revenue_by_brand.png")
if "agg" not in matplotlib.get_backend().lower():
    plt.show()
plt.close(fig)

# %% [markdown]
# ## Q7. Pricing, timing and seasonality (POS.dta + categories.csv)

# %% Q7a: daily sales volume
daily = sql("""SELECT day, count(*) AS units, sum(price) AS revenue, avg(sale) AS share_discounted,
                      avg(percent_off) AS avg_pct_off FROM pos GROUP BY day ORDER BY day""")
daily["day"] = pd.to_datetime(daily["day"])
daily = daily.set_index("day")
full_range = pd.date_range(daily.index.min(), daily.index.max())
print(f"Days in range: {len(full_range)} | days with sales: {len(daily)} | missing days: {len(full_range) - len(daily)}")
print(f"First and last day are partial: {daily['units'].iloc[0]:,} and {daily['units'].iloc[-1]:,} units "
      f"vs a median day of {daily['units'].median():,.0f}")
daily["dow"] = daily.index.day_name()

# Data-gap check: with ~1,400 sales per hour even at night, every hour of a full day should have
# sales. Days with missing hours are recording gaps, not low demand: flag them and keep them out
# of the smoothing and the time-of-day regressions below.
hours_seen = sql("SELECT day, count(DISTINCT hour) AS hours FROM pos GROUP BY day")
hours_seen["day"] = pd.to_datetime(hours_seen["day"])
daily["hours_recorded"] = hours_seen.set_index("day")["hours"]
DST_START = pd.Timestamp("2013-03-10")    # clocks jump from 2 am to 3 am: 23 hours is normal that day
gap_days = [x for x in daily.index[daily["hours_recorded"] < 24]
            if x not in (daily.index[0], daily.index[-1], DST_START)]  # first/last day are partial anyway
print("Days with missing hours (recording gaps):")
print(daily.loc[gap_days, ["units", "hours_recorded", "dow"]].to_string())
print("\nBusiest days:\n" + daily.nlargest(6, "units")[["units", "revenue", "share_discounted", "dow"]].round(3).to_string())
print("\nQuietest full days:\n" + daily.iloc[1:-1].nsmallest(5, "units")[["units", "revenue", "dow"]].round(3).to_string())
dow_avg = daily.iloc[1:-1].groupby("dow")["units"].mean().reindex(
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
print("\nAverage units by day of week:\n" + dow_avg.round(0).to_string())
print(f"Correlation of daily units with share discounted: {daily['units'].corr(daily['share_discounted']):.2f}")

# %% Q7b: total sales and revenue by date
d = daily.iloc[1:-1].copy()                                        # drop the two partial days
peaks = d.nlargest(3, "units")
fig, (ax, ax2) = plt.subplots(2, 1, figsize=(9, 5.6), sharex=True)
ax.plot(d.index, d["units"], color=DARK_GREEN, linewidth=1)
ax2.plot(d.index, d["revenue"], color=SALMON, linewidth=1)
top_day = peaks.index[0]
ax.annotate(f"Cyber Monday ({top_day:%b %d})\n{peaks['units'].iloc[0]:,.0f} units", (top_day, peaks["units"].iloc[0]),
            xytext=(8, -2), textcoords="offset points", fontsize=8, color=INK, va="top")
ax.plot(gap_days, d.loc[gap_days, "units"], "o", color=DARK_RED, ms=4)   # recording gaps
ax2.plot(gap_days, d.loc[gap_days, "revenue"], "o", color=DARK_RED, ms=4)
ax.set_ylabel("Units per day")
ax2.set_ylabel("Revenue per day")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x / 1e3:,.0f}k"))
ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x / 1e6:,.1f}M"))
ax.set_ylim(0, None)
ax2.set_ylim(0, None)
finish(fig, ax, "q7_daily_sales_revenue", "Cyber Monday is the biggest day; sales follow a weekly rhythm",
       "Units sold (top) and revenue (bottom) per day; red dots = days with missing hours of records",
       note="First and last (partial) days dropped.")

# %% Q7c: smoothing: 7-day and 28-day moving averages, and an STL trend
# Gap days are set to missing first, so a recording outage does not drag the averages down.
from statsmodels.tsa.seasonal import STL

for col in ["units", "revenue"]:
    s_ = d[col].mask(d.index.isin(gap_days))
    d[f"{col}_ma7"] = s_.rolling(7, center=True, min_periods=5).mean()     # removes the weekly cycle
    d[f"{col}_ma28"] = s_.rolling(28, center=True, min_periods=21).mean()  # monthly trend
stl_input = d["units"].mask(d.index.isin(gap_days)).interpolate()
stl = STL(stl_input, period=7, robust=True).fit()                  # trend + weekly pattern + rest
weekly_share = 1 - (stl.resid + stl.trend).var() / stl_input.var()
print(f"STL: the weekly pattern alone explains about {weekly_share:.0%} of day-to-day variation in units")

fig, (ax, ax2) = plt.subplots(2, 1, figsize=(9, 5.6), sharex=True)
for a, col, color, fmt in [(ax, "units", DARK_GREEN, lambda x, _: f"{x / 1e3:,.0f}k"),
                           (ax2, "revenue", SALMON, lambda x, _: f"${x / 1e6:,.1f}M")]:
    a.plot(d.index, d[col], color=color, linewidth=0.6, alpha=0.3, label="Daily (raw)")
    a.plot(d.index, d[f"{col}_ma7"], color=color, linewidth=1.6, label="7-day average")
    a.plot(d.index, d[f"{col}_ma28"], color=INK, linewidth=1.6, linestyle="--", label="28-day average")
    a.yaxis.set_major_formatter(FuncFormatter(fmt))
    a.set_ylim(0, None)
    a.legend(loc="lower left", ncol=3, fontsize=8)
ax.set_ylabel("Units per day")
ax2.set_ylabel("Revenue per day")
early = d.loc[:"2012-11-15", "revenue"].mean()
late = d.loc["2013-02-01":"2013-07-31", "revenue"].mean()
print(f"Average daily revenue: Jul 13-Nov 15 2012 ${early / 1e6:.2f}M vs Feb-Jul 2013 ${late / 1e6:.2f}M "
      f"({late / early - 1:+.0%}); units {d.loc[:'2012-11-15', 'units'].mean():,.0f} vs "
      f"{d.loc['2013-02-01':'2013-07-31', 'units'].mean():,.0f}")
finish(fig, ax, "q7_smoothed_sales_revenue", "Sales build to a December peak, then run lower through 2013",
       "Daily units (top) and revenue (bottom): raw (faint), 7-day and 28-day centred moving averages")

# %% Q7d: what are the category codes? (Bonus: inferred from product data and best sellers)
cat_chars = categories.merge(stock, on="sku", how="left", validate="one_to_many")
print(f"categories {categories.shape} + stock_chars -> {cat_chars.shape} (one row per product-color)")
evidence = cat_chars.groupby("categ").agg(
    skus=("sku", "nunique"),
    boot_shaft=("boot_shaft", lambda x: x.notna().mean()),
    heel_style=("heel_style", lambda x: x.notna().mean()),
    open_or_peep_toe=("toe_style", lambda x: x.isin(["Open Toe", "Peep Toe"]).mean()),
    athletic=("occasion", lambda x: (x == "Athletic").mean()),
    median_price=("orig_price", "median"))
con.register("categories", categories)
top_items = sql("""
    WITH x AS (SELECT c.categ, p.item, count(*) AS n,
                      row_number() OVER (PARTITION BY c.categ ORDER BY count(*) DESC) AS r
               FROM pos p JOIN categories c USING (sku) GROUP BY 1, 2)
    SELECT categ, string_agg(item, ' | ' ORDER BY r) AS best_sellers FROM x WHERE r <= 4 GROUP BY 1""")
evidence = evidence.join(top_items.set_index("categ"))
CATEG_NAMES = {0: "Boat shoes", 1: "Boots", 2: "Climbing shoes", 3: "Clogs & mules", 4: "Flats",
               5: "Heels & pumps", 6: "Loafers & moccasins", 7: "Oxfords & dress lace-ups", 8: "Sandals",
               9: "Slippers", 10: "Sneakers & athletic"}
evidence["our_guess"] = evidence.index.map(CATEG_NAMES)
print(evidence.round(2).to_string())

# %% Q7e: monthly sales pattern for three categories (indexed: each category's average month = 100)
cat_month = sql("""SELECT c.categ, date_trunc('month', p.day) AS month, count(*) AS units,
                          count(DISTINCT p.day) AS days
                   FROM pos p JOIN categories c USING (sku) WHERE c.categ IN (1, 8, 10) GROUP BY 1, 2""")
cat_month["per_day"] = cat_month["units"] / cat_month["days"]      # fair for partial months
cat_month["index"] = cat_month["per_day"] / cat_month.groupby("categ")["per_day"].transform("mean") * 100
wide = cat_month.pivot(index="month", columns="categ", values="index").sort_index()
print(wide.round(0).to_string())

fig, ax = plt.subplots(figsize=(8, 4.4))
for code, color in [(1, DARK_RED), (8, "#c9a227"), (10, DARK_GREEN)]:
    ax.plot(wide.index, wide[code], color=color, linewidth=2.5, marker="o", ms=4)
    ax.text(wide.index[-1], wide[code].iloc[-1], f"  {code}: {CATEG_NAMES[code]}", color=color,
            fontweight="bold", va="center", fontsize=9)
ax.axhline(100, color=GREY, linewidth=0.8)
ax.set_ylabel("Units per day (category average month = 100)")
finish(fig, ax, "q7_category_seasonality", "Boots peak in winter, sandals in summer; sneakers stay steady",
       "Monthly sales per day for three category codes, indexed to each category's own average")

# %% Q7f: what matters more: time of day, day of week or month?
# Hourly unit counts for every hour of every full day, then: how much of the variation does each
# set of dummies explain (R-squared)? Partial R2 = what is lost when that set is dropped.
hourly = sql("SELECT day, hour, count(*) AS units FROM pos GROUP BY ALL")
hourly["day"] = pd.to_datetime(hourly["day"])
full_days = d.index.difference(gap_days)                           # complete days only
grid = pd.MultiIndex.from_product([full_days, range(24)], names=["day", "hour"]).to_frame(index=False)
hourly = grid.merge(hourly, on=["day", "hour"], how="left", validate="one_to_one").fillna({"units": 0})
hourly = hourly[~((hourly["day"] == DST_START) & (hourly["hour"] == 2))]   # that hour never existed
hourly["dow"] = hourly["day"].dt.dayofweek
hourly["month"] = hourly["day"].dt.month
print(f"Hourly observations: {len(hourly):,} ({len(full_days)} complete days x 24)")
full_r2 = smf.ols("units ~ C(hour) + C(dow) + C(month)", hourly).fit().rsquared
r2 = []
for name, term in [("Time of day (24 hours)", "C(hour)"), ("Day of week (7)", "C(dow)"), ("Month (12)", "C(month)")]:
    alone = smf.ols(f"units ~ {term}", hourly).fit().rsquared
    others = " + ".join(t for t in ["C(hour)", "C(dow)", "C(month)"] if t != term)
    partial = full_r2 - smf.ols(f"units ~ {others}", hourly).fit().rsquared
    r2.append({"factor": name, "R2 alone": alone, "R2 lost if dropped": partial})
r2 = pd.DataFrame(r2).set_index("factor")
print(r2.round(3).to_string())
print(f"All three together: R2 = {full_r2:.3f}")

# Second view: for planning DAILY volume (staffing, warehouse), compare weekday vs month on daily totals
dd = d.loc[full_days].assign(dow=lambda x: x.index.dayofweek, month=lambda x: x.index.month)
print(f"Daily totals ({len(dd)} days): R2 day of week = {smf.ols('units ~ C(dow)', dd).fit().rsquared:.3f}, "
      f"R2 month = {smf.ols('units ~ C(month)', dd).fit().rsquared:.3f}")

fig, ax = plt.subplots(figsize=(7, 3))
ax.barh(r2.index[::-1], r2["R2 alone"][::-1] * 100, color=DARK_GREEN, height=0.6)
for y, v in enumerate(r2["R2 alone"][::-1] * 100):
    ax.text(v, y, f" {v:.0f}%", va="center", fontsize=9)
ax.set_xlim(0, 100)
ax.set_xlabel("% of hour-to-hour variation in units explained (R-squared)")
ax.grid(axis="y", visible=False)
finish(fig, ax, "q7_time_of_day_vs_week_vs_month", "Time of day matters far more than weekday or month",
       "Regression of hourly units sold on each set of time dummies")

# %% [markdown]
# ## Q8 support: segment scorecard for the executive summary
# One table per segment type: share of units and revenue, average price, how often it is
# discounted, and its average product rating. This is what the recommendations are based on.

# %% Q8: segment scorecard
con.register("sku_rating", prod[["sku", "overall", "comfort"]])
for seg, expr, src in [("gender", "gender", "pos_f"),
                       ("category", "categ", "pos_f JOIN categories USING (sku)")]:
    tab = sql(f"""
        SELECT {expr} AS segment, count(*) AS units, sum(price) AS revenue, avg(price) AS avg_price,
               avg(sale) AS share_discounted, avg(CASE WHEN sale = 1 THEN percent_off END) AS pct_off_when_disc,
               avg(r.overall) AS avg_rating, avg(r.comfort) AS avg_comfort
        FROM {src} LEFT JOIN sku_rating r USING (sku)
        WHERE {expr} IS NOT NULL GROUP BY 1""")
    tab["units_share"] = tab["units"] / tab["units"].sum()
    tab["revenue_share"] = tab["revenue"] / tab["revenue"].sum()
    if seg == "category":
        tab["segment"] = tab["segment"].map(CATEG_NAMES)
    cols = ["segment", "units_share", "revenue_share", "avg_price", "share_discounted",
            "pct_off_when_disc", "avg_rating", "avg_comfort"]
    print(f"\nBy {seg} (ratings are unit-weighted averages of product ratings):")
    print(tab.sort_values("revenue", ascending=False)[cols].round(3).to_string(index=False))

print("\nReview-count coefficient in the ratings regressions (log reviews last month):")
for name, f in models.items():
    print(f"  {name}: {f.params['log_reviews_lag']:+.3f} (SE {f.bse['log_reviews_lag']:.3f})"
          if "log_reviews_lag" in f.params else f"  {name}: not in model")


# %% [markdown]
# ## Final checks: raw files unchanged, key numbers reproduced
# The values below were recorded during the question-by-question review (hw2/results_log.md).
# A clean Run All must reproduce them exactly.

# %% Final checks
for f in RAW:
    assert sha256(f) == raw_hash[f.name], f"RAW FILE CHANGED: {f.name}"
print("Raw files unchanged:", ", ".join(raw_hash))

key_numbers = {
    "Sales rows (units)": (clean_n, 13_546_258),
    "Brands in brand_list": (brand_list["brand"].nunique(), 615),
    "Brand names in POS": (int(pos_brands["n"][0]), 842),
    "Sales matched on sku + color (%)": (round(keys.iloc[0, 0] * 100, 1), 95.2),
    "Median price paid ($)": (round(stats.loc[1, "median"], 2), 70.99),
    "Women: share of units discounted (%)": (round(disc.set_index("gender").loc["Women", "share_discounted"] * 100, 1), 32.8),
    "Average look rating": (round(dims.loc["look", "mean"], 3), 4.668),
    "Review rows matched to features (%)": (round((rv_f["_merge"] == "both").mean() * 100, 1), 95.9),
    "California units": (int(by_state.set_index("state").loc["CA", "units"]), 1_920_377),
    "Rating effect, product FE": (round(reg_table.iloc[2, 0], 3), -0.043),
    "Top 10 brands' revenue share (%)": (round(cum[9] * 100, 1), 33.3),
    "Biggest day (units)": (int(peaks["units"].iloc[0]), 57_736),
    "R2 time of day": (round(r2.iloc[0, 0], 3), 0.856),
}
check = pd.DataFrame([(k, a, b) for k, (a, b) in key_numbers.items()],
                     columns=["number", "this run", "recorded"], dtype=object).set_index("number")
check["match"] = check["this run"] == check["recorded"]
print(check.to_string())
assert check["match"].all(), "a key number changed - investigate before submitting"
print(f"All {len(check)} key numbers reproduced.")
