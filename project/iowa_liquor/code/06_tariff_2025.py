"""
06_tariff_2025.py: the 2025 tariffs on UK and EU spirits in Iowa.
  * Did Iowa's posted prices rise (pass-through)?
  * Did Iowa buyers buy less of the tariffed spirits, and did stores stock up BEFORE the tariffs (anticipation)?
  * WHERE did demand go? Substitution to the domestic/tariff-free product in the same spirit type (within-nest) vs elsewhere.

Verified tariff dates (docs/data_notes.md; CBP CSMS 64649265, EO 14257, EO 14326):
  UK spirits: +10% from Apr 5 2025 (May 8 2025 US-UK deal left spirits at 10%).
  EU spirits: +10% from Apr 5 2025, raised to 15% all-in from Aug 7 2025 (no wine/spirits carve-out).
  Mexico (tequila/mezcal) and Canada (Canadian whisky): USMCA-qualifying goods exempt from Mar 7 2025 -> effectively 0%.
  Domestic (US, incl. Puerto Rico / USVI rum): no tariff.

Treatment is assigned by ABD category (the data have no country of origin). Mixed-origin categories (rum, cream liqueurs,
RTD, specialty packs) are left out. Main sample: Jan 2023 - Dec 2025 (posted price is robust to the Nov 2025 system change).

Run:  uv run --with duckdb --with pandas --with numpy --with matplotlib --with tabulate python code/06_tariff_2025.py
"""
import os
import sys
import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from econ import absorb, tsls
from nests import nest_of

DATA_DIR = os.environ.get("IOWA_DATA_DIR", os.path.expanduser("~/mgt634_data/iowa_liquor"))
B = os.path.join(DATA_DIR, "build").replace("\\", "/")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
try:
    sys.path.insert(0, os.path.abspath(os.path.join(OUT, "..", "..", "..", "..")))
    import upshot_style as us
    us.use_style()
except Exception:
    pass

UK_WHISKY = ["SCOTCH WHISKIES", "SINGLE MALT SCOTCH"]
UK_GIN = ["IMPORTED DRY GINS"]
UK = UK_WHISKY + UK_GIN
EU = ["IRISH WHISKIES", "IMPORTED VODKAS", "IMPORTED FLAVORED VODKA", "IMPORTED BRANDIES",
      "IMPORTED CORDIALS & LIQUEURS", "IMPORTED CORDIALS & LIQUEUR", "IMPORTED SCHNAPPS"]
EXEMPT = ["AMERICAN VODKAS", "AMERICAN FLAVORED VODKA", "STRAIGHT BOURBON WHISKIES", "TENNESSEE WHISKIES",
          "STRAIGHT RYE WHISKIES", "BLENDED WHISKIES", "BOTTLED IN BOND BOURBON", "SINGLE BARREL BOURBON WHISKIES",
          "AMERICAN DRY GINS", "AMERICAN BRANDIES", "AMERICAN SCHNAPPS", "AMERICAN CORDIALS & LIQUEURS",
          "AMERICAN CORDIALS & LIQUEUR", "100% AGAVE TEQUILA", "MIXTO TEQUILA", "MEZCAL", "CANADIAN WHISKIES"]
START, END = "2023-01-01", "2026-10-01"     # data run through Oct 2026
T1 = pd.Timestamp("2025-04-01")      # Apr 5 2025: 10% on UK + EU  (event month 0)
T2 = pd.Timestamp("2025-08-01")      # Aug 7 2025: EU to 15%
T3 = pd.Timestamp("2026-03-01")      # Feb 24 2026: IEEPA tariffs struck down -> Section 122 10% (EU back to 10%); Mar = first full month
T4 = pd.Timestamp("2026-08-01")      # Jul 24 2026: UK whisky 0% (Section 301), UK gin stays 10%; Aug = first full month

