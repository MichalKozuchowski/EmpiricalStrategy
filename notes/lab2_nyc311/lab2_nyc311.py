"""MGT 634 Lab Day 2: NYC 311 Service Analytics (all questions, one command).

Run:   python lab2_nyc311.py            (on the cluster, from a terminal or `%run lab2_nyc311.py`)
Team:  Michal Kozuchowski, Laila Lapins, Nick Giamalis, Raymond Chang, Sean Weller

What happens, in order (each block is labelled with its question number):
  0. Setup: find the 311 JSON files, read cores/memory, start DuckDB (SQL engine that streams
     data from disk, so the full data never has to fit in memory - Class 7).
  1. Load: convert the JSON files once into a compact Parquet copy (raw text kept). Broken files
     are repaired: every complete record before the break is recovered and logged.
  2. Clean table `sr` (typed dates, borough, ZIP, standardized complaint types, categories).
  Q1-Q11: each block prints its numbers, saves charts to output/figures, and writes the
  answers to output/results.md. Q8 writes an interactive map to output/q8_dashboard.html.
The raw JSON files are only read, never changed.
"""
import glob
import json
import os
import re
import site
import subprocess
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path


def need(package, pip_name=None):
    """Import a package; if missing, install it for this user (the cluster has no uv)."""
    try:
        return __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "-q", pip_name or package])
        sys.path.insert(0, site.getusersitepackages())
        return __import__(package)


for pkg in ["duckdb", "pyarrow", "statsmodels", "plotly"]:
    need(pkg)

import duckdb
import matplotlib
if "ipykernel" not in sys.modules:
    matplotlib.use("Agg")                                  # script run: save charts to files only
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import statsmodels.formula.api as smf
from matplotlib.ticker import FuncFormatter

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_colwidth", 70)

# =============================================================================================
# 0. SETUP: files, output folders, computer size, DuckDB
# =============================================================================================
try:
    HERE = Path(__file__).resolve().parent
except NameError:                                          # pasted into a Jupyter cell
    HERE = Path.cwd()
SEARCH = [os.environ.get("NYC311_DATA", os.path.expanduser("~/esai_2026/data/311")), "~/esai_2026/data/*311*/", "~/esai_2026/data/*/", "~/esai_2026/data/*/*/",
          "~/esai_2026/class/*/", "~/esai_2026/class/*/*/", "~/esai_2026/class/*/*/*/",
          "/gpfs/project/esai_2026/data/*/", "/gpfs/project/esai_2026/data/*/*/",
          str(HERE / "data"), str(HERE.parents[1] / "data" / "nyc311" / "data"), "~/data/", "~/"]
DATA = None
for pattern in [s for s in SEARCH if s]:
    for folder in sorted(glob.glob(os.path.expanduser(pattern))):
        if glob.glob(os.path.join(folder, "311_batch_*.json")):
            DATA = Path(folder)
            break
    if DATA:
        break
assert DATA, "No 311_batch_*.json files found: set NYC311_DATA=/path/to/folder and re-run"
FILES = sorted(glob.glob(str(DATA / "311_batch_*.json")))
STRIDE = int(os.environ.get("STRIDE", "1"))                # STRIDE=30: every 30th file (quick test run)
FILES = FILES[::STRIDE]

OUT = HERE / "lab2_output"                                  # own folder: nothing else gets mixed in
FIG = OUT / "figures"
WORK = Path(os.environ.get("NYC311_WORK", "~/lab2_cache")).expanduser() / f"stride{STRIDE}"
PARTS = WORK / "parts"
for p in [OUT, FIG, PARTS, WORK / "tmp"]:
    p.mkdir(parents=True, exist_ok=True)


def cores():
    for v in ["SLURM_CPUS_PER_TASK", "SLURM_CPUS_ON_NODE"]:
        if os.environ.get(v, "").isdigit():
            return int(os.environ[v])
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        return os.cpu_count() or 1


def memory_gb():
    if os.environ.get("SLURM_MEM_PER_NODE", "").isdigit():
        return int(os.environ["SLURM_MEM_PER_NODE"]) / 1024
    for f in ["/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"]:
        try:
            v = open(f).read().strip()
            if v.isdigit() and int(v) < 1 << 50:
                return int(v) / 1024 ** 3
        except OSError:
            pass
    return 8.0


CORES, MEM = cores(), memory_gb()
con = duckdb.connect()
con.execute(f"SET threads = {CORES}")
con.execute(f"SET memory_limit = '{max(1, int(MEM * 0.6))}GB'")          # spill to disk, never crash
con.execute(f"SET temp_directory = '{(WORK / 'tmp').as_posix()}'")
con.execute("SET preserve_insertion_order = false")
sql = lambda q: con.sql(q).df()

REPORT = []                                                 # everything written to results.md


def say(*lines):
    """Print and keep for results.md."""
    for line in lines:
        print(line)
        REPORT.append(str(line))


def table(df, title=None, n=40):
    if title:
        say(f"\n**{title}**")
    txt = df.head(n).to_string(index=False)
    print(txt)
    REPORT.append("```\n" + txt + "\n```")


say(f"# MGT 634 Lab Day 2: NYC 311 Service Analytics", "",
    f"Data: {DATA} | {len(FILES):,} files used (every {STRIDE}th file)" if STRIDE > 1 else
    f"Data: {DATA} | {len(FILES):,} files", f"Computer: {CORES} cores, {MEM:.0f} GB memory")

# ---- chart style (Upshot look) ----
DARK_GREEN, SAGE, CREAM, SALMON, DARK_RED, GOLD = "#636e4f", "#a3ae8d", "#fbebb7", "#d1725c", "#993f2a", "#c9a227"
INK, GREY, LIGHT = "#121212", "#737373", "#eeeeee"
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9.5, "axes.titlesize": 12.5, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.edgecolor": "#999999", "axes.labelcolor": "#555555", "axes.grid": True,
    "axes.axisbelow": True, "grid.color": LIGHT, "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "xtick.color": "#555555", "ytick.color": "#555555", "ytick.left": False,
    "legend.frameon": False, "savefig.dpi": 200, "savefig.bbox": "tight", "figure.facecolor": "white",
    "axes.prop_cycle": matplotlib.cycler(color=[DARK_GREEN, SALMON, SAGE, DARK_RED, GOLD])})
if "text.parse_math" in plt.rcParams:
    plt.rcParams["text.parse_math"] = False
thousands = FuncFormatter(lambda x, _: f"{x:,.0f}")


def save(fig, name, title=None, subtitle=None, ax=None, note=None):
    """Finding as title, grey subtitle, source line under everything, save PNG."""
    if ax is not None and title:
        ax.set_title(title, pad=22 if subtitle else 8)
        if subtitle:
            ax.text(0, 1.015, subtitle, transform=ax.transAxes, color=GREY, fontsize=9, va="bottom")
    r = fig.canvas.get_renderer()
    bottom = min(a.get_tightbbox(r).transformed(fig.transFigure.inverted()).y0 for a in fig.axes)
    fig.text(0.01, bottom - 0.015, "Source: NYC 311 service requests" + (f"; {note}" if note else "") + ".",
             color=GREY, fontsize=7.5, va="top")
    fig.savefig(FIG / f"{name}.png")
    plt.show()
    plt.close(fig)
    REPORT.append(f"![{name}](figures/{name}.png)")


