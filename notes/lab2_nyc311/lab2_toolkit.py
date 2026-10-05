# %% [markdown]
# # MGT 634 Lab Day 2: NYC 311 review (heat complaints and the OSC Monitoring Tool)
# Team: Michal Kozuchowski, Laila Lapins, Nick Giamalis, Raymond Chang, Sean Weller
#
# **What this notebook does, in order**
# 1. Setup: packages, find the 311 files, read how many cores / how much memory this session has.
# 2. Recon: how many files, how big, what years, are the columns the same in every file?
# 3. Convert once: DuckDB reads the ~3,000 JSON files in groups and writes a compact Parquet copy
#    (only the columns we need, with proper types). The raw JSON files are never changed.
# 4. Clean view `sr`: one row per service request, with clean dates, borough, ZIP, heat flags.
# 5. Analysis blocks: (A) replicate the OSC report's numbers, (B) heat-complaint deep dive for the
#    Mayor's "investigate every heat complaint" pledge, (C) time to close, (D) charts.
# 6. Helpers for new material handed out in class: profile any file, merge with a size report,
#    run any SQL in one line.
#
# **Why DuckDB + Parquet (Class 7):** the full data needs 64 GB+ in pandas. DuckDB streams the
# files from disk, uses all cores, and spills to disk instead of crashing; Parquet makes every
# later query take seconds. Only small summary tables are brought into pandas.

# %% Setup: packages, settings, file locations
import glob
import json
import os
import re
import shutil
import site
import subprocess
import sys
import time
from pathlib import Path


def need(package, pip_name=None):
    """Import a package; if missing, install it for this user (the cluster has no uv)."""
    try:
        return __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "-q", pip_name or package])
        sys.path.insert(0, site.getusersitepackages())      # make the fresh install visible
        return __import__(package)


for pkg in ["duckdb", "pyarrow"]:
    need(pkg)

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_colwidth", 120)

# ---- Which files? Search the usual course folders for the 311 batch files ----
SEARCH = ["~/esai_2026/data/*311*/", "~/esai_2026/data/*/", "~/esai_2026/data/*/*/", "~/esai_2026/class/*/",
          "~/esai_2026/class/*/*/", "/gpfs/project/esai_2026/data/*/", "/gpfs/project/esai_2026/data/*/*/",
          "~/", "~/Downloads/"]
DATA = None
for pattern in SEARCH:
    for folder in sorted(glob.glob(os.path.expanduser(pattern))):
        if glob.glob(os.path.join(folder, "311_batch_*.json")):
            DATA = Path(folder)
            break
    if DATA:
        break
# DATA = Path("~/esai_2026/data/NYC311").expanduser()     # <- or set the folder by hand here
assert DATA, "No 311_batch_*.json found: run print(os.listdir(os.path.expanduser('~/esai_2026/data')))"
FILES = sorted(glob.glob(str(DATA / "311_batch_*.json")))
print(f"Data folder: {DATA}  ({len(FILES):,} batch files)")

# ---- Production run or quick sample? ----
# STRIDE = 1 uses every file (big 4-core / 32 GB session). Teammates on small sessions set
# STRIDE = 30: every 30th file, spread evenly over all years (files are in time order), so
# results are a ~3% sample; multiply counts by STRIDE for rough full-data totals.
STRIDE = 1
FILES = FILES[::STRIDE]
if STRIDE > 1:
    print(f"QUICK SAMPLE MODE: {len(FILES)} files (every {STRIDE}th); counts are ~1/{STRIDE} of the real totals")

# ---- Where our own outputs go (home folder; the course folder is read-only) ----
WORK = Path(f"~/lab2_cache{'' if STRIDE == 1 else f'_sample{STRIDE}'}").expanduser()   # separate cache per mode
PARTS = WORK / "parts"                                     # Parquet copy, one part per group of files
FIG = Path("~/lab2_output/figures").expanduser()
for p in [WORK, PARTS, FIG, WORK / "duck_tmp"]:
    p.mkdir(parents=True, exist_ok=True)


# ---- How much computer do we have? (Slurm / OnDemand limits first, then the machine itself) ----
def cores_available():
    for var in ["SLURM_CPUS_PER_TASK", "SLURM_CPUS_ON_NODE"]:
        if os.environ.get(var, "").isdigit():
            return int(os.environ[var])
    try:
        return len(os.sched_getaffinity(0))                # cores this process may use (Linux)
    except AttributeError:
        return os.cpu_count() or 1


