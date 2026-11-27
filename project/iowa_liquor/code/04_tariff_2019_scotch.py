"""
04_tariff_2019_scotch.py: the 2019-21 "Airbus" tariffs in Iowa (v2, after independent review).

Verified (USTR / Federal Register 2019-22056, 2021-05354, 2021-14550; DISCUS timeline):
  25% from Oct 18 2019 on (a) UK single-malt Scotch (and N. Irish single malt), (b) liqueurs/cordials from the UK,
  Germany, Ireland, Italy, Spain. Suspended Mar 4 2021 (UK) / Mar 11 2021 (EU), then 5-year suspensions (Jul 2021).
  Republic of Ireland whiskey and French liqueurs were NOT covered. (French/German cognac only Jan 12-Mar 11 2021.)

Design: item x month DiD / event study, item + month FE, SE clustered by item, $-weighted by pre-period dollars
(and unweighted), regular-price items only ($1-$150; collector bottles excluded).
  Treated 1: SINGLE MALT SCOTCH
  Treated 2: covered liqueurs (Germany, Ireland, Italy, Spain, UK brands; French liqueurs excluded)
  Placebo  : Republic of Ireland whiskey (EU but not covered) vs the same whisky controls
  Window   : Jul 2018-Dec 2023 ('after' = Mar-Dec 2021, 'after_22_23' = 2022-23: did the step persist?)
  Controls : blended Scotch + American/Canadian whiskies (for 1); American cordials/liqueurs/schnapps (for 2)
Caveats (docs/review_log.md): same importers sell treated and control Scotch (portfolio cost-spreading biases toward 0);
bourbon faced EU/UK retaliation 2018-21; COVID premiumization; "after" = suspension, not repeal.
Pass-through: the tariff is charged on the CUSTOMS value, which is only a fraction of the supplier's price to Iowa
(excise, importer margin, freight are added); see output for the implied pass-through at several customs shares.

Run:  uv run --with duckdb --with pandas --with numpy --with matplotlib --with tabulate python code/04_tariff_2019_scotch.py
"""
import os
import sys
import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from econ import absorb, tsls

DATA_DIR = os.environ.get("IOWA_DATA_DIR", os.path.expanduser("~/mgt634_data/iowa_liquor"))
B = os.path.join(DATA_DIR, "build").replace("\\", "/")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
try:
    sys.path.insert(0, os.path.abspath(os.path.join(OUT, "..", "..", "..", "..")))
    import upshot_style as us
    us.use_style()
except Exception:
    pass

START, END = "2018-07-01", "2023-12-01"        # through 2023: one-time step vs continuing drift
ON, OFF = pd.Timestamp("2019-11-01"), pd.Timestamp("2021-03-01")      # Oct 18 -> Nov is the first full month
BASE0 = pd.Timestamp("2018-10-01")
COVERED_LIQUEUR_BRANDS = ["JAGERMEISTER", "RUMPLE MINZE", "BAILEYS", "CAROLANS", "RYANS", "LICOR 43", "DISARONNO",
                          "FRANGELICO", "APEROL", "CAMPARI", "AVERNA", "ROMANA", "CARAVELLA", "LUXARDO", "GRANGALA",
                          "DRAMBUIE", "FERNET BRANCA", "NONINO"]           # DE, IE, IT, ES, UK (France excluded)
SCOTCH_CTRL = ["SCOTCH WHISKIES", "STRAIGHT BOURBON WHISKIES", "TENNESSEE WHISKIES", "CANADIAN WHISKIES",
               "BLENDED WHISKIES", "STRAIGHT RYE WHISKIES"]
LIQ_CTRL = ["AMERICAN CORDIALS & LIQUEURS", "AMERICAN CORDIALS & LIQUEUR", "AMERICAN SCHNAPPS", "CREAM LIQUEURS",
            "COFFEE LIQUEURS"]

d = duckdb.sql(f"""SELECT m.item_no, m.month, m.bottles, m.dollars, m.price_posted, i.category_name, i.im_desc
                   FROM '{B}/item_month.parquet' m JOIN '{B}/items.parquet' i USING (item_no)
                   WHERE m.month BETWEEN '{START}' AND '{END}' AND m.price_posted BETWEEN 1 AND 150""").df()
d["im_desc"] = d.im_desc.fillna("")
covered_liq = d.im_desc.str.upper().str.contains("|".join(COVERED_LIQUEUR_BRANDS))
d["design"] = np.select(
    [d.category_name == "SINGLE MALT SCOTCH", d.category_name.isin(SCOTCH_CTRL),
     covered_liq, d.category_name.isin(LIQ_CTRL) & ~covered_liq],
    ["scotch_T", "scotch_C", "liq_T", "liq_C"], "drop")
# PLACEBO: Republic of Ireland whiskey (EU, NOT covered in 2019) vs the same whisky controls; Bushmills (N. Ireland = UK) excluded
irish = (d.category_name == "IRISH WHISKIES") & ~d.im_desc.str.upper().str.contains("BUSHMILLS")
d.loc[irish, "design"] = "irish_T"
d = d[d.design != "drop"].copy()
d["log_p"], d["log_q"] = np.log(d.price_posted), np.log(d.bottles)
pre = d[(d.month >= BASE0) & (d.month < ON)]
keep_items = set(pre.item_no) & set(d.loc[(d.month >= ON) & (d.month < OFF), "item_no"])
d = d[d.item_no.isin(keep_items)].copy()
d["w"] = d.item_no.map(pre.groupby("item_no").dollars.sum())