# =============================================================================================
# 1. LOAD: JSON files -> Parquet copy (raw text), repairing broken files
# =============================================================================================
t0 = time.time()
first = json.load(open(FILES[0]))
FIELDS = sorted({k for r in first[:2000] for k in r} - {"location"})          # nested duplicate of lat/lon
for f in FILES[1:: max(1, len(FILES) // 8)]:                                  # pick up fields added later
    try:
        FIELDS = sorted(set(FIELDS) | {k for r in json.load(open(f))[:2000] for k in r} - {"location"})
    except ValueError:
        pass
spec = "{" + ", ".join(f"'{k}': 'VARCHAR'" for k in FIELDS) + "}"
GROUP = 50 if MEM >= 16 else 10
groups = [FILES[i:i + GROUP] for i in range(0, len(FILES), GROUP)]
REPAIR_LOG = WORK / "repaired_files.json"                   # remembered across runs
repaired = json.load(open(REPAIR_LOG)) if REPAIR_LOG.exists() else []


def salvage(path):
    """Read a JSON array record by record and keep every complete record before a break."""
    text, dec, i, recs = open(path).read(), json.JSONDecoder(), 1, []
    while True:
        try:
            obj, j = dec.raw_decode(text, i)
        except ValueError:
            break
        recs.append(obj)
        i = j
        while i < len(text) and text[i] in ", \n\r\t":
            i += 1
    return recs


for gi, group in enumerate(groups):
    out = PARTS / f"part_{gi:05d}.parquet"
    if out.exists():
        continue
    good = []
    for f in group:                                         # quick validity check per file
        try:
            con.execute(f"SELECT count(*) FROM read_json('{Path(f).as_posix()}', format='array', columns={spec})")
            good.append(f)
        except Exception:
            recs = salvage(f)
            repaired.append((Path(f).name, len(recs)))
            if recs:
                df_fix = pd.DataFrame(recs).reindex(columns=FIELDS).astype("string")
                df_fix["filename"] = Path(f).as_posix()
                df_fix.to_parquet(PARTS / f"repaired_{Path(f).stem}.parquet", index=False)
    if good:
        lst = "[" + ", ".join(f"'{Path(f).as_posix()}'" for f in good) + "]"
        con.execute(f"""COPY (SELECT * FROM read_json({lst}, format='array', columns={spec}, filename=true))
                        TO '{out.as_posix()}' (FORMAT parquet, COMPRESSION zstd)""")
    if (gi + 1) % 10 == 0:
        print(f"  converted {gi + 1}/{len(groups)} groups ({time.time() - t0:.0f}s)")
json.dump(repaired, open(REPAIR_LOG, "w"))
con.execute(f"CREATE OR REPLACE VIEW raw AS SELECT * FROM read_parquet('{(PARTS / '*.parquet').as_posix()}', union_by_name=true)")
n_raw = sql("SELECT count(*) FROM raw").iloc[0, 0]
say(f"Loaded {n_raw:,} records in {time.time() - t0:.0f}s. Broken (truncated) files repaired: "
    + (", ".join(f"{a} ({b:,} complete records recovered)" for a, b in repaired) if repaired else "none"))

# =============================================================================================
# 2. CLEAN TABLE `sr` (one row per request) + standardized complaint types
# =============================================================================================
# Complaint-type standardization (Q3b): rules live in two small, editable tables, so new data is
# handled automatically: (1) a normalizer (case, spaces, punctuation, plurals) and (2) an explicit
# alias table for known renames. Unknown new types fall through the normalizer and are flagged.
ALIASES = {
    "HEATING": "HEAT/HOT WATER", "HEAT/HOT WATER": "HEAT/HOT WATER",
    "DERELICT VEHICLES": "DERELICT VEHICLE", "GENERAL CONSTRUCTION": "GENERAL CONSTRUCTION/PLUMBING",
    "NONCONST": "NON-CONSTRUCTION (HPD)", "PAINT - PLASTER": "PAINT/PLASTER", "PAINT/PLASTER": "PAINT/PLASTER",
    "NOISE": "NOISE - OTHER (DEP)", "HPD LITERATURE REQUEST": "LITERATURE REQUEST",
    "STREET LIGHT CONDITION": "STREET LIGHT CONDITION", "SEWER": "SEWER",
    "TRAFFIC/ILLEGAL PARKING": "ILLEGAL PARKING", "ILLEGAL PARKING": "ILLEGAL PARKING",
    "BROKEN MUNI METER": "BROKEN PARKING METER", "BROKEN PARKING METER": "BROKEN PARKING METER",
    "DHS ADVANTAGE -LANDLORD/BROKER": "DHS ADVANTAGE - LANDLORD/BROKER",
    "UNSANITARY CONDITION": "UNSANITARY CONDITION", "ELECTRIC": "ELECTRIC", "PLUMBING": "PLUMBING",
}
# Category = where the problem comes from (Q9): building owners, the city's own infrastructure and
# services, people in the neighborhood, nature/weather, or information/admin requests.
CATEGORY_RULES = [  # (category, keywords searched in the standardized type), first match wins
    ("Information / admin request", ["LITERATURE", "SCRIE", "DOF ", "DCA ", "LICENSE", "DHS ADVANTAGE", "CONSUMER",
                                     "REQUEST", "PAYMENT", "OWNER ISSUE", "OPINION", "SPECIAL ENFORCEMENT"]),
    ("Nature / weather", ["SNOW", "TREE", "FLOOD", "ICE", "RODENT", "MOSQUITO", "DEAD ANIMAL", "PLANT", "HEAT INDEX"]),
    ("Building owner / landlord", ["HEAT", "PLUMBING", "PAINT", "CONSTRUCTION", "ELECTRIC", "APPLIANCE", "ELEVATOR",
                                   "DOOR", "WINDOW", "FLOORING", "WATER LEAK", "UNSANITARY", "MOLD", "BUILDING",
                                   "SAFETY", "BOILER", "OUTSIDE BUILDING", "GENERAL", "NON-CONSTRUCTION", "INDOOR AIR"]),
    ("Neighbors / public behavior", ["NOISE", "PARKING", "DRIVEWAY", "DERELICT", "ABANDONED", "GRAFFITI", "DIRTY",
                                     "LITTER", "VENDING", "SMOKING", "DRINKING", "ANIMAL", "HOMELESS", "PANHANDLING",
                                     "TAXI", "FOR HIRE", "VEHICLE", "BIKE", "FIREWORK", "ILLEGAL", "URINATING"]),
    ("City infrastructure / services", ["STREET", "SIDEWALK", "TRAFFIC", "SIGNAL", "LIGHT", "SEWER", "WATER", "METER",
                                        "SANITATION", "COLLECTION", "HYDRANT", "CURB", "HIGHWAY", "BRIDGE", "PARK",
                                        "RECYCLING", "BUS", "SUBWAY", "SCHOOL", "AIR QUALITY", "DEP", "CATCH BASIN"]),
]


def normalize(t):
    """Upper case, trim, single spaces, consistent ' - ' and '/' spacing."""
    t = re.sub(r"\s+", " ", str(t).upper().strip())
    t = re.sub(r"\s*-\s*", " - ", t)
    return re.sub(r"\s*/\s*", "/", t)


def standardize(t):
    n = normalize(t)
    return ALIASES.get(n, n)


def category(std):
    for cat, words in CATEGORY_RULES:                      # whole-word start: "TREE" must not match "STREET"
        if any(re.search(r"\b" + re.escape(w.strip()), std) for w in words):
            return cat
    return "Other"


types = sql("SELECT complaint_type, upper(agency) AS agency, count(*) AS n FROM raw GROUP BY ALL")
type_map = (types.groupby("complaint_type", as_index=False)
            .agg(n=("n", "sum"), agency=("agency", lambda s: "/".join(sorted(set(s.dropna()))))))
type_map["normalized"] = type_map["complaint_type"].map(normalize)
type_map["standard_type"] = type_map["complaint_type"].map(standardize)
type_map["category"] = type_map["standard_type"].map(category)
type_map.sort_values("n", ascending=False).to_csv(OUT / "complaint_type_map.csv", index=False)
con.register("type_map", type_map[["complaint_type", "standard_type", "category"]])

import hashlib                                              # rebuild the clean table whenever the rules change
RULES_ID = hashlib.md5(type_map[["complaint_type", "standard_type", "category"]].to_csv().encode()).hexdigest()[:8]
SR = WORK / f"sr_clean_{RULES_ID}.parquet"
DISGUISED = "('', 'N/A', 'NA', 'UNSPECIFIED', 'UNKNOWN', 'NONE', 'NULL', '0', '0 UNSPECIFIED', '00000')"
dupes = sql("SELECT count(*) - count(DISTINCT unique_key) AS d FROM raw").iloc[0, 0]   # cheap check
say(f"Duplicate request ids across files: {dupes:,}")
DEDUPE = ("" if dupes == 0 else                            # light de-duplication only if needed (no 28M-row sort)
          "WHERE (unique_key, filename) IN (SELECT unique_key, max(filename) FROM raw GROUP BY 1)")
if not SR.exists():
    con.execute(f"""
    COPY (
    WITH one AS (SELECT * FROM raw {DEDUPE}),
    t AS (
        SELECT one.*, m.standard_type, m.category,
               TRY_CAST(created_date AS TIMESTAMP) AS created, TRY_CAST(closed_date AS TIMESTAMP) AS closed_raw,
               TRY_CAST(latitude AS DOUBLE) AS lat, TRY_CAST(longitude AS DOUBLE) AS lon,
               regexp_extract(incident_zip, '^(\\d{{5}})', 1) AS zip5
        FROM one LEFT JOIN type_map m USING (complaint_type))
    SELECT *,
        CASE WHEN upper(borough) IN ('MANHATTAN','BRONX','BROOKLYN','QUEENS','STATEN ISLAND') THEN upper(borough)
             WHEN left(bbl,1)='1' THEN 'MANHATTAN' WHEN left(bbl,1)='2' THEN 'BRONX' WHEN left(bbl,1)='3' THEN 'BROOKLYN'
             WHEN left(bbl,1)='4' THEN 'QUEENS' WHEN left(bbl,1)='5' THEN 'STATEN ISLAND'
             WHEN left(zip5,3) IN ('100','101','102') THEN 'MANHATTAN' WHEN left(zip5,3)='103' THEN 'STATEN ISLAND'
             WHEN left(zip5,3)='104' THEN 'BRONX' WHEN left(zip5,3)='112' THEN 'BROOKLYN'
             WHEN left(zip5,3) IN ('110','111','113','114','116') THEN 'QUEENS' END AS boro,
        CASE WHEN regexp_matches(community_board, '^\\d{{2}} ') THEN community_board END AS cd,
        CAST(created AS DATE) AS day, created = date_trunc('day', created) AS created_midnight,
        CASE WHEN closed_raw >= created AND year(closed_raw) >= 2003 AND closed_raw <= current_timestamp
             THEN closed_raw END AS closed,
        CASE WHEN closed_raw >= created AND year(closed_raw) >= 2003 AND closed_raw <= current_timestamp
             THEN date_diff('second', created, closed_raw) / 86400.0 END AS days_to_close,
        upper(status) <> 'CLOSED' OR status IS NULL AS unresolved,
        lat BETWEEN 40.4 AND 41.0 AND lon BETWEEN -74.3 AND -73.6 AS in_nyc
    FROM t) TO '{SR.as_posix()}' (FORMAT parquet, COMPRESSION zstd)""")
con.execute(f"CREATE OR REPLACE VIEW sr AS SELECT * FROM read_parquet('{SR.as_posix()}')")
N = sql("SELECT count(*) FROM sr").iloc[0, 0]
span = sql("SELECT min(created) AS first, max(created) AS last FROM sr").iloc[0]
say(f"Clean table: {N:,} requests ({n_raw - N:,} duplicate ids removed), {span['first']} to {span['last']}.")

# =============================================================================================
# Q1. DATA QUALITY: missing values, including disguised and "not applicable" missingness
# =============================================================================================
say("", "## Q1. Missing values and data quality")
say("Missing is counted three ways: (1) truly empty (NULL); (2) **disguised** missing: text such as "
    "'Unspecified', 'N/A', 'UNKNOWN', '0 Unspecified', '00000', or impossible values (dates before 2003, "
    "coordinates outside NYC); (3) **not applicable**: a column that is only ever filled for some complaint "
    "types (e.g. taxi or bridge fields) is judged only on the complaint types where it is used.")
cols = [c for c in FIELDS if c not in ("filename",)]
null_expr = ", ".join(f"avg(({c} IS NULL)::INT) AS \"{c}\"" for c in cols)
disg_expr = ", ".join(f"avg((upper(trim({c})) IN {DISGUISED} OR upper({c}) LIKE 'UNSPECIFIED%')::INT) AS \"{c}\"" for c in cols)
nulls = sql(f"SELECT {null_expr} FROM raw").T[0]
disg = sql(f"SELECT {disg_expr} FROM raw").T[0]
# impossible values in date / coordinate columns count as disguised missing too
for c in ["closed_date", "due_date", "resolution_action_updated_date", "created_date"]:
    if c in cols:
        disg[c] += sql(f"SELECT avg((TRY_CAST({c} AS TIMESTAMP) < TIMESTAMP '2003-01-01')::INT) FROM raw").iloc[0, 0]
for c in ["latitude", "longitude"]:
    if c in cols:
        disg[c] += sql(f"SELECT avg((TRY_CAST({c} AS DOUBLE) = 0)::INT) FROM raw").iloc[0, 0]
# "not applicable": complaint types that ever fill the column = where it applies
filled = ", ".join(f"avg(({c} IS NOT NULL AND upper(trim({c})) NOT IN {DISGUISED} "
                   f"AND upper({c}) NOT LIKE 'UNSPECIFIED%')::DOUBLE) AS \"{c}\"" for c in cols)
per_type = sql(f"SELECT complaint_type AS type_key, count(*) AS n_rows, {filled} FROM raw GROUP BY 1")   # one pass over the data
appl_rows = []
for c in cols:
    used = per_type[c] > 0.05                               # complaint types that actually use this column
    w = per_type.loc[used, "n_rows"]
    mwa = 1 - (per_type.loc[used, c] * w).sum() / w.sum() if w.sum() else float("nan")
    appl_rows.append((c, int(used.sum()), mwa))
appl = pd.DataFrame(appl_rows, columns=["column", "types_using", "mwa"]).set_index("column")
miss = pd.DataFrame({"null_%": nulls * 100, "disguised_%": disg * 100}).round(1)
miss["total_missing_%"] = (miss["null_%"] + miss["disguised_%"]).clip(upper=100).round(1)
miss = miss.join(appl)
miss["n_types_total"] = type_map["complaint_type"].nunique()
miss["missing_where_applicable_%"] = (miss.pop("mwa") * 100).round(1)
miss = miss.sort_values("total_missing_%", ascending=False).reset_index().rename(columns={"index": "column"})
table(miss, "Missing values by column (% of all requests)", 60)
miss.to_csv(OUT / "q1_missing_values.csv", index=False)
other = sql(f"""SELECT sum((upper(status) LIKE '%TEST%')::INT) AS test_status_rows,
                       sum((TRY_CAST(closed_date AS TIMESTAMP) < TRY_CAST(created_date AS TIMESTAMP))::INT) AS closed_before_created,
                       sum((TRY_CAST(created_date AS TIMESTAMP) = date_trunc('day', TRY_CAST(created_date AS TIMESTAMP)))::INT) AS created_exactly_midnight,
                       count(*) - count(DISTINCT unique_key) AS duplicate_ids
                FROM raw""")
table(other, "Other data quality issues (rows)")

fig, ax = plt.subplots(figsize=(8, 7))
m = miss[miss["total_missing_%"] > 0].sort_values("total_missing_%")
ax.barh(m["column"], m["null_%"], color=SAGE, label="Empty (NULL)")
ax.barh(m["column"], m["disguised_%"], left=m["null_%"], color=SALMON, label="Disguised ('Unspecified', 'N/A', impossible)")
ax.scatter(m["missing_where_applicable_%"], m["column"], color=INK, s=14, zorder=5, label="Missing where the column applies")
ax.set_xlim(0, 100)
ax.set_xlabel("% of requests")
ax.legend(loc="lower right", fontsize=8)
ax.grid(axis="y", visible=False)
save(fig, "q1_missing_values", "Much of the 'missing' data is disguised or simply not applicable",
     "Share of requests missing each field; dot = missing among complaint types that use the field", ax)

# =============================================================================================
# Q2. CONSISTENCY OVER TIME: daily openings, closings, anomalies
# =============================================================================================
say("", "## Q2. Is data collection consistent over time?")
daily = sql("""SELECT day, count(*) AS opened, avg(created_midnight::INT) AS share_midnight FROM sr
               WHERE created IS NOT NULL GROUP BY 1 ORDER BY 1""")
daily["day"] = pd.to_datetime(daily["day"])
closed_d = sql("SELECT CAST(closed AS DATE) AS day, count(*) AS closed FROM sr WHERE closed IS NOT NULL GROUP BY 1")
closed_d["day"] = pd.to_datetime(closed_d["day"])
full = pd.DataFrame({"day": pd.date_range(daily["day"].min(), daily["day"].max())})
d = full.merge(daily, on="day", how="left").merge(closed_d, on="day", how="left").fillna({"opened": 0, "closed": 0})
d["med28"] = d["opened"].rolling(29, center=True, min_periods=7).median()
d["ratio"] = d["opened"] / d["med28"].where(d["med28"] > 0)
gaps = d[d["opened"] == 0]
low = d[(d["ratio"] < 0.5) & (d["opened"] > 0)]
spikes = d[d["ratio"] > 2]
say(f"Days in range: {len(d):,}; days with zero requests: {len(gaps):,}; days below half of the local "
    f"median: {len(low):,}; days above twice the local median: {len(spikes):,}.")
if len(gaps):
    table(gaps[["day"]].assign(day=gaps["day"].dt.date).head(20), "Days with no requests at all (first 20)")
table(d.assign(day=d["day"].dt.date).sort_values("ratio", ascending=False)[["day", "opened", "med28", "ratio"]].head(10).round(2),
      "Biggest spikes vs the local 4-week median")
table(d.assign(day=d["day"].dt.date)[d["opened"] > 0].sort_values("ratio")[["day", "opened", "med28", "ratio"]].head(10).round(2),
      "Biggest dips vs the local 4-week median")
yr = sql("""SELECT year(created) AS year, count(*) AS requests, avg(created_midnight::INT) AS share_created_at_midnight,
                   avg((closed IS NULL)::INT) AS share_no_valid_close FROM sr GROUP BY 1 ORDER BY 1""")
table(yr.round(3), "By year: volume and timestamp precision")

# Q2b. closing times
say("", "### Q2b. When are complaints closed?")
close_hour = sql("SELECT hour(closed_raw) AS hour, count(*) AS n FROM sr WHERE closed_raw IS NOT NULL GROUP BY 1 ORDER BY 1")
close_issues = sql("""SELECT sum((closed_raw IS NULL)::INT) AS no_closed_date,
                             sum((year(closed_raw) < 2003)::INT) AS closed_before_2003_placeholder,
                             sum((closed_raw < created)::INT) AS closed_before_opened,
                             sum((closed_raw = created)::INT) AS closed_same_second_as_opened,
                             sum((closed_raw > current_timestamp)::INT) AS closed_in_future,
                             sum((closed_raw = date_trunc('day', closed_raw))::INT) AS closed_exactly_midnight,
                             sum((days_to_close > 365)::INT) AS open_over_1_year
                      FROM sr""")
table(close_issues, "Closing-date problems (rows)")
bulk = sql("""SELECT closed_raw AS closed_timestamp, count(*) AS requests_closed, any_value(upper(agency)) AS agency
              FROM sr WHERE closed_raw IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10""")
table(bulk, "Most common exact closing timestamps (batch closures by a system, not by people)")
table(close_hour.T.reset_index(drop=True).rename(index={0: "hour", 1: "n"}).T.T, "Closures by hour of day")

# Q2c. openings and closings: over time, day of week, week of year
d["dow"] = d["day"].dt.dayofweek
d["week"] = d["day"].dt.isocalendar().week.astype(int)
fig = plt.figure(figsize=(11, 7.5))
gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1], hspace=0.45, wspace=0.25)
ax0 = fig.add_subplot(gs[0, :])
ax0.plot(d["day"], d["opened"].rolling(7, center=True).mean(), color=DARK_GREEN, linewidth=1.5, label="Opened (7-day average)")
ax0.plot(d["day"], d["closed"].rolling(7, center=True).mean(), color=SALMON, linewidth=1.5, label="Closed (7-day average)")
ax0.yaxis.set_major_formatter(thousands)
ax0.legend(loc="upper left")
ax0.set_title("311 requests opened and closed per day", fontsize=11)
dn = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ax1 = fig.add_subplot(gs[1, 0])
dw = d.groupby("dow")[["opened", "closed"]].mean()
ax1.bar(np.arange(7) - 0.2, dw["opened"], 0.4, color=DARK_GREEN, label="Opened")
ax1.bar(np.arange(7) + 0.2, dw["closed"], 0.4, color=SALMON, label="Closed")
ax1.set_xticks(range(7))
ax1.set_xticklabels(dn)
ax1.yaxis.set_major_formatter(thousands)
ax1.set_title("Average per day, by day of week", fontsize=11)
ax1.grid(axis="x", visible=False)
ax2 = fig.add_subplot(gs[1, 1])
wk = d.groupby("week")[["opened", "closed"]].mean()
ax2.plot(wk.index, wk["opened"], color=DARK_GREEN, marker="o", ms=3)
ax2.plot(wk.index, wk["closed"], color=SALMON, marker="o", ms=3)
ax2.yaxis.set_major_formatter(thousands)
ax2.set_xlabel("Week of year")
ax2.set_title("Average per day, by week of year", fontsize=11)
weekend_drop = 1 - dw.loc[[5, 6], "opened"].mean() / dw.loc[0:4, "opened"].mean()
fig.suptitle(f"Requests drop {weekend_drop:.0%} on weekends; closings follow openings with a lag",
             x=0.06, ha="left", fontweight="bold", fontsize=13)