def memory_available_gb():
    if os.environ.get("SLURM_MEM_PER_NODE", "").isdigit():
        return int(os.environ["SLURM_MEM_PER_NODE"]) / 1024
    for f in ["/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"]:
        try:
            v = open(f).read().strip()
            if v.isdigit() and int(v) < 1 << 50:
                return int(v) / 1024 ** 3
        except OSError:
            pass
    try:
        return int(re.search(r"MemTotal:\s+(\d+)", open("/proc/meminfo").read()).group(1)) / 1024 ** 2
    except OSError:
        return 8.0                                         # unknown (e.g. Windows): be careful


CORES, MEM_GB = cores_available(), memory_available_gb()
free_gb = shutil.disk_usage(WORK).free / 1024 ** 3
print(f"Cores: {CORES} | memory: {MEM_GB:.0f} GB | free disk in home: {free_gb:.0f} GB")

# DuckDB: use all cores, at most ~60% of memory, spill to disk instead of crashing
con = duckdb.connect()
con.execute(f"SET threads = {CORES}")
con.execute(f"SET memory_limit = '{max(1, int(MEM_GB * 0.6))}GB'")
con.execute(f"SET temp_directory = '{(WORK / 'duck_tmp').as_posix()}'")
con.execute("SET preserve_insertion_order = false")       # lets big COPY jobs stream with less memory


def sql(q):
    """Run DuckDB SQL and return a pandas table."""
    return con.sql(q).df()


def show(q, n=30):
    """Run SQL and print up to n rows as a plain-text table."""
    print(sql(q).head(n).to_string(index=False))


# ---- Chart style: Upshot look (same as HW2) ----
DARK_GREEN, SAGE, CREAM, SALMON, DARK_RED = "#636e4f", "#a3ae8d", "#fbebb7", "#d1725c", "#993f2a"
INK, GREY, LIGHT = "#121212", "#737373", "#eeeeee"
import logging
from matplotlib import font_manager
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # no "font not found" spam
for f in glob.glob(os.path.expanduser("~/fonts/LibreFranklin-*.ttf")):  # Upshot font, if uploaded
    font_manager.fontManager.addfont(f)
HAS_FRANKLIN = any(f.name == "Libre Franklin" for f in font_manager.fontManager.ttflist)
plt.rcParams.update({
    "font.family": "Libre Franklin" if HAS_FRANKLIN else "DejaVu Sans", "font.size": 9.5, "axes.titlesize": 12,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.edgecolor": "#999999",
    "axes.labelcolor": "#666666", "axes.grid": True, "axes.axisbelow": True, "grid.color": LIGHT,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "xtick.color": "#666666", "ytick.color": "#666666", "ytick.left": False, "legend.frameon": False,
    "axes.prop_cycle": matplotlib.cycler(color=[DARK_GREEN, SALMON, SAGE, DARK_RED, "#c9a227"]),
    "savefig.dpi": 200, "savefig.bbox": "tight", "figure.facecolor": "white",
})
if "text.parse_math" in plt.rcParams:
    plt.rcParams["text.parse_math"] = False                # "$" is a dollar sign, not math


def finish(fig, ax, name, title, subtitle=None, note=None):
    """Finding as the title, grey subtitle, source line under everything, save PNG, show."""
    ax.set_title(title, pad=22 if subtitle else 8)
    if subtitle:
        ax.text(0, 1.015, subtitle, transform=ax.transAxes, color=GREY, fontsize=9, va="bottom")
    r = fig.canvas.get_renderer()
    bottom = min(a.get_tightbbox(r).transformed(fig.transFigure.inverted()).y0 for a in fig.axes)
    fig.text(0.01, bottom - 0.015, "Source: NYC 311 service requests (NYC Open Data)." + (" " + note if note else ""),
             color=GREY, fontsize=7.5, va="top")
    fig.savefig(FIG / f"{name}.png")
    if "agg" not in matplotlib.get_backend().lower():
        plt.show()
    plt.close(fig)


thousands = FuncFormatter(lambda x, _: f"{x:,.0f}")

# %% [markdown]
# ## 1. Recon: what did the city send us?
# Files are named by batch number. In the sample, batch 0001 holds the lowest request ids
# (mostly 2010), so the batch number roughly tracks time. We check that on a spread of files,
# and check that the columns are the same everywhere (records leave out fields they don't have).

# %% 1. Recon
sizes = [os.path.getsize(f) for f in FILES]
print(f"{len(FILES):,} files, {sum(sizes) / 1024 ** 3:.1f} GB on disk, "
      f"{min(sizes) / 1e6:.1f}-{max(sizes) / 1e6:.1f} MB each")
