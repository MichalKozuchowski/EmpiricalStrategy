# Class 7 — Slide Deck: "Querying, Merging, and Summarizing Data"
**Kevin Williams, MGT 634: ESAI.** Companion:
[class7-sql-cheat-sheet.md](class7-sql-cheat-sheet.md) (DataCamp SQL Basics Cheat Sheet).

## Why this matters
Data is often spread across sources (e.g. one system for prices/quantities, another for
costs — need both merged to infer profits). At scale (200M+ rows), you can't wait an hour for
summary stats — need the right tool, and possibly different tools for small vs. large data.

## Merge cardinality types (pandas `pd.merge`)
- **1:1** — both keys unique on each side; simplest case: `pd.merge(df_left, df_right, on='id')`
- **1:n** — left is unique, right has repeats (e.g. one customer, many orders). Use
  `how='right'` to keep all right-side rows even if unmatched on the left.
- **n:1** — left has repeats, right is unique (e.g. many orders, one customer lookup). Use
  `how='left'` to keep all left-side rows.
- **n:n** — neither side is unique. Produces **all possible combinations** of matching keys
  (Cartesian product on the matched key) — can silently blow up row count/memory. Handle with care.
- **Merge gone "wrong"** — classic bug: expecting an n:1 merge (6 orders → 6 rows) but the
  lookup table has a duplicate key (e.g. both "Bob" and "Robert" with `customer_id=2`) →
  silently produces 7 rows instead of 6. **Always check `df.shape` before and after a merge** —
  did it change size unexpectedly? Significant shrinkage may mean a merge-key mismatch;
  significant growth may mean an accidental many-to-many.

## Tools for merging at scale
| Tool | Why | Key idea |
|---|---|---|
| **pandas** | Baseline; fine only if everything fits comfortably in RAM | In-memory, single-threaded by default |
| **Dask** | Pandas/NumPy-alike syntax — if you know pandas, you mostly know Dask | Splits data into partitions (`npartitions=`), computes in parallel/chunks/on disk; **lazy** — nothing runs until `.compute()`. Can merge many files via `dd.read_parquet("path/*")`, combine with a small in-memory pandas table via `broadcast=True`, and write straight to disk with `.to_parquet()` without pulling everything into RAM |
| **DuckDB** | In-process SQL engine inside your Python script; very fast; LLMs are good at writing SQL for it | Register pandas DataFrames as SQL tables (`con.register("df_left", df_left)`), run `SELECT ... FROM ... JOIN ... USING(key)` via `duckdb.query(...).df()`. Benchmark from the deck: a real two-key merge over hundreds of millions of flight-record rows "did not compute" in pandas at all, but took **13 seconds** in DuckDB |
| **Polars** | Written in Rust, built for speed/memory efficiency; multi-threaded by default | Similar `.join()` API to pandas; use small dtypes (`int32`/`float32`) to save memory; can also be **lazy** (`.lazy()` → build a query plan → `.collect()` to execute), same idea as Dask's laziness |

**Benchmark (2-key merge, N = 1–9 million rows, deck's own timing chart)**: pandas scales
roughly linearly and is by far the slowest (~2.5s at 9M rows); DuckDB and Polars both stay
far flatter and faster (DuckDB fastest, under ~0.1s; Polars close behind, under ~0.3s).
**Takeaway: for genuinely large data, you need large-data tools — pandas alone doesn't cut it.**
Sampling the large dataset is always an alternative, but has its own pros/cons (not explored
in depth in this deck).

## Applied example: merging ACS demographics onto Chicago taxi data
- Goal: merge American Community Survey (ACS) household-income data (2013–2023) onto Chicago
  taxi trip data.
- **The merge key doesn't match out of the box**:
  - ACS records geography via `GISJOIN`, e.g. `G0100010020100`
  - Taxi data records `Pickup Census Tract` / `Dropoff Census Tract` as plain numbers, e.g.
    `17031980000.0`
- **Decoding a GEOID** (14-character Census geographic identifier, used in ACS summary files
  and API output):

  | Segment | Meaning | Example |
  |---|---|---|
  | `G` | prefix indicating a geographic ID | `G` |
  | `01` | State FIPS code | `01` = Alabama |
  | `0001` | County FIPS code | `0001` = Autauga County |
  | `0020100` | Tract/block-group code | maps to a Census tract or block group |

  — worth just **asking an AI tool** to explain an unfamiliar identifier format like this
  (and to explain how the *other* dataset's key is structured too), rather than guessing.

- **Practical tips**:
  - Read the ACS file with `encoding="latin1"` (not default UTF-8) —
    `pd.read_csv(path + "nhgis0040_ds244_20195_tract.csv", encoding="latin1")`
  - ACS covers the whole US; taxi data covers only Chicago — filter the ACS frame down
    (e.g. `.loc[]`) before merging, rather than merging against the full national table
  - When testing code, grab just the first 50,000 rows of the (large) taxi data first
  - Cluster paths used in the demo:
    `/home/kw468/esai_2026/data/chicago_taxi_trips_2024/Taxi_Trips_2024.csv`
    `/home/kw468/esai_2026/data/acs/nhgis0040_ds244_20195_tract.csv`

- **"My AI funcs" — helper functions the professor had AI write for him** (shown as slide
  examples of exactly this kind of AI-assisted key-reconciliation work):
  - `acs_G_to_geoid11(x)`: strips the leading `G` and normalizes an ACS GEOID (11- or
    13-digit variants) down to the standard 11-digit `SSCCCtttttt` tract GEOID
  - `to_geoid11_str(series)`: vectorized pandas version — strips a trailing `.0`, strips
    non-digits, zero-pads to 11 digits (for converting the taxi data's numeric tract column
    into the same GEOID11 format)
  - `median_from_b19001_row(row, top_cap=250_000)`: approximates a **median household income**
    from the ACS's binned income-distribution table (`ALW0E001`–`ALW0E017`, i.e. table B19001)
    via within-bin linear interpolation — finds the income bin where the cumulative household
    count first reaches 50% of the total, then interpolates a specific dollar value within
    that bin (capping the open-ended top bin at `top_cap`)
  - ACS income bin reference (`ALW0E001`–`ALW0E017`, table B19001): `E001`=total households,
    `E002`=<$10k, `E003`=$10–15k, `E004`=$15–20k, ... up to `E017`=$200k+ (17 bins total,
    left-closed/right-open except the last open-ended bin)