save(fig, "q2_openings_closings")

# =============================================================================================
# Q3. COMPLAINT TYPE CONSISTENCY
# =============================================================================================
say("", "## Q3. Complaint type consistency")
say(f"{type_map['complaint_type'].nunique():,} distinct complaint_type spellings collapse to "
    f"{type_map['standard_type'].nunique():,} standardized types.")
variants = (type_map.groupby("standard_type")
            .agg(spellings=("complaint_type", lambda s: " | ".join(sorted(s))), n=("n", "sum"), k=("complaint_type", "size"))
            .query("k > 1").sort_values("n", ascending=False).reset_index())
table(variants[["standard_type", "spellings", "n"]], "Same category, different names (merged by our rules)", 25)
# near-duplicates the rules have NOT merged yet: string similarity between standardized names
std_names = type_map.groupby("standard_type")["n"].sum().sort_values(ascending=False)
names = list(std_names.index[:400])
pairs = []
for i, a in enumerate(names):
    for b in names[i + 1:]:
        r = SequenceMatcher(None, a, b).ratio()
        if r >= 0.85:
            pairs.append((a, b, round(r, 2), int(std_names[a]), int(std_names[b])))
table(pd.DataFrame(pairs, columns=["type_a", "type_b", "similarity", "n_a", "n_b"]).sort_values("similarity", ascending=False),
      "Possible duplicates still to review (similar names)", 25)