numbers = sorted(int(re.search(r"(\d+)$", Path(f).stem).group(1)) for f in FILES)   # last number in the name
missing_numbers = sorted(set(range(numbers[0], numbers[-1] + 1)) - set(numbers))
print(f"Batch numbers {numbers[0]}-{numbers[-1]}; missing numbers: {missing_numbers[:20]}"
      f"{' ...' if len(missing_numbers) > 20 else ''}")

spread = sorted(set(FILES[int(i)] for i in np.linspace(0, len(FILES) - 1, min(9, len(FILES)))))
keys_seen, recon = {}, []
for f in spread:
    try:
        with open(f) as fh:
            records = json.load(fh)
    except ValueError:                                     # broken file: note it and move on
        recon.append({"file": Path(f).name, "rows": "UNREADABLE"})
        continue
    for r in records:
        for k in r:
            keys_seen[k] = keys_seen.get(k, 0) + 1
    created = pd.to_datetime(pd.Series([r.get("created_date") for r in records]), errors="coerce")
    recon.append({"file": Path(f).name, "rows": len(records), "first_created": created.min(),
                  "last_created": created.max(), "median_created": created.median()})
print(pd.DataFrame(recon).to_string(index=False))
print(f"\nFields seen in these files ({len(keys_seen)}):", ", ".join(sorted(keys_seen)))

# %% [markdown]
# ## 2. Convert once: JSON files -> compact Parquet copy (resumable)
# * Groups of `GROUP` files are read by DuckDB in parallel and written as one Parquet part.
# * If the cell is interrupted, re-running it skips parts that are already done.
# * All fields are read as text first (safest), then converted with TRY_CAST: a bad value
#   becomes empty (NULL) instead of stopping the job, and we count those afterwards.
# * Dropped: the nested `location` (duplicate of latitude/longitude) and taxi/bridge fields that
#   are >98% empty. Add any field to KEEP if a question needs it.

# %% 2. Convert
KEEP = ["unique_key", "created_date", "closed_date", "due_date", "resolution_action_updated_date",
        "agency", "agency_name", "complaint_type", "descriptor", "location_type", "incident_zip",
        "incident_address", "street_name", "address_type", "city", "status", "resolution_description",
        "community_board", "bbl", "borough", "open_data_channel_type", "latitude", "longitude",
        "facility_type", "park_borough"]
KEEP += [k for k in keys_seen if k not in KEEP and k != "location"     # new fields: keep them too
         and k not in ["taxi_pick_up_location", "taxi_company_borough", "bridge_highway_name",
                       "bridge_highway_direction", "road_ramp", "bridge_highway_segment", "vehicle_type",
                       "landmark", "intersection_street_1", "intersection_street_2", "cross_street_1",
                       "cross_street_2", "x_coordinate_state_plane", "y_coordinate_state_plane"]]
columns_spec = "{" + ", ".join(f"'{k}': 'VARCHAR'" for k in KEEP) + "}"
TS = lambda c: f"TRY_CAST({c} AS TIMESTAMP)"
select = f"""
    TRY_CAST(unique_key AS BIGINT) AS unique_key,
    {TS('created_date')} AS created, {TS('closed_date')} AS closed, {TS('due_date')} AS due,
    {TS('resolution_action_updated_date')} AS resolution_updated,
    TRY_CAST(latitude AS DOUBLE) AS latitude, TRY_CAST(longitude AS DOUBLE) AS longitude,
    TRY_CAST(regexp_extract(filename, '(\\d+)\\.json$', 1) AS INTEGER) AS batch,
    {", ".join(k for k in KEEP if k not in ["unique_key", "created_date", "closed_date", "due_date",
               "resolution_action_updated_date", "latitude", "longitude"])}"""