cats = ", ".join(f"'{c}'" for c in UK + EU + EXEMPT)
d = duckdb.sql(f"""SELECT m.item_no, m.month, m.bottles, m.liters, m.dollars, m.price_posted, i.category_name
                   FROM '{B}/item_month.parquet' m JOIN '{B}/items.parquet' i USING (item_no)
                   WHERE i.category_name IN ({cats}) AND m.month BETWEEN '{START}' AND '{END}'
                         AND m.price_posted BETWEEN 1 AND 150""").df()
d["group"] = np.select([d.category_name.isin(UK_WHISKY), d.category_name.isin(UK_GIN), d.category_name.isin(EU)],
                       ["UK whisky", "UK gin", "EU"], "Exempt (US/MX/CA)")
d["treated"] = (d.group != "Exempt (US/MX/CA)").astype(int)
d["nest"] = d.category_name.map(nest_of)
d["log_p"], d["log_q"] = np.log(d.price_posted), np.log(d.bottles)
d["rel"] = (d.month.dt.year - 2025) * 12 + d.month.dt.month - 4          # 0 = Apr 2025
# within-item comparisons only: keep items sold both before (2024) and after (May-Dec 2025) the tariff
pre_items = set(d.loc[d.month.dt.year == 2024, "item_no"]); post_items = set(d.loc[d.month >= "2025-05-01", "item_no"])
d = d[d.item_no.isin(pre_items & post_items)].copy()
print(f"Panel: {len(d):,} item-months, {d.item_no.nunique():,} items |",
      d.groupby("group").item_no.nunique().to_dict(), flush=True)

# ---------------- 1. Price pass-through and quantity: DiD by group, item + month FE ----------------
# one dummy per (group, tariff regime); each coefficient = change vs Jan 2023-Dec 2024 relative to exempt spirits
g, m = d.group, d.month
REG = {"pre_q1 (Jan-Mar 2025, all tariffed)": (d.treated == 1) & (m >= "2025-01-01") & (m < T1),
       "UK whisky 10% (Apr25-Jul26)": (g == "UK whisky") & (m >= T1) & (m < T4),
       "UK whisky 0% (Aug26+)": (g == "UK whisky") & (m >= T4),
       "UK gin 10% (Apr25+)": (g == "UK gin") & (m >= T1),
       "EU 10% (Apr-Jul25)": (g == "EU") & (m >= T1) & (m < T2),
       "EU 15% (Aug25-Feb26)": (g == "EU") & (m >= T2) & (m < T3),
       "EU 10% (Mar26+)": (g == "EU") & (m >= T3)}
regs = []
for k, v in REG.items():
    col = "r_" + str(len(regs)); d[col] = v.astype(float); regs.append(col)
names = dict(zip(regs, REG.keys()))
did = {}
for y in ["log_p", "log_q"]:
    dm, keep, dums = absorb(d, ["item_no", "month"], [y] + regs)
    r = tsls(dm, y, exog=regs, clusters=d.item_no.to_numpy()[keep], controls=dums)
    did[y] = r["table"][["coef", "se"]]
did = pd.concat(did, axis=1).round(4).rename(index=names)
print("\nDiD vs exempt (US/MX/CA) spirits, item + month FE, SE clustered by item (log points):\n", did.to_string(), flush=True)

# ---------------- 2. Event study by month, separately for UK and EU ----------------
ev = {}
for grp in ["UK whisky", "UK gin", "EU"]:
    sub = d[d.group.isin([grp, "Exempt (US/MX/CA)"])].copy()
    sub["tr"] = (sub.group == grp).astype(int)
    rels = [k for k in sorted(sub.rel.unique()) if k != -1]                   # Mar 2025 = reference
    for k in rels:
        sub[f"e{k}"] = ((sub.rel == k) & (sub.tr == 1)).astype(float)
    ecols = [f"e{k}" for k in rels]
    for y in ["log_p", "log_q"]:
        dm, keep, dums = absorb(sub, ["item_no", "month"], [y] + ecols)
        r = tsls(dm, y, exog=ecols, clusters=sub.item_no.to_numpy()[keep], controls=dums)
        t = r["table"].copy(); t["k"] = rels
        ev[(grp, y)] = pd.concat([t, pd.DataFrame({"coef": [0.0], "se": [0.0], "k": [-1]})]).sort_values("k")