rare = type_map[type_map["n"] < 10].sort_values("n")
table(rare[["complaint_type", "agency", "n"]], f"Unusual entries: {len(rare)} types with fewer than 10 requests", 15)
info = type_map[type_map["category"] == "Information / admin request"]
say(f"Non-complaints mixed in: {len(info)} types are information or admin requests (e.g. "
    f"{', '.join(info.sort_values('n', ascending=False)['complaint_type'].head(5))}), "
    f"{info['n'].sum() / type_map['n'].sum():.1%} of all requests.")
say("**Q3b strategy:** keep the raw field untouched and add two columns. (1) `standard_type` = an automatic "
    "normalizer (case, spaces, punctuation) plus a small alias table for known renames (HEATING -> HEAT/HOT "
    "WATER, Derelict Vehicles -> Derelict Vehicle...). (2) `category` = keyword rules (building owner, city "
    "infrastructure, neighbors, nature/weather, information request). Both tables live in code and are written "
    "to `complaint_type_map.csv`. When new data arrives, unseen types are normalized automatically and listed "
    "by the similarity check for a one-line alias decision, so nothing is silently dropped and the "
    "original granularity (`descriptor`) is kept.")

# =============================================================================================
# Q4. RESPONSE TIMES (time to closure)
# =============================================================================================
say("", "## Q4. Time to closure")
st = sql("""SELECT count(*) AS n, avg(days_to_close) AS mean_days, median(days_to_close) AS median_days,
                   stddev(days_to_close) AS sd_days, quantile_cont(days_to_close, 0.25) AS q1,
                   quantile_cont(days_to_close, 0.75) AS q3, quantile_cont(days_to_close, 0.9) AS p90,
                   quantile_cont(days_to_close, 0.99) AS p99, max(days_to_close) AS max_days
            FROM sr WHERE days_to_close IS NOT NULL""").iloc[0]