GROUP = 50 if MEM_GB >= 16 else 10                         # files per Parquet part (fewer if memory is small)
groups = [FILES[i:i + GROUP] for i in range(0, len(FILES), GROUP)]
start, bad_files = time.time(), []
for gi, group in enumerate(groups):
    out = PARTS / f"part_{gi:04d}.parquet"
    if out.exists():
        continue                                             # already converted (resume)
    file_list = "[" + ", ".join(f"'{Path(f).as_posix()}'" for f in group) + "]"
    try:
        con.execute(f"""COPY (SELECT {select} FROM read_json({file_list}, format = 'array',
                        columns = {columns_spec}, filename = true, maximum_object_size = 104857600))
                        TO '{out.as_posix()}' (FORMAT parquet, COMPRESSION zstd)""")
    except Exception as e:                                   # one bad file: find it, skip it, log it
        print(f"  group {gi} failed ({type(e).__name__}); retrying file by file")
        good = []
        for f in group:
            try:
                con.execute(f"SELECT count(*) FROM read_json('{Path(f).as_posix()}', format='array', columns={columns_spec})")
                good.append(f)
            except Exception:
                bad_files.append(f)
        if good:
            file_list = "[" + ", ".join(f"'{Path(f).as_posix()}'" for f in good) + "]"
            con.execute(f"""COPY (SELECT {select} FROM read_json({file_list}, format = 'array',
                            columns = {columns_spec}, filename = true, maximum_object_size = 104857600))
                            TO '{out.as_posix()}' (FORMAT parquet, COMPRESSION zstd)""")
    done, elapsed = gi + 1, time.time() - start
    if done % 5 == 0 or done == len(groups):
        print(f"  {done}/{len(groups)} parts done ({elapsed:.0f}s so far)")
print("Unreadable files:", [Path(f).name for f in bad_files] or "none")

PQ = (PARTS / "*.parquet").as_posix()
con.execute(f"CREATE OR REPLACE VIEW raw AS SELECT * FROM read_parquet('{PQ}')")
size_gb = sum(p.stat().st_size for p in PARTS.glob("*.parquet")) / 1024 ** 3
print(f"Parquet copy: {len(list(PARTS.glob('*.parquet')))} parts, {size_gb:.2f} GB")


# %% [markdown]
# ## 3. Clean view `sr`: one row per service request
# Cleaning decisions (each one is counted in the check table below):
# * **Duplicate request ids** (same `unique_key` in two files): keep one copy.
# * **Borough**: "Unspecified" for many requests (62% in the sample), so fill it from the building
#   id (`bbl`: first digit 1 = Manhattan, 2 = Bronx, 3 = Brooklyn, 4 = Queens, 5 = Staten Island),
#   then from the ZIP code.
# * **ZIP**: keep the first 5 digits (some are 9-digit); valid NYC ZIPs start with 100-104
#   (Manhattan, Staten Island, Bronx) or 110-114, 116 (Queens, Brooklyn).
# * **Closed date**: not trusted if missing, before the request was opened, before 2003 (311
#   started in March 2003; the data has 1900-01-01 placeholders) or in the future.
# * **Time of day**: many requests carry only a date (stamped exactly midnight), so response
#   times are measured in days, and hour-of-day results use only requests with a real time.
# * **Heat**: the label changed over time ("HEATING" in older years, "HEAT/HOT WATER" later), so
#   both count as residential heat. "Non-Residential Heat" is kept separate.
# * **Heat season**: Oct 1 - May 31 (the legal heat season); season "2024-25" = Oct 2024 - May 2025.

# %% 3. Clean view
dupes = sql("SELECT count(*) - count(DISTINCT unique_key) AS n FROM raw").iloc[0, 0]
print(f"Duplicate request ids across files: {dupes:,}")
dedupe = ("QUALIFY row_number() OVER (PARTITION BY unique_key ORDER BY batch DESC) = 1"   # latest copy wins
          if dupes else "")
SR_PQ = WORK / "sr_clean.parquet"
REBUILD = False                                   # set True after changing the cleaning rules below
clean_sql = f"""
WITH one AS (
    SELECT * FROM raw {dedupe}
), b AS (
    SELECT *,
        regexp_extract(incident_zip, '^(\\d{5})', 1)                                   AS zip5,
        CASE WHEN upper(borough) IN ('MANHATTAN','BRONX','BROOKLYN','QUEENS','STATEN ISLAND') THEN upper(borough)
             WHEN left(bbl, 1) = '1' THEN 'MANHATTAN' WHEN left(bbl, 1) = '2' THEN 'BRONX'
             WHEN left(bbl, 1) = '3' THEN 'BROOKLYN'  WHEN left(bbl, 1) = '4' THEN 'QUEENS'
             WHEN left(bbl, 1) = '5' THEN 'STATEN ISLAND' END                           AS boro_from_bbl
    FROM one
)
SELECT *,
    zip5 SIMILAR TO '(10[0-4]|11[0-4]|116)[0-9]{2}'                                   AS nyc_zip,
    coalesce(boro_from_bbl,
             CASE WHEN left(zip5, 3) IN ('100','101','102') THEN 'MANHATTAN' WHEN left(zip5, 3) = '103' THEN 'STATEN ISLAND'
                  WHEN left(zip5, 3) = '104' THEN 'BRONX' WHEN left(zip5, 3) = '112' THEN 'BROOKLYN'
                  WHEN left(zip5, 3) IN ('110','111','113','114','116') THEN 'QUEENS' END)    AS boro,
    year(created) AS year, month(created) AS month, CAST(created AS DATE) AS day,
    created = date_trunc('day', created)                                               AS date_only,
    (closed IS NOT NULL AND closed >= created AND year(closed) >= 2003
         AND closed <= current_timestamp)                                               AS closed_ok,
    CASE WHEN closed IS NOT NULL AND closed >= created AND year(closed) >= 2003 AND closed <= current_timestamp
         THEN date_diff('second', created, closed) / 86400.0 END                       AS days_to_close,
    upper(complaint_type) IN ('HEATING', 'HEAT/HOT WATER')                             AS heat,
    CASE WHEN month(created) >= 10 THEN year(created)::VARCHAR || '-' || right((year(created) + 1)::VARCHAR, 2)
         WHEN month(created) <= 5 THEN (year(created) - 1)::VARCHAR || '-' || right(year(created)::VARCHAR, 2)
    END                                                                                AS heat_season
FROM b
"""
# Save the clean table once (seconds to query afterwards); re-running the cell reuses it
if REBUILD or not SR_PQ.exists():
    t0 = time.time()
    con.execute(f"COPY ({clean_sql}) TO '{SR_PQ.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")
    print(f"Clean table saved in {time.time() - t0:.0f}s")
