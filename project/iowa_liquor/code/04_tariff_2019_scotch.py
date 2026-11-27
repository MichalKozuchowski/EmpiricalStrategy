"""
04_tariff_2019_scotch.py: did the US 25% tariff on single-malt Scotch (Oct 18 2019 -> suspended Mar 4 2021) reach Iowa,
and did Iowa buyers cut back?

Design: difference-in-differences / event study on the item x month panel.
  Treated : items in category SINGLE MALT SCOTCH
  Control : SCOTCH WHISKIES (blended Scotch, not covered) + American/Canadian whiskies (not covered)
            (Irish whiskey left out: whether it was covered in 2019 is not yet verified)
  Outcomes: log posted price (pass-through) and log bottles (quantity)
  Fixed effects: item + month; standard errors clustered by item.
  Event time is relative to Sep 2019 (last month before the tariff).

Run:  uv run --with duckdb --with pandas --with numpy --with statsmodels --with pyhdfe --with matplotlib --with tabulate python code/04_tariff_2019_scotch.py
"""
import os
import sys
import duckdb
import numpy as np
import pandas as pd
import pyhdfe
import statsmodels.api as sm
import matplotlib.pyplot as plt

DATA_DIR = os.environ.get("IOWA_DATA_DIR", os.path.expanduser("~/mgt634_data/iowa_liquor"))
B = os.path.join(DATA_DIR, "build").replace("\\", "/")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
try:
    sys.path.insert(0, os.path.abspath(os.path.join(OUT, "..", "..", "..", "..")))
    import upshot_style as us
    us.use_style()
except Exception:
    pass

TREATED = ["SINGLE MALT SCOTCH"]
CONTROL = ["SCOTCH WHISKIES", "STRAIGHT BOURBON WHISKIES", "TENNESSEE WHISKIES", "CANADIAN WHISKIES",
           "BLENDED WHISKIES", "STRAIGHT RYE WHISKIES"]
START, END, REF = "2018-07-01", "2021-12-01", "2019-09-01"
ON, OFF = pd.Timestamp("2019-10-01"), pd.Timestamp("2021-03-01")

cats = ", ".join(f"'{c}'" for c in TREATED + CONTROL)
d = duckdb.sql(f"""SELECT m.item_no, m.month, m.bottles, m.price_posted, i.category_name
                   FROM '{B}/item_month.parquet' m JOIN '{B}/items.parquet' i USING (item_no)
                   WHERE i.category_name IN ({cats}) AND m.month BETWEEN '{START}' AND '{END}'""").df()
d["treated"] = d["category_name"].isin(TREATED).astype(int)
# keep items observed both before and after the tariff (so changes are within-item, not composition)
pre = d[d.month < ON].groupby("item_no").size(); post = d[(d.month >= ON) & (d.month < OFF)].groupby("item_no").size()
keep = pre.index.intersection(post.index)
d = d[d.item_no.isin(keep)].copy()
d["log_p"], d["log_q"] = np.log(d["price_posted"]), np.log(d["bottles"])
print(f"Panel: {len(d):,} item-months, {d.item_no.nunique()} items "
      f"({d[d.treated == 1].item_no.nunique()} single malts, {d[d.treated == 0].item_no.nunique()} controls)")


def fe_ols(df, y, xcols):
    """OLS with item + month fixed effects absorbed (pyhdfe), SEs clustered by item."""
    codes = np.column_stack([pd.factorize(df.item_no)[0], pd.factorize(df.month)[0]])
    alg = pyhdfe.create(codes)
    Z = alg.residualize(df[[y] + xcols].to_numpy(float))
    res = sm.OLS(Z[:, 0], Z[:, 1:]).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df.item_no)[0]})
    return pd.DataFrame({"coef": res.params, "se": res.bse}, index=xcols)


# ---- simple DiD: tariff on (Oct19-Feb21) and after removal (Mar21+), relative to pre ----
d["on"] = ((d.month >= ON) & (d.month < OFF)).astype(int) * d.treated
d["after"] = (d.month >= OFF).astype(int) * d.treated
did = pd.concat({y: fe_ols(d, y, ["on", "after"]) for y in ["log_p", "log_q"]})
print("\nDiD (treated = single malt Scotch). Coefficients are log points (x100 ~ %):\n", did.round(4).to_string())

# ---- event study by quarter relative to the tariff ----
d["q_rel"] = ((d.month.dt.year - 2019) * 12 + d.month.dt.month - 10) // 3          # 0 = Oct-Dec 2019
qs = sorted(d.q_rel.unique())
ref = -1                                                                             # Jul-Sep 2019 = reference
evcols = []
for k in qs:
    if k == ref:
        continue
    c = f"ev_{k}"
    d[c] = ((d.q_rel == k) & (d.treated == 1)).astype(int)
    evcols.append(c)
ev = {y: fe_ols(d, y, evcols) for y in ["log_p", "log_q"]}

fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
for ax, (y, lab) in zip(axes, [("log_p", "Posted price (log points)"), ("log_q", "Bottles (log points)")]):
    e = ev[y].copy(); e["k"] = [int(c.split("_")[1]) for c in e.index]
    e = pd.concat([e, pd.DataFrame({"coef": [0], "se": [0], "k": [ref]})]).sort_values("k")
    ax.axhline(0, color="#999999", lw=1)
    ax.axvspan(-0.5, (OFF.year - 2019) * 4 + (OFF.month - 10) // 3 - 0.5, color="#fbebb7", alpha=0.6, label="25% tariff in force")
    ax.errorbar(e.k, e.coef, yerr=1.96 * e.se, fmt="o-", color="#993f2a", capsize=3, lw=1.5)
    ax.set_title(lab, loc="left"); ax.set_xlabel("Quarters relative to Oct 2019")
    ax.tick_params(labelbottom=True, labelleft=True)
axes[0].legend(loc="upper left", fontsize=8)
fig.suptitle("2019 single-malt Scotch tariff in Iowa: treated vs other whiskies (item + month FE, 95% CI)", x=0.01, ha="left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_tariff2019_event_study.png"), dpi=150)

with open(os.path.join(OUT, "tariff2019_results.md"), "w", encoding="utf-8") as f:
    f.write("# 2019 single-malt Scotch tariff: DiD (auto-generated by code/04_tariff_2019_scotch.py)\n\n")
    f.write(f"Panel: {len(d):,} item-months, {d.item_no.nunique()} items; item + month FE; SE clustered by item.\n\n")
    f.write(did.round(4).to_markdown())
print("Saved output/fig_tariff2019_event_study.png and output/tariff2019_results.md")