fence = st["q3"] + 1.5 * (st["q3"] - st["q1"])
n_out = sql(f"SELECT count(*) FROM sr WHERE days_to_close > {fence}").iloc[0, 0]
table(pd.DataFrame([st]).round(2), "Time to closure in days (valid closed dates only)")
say(f"Outliers (above Q3 + 1.5 x IQR = {fence:.1f} days): {n_out:,} requests ({n_out / st['n']:.1%}). "
    f"Mean ({st['mean_days']:.1f}) far above median ({st['median_days']:.1f}): a long right tail, so we use medians.")

# Q4b. areas: compare each community district with what its complaint mix would predict
say("", "### Q4b. Areas with longer than typical response times (mix-adjusted)")
area = sql("""
    WITH bench AS (SELECT standard_type, median(days_to_close) AS type_median FROM sr
                   WHERE days_to_close IS NOT NULL GROUP BY 1)
    SELECT boro, cd, count(*) AS n, median(days_to_close) AS median_days,
           median(days_to_close / NULLIF(type_median, 0)) AS ratio_vs_same_type_citywide
    FROM sr JOIN bench USING (standard_type)
    WHERE days_to_close IS NOT NULL AND cd IS NOT NULL GROUP BY 1, 2 HAVING count(*) >= 200
    ORDER BY ratio_vs_same_type_citywide DESC""")
table(area.head(10).round(2), "Slowest community districts (1.0 = typical for the same complaint types)")
table(area.tail(5).round(2), "Fastest community districts")
boro_t = sql("""WITH bench AS (SELECT standard_type, median(days_to_close) AS tm FROM sr WHERE days_to_close IS NOT NULL GROUP BY 1)
                SELECT boro, count(*) AS n, median(days_to_close) AS median_days,
                       median(days_to_close / NULLIF(tm, 0)) AS ratio_vs_typical
                FROM sr JOIN bench USING (standard_type) WHERE days_to_close IS NOT NULL AND boro IS NOT NULL
                GROUP BY 1 ORDER BY ratio_vs_typical DESC""")
table(boro_t.round(2), "By borough")

# Q4c. agencies: raw vs adjusted for how hard the complaint is
say("", "### Q4c. Agencies: fast because good, or because their complaints are easy?")
samp = sql(f"""SELECT upper(agency) AS agency, category, boro, standard_type, month(created) AS month,
                      dayofweek(created) AS dow, coalesce(open_data_channel_type, 'UNKNOWN') AS channel,
                      ln(1 + 24 * days_to_close) AS log_hours
               FROM sr WHERE days_to_close IS NOT NULL AND boro IS NOT NULL
               USING SAMPLE {min(400_000, int(N))} ROWS""")
top_ag = samp["agency"].value_counts()
samp = samp[samp["agency"].isin(top_ag[top_ag >= 300].index)]
raw_fit = smf.ols("log_hours ~ C(agency)", samp).fit()
adj_fit = smf.ols("log_hours ~ C(agency) + C(category) + C(boro) + C(month) + C(dow) + C(channel)", samp).fit()
base = sorted(samp["agency"].unique())[0]
ag = pd.DataFrame({
    "agency": sorted(samp["agency"].unique()),
}).assign(
    raw_effect=lambda x: [0.0 if a == base else raw_fit.params.get(f"C(agency)[T.{a}]", np.nan) for a in x["agency"]],
    adjusted_effect=lambda x: [0.0 if a == base else adj_fit.params.get(f"C(agency)[T.{a}]", np.nan) for a in x["agency"]])
med = samp.assign(h=np.expm1(samp["log_hours"]) / 24).groupby("agency")["h"].median().rename("median_days")
ag = ag.merge(med, on="agency").merge(top_ag.rename("n_sample"), left_on="agency", right_index=True)
for c in ["raw_effect", "adjusted_effect"]:                 # relative to the average agency, as % time
    ag[c.replace("effect", "vs_avg_%")] = ((np.exp(ag[c] - ag[c].mean()) - 1) * 100).round(0)
ag["rank_raw"] = ag["raw_vs_avg_%"].rank().astype(int)
ag["rank_adjusted"] = ag["adjusted_vs_avg_%"].rank().astype(int)
ag = ag.sort_values("adjusted_vs_avg_%")
table(ag[["agency", "n_sample", "median_days", "raw_vs_avg_%", "adjusted_vs_avg_%", "rank_raw", "rank_adjusted"]].round(2),
      "Agency speed vs the average agency (negative = faster); adjusted = same kind of problem, borough, month, weekday, channel")
say(f"Model fit: R2 agency only {raw_fit.rsquared:.2f}; with difficulty controls {adj_fit.rsquared:.2f} "
    f"(random sample of {len(samp):,} closed requests, log hours to close).")