con.execute(f"CREATE OR REPLACE VIEW sr AS SELECT * FROM read_parquet('{SR_PQ.as_posix()}')")

checks = sql("""
    SELECT count(*) AS requests,
           sum((created IS NULL)::INT)                AS no_created_date,
           sum((NOT closed_ok AND closed IS NOT NULL)::INT) AS bad_closed_date,
           sum((closed IS NULL)::INT)                 AS not_closed,
           sum(date_only::INT)                        AS date_only_timestamp,
           sum((zip5 = '' OR zip5 IS NULL)::INT)      AS no_zip,
           sum((zip5 <> '' AND NOT nyc_zip)::INT)     AS non_nyc_zip,
           sum((upper(borough) NOT IN ('MANHATTAN','BRONX','BROOKLYN','QUEENS','STATEN ISLAND')
                OR borough IS NULL)::INT)             AS borough_unspecified,
           sum((boro IS NULL)::INT)                   AS borough_still_unknown,
           sum(heat::INT)                             AS heat_requests,
           min(created) AS first_created, max(created) AS last_created
    FROM sr""")
print(checks.T.rename(columns={0: "value"}).to_string())
print("\nRequests by year:")
show("SELECT year, count(*) AS requests, sum(heat::INT) AS heat FROM sr GROUP BY 1 ORDER BY 1", 40)

# %% [markdown]
# ## A. Check our pipeline against the OSC report (its Appendix B, 2019 / 2023 / 2024)
# If our counts match, the city can trust our numbers. If not, the gap is itself a finding (OSC
# notes the city revises the dataset and OSC dropped retired complaint types).

# %% A. OSC replication
OSC = pd.DataFrame([
    ("NYPD", "ILLEGAL PARKING", 198346, 476809, 505733), ("NYPD", "NOISE - RESIDENTIAL", 232848, 298453, 379297),
    ("HPD", "HEAT/HOT WATER", 212565, 231323, 264746), ("NYPD", "BLOCKED DRIVEWAY", 137736, 166430, 170192),
    ("NYPD", "NOISE - STREET/SIDEWALK", 97913, 147449, 163002), ("HPD", "UNSANITARY CONDITION", 63225, 116703, 120903),
    ("DOT", "STREET CONDITION", 88460, 64962, 72485), ("NYPD", "ABANDONED VEHICLE", 24179, 64946, 70326),
    ("NYPD", "NOISE - COMMERCIAL", 40493, 67749, 68346), ("HPD", "PLUMBING", 36016, 62871, 65933),
    ("ALL", "TOTAL", 2157336, 3199600, 3428573)], columns=["agency", "type", "osc_2019", "osc_2023", "osc_2024"])
ours = sql("""SELECT upper(agency) AS agency, upper(complaint_type) AS type, year, count(*) AS n
              FROM sr WHERE year IN (2019, 2023, 2024) GROUP BY ALL""")
