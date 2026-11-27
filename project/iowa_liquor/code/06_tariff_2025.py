"""
06_tariff_2025.py: the 2025-26 tariffs on UK and EU spirits in Iowa (v2, after independent review).
  * Pass-through: did Iowa's posted prices of UK/EU spirits rise relative to tariff-free (US, USMCA) spirits?
  * Quantity: did Iowa buyers buy less (liters)? Did stores stock up before Apr 2025?
  * Substitution: did tariffed products lose share within their spirit type?

Verified tariff path (docs/data_notes.md; CBP CSMS 64649265, EO 14257, EO 14326, Section 122/301 notices):
  UK: 10% from Apr 5 2025 (May 8 2025 deal left spirits at 10%); Section 122 10% from Feb 24 2026; from Jul 24 2026
      Section 301: UK WHISKY 0%, other UK spirits (gin) 10%.
  EU: 10% Apr 5 2025 -> 15% all-in Aug 7 2025 -> 10% (Section 122) Feb 24 2026 -> 10% (Section 301) Jul 24 2026.
  Mexico/Canada: USMCA-qualifying goods exempt from Mar 7 2025 (tequila, Canadian whisky) -> control group.
  US (incl. Puerto Rico / USVI rum): no tariff -> control group.

Design changes after review (docs/review_log.md):
  * treatment by COUNTRY OF ORIGIN (brand rules in nests.origin_of), not by ABD category
    (e.g. "IMPORTED SCHNAPPS" is mostly Canadian Dr. McGillicuddy's = exempt; Bushmills = UK not EU)
  * base period = the 12 months right before the tariff (Apr 2024-Mar 2025), so older drifts are not called effects;
    event study normalized to Mar 2025 shows leads
  * outcomes: log posted price per bottle (= per liter within an item) and log liters; weighted by each item's
    pre-period dollars (what consumers actually buy) and unweighted
  * gift/specialty packs and special orders excluded (composition)

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
from nests import nest_of, origin_of

DATA_DIR = os.environ.get("IOWA_DATA_DIR", os.path.expanduser("~/mgt634_data/iowa_liquor"))
B = os.path.join(DATA_DIR, "build").replace("\\", "/")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
try:
    sys.path.insert(0, os.path.abspath(os.path.join(OUT, "..", "..", "..", "..")))
    import upshot_style as us
    us.use_style()
except Exception:
    pass

START, END = "2023-01-01", "2026-10-01"
T1 = pd.Timestamp("2025-04-01")      # Apr 5 2025: 10% on UK + EU (event month 0)
T2 = pd.Timestamp("2025-08-01")      # Aug 7 2025: EU to 15%
T3 = pd.Timestamp("2026-03-01")      # Feb 24 2026: IEEPA struck down -> Section 122 10% (EU back to 10%)
T4 = pd.Timestamp("2026-08-01")      # Jul 24 2026: UK whisky 0% (Section 301); UK gin and EU stay at 10%
BASE0, BASE1 = pd.Timestamp("2024-04-01"), pd.Timestamp("2025-03-01")

d = duckdb.sql(f"""SELECT m.item_no, m.month, m.bottles, m.liters, m.dollars, m.price_posted, i.category_name,
                          i.im_desc, i.ml
                   FROM '{B}/item_month.parquet' m JOIN '{B}/items.parquet' i USING (item_no)
                   WHERE m.month BETWEEN '{START}' AND '{END}' AND m.price_posted BETWEEN 1 AND 150
                     AND i.category_name NOT IN ('TEMPORARY & SPECIALTY PACKAGES', 'SPECIAL ORDER ITEMS',
                                                 'DELISTED / SPECIAL ORDER ITEMS')""").df()
d = d[d.liters > 0].copy()                                                       # a few items have ml = 0 (log undefined)
d["origin"] = [origin_of(a, b) for a, b in zip(d.im_desc, d.category_name)]
d["nest"] = d.category_name.map(nest_of)
d["group"] = np.select([(d.origin == "UK") & (d.nest == "Whiskey"), d.origin == "UK", d.origin == "EU",
                        d.origin.isin(["US", "USMCA"])],
                       ["UK whisky", "UK other (gin etc.)", "EU", "Control (US + USMCA)"], "drop")
d = d[d.group != "drop"].copy()
d["treated"] = (d.group != "Control (US + USMCA)").astype(int)
d["log_p"], d["log_l"] = np.log(d.price_posted), np.log(d.liters)
d["rel"] = (d.month.dt.year - 2025) * 12 + d.month.dt.month - 4                  # 0 = Apr 2025
# within-item comparisons: items sold in the base year AND after the tariff (May 2025+)
base_items = set(d.loc[(d.month >= BASE0) & (d.month <= BASE1), "item_no"])
post_items = set(d.loc[d.month >= "2025-05-01", "item_no"])
d = d[d.item_no.isin(base_items & post_items)].copy()
w_item = d[(d.month >= BASE0) & (d.month <= BASE1)].groupby("item_no").dollars.sum()
d["w"] = d.item_no.map(w_item)                                                      # pre-period dollars (constant per item)
share700 = d.loc[(d.treated == 1) & (d.month >= T1)].pipe(lambda x: x.loc[x.ml == 700, "dollars"].sum() / x.dollars.sum())
print(f"Panel: {len(d):,} item-months, {d.item_no.nunique():,} items |", d.groupby("group").item_no.nunique().to_dict(),
      f"| 700 ml share of treated dollars after Apr 2025: {share700:.1%}", flush=True)
print("Treated dollars in base year by group ($M):", (d[(d.month >= BASE0) & (d.month <= BASE1)].groupby("group").dollars.sum() / 1e6).round(1).to_dict())

# ---------------- 1. DiD by group x tariff regime (base = Apr 2024-Mar 2025), item + month FE ----------------
dd = d[d.month >= BASE0].copy()
g, m = dd.group, dd.month
REG = {"Jan-Mar 2025 lead (stocking-up)": (dd.treated == 1) & (m >= "2025-01-01") & (m < T1),
       "UK whisky: 10% (Apr25-Jul26)": (g == "UK whisky") & (m >= T1) & (m < T4),
       "UK whisky: 0% (Aug26+)": (g == "UK whisky") & (m >= T4),
       "UK gin etc.: 10% (Apr25+)": (g == "UK other (gin etc.)") & (m >= T1),
       "EU: 10% (Apr-Jul25)": (g == "EU") & (m >= T1) & (m < T2),
       "EU: 15% (Aug25-Feb26)": (g == "EU") & (m >= T2) & (m < T3),
       "EU: 10% (Mar26+)": (g == "EU") & (m >= T3)}
regs = [f"r{i}" for i in range(len(REG))]
for c, v in zip(regs, REG.values()):
    dd[c] = v.astype(float)
res = {}
for y in ["log_p", "log_l"]:
    dm, keep, dums = absorb(dd, ["item_no", "month"], [y] + regs)
    for wname, wts in [("unweighted", None), ("$-weighted", dd.w.to_numpy()[keep])]:
        r = tsls(dm, y, exog=regs, clusters=dd.item_no.to_numpy()[keep], controls=dums, weights=wts)
        res[(y, wname)] = r["table"]["coef"].round(4).astype(str) + " (" + r["table"]["se"].round(4).astype(str) + ")"
did = pd.DataFrame(res); did.index = list(REG.keys())
did.columns = [f"{'log price' if a == 'log_p' else 'log liters'}, {b}" for a, b in did.columns]
print("\nDiD vs US + USMCA spirits; base Apr 2024-Mar 2025; item + month FE; SE clustered by item:\n", did.to_string(), flush=True)

# ---------------- 2. Event study (monthly, base = Mar 2025), $-weighted ----------------
ev = {}
for grp in ["UK whisky", "UK other (gin etc.)", "EU"]:
    sub = d[d.group.isin([grp, "Control (US + USMCA)"])].copy()
    sub["tr"] = (sub.group == grp).astype(int)
    rels = [k for k in sorted(sub.rel.unique()) if k != -1]
    for k in rels:
        sub[f"e{k}"] = ((sub.rel == k) & (sub.tr == 1)).astype(float)
    ecols = [f"e{k}" for k in rels]
    for y in ["log_p", "log_l"]:
        dm, keep, dums = absorb(sub, ["item_no", "month"], [y] + ecols)
        r = tsls(dm, y, exog=ecols, clusters=sub.item_no.to_numpy()[keep], controls=dums, weights=sub.w.to_numpy()[keep])
        t = r["table"].copy(); t["k"] = rels
        ev[(grp, y)] = pd.concat([t, pd.DataFrame({"coef": [0.0], "se": [0.0], "k": [-1]})]).sort_values("k")

fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.6))
colors = {"UK whisky": "#993f2a", "UK other (gin etc.)": "#636e4f", "EU": "#2b6cb0"}
for ax, (y, lab) in zip(axes, [("log_p", "Posted Iowa price vs US + USMCA spirits (log points)"),
                               ("log_l", "Liters vs US + USMCA spirits (log points)")]):
    ax.axhline(0, color="#999999", lw=1)
    for x_, c_ in [(-0.5, "#121212"), (3.5, "#2b6cb0"), (10.5, "#2b6cb0"), (15.5, "#993f2a")]:
        ax.axvline(x_, color=c_, lw=0.8, ls="--")
    for grp, c in colors.items():
        e = ev[(grp, y)]
        off = {"UK whisky": -0.2, "UK other (gin etc.)": 0.0, "EU": 0.2}[grp]
        ax.errorbar(e.k + off, e.coef, yerr=1.96 * e.se, fmt="o-", color=c, ms=3, lw=1.1, capsize=0, label=grp)
    ax.set_title(lab, loc="left", fontsize=11)
    ax.set_xlabel("Months rel. to Apr 2025 | lines: 10% on; EU 15% (Aug25); EU 10% (Mar26); UK whisky 0% (Aug26)", fontsize=8)
    ax.tick_params(labelbottom=True, labelleft=True)
axes[0].legend(loc="upper left", fontsize=8)
fig.suptitle("2025-26 UK/EU spirits tariffs: no detectable pass-through to Iowa's posted prices ($-weighted, 95% CI)",
             x=0.01, ha="left", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_tariff2025_event_study.png"), dpi=150)

# ---------------- 3. Within-nest share of tariffed products (liters), year before vs tariff year ----------------
P0, P1 = "Apr24-Mar25 (before)", "Apr25-Mar26 (tariff year)"
agg = d.copy()
agg["period"] = np.select([(agg.month >= BASE0) & (agg.month < T1), (agg.month >= T1) & (agg.month < "2026-04-01")], [P0, P1], "x")
agg = agg[agg.period != "x"]
tab = agg.groupby(["nest", "group", "period"]).liters.sum().unstack("period")
tab["change_%"] = (tab[P1] / tab[P0] - 1) * 100
sh = tab[[P0, P1]].div(tab.groupby(level="nest")[[P0, P1]].transform("sum")) * 100
tab["share_before_%"], tab["share_after_%"] = sh[P0], sh[P1]
tab = tab.round(1)
print("\nLiters by spirit type and origin group (same items, both years):\n", tab.to_string(), flush=True)

with open(os.path.join(OUT, "tariff2025_results.md"), "w", encoding="utf-8") as f:
    f.write("# 2025-26 UK/EU spirits tariffs in Iowa (auto-generated by code/06_tariff_2025.py, v2)\n\n")
    f.write(f"Panel: {len(d):,} item-months, {d.item_no.nunique():,} items sold both in Apr 2024-Mar 2025 and after Apr 2025. "
            "Treatment by country of origin (brand rules, nests.origin_of); control = US + USMCA (tariff-free). "
            f"700 ml bottles are {share700:.1%} of treated dollars after Apr 2025.\n\n")
    f.write("## DiD by tariff regime (log points; base = Apr 2024-Mar 2025; item + month FE; SE clustered by item)\n\n")
    f.write(did.to_markdown() + "\n\n## Liters by spirit type, tariff year vs year before\n\n" + tab.to_markdown() + "\n")
print("Saved output/tariff2025_results.md and fig_tariff2025_event_study.png")