# =============================================================================================
# Q5. TOP 10 COMPLAINT TYPES (board-ready)
# =============================================================================================
say("", "## Q5. Top 10 complaint types")
top10 = sql("""SELECT standard_type, category, count(*) AS n FROM sr GROUP BY 1, 2 ORDER BY n DESC LIMIT 10""")
top10["share"] = top10["n"] / N
table(top10.round(3), "Top 10 standardized complaint types")
cat_color = {"Building owner / landlord": DARK_RED, "City infrastructure / services": DARK_GREEN,
             "Neighbors / public behavior": GOLD, "Nature / weather": SAGE, "Information / admin request": "#9e9e9e",
             "Other": "#cccccc"}
fig, ax = plt.subplots(figsize=(9, 5.2))
t = top10.iloc[::-1]
ax.barh(t["standard_type"].str.title(), t["n"], color=[cat_color[c] for c in t["category"]], height=0.68)
for y, (v, s) in enumerate(zip(t["n"], t["share"])):
    ax.text(v, y, f"  {v:,.0f}  ({s:.1%})", va="center", fontsize=9)
ax.xaxis.set_major_formatter(thousands)
ax.set_xlim(0, t["n"].max() * 1.25)
ax.grid(axis="y", visible=False)
ax.set_xlabel("Number of 311 requests")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=cat_color[c], label=c) for c in dict.fromkeys(top10["category"])],
          loc="lower right", fontsize=8.5, title="Source of the problem", title_fontsize=8.5)
save(fig, "q5_top10_complaints", f"{top10['standard_type'].iloc[0].title()} is New York's #1 311 complaint",
     f"Top 10 complaint types, {span['first']:%b %Y} - {span['last']:%b %Y} ({top10['share'].sum():.0%} of all requests)", ax)

# =============================================================================================
# Q6. WEATHER: volume and content of complaints vs temperature, rain, snow
# =============================================================================================
say("", "## Q6. Complaints and the weather")
WEATHER = HERE / "nyc_weather_daily.csv"
if not WEATHER.exists():                                    # fetch from Open-Meteo (free historical API)
    import urllib.request
    url = ("https://archive-api.open-meteo.com/v1/archive?latitude=40.7128&longitude=-74.006&start_date=2010-01-01"
           f"&end_date={pd.Timestamp.today() - pd.Timedelta(days=5):%Y-%m-%d}&daily=temperature_2m_max,temperature_2m_min,"
           "temperature_2m_mean,precipitation_sum,snowfall_sum&temperature_unit=fahrenheit&precipitation_unit=inch"
           "&timezone=America%2FNew_York")
    w = pd.DataFrame(json.load(urllib.request.urlopen(url, timeout=60))["daily"])
    w.columns = ["date", "tmax_f", "tmin_f", "tmean_f", "precip_in", "snow_in"]
    w.to_csv(WEATHER, index=False)
weather = pd.read_csv(WEATHER, parse_dates=["date"])
say("Weather: daily Central Park-area observations from the Open-Meteo historical archive (ERA5): "
    "max/min/mean temperature (F), precipitation and snowfall (inches).")
wcat = sql("""SELECT day, category, standard_type, count(*) AS n FROM sr WHERE day IS NOT NULL GROUP BY ALL""")
wcat["day"] = pd.to_datetime(wcat["day"])
dayt = wcat.groupby("day")["n"].sum().rename("total").reset_index()
groups_q6 = {"Heat / hot water": wcat["standard_type"].eq("HEAT/HOT WATER"),
             "Sewer & water": wcat["standard_type"].str.contains("SEWER|WATER SYSTEM|FLOOD|CATCH BASIN", regex=True)
                              & ~wcat["standard_type"].eq("HEAT/HOT WATER"),
             "Snow & ice": wcat["standard_type"].str.contains(r"\bSNOW|\bICE\b", regex=True),
             "Noise": wcat["standard_type"].str.contains("NOISE"),
             "Trees": wcat["standard_type"].str.contains(r"\bTREE", regex=True)}
for g, mask in groups_q6.items():
    dayt = dayt.merge(wcat[mask].groupby("day")["n"].sum().rename(g).reset_index(), on="day", how="left")
dayt = dayt.fillna(0)
before = len(dayt)
dw_ = dayt.merge(weather, left_on="day", right_on="date", how="left", validate="one_to_one")
say(f"Merge daily complaints x weather on date: {before:,} days before, {len(dw_):,} after, "
    f"{dw_['tmean_f'].notna().mean():.1%} matched.")
dw_["dow"], dw_["month"] = dw_["day"].dt.dayofweek, dw_["day"].dt.month
cors = []
for g in ["total"] + list(groups_q6):
    if dw_[g].sum() > 0:
        f_ = smf.ols(f"Q('{g}') ~ tmin_f + precip_in + snow_in + C(dow)", dw_.dropna(subset=["tmin_f"])).fit()
        cors.append({"complaints": g, "per_day": dw_[g].mean(), "corr_min_temp": dw_[g].corr(dw_["tmin_f"]),
                     "corr_precip": dw_[g].corr(dw_["precip_in"]), "corr_snow": dw_[g].corr(dw_["snow_in"]),
                     "per_10F_colder": -10 * f_.params["tmin_f"], "per_inch_rain": f_.params["precip_in"],
                     "per_inch_snow": f_.params["snow_in"]})
cors = pd.DataFrame(cors)
table(cors.round(2), "Daily complaints vs weather (correlations; regression effects holding weekday fixed)")
# Board-ready version: average complaints per day in plain-English weather bands (bars), with the
# multiple of the mildest / driest band written on top. Heat uses the heating season only (Oct-May).
fig, axes = plt.subplots(1, 3, figsize=(13, 4.6), gridspec_kw={"wspace": 0.3})
panels = [("Heat / hot water complaints", "tmin_f", "Overnight low temperature",
           [-30, 10, 20, 30, 40, 50, 100], ["<10F", "10-20F", "20-30F", "30-40F", "40-50F", "50F+"], DARK_RED, True),
          ("Sewer & water complaints", "precip_in", "Rain that day",
           [-1, 0.01, 0.25, 1, 100], ["Dry", "Light\n(<0.25in)", "Moderate\n(0.25-1in)", "Heavy\n(1in+)"], DARK_GREEN, False),
          ("Tree complaints", "precip_in", "Rain that day",
           [-1, 0.01, 0.25, 1, 100], ["Dry", "Light\n(<0.25in)", "Moderate\n(0.25-1in)", "Heavy\n(1in+)"], SAGE, False)]