ours = pd.concat([ours, ours.groupby("year", as_index=False)["n"].sum().assign(agency="ALL", type="TOTAL")])
wide = ours.pivot_table(index=["agency", "type"], columns="year", values="n", aggfunc="sum").add_prefix("ours_")
rep = OSC.merge(wide.reset_index(), on=["agency", "type"], how="left", validate="one_to_one")
for y in [2019, 2023, 2024]:
    if f"ours_{y}" in rep:
        rep[f"diff_{y}_%"] = ((rep[f"ours_{y}"] / rep[f"osc_{y}"] - 1) * 100).round(1)
print(rep.to_string(index=False))

# %% [markdown]
# ## B. Heat complaints and the pledge to "investigate every single heat complaint"
# B1 volume by season, B2 what actually happened to each complaint (from the resolution text),
# B3 repeat complaints from the same building, B4 peak days and inspector needs, B5 since Oct 1 2026.

# %% B1. Heat volume by season, and the label change
show("""SELECT coalesce(heat_season, 'Jun-Sep (off season)') AS heat_season, upper(complaint_type) AS label,
               count(*) AS complaints
        FROM sr WHERE heat GROUP BY ALL ORDER BY 1, 2""", 60)

# %% B2. Outcome of each heat complaint, read from the resolution text
# Order matters: the first matching rule wins ("not able to gain access ... to inspect" must be
# read as no access, not as an inspection). Edit the patterns here if new wording shows up;
# the cell prints the most common unmatched texts so we can extend the list in seconds.
OUTCOME_RULES = [
    ("Still open", "status IS NULL OR upper(status) NOT IN ('CLOSED')"),
    ("No access", "resolution_description ILIKE '%not able to gain access%' OR resolution_description ILIKE '%unable to gain access%' OR resolution_description ILIKE '%no access%'"),
    ("Restored per tenant", "resolution_description ILIKE '%advised by a tenant%' OR resolution_description ILIKE '%had been restored%'"),
    ("Corrected per phone/occupant", "resolution_description ILIKE '%contacted an occupant%' OR resolution_description ILIKE '%verified that the following conditions were corrected%' OR resolution_description ILIKE '%contacted a tenant%'"),
    ("Inspected: no violation", "resolution_description ILIKE '%no violations were issued%' OR resolution_description ILIKE '%no violation%'"),
    ("Inspected: violation issued", "resolution_description ILIKE '%violation%issued%' OR resolution_description ILIKE '%issued%violation%'"),
    ("Inspected: other", "resolution_description ILIKE '%inspect%' OR resolution_description ILIKE '%observed%'"),
    ("Duplicate / referred", "resolution_description ILIKE '%duplicate%' OR resolution_description ILIKE '%referred%'"),
]


def outcome_case(rules=None):
    rules = rules or OUTCOME_RULES
    return "CASE " + " ".join(f"WHEN {cond} THEN '{name}'" for name, cond in rules) + " ELSE 'Other / unclear' END"


con.execute(f"""CREATE OR REPLACE VIEW heat AS
                SELECT *, {outcome_case()} AS outcome,
                       resolution_description ILIKE '%more than one complaint%' AS multi_complaint_note,
                       outcome LIKE 'Inspected%' AS inspected
                FROM sr WHERE heat""")
mix = sql("""SELECT heat_season, outcome, count(*) AS n FROM heat WHERE heat_season IS NOT NULL GROUP BY ALL""")
mix_wide = mix.pivot_table(index="heat_season", columns="outcome", values="n", aggfunc="sum", fill_value=0)
mix_share = (mix_wide.div(mix_wide.sum(axis=1), axis=0) * 100).round(1)
print("Outcome mix of heat complaints by season (% of complaints):")
print(mix_share.to_string())
print("\nMost common texts not matched by any rule (extend OUTCOME_RULES if these matter):")
show("""SELECT left(resolution_description, 160) AS text, count(*) AS n FROM heat
        WHERE outcome = 'Other / unclear' GROUP BY 1 ORDER BY n DESC""", 10)

# %% B3. Repeat complaints: how many buildings are behind the complaints?
repeat = sql("""
    WITH per_bldg AS (SELECT heat_season, bbl, count(*) AS n FROM heat
                      WHERE heat_season IS NOT NULL AND bbl IS NOT NULL AND bbl NOT IN ('', '0') GROUP BY 1, 2),
         ranked AS (SELECT *, percent_rank() OVER (PARTITION BY heat_season ORDER BY n DESC) AS pr FROM per_bldg)
    SELECT heat_season, sum(n) AS complaints_with_bbl, count(*) AS buildings,
           sum(n) / count(*) AS complaints_per_building,
           sum(CASE WHEN n >= 5 THEN n ELSE 0 END) / sum(n) AS share_from_5plus_buildings,
           sum(CASE WHEN pr <= 0.01 THEN n ELSE 0 END) / sum(n) AS share_from_top1pct_buildings
    FROM ranked GROUP BY 1 ORDER BY 1""")