results, ev_store = {}, {}
for label, T, C in [("Single-malt Scotch", "scotch_T", "scotch_C"), ("Covered EU/UK liqueurs", "liq_T", "liq_C"),
                    ("PLACEBO: Irish whiskey (not covered)", "irish_T", "scotch_C")]:
    s = d[d.design.isin([T, C])].copy()
    s["tr"] = (s.design == T).astype(int)
    s["on"] = (s.tr * ((s.month >= ON) & (s.month < OFF))).astype(float)
    s["after"] = (s.tr * ((s.month >= OFF) & (s.month < pd.Timestamp("2022-01-01")))).astype(float)
    s["after_22_23"] = (s.tr * (s.month >= pd.Timestamp("2022-01-01"))).astype(float)
    print(f"{label}: {s[s.tr == 1].item_no.nunique()} treated items, {s[s.tr == 0].item_no.nunique()} controls", flush=True)
    for y in ["log_p", "log_q"]:
        dm, keep, dums = absorb(s, ["item_no", "month"], [y, "on", "after", "after_22_23"])
        for wn, wts in [("unweighted", None), ("$-weighted", s.w.to_numpy()[keep])]:
            r = tsls(dm, y, exog=["on", "after", "after_22_23"], clusters=s.item_no.to_numpy()[keep], controls=dums, weights=wts)
            t = r["table"]
            for k in ["on", "after", "after_22_23"]:
                results[(label, k, y, wn)] = f"{t.loc[k, 'coef']:.4f} ({t.loc[k, 'se']:.4f})"
    # quarterly event study for the figure ($-weighted)
    s["q"] = ((s.month.dt.year - 2019) * 12 + s.month.dt.month - 11) // 3            # 0 = Nov 2019-Jan 2020
    qs = [k for k in sorted(s.q.unique()) if k != -1]
    for k in qs:
        s[f"q{k}"] = ((s.q == k) & (s.tr == 1)).astype(float)
    for y in ["log_p", "log_q"]:
        dm, keep, dums = absorb(s, ["item_no", "month"], [y] + [f"q{k}" for k in qs])
        r = tsls(dm, y, exog=[f"q{k}" for k in qs], clusters=s.item_no.to_numpy()[keep], controls=dums,
                 weights=s.w.to_numpy()[keep])
        t = r["table"].copy(); t["k"] = qs
        ev_store[(label, y)] = pd.concat([t, pd.DataFrame({"coef": [0.0], "se": [0.0], "k": [-1]})]).sort_values("k")

tab = pd.Series(results).unstack([2, 3])
tab.columns = [f"{'log price' if a == 'log_p' else 'log bottles'}, {b}" for a, b in tab.columns]
print("\n", tab.to_string(), flush=True)

# implied pass-through of the 25% tariff for a range of customs-value shares of Iowa's supplier price
scotch_on = float(results[("Single-malt Scotch", "on", "log_p", "$-weighted")].split()[0])
pt = pd.DataFrame({"customs value / Iowa supplier price": [0.3, 0.4, 0.5, 0.6, 1.0]})
pt["full pass-through would raise Iowa price by %"] = 25 * pt.iloc[:, 0]
pt["implied pass-through %"] = (np.expm1(scotch_on) * 100 / pt.iloc[:, 1] * 100).round(0)
print("\nImplied pass-through (single malt, $-weighted 'on' estimate):\n", pt.to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.3))
for ax, (y, lab) in zip(axes, [("log_p", "Posted Iowa price (log points)"), ("log_q", "Bottles (log points)")]):
    ax.axhline(0, color="#999999", lw=1)
    ax.axvspan(-0.5, 5.5, color="#fbebb7", alpha=0.6, label="25% tariff in force (Nov 2019-Feb 2021)")
    for (label, c, off) in [("Single-malt Scotch", "#993f2a", -0.15), ("Covered EU/UK liqueurs", "#2b6cb0", 0.0),
                            ("PLACEBO: Irish whiskey (not covered)", "#999999", 0.15)]:
        e = ev_store[(label, y)]
        ax.errorbar(e.k + off, e.coef, yerr=1.96 * e.se, fmt="o-", color=c, capsize=2, lw=1.3, ms=4, label=label)
    ax.set_title(lab, loc="left"); ax.set_xlabel("Quarters relative to Nov 2019"); ax.tick_params(labelbottom=True, labelleft=True)
axes[0].legend(loc="lower left", fontsize=7.5, framealpha=0.95)
fig.suptitle("2019 Airbus tariffs in Iowa: treated vs untariffed products ($-weighted, item + month FE, 95% CI)", x=0.01, ha="left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_tariff2019_event_study.png"), dpi=150)

with open(os.path.join(OUT, "tariff2019_results.md"), "w", encoding="utf-8") as f:
    f.write("# 2019-21 Airbus tariffs in Iowa (auto-generated by code/04_tariff_2019_scotch.py, v2)\n\n")
    f.write("Item + month FE; SE clustered by item; regular-price items ($1-150) sold before and during the tariff. "
            "'on' = Nov 2019-Feb 2021, 'after' = Mar-Dec 2021 (suspension), 'after_22_23' = Jan 2022-Dec 2023. "
            "PLACEBO = Republic of Ireland whiskey (EU, not covered in 2019) vs the whisky controls.\n\n")
    f.write(tab.to_markdown() + "\n\n## Implied pass-through of the 25% tariff (single malt)\n\n" + pt.to_markdown(index=False) +
            "\n\nThe customs value share is not yet measured (needs Census trade data; see docs/project_plan.md).\n")
print("Saved output/tariff2019_results.md and figure")