for ax, (g, x, xl, edges, labels, color, heat_season) in zip(axes, panels):
    sub = dw_.dropna(subset=[x])
    if heat_season:
        sub = sub[sub["month"].isin([10, 11, 12, 1, 2, 3, 4, 5])]
    band = pd.cut(sub[x], edges, labels=labels)
    col = {"Heat / hot water complaints": "Heat / hot water", "Sewer & water complaints": "Sewer & water",
           "Tree complaints": "Trees"}[g]                                       # daily count column for this panel
    b = sub.groupby(band, observed=False)[col].agg(["mean", "size"])
    base = b["mean"].iloc[-1] if heat_season else b["mean"].iloc[0]          # mildest / driest band
    bars = ax.bar(range(len(b)), b["mean"], color=color, width=0.7)
    for i, (v, n) in enumerate(zip(b["mean"], b["size"])):
        if n > 0 and v == v:
            ax.text(i, v, f"{v:,.0f}\n({v / base:.1f}x)" if base else f"{v:,.0f}", ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(range(len(b)))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylim(0, b["mean"].max() * 1.3)
    ax.set_xlabel(xl)
    ax.set_title(g, fontsize=10.5)
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(thousands)
axes[0].set_ylabel("Average complaints per day")
r_heat = cors.set_index("complaints").loc["Heat / hot water", "per_10F_colder"] if "Heat / hot water" in set(cors["complaints"]) else np.nan
fig.suptitle(f"Weather predicts what New Yorkers call about: +{r_heat:,.0f} heat complaints a day for every 10F colder",
             x=0.01, ha="left", fontweight="bold", fontsize=12, y=1.04)
save(fig, "q6_weather", note="weather: Open-Meteo historical archive; (x) = multiple of the mildest / driest days")

# =============================================================================================
# Q7. GEOGRAPHY: concentration and disparities, with 3 insights on the chart
# =============================================================================================
say("", "## Q7. Where complaints come from")
POP = {"BRONX": 1472654, "BROOKLYN": 2736074, "MANHATTAN": 1694251, "QUEENS": 2405464, "STATEN ISLAND": 495747}  # 2020 Census
geo_b = sql("""SELECT boro, count(*) AS n, avg(unresolved::INT) AS share_unresolved, median(days_to_close) AS median_days,
                      avg((category = 'Building owner / landlord')::INT) AS share_housing
               FROM sr WHERE boro IS NOT NULL GROUP BY 1""")
geo_b["per_1000"] = geo_b["n"] / geo_b["boro"].map(POP) * 1000 / max(1, (span["last"] - span["first"]).days / 365.25)
geo_b = geo_b.sort_values("per_1000", ascending=False)
table(geo_b.round(3), "By borough (per 1,000 residents per year, 2020 Census population)")
cdt = sql("""SELECT cd, count(*) AS n, avg((category='Building owner / landlord')::INT) AS share_housing
             FROM sr WHERE cd IS NOT NULL GROUP BY 1 ORDER BY n DESC""")
top_cd_share = cdt["n"].head(10).sum() / cdt["n"].sum()
pts = sql("""SELECT round(lat, 3) AS lat, round(lon, 3) AS lon, count(*) AS n FROM sr WHERE in_nyc GROUP BY 1, 2""")
hi, lo = geo_b.iloc[0], geo_b.iloc[-1]
housing_top = geo_b.sort_values("share_housing", ascending=False).iloc[0]
ins = [f"1. {hi['boro'].title()} files {hi['per_1000'] / lo['per_1000']:.1f}x as many requests per resident as {lo['boro'].title()}",
       f"2. 10 of {len(cdt)} community districts generate {top_cd_share:.0%} of requests",
       f"3. {housing_top['share_housing']:.0%} of {housing_top['boro'].title()} requests are about housing conditions"]
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 6.5), gridspec_kw={"width_ratios": [1.2, 1], "wspace": 0.45})
hb = ax.hexbin(pts["lon"], pts["lat"], C=pts["n"], reduce_C_function=np.sum, gridsize=60,
               norm=matplotlib.colors.LogNorm(),
               cmap=matplotlib.colors.LinearSegmentedColormap.from_list("u", ["#f3f0e2", SAGE, DARK_GREEN, INK]), mincnt=1)
ax.set_aspect(1.3)
ax.axis("off")
cb = fig.colorbar(hb, ax=ax, orientation="horizontal", fraction=0.04, pad=0.02, aspect=35)
cb.ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))   # 10, 100, 1,000 (no math text)
cb.set_label("Requests per hexagon, 2010-2021 (log scale)")
cb.outline.set_visible(False)
ax.set_title("Where requests come from", fontsize=11)
ax2.barh(geo_b["boro"].str.title()[::-1], geo_b["per_1000"][::-1], color=DARK_GREEN, height=0.6)
for y, (v, md) in enumerate(zip(geo_b["per_1000"][::-1], geo_b["median_days"][::-1])):
    ax2.text(v, y, f"  {v:,.0f}  (median {md:.1f} days to close)", va="center", fontsize=8.5)
ax2.set_xlim(0, geo_b["per_1000"].max() * 1.6)
ax2.set_title("Requests per 1,000 residents per year", fontsize=11)
ax2.grid(axis="y", visible=False)
ax2.text(0, -0.16, "Three insights\n" + "\n".join(ins), transform=ax2.transAxes, fontsize=10, color=INK,
         va="top", linespacing=1.5, bbox=dict(boxstyle="round,pad=0.6", facecolor="#f3f0e2", edgecolor="none"))
fig.suptitle("311 demand is uneven: the Bronx files the most per resident, and housing drives it", x=0.01, ha="left",
             fontweight="bold", fontsize=13)
save(fig, "q7_geography", note="population: 2020 Census")
say(*ins)

# =============================================================================================
# Q8. WEB DASHBOARD (zoomable map with complaint details)
# =============================================================================================
say("", "## Q8. Interactive dashboard: lab2_output/q8_dashboard.html")
cells = sql("""SELECT round(lat, 3) AS lat, round(lon, 3) AS lon, boro, any_value(cd) AS district,
                      count(*) AS requests, mode(standard_type) AS top_complaint, mode(category) AS main_source,
                      median(days_to_close) AS median_days_to_close, avg(unresolved::INT) AS share_unresolved
               FROM sr WHERE in_nyc GROUP BY 1, 2, 3 HAVING count(*) >= 3""")
cells["share_unresolved"] = (cells["share_unresolved"] * 100).round(1)
cells["median_days_to_close"] = cells["median_days_to_close"].round(1)
kw = dict(lat="lat", lon="lon", color="main_source", size="requests", size_max=18, zoom=10, opacity=0.6,
          hover_name="top_complaint", color_discrete_map=cat_color, height=750,
          hover_data={"district": True, "requests": True, "median_days_to_close": True, "share_unresolved": True,
                      "lat": False, "lon": False},
          title="NYC 311 requests: zoom in and hover for details (each dot = ~100 m block of the city)")
if hasattr(px, "scatter_map"):
    fig8 = px.scatter_map(cells, **kw, map_style="carto-positron")
else:
    fig8 = px.scatter_mapbox(cells, **kw, mapbox_style="carto-positron")
fig8.write_html(OUT / "q8_dashboard.html", include_plotlyjs="cdn")
say(f"{len(cells):,} map cells; colour = main source of complaints; size = number of requests; hover shows the "
    "top complaint, district, median days to close and % unresolved.")

# =============================================================================================
# Q9. EQUITY: unresolved complaints x area x complaint source (one chart)
# =============================================================================================
say("", "## Q9. Equity in service delivery")
eq = sql("""
    WITH bench AS (SELECT standard_type, median(days_to_close) AS tm FROM sr WHERE days_to_close IS NOT NULL GROUP BY 1)
    SELECT cd, any_value(boro) AS boro, count(*) AS n, sum(unresolved::INT) AS unresolved_n,
           avg(unresolved::INT) AS share_unresolved, median(days_to_close / NULLIF(tm, 0)) AS speed_ratio,
           mode(category) AS main_source, mode(standard_type) AS top_type,
           avg((category = 'Building owner / landlord')::INT) AS share_landlord,
           avg((category = 'City infrastructure / services')::INT) AS share_city,
           avg((category = 'Neighbors / public behavior')::INT) AS share_neighbors,
           avg((category = 'Nature / weather')::INT) AS share_nature
    FROM sr LEFT JOIN bench USING (standard_type) WHERE cd IS NOT NULL GROUP BY 1 HAVING count(*) >= 200""")
table(eq.sort_values("unresolved_n", ascending=False).head(10).round(3), "Districts with the most unresolved requests")
src = sql("""SELECT boro, category, count(*) AS n, avg(unresolved::INT) AS share_unresolved, median(days_to_close) AS median_days
             FROM sr WHERE boro IS NOT NULL GROUP BY 1, 2""")