print(repeat.round(3).to_string(index=False))
same_day = sql("""SELECT heat_season, count(*) AS complaints, count(DISTINCT (bbl, day)) AS building_days
                  FROM heat WHERE heat_season IS NOT NULL AND bbl IS NOT NULL AND bbl <> '' GROUP BY 1 ORDER BY 1""")
same_day["complaints_per_building_day"] = (same_day["complaints"] / same_day["building_days"]).round(2)
print(same_day.to_string(index=False))

# %% B4. Peak days and how many inspectors "every complaint" needs
# One visit covers a building-wide heat outage, so the workload is unique building-days, not
# raw complaints. INSPECTIONS_PER_DAY is an assumption: change it to the city's number.
INSPECTIONS_PER_DAY = 8
peaks = sql("""
    WITH d AS (SELECT heat_season, day, count(*) AS complaints, count(DISTINCT bbl) AS buildings
               FROM heat WHERE heat_season IS NOT NULL GROUP BY 1, 2)
    SELECT heat_season, avg(complaints) AS avg_per_day, quantile_cont(complaints, 0.95) AS p95_day,
           max(complaints) AS peak_day, arg_max(day, complaints) AS peak_date,
           avg(buildings) AS avg_buildings_per_day, max(buildings) AS peak_buildings
    FROM d GROUP BY 1 ORDER BY 1""")
peaks["inspectors_avg_day"] = np.ceil(peaks["avg_buildings_per_day"] / INSPECTIONS_PER_DAY)
peaks["inspectors_peak_day"] = np.ceil(peaks["peak_buildings"] / INSPECTIONS_PER_DAY)
print(peaks.round(1).to_string(index=False))

# %% B5. Since October 1, 2026: is every heat complaint being investigated?
last = sql("SELECT max(created) FROM sr").iloc[0, 0]
print(f"Data runs to: {last}")
if pd.Timestamp(last) >= pd.Timestamp("2026-10-01"):
    window_days = (pd.Timestamp(last).normalize() - pd.Timestamp("2026-10-01")).days + 1
    cmp_ = sql(f"""
        SELECT year, count(*) AS complaints, avg(inspected::INT) AS share_inspected,
               avg((outcome = 'No access')::INT) AS share_no_access, avg((outcome = 'Still open')::INT) AS share_open,
               median(days_to_close) AS median_days_to_close
        FROM heat WHERE month = 10 AND day(created) <= {window_days} GROUP BY 1 ORDER BY 1""")
    print(f"First {window_days} days of October, each year:")
    print(cmp_.round(3).to_string(index=False))
else:
    print("No data after Oct 1, 2026 yet: report the pre-pledge baseline and the metric to monitor.")

# %% [markdown]
# ## C. Time to close (days), by agency and for heat by borough
# Only requests with a trustworthy closed date (see section 3). Medians, because a few requests
# stay open for years and would distort an average.

# %% C. Time to close
show("""SELECT upper(agency) AS agency, count(*) AS closed_requests, median(days_to_close) AS median_days,
               quantile_cont(days_to_close, 0.9) AS p90_days
        FROM sr WHERE closed_ok GROUP BY 1 ORDER BY closed_requests DESC""", 15)
show("""SELECT heat_season, boro, count(*) AS n, median(days_to_close) AS median_days, avg(inspected::INT) AS share_inspected
        FROM heat WHERE closed_ok AND boro IS NOT NULL AND heat_season >= '2019' GROUP BY ALL ORDER BY 1, 2""", 60)

# %% [markdown]
# ## D. Charts (Upshot style). Each saves a PNG in ~/lab2_output/figures.

# %% D1. Heat complaints per season, with the label change visible
s1 = sql("""SELECT heat_season, sum((upper(complaint_type) = 'HEATING')::INT) AS heating,
                   sum((upper(complaint_type) = 'HEAT/HOT WATER')::INT) AS heat_hot_water
            FROM heat WHERE heat_season IS NOT NULL GROUP BY 1 ORDER BY 1""")
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(s1["heat_season"], s1["heating"], color=SAGE, label='Labelled "HEATING"')
ax.bar(s1["heat_season"], s1["heat_hot_water"], bottom=s1["heating"], color=DARK_GREEN, label='Labelled "HEAT/HOT WATER"')
ax.yaxis.set_major_formatter(thousands)
ax.tick_params(axis="x", rotation=45)
ax.legend(loc="upper left")
ax.grid(axis="x", visible=False)
full = s1.iloc[:-1] if len(s1) > 1 else s1
top = full.assign(total=full["heating"] + full["heat_hot_water"]).sort_values("total").iloc[-1]
finish(fig, ax, "d1_heat_by_season", f"Heat complaints peaked in {top['heat_season']} at {top['total']:,.0f}",
       "Residential heat / hot water service requests, Oct 1 - May 31")