fig, axes = plt.subplots(1, 2, figsize=(13, 4.4))
colors = {"UK whisky": "#993f2a", "UK gin": "#636e4f", "EU": "#2b6cb0"}
for ax, (y, lab) in zip(axes, [("log_p", "Posted Iowa price vs exempt spirits (log points)"),
                               ("log_q", "Bottles vs exempt spirits (log points)")]):
    ax.axhline(0, color="#999999", lw=1)
    for x_, c_ in [(-0.5, "#121212"), (3.5, "#2b6cb0"), (10.5, "#2b6cb0"), (15.5, "#993f2a")]:
        ax.axvline(x_, color=c_, lw=1, ls="--")
    for grp, c in colors.items():
        e = ev[(grp, y)]
        off = {"UK whisky": -0.2, "UK gin": 0.0, "EU": 0.2}[grp]
        ax.errorbar(e.k + off, e.coef, yerr=1.96 * e.se, fmt="o-", color=c, ms=3, lw=1.2, capsize=0, label=grp)
    ax.set_xlim(-15, d.rel.max() + 0.5)
    ax.set_title(lab, loc="left", fontsize=11); ax.set_xlabel("Months rel. to Apr 2025 | lines: 10% on, EU 15% (Aug25), EU back to 10% (Mar26), UK whisky 0% (Aug26)")
    ax.tick_params(labelbottom=True, labelleft=True)
axes[0].legend(loc="upper left", fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_tariff2025_event_study.png"), dpi=150)

# ---------------- 3. Where did demand go? Nest-level shares, tariffed vs domestic within the same spirit type -------------
agg = d.copy()
P0, P1 = "Apr24-Mar25 (before)", "Apr25-Mar26 (tariff year)"
agg["period"] = np.select([(agg.month >= "2024-04-01") & (agg.month < T1), (agg.month >= T1) & (agg.month < "2026-04-01")],
                          [P0, P1], "other")
agg = agg[agg.period != "other"]
nest_tab = (agg.groupby(["nest", "group", "period"]).liters.sum().unstack("period"))
nest_tab["change_%"] = (nest_tab[P1] / nest_tab[P0] - 1) * 100
share = nest_tab[[P0, P1]].div(nest_tab.groupby(level="nest")[[P0, P1]].transform("sum"))
nest_tab["share_of_nest_before_%"] = (share[P0] * 100).round(1)
nest_tab["share_of_nest_after_%"] = (share[P1] * 100).round(1)
nest_tab = nest_tab.round(1)
print("\nLiters, tariff year (Apr25-Mar26) vs year before, by spirit type and tariff group:\n", nest_tab.to_string(), flush=True)

with open(os.path.join(OUT, "tariff2025_results.md"), "w", encoding="utf-8") as f:
    f.write("# 2025 UK/EU spirits tariffs in Iowa (auto-generated by code/06_tariff_2025.py)\n\n")
    f.write(f"Panel: {len(d):,} item-months, {d.item_no.nunique():,} items (sold in 2024 and after May 2025); "
            "item + month FE; SE clustered by item. Treatment by ABD category; control = US/Mexico/Canada (tariff-free).\n\n")
    f.write("## DiD (log points; x100 ~ %)\n\n" + did.to_markdown() + "\n\n")
    f.write("Coefficients are relative to 2023-2024 for the same items, net of exempt-spirit trends. pre_q1 = anticipation window.\n\n")
    f.write("## Liters by spirit type, tariff year (Apr 2025-Mar 2026) vs the year before\n\n" + nest_tab.to_markdown() + "\n")
print("Saved output/tariff2025_results.md and fig_tariff2025_event_study.png")
