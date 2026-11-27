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
  Review 2 (sections 4-5): group-specific linear trends (EU pre-period drift); re-numbered products (new item number,
  same description + size) to catch price rises hidden in re-listings.

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
d_all = d.copy()                                                                  # before the balanced-item filter (for 4.)
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

# ---------------- 4. Robustness (review 2): group-specific linear trends from Jan 2023 ----------------
# The EU-vs-control price gap drifted down in 2023-24. Allow each treated group its own linear time trend
# (item + month FE; regimes as in 1.; sample from Jan 2023 so the trend is pinned down mostly by 27 pre-tariff months).
tt = d.copy()
g2, m2 = tt.group, tt.month
REG2 = {k: None for k in REG}
REG2["Jan-Mar 2025 lead (stocking-up)"] = (tt.treated == 1) & (m2 >= "2025-01-01") & (m2 < T1)
REG2["UK whisky: 10% (Apr25-Jul26)"] = (g2 == "UK whisky") & (m2 >= T1) & (m2 < T4)
REG2["UK whisky: 0% (Aug26+)"] = (g2 == "UK whisky") & (m2 >= T4)
REG2["UK gin etc.: 10% (Apr25+)"] = (g2 == "UK other (gin etc.)") & (m2 >= T1)
REG2["EU: 10% (Apr-Jul25)"] = (g2 == "EU") & (m2 >= T1) & (m2 < T2)
REG2["EU: 15% (Aug25-Feb26)"] = (g2 == "EU") & (m2 >= T2) & (m2 < T3)
REG2["EU: 10% (Mar26+)"] = (g2 == "EU") & (m2 >= T3)
for c, v in zip(regs, REG2.values()):
    tt[c] = v.astype(float)
trends = []
for grp in ["UK whisky", "UK other (gin etc.)", "EU"]:
    cn = "trend_" + grp.split()[0] + ("_o" if "other" in grp else "")
    tt[cn] = ((tt.group == grp) * tt.rel / 12).astype(float)                       # years since Apr 2025
    trends.append(cn)
rob = {}
for y in ["log_p"]:
    dm, keep, dums = absorb(tt, ["item_no", "month"], [y] + regs + trends)
    for wname, wts in [("unweighted", None), ("$-weighted", tt.w.to_numpy()[keep])]:
        r = tsls(dm, y, exog=regs + trends, clusters=tt.item_no.to_numpy()[keep], controls=dums, weights=wts)
        rob[f"log price, {wname}, group trends"] = r["table"]["coef"].round(4).astype(str) + " (" + r["table"]["se"].round(4).astype(str) + ")"
rob = pd.DataFrame(rob); rob.index = list(REG.keys()) + [f"linear trend per year: {c[6:]}" for c in trends]
print("\nRobustness: group-specific linear trends (sample Jan 2023-Oct 2026):\n", rob.to_string(), flush=True)

# ---------------- 5. Re-numbered products (review 2): did suppliers raise prices by launching a NEW item number? ----------------
# A within-item panel would miss a price rise hidden in a re-listing (e.g. Hennessy 48106 -> 48241).
# Match items that stop selling after Oct 2024 to a NEW item number (first sold Jan 2025 or later) from the same vendor,
# same bottle size and same first two words of the description (e.g. "HENNESSY XO" -> "HENNESSY XO GB UPGRADE"),
# new item first sold within 3 months before / 6 months after the old one's last sale (closest match kept);
# compare the new item's first posted price with the old item's last posted price.
a = d_all.copy()
vend = duckdb.sql(f"SELECT item_no, vendor_name FROM '{B}/items.parquet'").df().set_index("item_no").vendor_name
a["key"] = (a.item_no.map(vend).fillna("") + "_" + a.ml.astype(str) + "_" +
            a.im_desc.fillna("").str.upper().str.replace(r"[^A-Z0-9 ]", "", regex=True).str.split().str[:2].str.join(" "))
first = a.groupby("item_no").month.min(); last = a.groupby("item_no").month.max()
old = a[a.item_no.isin(last[(last >= "2024-10-01") & (last < "2026-08-01")].index) &
        a.item_no.isin(first[first < "2024-10-01"].index)]
new = a[a.item_no.isin(first[first >= "2025-01-01"].index)]
o = old.sort_values("month").groupby("item_no").agg(key=("key", "last"), group=("group", "last"),
                                                     p_old=("price_posted", "last"), m_old=("month", "last"))
n_ = new.sort_values("month").groupby("item_no").agg(key=("key", "first"), p_new=("price_posted", "first"),
                                                     m_new=("month", "first"), dollars=("dollars", "sum"))
pairs = o.reset_index().merge(n_.reset_index(), on="key", suffixes=("_old", "_new"))
print(f"Re-number merge: {len(o):,} exiting x {len(n_):,} new items -> {len(pairs):,} pairs", flush=True)
pairs = pairs[(pairs.m_new >= pairs.m_old - pd.DateOffset(months=3)) & (pairs.m_new <= pairs.m_old + pd.DateOffset(months=6))]
pairs["gap"] = (pairs.m_new - pairs.m_old).abs()
pairs = pairs.sort_values("gap").drop_duplicates("item_no_new").drop_duplicates("item_no_old")   # one-to-one, closest in time
pairs["dlog_p"] = np.log(pairs.p_new / pairs.p_old)
pairs = pairs[pairs.dlog_p.abs() <= 0.7]                                                           # different products
pairs["post_tariff"] = pairs.m_new >= T1
pairs["group"] = np.where(pairs.group == "Control (US + USMCA)", "Control (US + USMCA)", "Tariffed (UK + EU)")
renum = pairs.groupby(["group", "post_tariff"]).agg(pairs=("dlog_p", "size"), mean_dlog_p=("dlog_p", "mean"),
                                                    median_dlog_p=("dlog_p", "median"),
                                                    share_higher=("dlog_p", lambda x: (x > 0.01).mean())).round(3)
print("\nRe-numbered items (old -> new item number, same vendor + size + first two words of name):\n", renum.to_string(), flush=True)

with open(os.path.join(OUT, "tariff2025_results.md"), "w", encoding="utf-8") as f:
    f.write("# 2025-26 UK/EU spirits tariffs in Iowa (auto-generated by code/06_tariff_2025.py, v2)\n\n")
    f.write(f"Panel: {len(d):,} item-months, {d.item_no.nunique():,} items sold both in Apr 2024-Mar 2025 and after Apr 2025. "
            "Treatment by country of origin (brand rules, nests.origin_of); control = US + USMCA (tariff-free). "
            f"700 ml bottles are {share700:.1%} of treated dollars after Apr 2025.\n\n")
    f.write("## DiD by tariff regime (log points; base = Apr 2024-Mar 2025; item + month FE; SE clustered by item)\n\n")
    f.write(did.to_markdown() + "\n\n## Liters by spirit type, tariff year vs year before\n\n" + tab.to_markdown() + "\n")
    f.write("\n## Robustness: group-specific linear trends (sample Jan 2023-Oct 2026; trends in log points per year)\n\n"
            + rob.to_markdown() + "\n")
    f.write("\n## Re-numbered products: new item number, same vendor + bottle size + first two words of the name (log price new vs old)\n\n"
            "If suppliers passed the tariff on by re-listing products, treated groups would show higher prices on "
            "post-tariff re-listings than controls.\n\n" + renum.to_markdown() + "\n")
print("Saved output/tariff2025_results.md and fig_tariff2025_event_study.png")