# %% D2. What happened to heat complaints (outcome mix per season)
order = ["Inspected: violation issued", "Inspected: no violation", "Inspected: other", "No access",
         "Restored per tenant", "Corrected per phone/occupant", "Duplicate / referred", "Other / unclear", "Still open"]
palette = [DARK_GREEN, SAGE, "#c8cfb8", SALMON, CREAM, "#e8d48a", "#bdbdbd", "#e3e3e3", DARK_RED]
ms = mix_share.reindex(columns=[c for c in order if c in mix_share.columns])
fig, ax = plt.subplots(figsize=(8.5, 4.5))
left = np.zeros(len(ms))
for c, color in zip(order, palette):
    if c in ms:
        ax.barh(ms.index, ms[c], left=left, color=color, label=c, height=0.7)
        left += ms[c].values
ax.set_xlim(0, 100)
ax.set_xlabel("% of heat complaints")
ax.grid(False)
ax.legend(ncol=3, fontsize=7.5, loc="upper left", bbox_to_anchor=(0, -0.12))
insp_cols = [c for c in ms.columns if c.startswith("Inspected")]
latest_full = ms.index[-2] if len(ms) > 1 else ms.index[-1]           # last season may still be running
insp_share = ms.loc[latest_full, insp_cols].sum()
finish(fig, ax, "d2_heat_outcomes", f"Only {insp_share:.0f}% of heat complaints in {latest_full} led to an inspection",
       "Outcome of each heat complaint, from the city's resolution text, by heating season")

# %% D3. Daily heat complaints (shows cold-snap peaks that set inspector needs)
daily = sql("SELECT day, count(*) AS complaints FROM heat GROUP BY 1 ORDER BY 1")
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.plot(pd.to_datetime(daily["day"]), daily["complaints"], color=DARK_GREEN, linewidth=0.7)
ax.yaxis.set_major_formatter(thousands)
ax.set_ylim(0, None)
finish(fig, ax, "d3_heat_daily", "Heat complaints spike on the coldest days",
       "Residential heat / hot water complaints per day")


# %% [markdown]
# ## E. Helpers for new material handed out in class
# * `profile(path)`: what is in any CSV / Excel / JSON / Parquet / Stata file?
# * `merge_report(left, right, on, validate)`: pandas merge that prints rows before/after, the
#   match rate, and flags a blow-up or shrink (Class 7 rule).
# * `to_duck(df, "name")`: make any pandas table queryable in SQL next to the 311 data.
# * `show("SELECT ...")`: any question about the full 311 data in one line.

# %% E. Helpers
def profile(path, n=5):
    """Load a file of any common type and print its shape, columns, missing values and examples."""
    p = Path(path).expanduser()
    readers = {".csv": pd.read_csv, ".xlsx": pd.read_excel, ".xls": pd.read_excel, ".parquet": pd.read_parquet,
               ".dta": pd.read_stata, ".json": lambda f: pd.read_json(f, dtype=False)}
    df = readers[p.suffix.lower()](p)
    print(f"{p.name}: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(pd.DataFrame({"type": df.dtypes.astype(str), "missing_%": (df.isna().mean() * 100).round(1),
                        "unique": df.nunique(), "example": df.iloc[0].astype(str).str[:40]}).to_string())
    print(df.head(n).to_string())
    return df


def merge_report(left, right, on, how="left", validate="many_to_one"):
    """pandas merge that reports its size before/after and how many rows matched."""
    out = left.merge(right, on=on, how=how, validate=validate, indicator=True)
    print(f"Rows before: {len(left):,} | after: {len(out):,} (x{len(out) / max(1, len(left)):.2f})"
          + ("  FLAG: size changed" if len(out) != len(left) and how == "left" else ""))
    print(out["_merge"].value_counts().to_string())
    return out.drop(columns="_merge")


def to_duck(df, name):
    """Register a pandas table so SQL can join it to the 311 views (sr, heat)."""
    con.register(name, df)
    print(f"'{name}' is now available in SQL ({len(df):,} rows)")


print("Toolkit ready. Views: raw, sr, heat. Helpers: show(), sql(), profile(), merge_report(), to_duck()")
