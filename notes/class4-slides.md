# Class 4 — Slide Deck: "Summarizing Data"
**Pierre Bodéré (guest instructor), Sep 15, 2026** — application: Pennsylvania preschool market
data. Companion paper: [class4-reading-notes.md](class4-reading-notes.md) (Bodéré's own research,
the empirical basis for today's dataset).

## Plan for today
- Basics of data exploration, applied to the preschool market:
  - Demand side: spatially disaggregated census data (block-group, tract)
  - Supply side: early education providers in Pennsylvania, 2010–2018
- Key steps in a data processing pipeline: missing data (why is it missing?), outliers (should we
  care, what to do about them)
- Can be automated, but you often learn about the data in the process — if using AI for the
  pipeline, report key statistics of raw/clean data; can also store favorite functions in a
  `utils.py` file and `import utils` for reuse

## Loading data
```python
import pandas as pd
import os

projectPath = "/gpfs/project/esai_2026/"
dataPath = os.path.join(projectPath, "data", "preschools")
print(dataPath)

df_preschools = pd.read_csv(os.path.join(dataPath, "data_preschools.csv"))
df_blockgroup = pd.read_csv(os.path.join(dataPath, "data_blockgroup_2010_2018.csv"))
```
**Note**: don't hesitate to use the Census in your own work — IPUMS (USA, CPS, International,
Global Health, NHGIS, IHGIS) all offer free microdata/summary tables.