table(src.pivot(index="category", columns="boro", values="n").fillna(0).astype(int).reset_index(), "Requests by source and borough")
table(src.pivot(index="category", columns="boro", values="median_days").round(1).reset_index(), "Median days to close by source and borough")
# One chart: each bubble = a residential community district (parks/airports with few requests left out)
# x = share of its requests still unresolved, y = speed vs the same complaint types citywide,
# colour = where most of its complaints come from, size = volume.
cdq = eq[eq["n"] >= 0.1 * eq["n"].median()].copy()      # drops parks/airports (tiny counts)
fig, ax = plt.subplots(figsize=(10.5, 6.5))
for cat, g in cdq.groupby("main_source"):
    ax.scatter(g["share_unresolved"] * 100, g["speed_ratio"], s=g["n"] / cdq["n"].max() * 700,
               color=cat_color.get(cat, "#999"), alpha=0.8, edgecolors="white", linewidths=0.6, label=cat)
label_rows = pd.concat([cdq.nlargest(4, "speed_ratio"), cdq.nlargest(3, "share_unresolved")]).drop_duplicates("cd")
for _, r in label_rows.iterrows():
    ax.annotate(r["cd"].title(), (r["share_unresolved"] * 100, r["speed_ratio"]), xytext=(7, 0),
                textcoords="offset points", fontsize=8.5, va="center", fontweight="bold")
ax.axhline(1, color=GREY, linewidth=0.8, linestyle=":")
ax.axvline(cdq["share_unresolved"].median() * 100, color=GREY, linewidth=0.8, linestyle=":")
ax.text(0.99, 0.98, "Slower AND more unresolved", transform=ax.transAxes, ha="right", va="top", color=GREY, style="italic")
ax.set_xlabel("% of the district's requests still unresolved")
ax.set_ylabel("Time to close vs same complaint types citywide (1 = typical)")
leg = ax.legend(title="Main source of complaints (bubble size = volume)", fontsize=8.5, title_fontsize=8.5,
                loc="upper left", bbox_to_anchor=(0, -0.13), ncol=3, markerscale=0.5)
slow1, slow2 = cdq.nlargest(2, "speed_ratio").itertuples()
most_open = cdq.nlargest(1, "share_unresolved").iloc[0]
save(fig, "q9_equity",
     f"{slow1.cd.title()} and {slow2.cd.title()} wait ~{(slow1.speed_ratio - 1) * 100:.0f}% longer for the same complaints; "
     f"{most_open['cd'].title()} leaves the most unresolved",
     f"{len(cdq)} community districts; dotted lines = citywide typical speed and median unresolved share", ax)

# =============================================================================================
# Q10. FEATURES FOR PREDICTING VOLUME, and their link to response times
# =============================================================================================
say("", "## Q10. Predicting complaint volume")
dv = dw_.copy()
dv["week"] = dv["day"].dt.isocalendar().week.astype(int)
dv["lag7"] = dv["total"].shift(7)
dv["holiday"] = dv["day"].dt.strftime("%m-%d").isin(["01-01", "07-04", "12-25", "11-11", "05-30", "09-01"])
dv = dv.dropna(subset=["tmin_f", "lag7"])
feat_sets = {"Day of week": "C(dow)", "Month": "C(month)", "Weather": "tmin_f + precip_in + snow_in",
             "Last week's volume": "lag7"}
rows = []
for name, f_ in feat_sets.items():
    if len(dv) > 30:
        rows.append({"feature": name, "R2_alone": smf.ols(f"total ~ {f_}", dv).fit().rsquared})
allf = smf.ols("total ~ " + " + ".join(feat_sets.values()), dv).fit() if len(dv) > 30 else None
r2t = pd.DataFrame(rows)
table(r2t.round(3), "How much of daily volume each feature explains")
if allf is not None:
    say(f"All together: R2 = {allf.rsquared:.3f} on {len(dv):,} days.")
rt = sql("""SELECT day, median(days_to_close) AS median_days, count(*) AS n FROM sr
            WHERE days_to_close IS NOT NULL GROUP BY 1""")
rt["day"] = pd.to_datetime(rt["day"])
rv = rt.merge(dv[["day", "total", "tmin_f", "precip_in", "snow_in", "dow", "month"]], on="day", how="inner")
corr_rt = rv[["median_days", "total", "tmin_f", "precip_in", "snow_in", "dow", "month"]].corr()["median_days"].drop("median_days")
table(corr_rt.round(3).rename("corr_with_median_days_to_close").reset_index(), "Are these features related to response times? (daily)")
fit_rt = smf.ols("median_days ~ total + tmin_f + precip_in + snow_in + C(dow) + C(month)", rv).fit(cov_type="HC1") if len(rv) > 30 else None
if fit_rt is not None:
    say(f"Regression of daily median days-to-close on volume, weather, weekday, month: R2 = {fit_rt.rsquared:.2f}; "
        f"+1,000 requests that day -> {fit_rt.params['total'] * 1000:+.2f} days (SE {fit_rt.bse['total'] * 1000:.2f}).")
say("Most valuable features: day of week and season (strong, regular cycles), weather (cold drives heat complaints, "
    "rain drives sewer/flooding, snow drives snow complaints), last week's volume (persistence), holidays, and "
    "borough / complaint category for area-level forecasts.")

# =============================================================================================
# Q11. EXECUTIVE SUMMARY (numbers filled in from the results above)
# =============================================================================================
say("", "## Q11. Executive summary for the Mayor (5 minutes)")
top_slow = area.iloc[0] if len(area) else None
best_ag, worst_ag = ag.iloc[0], ag.iloc[-1]
say("**Three critical findings**",
    f"1. The data needs fixing before it drives budgets: {miss.iloc[0]['column']} and other key fields are mostly "
    f"missing or disguised as 'Unspecified'; {other['created_exactly_midnight'].iloc[0] / n_raw:.0%} of requests carry "
    f"no real time of day; {type_map['complaint_type'].nunique()} complaint spellings collapse to "
    f"{type_map['standard_type'].nunique()} real types.",
    f"2. Demand is concentrated and seasonal: {top10['standard_type'].iloc[0].title()} alone is {top10['share'].iloc[0]:.0%} "
    f"of requests, and cold weather adds about {r_heat:,.0f} heat complaints a day per 10F drop.",
    f"3. Speed is uneven: requests take a median {st['median_days']:.1f} days but a mean {st['mean_days']:.1f}; "
    + (f"{top_slow['cd'].title()} waits {top_slow['ratio_vs_same_type_citywide']:.1f}x as long as typical for the same "
       f"complaint types; " if top_slow is not None else "")
    + f"{best_ag['agency']} is fastest and {worst_ag['agency']} slowest even after adjusting for complaint difficulty.",
    "**Two immediate actions**",
    "1. Standardize the data now: adopt the complaint-type map and required borough/ZIP/time fields at intake.",
    "2. Pre-position HPD heat inspectors and DEP sewer crews using the weather forecast (cold snaps, storms).",
    "**One long-term recommendation**",
    "Publish a mix-adjusted response-time scorecard by community district and agency (the dashboard in Q8), "
    "and fund the slowest districts to the citywide standard.")

(OUT / "results.md").write_text("\n".join(REPORT), encoding="utf-8")
import shutil                                               # one zip with everything for submission
for nb in [HERE / "MGT634_Lab2_NYC311_v3.ipynb", HERE / "lab2_nyc311.py"]:
    if nb.exists():
        shutil.copy(nb, OUT / nb.name)
shutil.make_archive(str(HERE / "MGT634_Lab2_NYC311_team"), "zip", OUT)
print("Submission zip:", HERE / "MGT634_Lab2_NYC311_team.zip")
print(f"\nDone in {time.time() - t0:.0f}s. Results: {OUT / 'results.md'} | charts: {FIG} | dashboard: {OUT / 'q8_dashboard.html'}")