## Missing data: why is it missing?
Three mechanisms (matters because the fix depends on which one you're facing):
- **MCAR** (Missing Completely At Random): missingness is pure chance — observed data stays
  representative. Example: exams placed randomly in 5 boxes, one box is lost.
- **MAR** (Missing At Random): missingness depends on *observed* characteristics — can proceed
  with imputation/multiple imputation. Example: exams sorted alphabetically, box with A–E is lost.
- **MNAR** (Missing Not At Random): missingness depends on the *unobserved* value itself, even
  conditional on what you do observe — needs a missingness/selection model or an instrument.
  Example: exams sorted by grade, the box with the top 20% is lost.

Why it matters in practice: high-income earners tend not to report income in surveys (biases
income-distribution estimates); patients drop out of drug trials based on their own unobserved
reaction to treatment (mis-measures both benefits and side effects).

**In the preschool data**: use `groupby` to explore missingness by county, year, rating.
```python
# Flag missing enrollment: 1 if missing, 0 otherwise
df_preschools["ind_enrol_miss"] = (
    df_preschools["enrollment_raw"].isna().astype(int)
)
# Missing-enrollment share by county, year, and rating
display(df_preschools.groupby("county_fips")["ind_enrol_miss"].mean())
display(df_preschools.groupby("year")["ind_enrol_miss"].mean())
display(df_preschools.groupby("stars_rating")["ind_enrol_miss"].mean())
```
Finding: enrollment is missing for STAR 1 (lowest-rated) centers specifically, and prices are
missing in early years — reflects that reporting standards are higher for higher-quality ratings,
and historic data is generally less complete.

## Outliers
- Concern: a single extreme point can drive a spurious relationship (slide showed a scatter where
  one outlier flips a near-zero slope to a strong positive one).
- But sometimes extreme values are plausible and real — check robustness to removing them rather
  than dropping automatically.
- Outliers can also *be* the insight: "mischievous responders" in teen surveys, corrupted sensor
  readings, inattentive responders in online experiments. Other variables (height, temperature,
  response time) can signal whether an observation is credible at all.

**Prices**: use `describe()` with custom quantiles to see the distribution's tails, then winsorize
(clip) rather than drop:
```python
# Display quantiles of real price distribution
df_preschools["price_clean_real2015"].describe(percentiles=[0.005, 0.25, 0.50, 0.75, 0.995])

# Select col and quantiles, and create new winsorized col
col = df_preschools["price_clean_real2015"]
lower, upper = col.quantile([0.005, 0.995])
df_preschools["price_clean_real2015_win"] = col.clip(lower=lower, upper=upper)
```
Reasonable approach absent a better alternative: winsorize rather than delete. Worth wrapping as a
reusable function that takes `(df, lower, upper, col)`.

**Enrollment** has a natural upper bound — licensed capacity — so use that as a defensible clip
ceiling instead of a quantile:
```python
display(df_preschools["enrollment_clean"].describe(percentiles=[0.005, 0.25, 0.50, 0.75, 0.995]))
display((df_preschools["enrollment_clean"] > df_preschools["capacity_clean"]).mean())

col = df_preschools["enrollment_clean"]
lower = col.quantile(0.005)
df_preschools["enrollment_clean_winCap"] = col.clip(
    lower=lower, upper=df_preschools["capacity_clean"],
)
```

## Descriptives I: preschools by quality and over time
```python
# Share of each star rating in 2010 and 2018
display(
    df_preschools.loc[df_preschools["year"].isin([2010, 2018])]
    .groupby("year")["stars_rating"]
    .value_counts(normalize=True)
    .unstack("year"))
# Mean clean characteristics in 2018, by star rating
display(
    df_preschools.loc[df_preschools["year"] == 2018]
    .groupby("stars_rating")[["price_clean_real2015",
        "enrollment_clean", "capacity_clean", "ind_accredited"]]
    .mean())
```
Findings: quality is rising over time; higher-rated centers are larger and pricier.

## Descriptives II: neighborhoods where children attend preschool
```python
# Calculate enrollment share; missing or nonpositive denominators give NaN.
denom = df_blockgroup["ct_age_3_and_4"]
df_blockgroup["sh_enrol_preschool"] = (
    df_blockgroup["ct_enrol_prschl"] / denom.where(denom > 0))
# Split enrollment shares into terciles across all observations.
df_blockgroup["enrol_tercile"] = pd.qcut(
    df_blockgroup["sh_enrol_preschool"], q=3, labels=["Low", "Middle", "High"])
# Average income, home value, rent, and college ratio by enrollment tercile.
display(df_blockgroup.groupby("enrol_tercile", observed=True)[["median_hhinc",
    "median_value", "median_rent", "ratio_clg"]].mean())
```
Finding: high-enrollment neighborhoods are richer, more educated, higher rent and property values.

## Descriptives III: preschool prices and quality across neighborhoods
Merging supply (preschools) with demand (block-group census data) — first check for duplicates,
then merge, then verify the row count was preserved:
```python
# 1. Define blockgroup year as the interval's last year: 2006-2010 -> 2010.
df_blockgroup["year"] = df_blockgroup["YEAR"].str.split("-").str[-1].astype(int)

# 2. Check that each dataset has unique identifiers within year.
assert not df_preschools.duplicated(["mpi_clean", "year"]).any(), (
    "Duplicate mpi_clean/year combinations in df_preschools.")
assert not df_blockgroup.duplicated(["GISJOIN", "year"]).any(), (
    "Duplicate GISJOIN/year combinations in df_blockgroup.")
print("Both datasets have unique identifier/year combinations.")

# 3. Select the blockgroup characteristics to merge.
bg_cols = ["median_rent", "median_hhinc", "population_total", "ratio_clg",
           "ct_age_under_5", "ct_age_3_and_4", "ct_enrol_prschl"]

# Keep all preschool rows; allow multiple preschools per blockgroup/year.
# Remove previously merged columns so this cell can be rerun.
df_preschools = df_preschools.drop(
    columns=bg_cols+["_bg_merge"], errors="ignore").merge(
    df_blockgroup[["GISJOIN", "year"]+bg_cols], on=["GISJOIN", "year"],
    how="left", validate="many_to_one", indicator="_bg_merge")

# Report matched and unmatched observations, then remove the merge flag.
print(df_preschools["_bg_merge"].value_counts())
df_preschools = df_preschools.drop(columns="_bg_merge")

# Split preschool prices into terciles across all observations.
df_preschools["price_tercile"] = pd.qcut(
    df_preschools["price_clean_real2015"], q=3, labels=["Low", "Middle", "High"])
# Average neighborhood characteristics by preschool-price tercile.
display(df_preschools.groupby("price_tercile", observed=True)[["median_hhinc",
    "median_rent", "ratio_clg"]].mean())
# Average neighborhood characteristics by accreditation status.
display(df_preschools.groupby("ind_accredited", observed=True)[["median_hhinc",
    "median_rent", "ratio_clg"]].mean())
```
Finding: high-price, high-quality centers are located in richer, higher-rent, more-educated
neighborhoods — the same story as Descriptives II, now shown from the supply side.

## Techniques worth remembering (cut across the whole deck)
- `validate="many_to_one"` (or `"one_to_one"`, etc.) on `.merge()` — fails loudly instead of
  silently duplicating rows if your uniqueness assumption is wrong
- `indicator=` on `.merge()` — reports matched vs. unmatched rows so you can see merge quality
  directly, rather than assuming it worked
- Two-sided `assert` statements *before* a merge to check both datasets have unique
  identifier/year combinations
- `pd.qcut(..., q=3, labels=[...])` — quick terciles for turning a continuous variable into
  Low/Middle/High groups for a groupby comparison
