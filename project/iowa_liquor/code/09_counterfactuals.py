"""
09_counterfactuals.py: policy counterfactuals for Iowa's liquor pricing (v2, after the second independent review).

Policies (today, Iowa Code 123.24: state price = manufacturer's price x 1.5):
  (A) HF 830 (2025, died in committee): MINIMUM UNIT PRICE $0.50 per 18 ml of pure alcohol; the state price becomes
      max(manufacturer price, MUP) + 50% of that max = 1.5 x max(c, MUP).
      Two SUPPLIER responses, which give the SAME shelf prices and quantities but split the money differently:
        A1 suppliers keep their list prices -> the floor gap goes to the state
        A2 suppliers raise list prices up to the floor where it binds (their price no longer moves the shelf price)
           -> the floor gap goes to SUPPLIERS (the classic minimum-unit-price windfall)
  (B) Revenue-neutral ALCOHOL-BASED markup: state price = c + $t per liter of pure alcohol, t solved so the state's
      margin is unchanged. No windfall: the price still moves 1:1 with the supplier's price.
Demand: calibrated nested logit with log price; nests = spirit type; Iowa x month market; base utilities inverted from
observed liter shares (baseline = average month Nov 2025-Oct 2026). Own-price elasticity is NOT a known number:
  -0.31 to -0.47 (code/07, price INCREASES, the relevant direction), -0.63 (code/05 logit), -1.0 (literature-style)
sigma (within-nest correlation) and market size M are not identified (08 invalid) -> results are reported as a RANGE
("fan") over sigma in {0, .5, .8} and M in {1.5, 2, 3} x observed liters. +60-160% price changes are extrapolations.
Cross-border leakage: floor-bound items sold in border counties; losing 10/25/50% of that volume is shown separately.
"Store spending" = extra wholesale dollars paid by stores (a proxy for what buyers pay), NOT consumer surplus.

Run:  uv run --with duckdb --with pandas --with numpy --with scipy --with tabulate python code/09_counterfactuals.py
"""
import os
import sys
import duckdb
import numpy as np
import pandas as pd
from scipy.optimize import brentq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nests import nest_of

DATA_DIR = os.environ.get("IOWA_DATA_DIR", os.path.expanduser("~/mgt634_data/iowa_liquor"))
B = os.path.join(DATA_DIR, "build").replace("\\", "/")
RAW = os.path.join(DATA_DIR, "raw").replace("\\", "/")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
MUP_PER_18ML = 0.50
ELASTICITIES = [-0.4, -0.63, -1.0]
SIGMAS, MMULTS = [0.0, 0.5, 0.8], [1.5, 2.0, 3.0]
BORDER = ["LYON", "OSCEOLA", "DICKINSON", "EMMET", "KOSSUTH", "WINNEBAGO", "WORTH", "MITCHELL", "HOWARD", "WINNESHIEK",
          "ALLAMAKEE", "CLAYTON", "DUBUQUE", "JACKSON", "CLINTON", "SCOTT", "MUSCATINE", "LOUISA", "DES MOINES", "LEE",
          "VAN BUREN", "DAVIS", "APPANOOSE", "WAYNE", "DECATUR", "RINGGOLD", "TAYLOR", "PAGE", "FREMONT", "MILLS",
          "POTTAWATTAMIE", "HARRISON", "MONONA", "WOODBURY", "PLYMOUTH", "SIOUX"]   # counties on a state line

# ---------- baseline: average month, Nov 2025 - Oct 2026 ----------
b = duckdb.sql(f"""SELECT m.item_no, SUM(m.bottles)/12 AS bottles, SUM(m.dollars)/SUM(m.bottles) AS price,
                          ANY_VALUE(i.category_name) AS category_name, ANY_VALUE(i.im_desc) AS im_desc, ANY_VALUE(i.ml) AS ml
                   FROM '{B}/item_month.parquet' m JOIN '{B}/items.parquet' i USING (item_no)
                   WHERE m.month BETWEEN '2025-11-01' AND '2026-10-01' AND i.ml > 0 GROUP BY 1""").df()
border_share = duckdb.sql(f"""SELECT item_no, SUM(CASE WHEN upper(county_name) IN ({", ".join(f"'{c}'" for c in BORDER)})
                                     THEN bottles ELSE 0 END) / SUM(bottles) AS border_share
                              FROM '{B}/county_item_month.parquet' WHERE month BETWEEN '2025-11-01' AND '2026-10-01'
                              GROUP BY 1""").df()
b["item_no"] = b.item_no.astype(str); border_share["item_no"] = border_share.item_no.astype(str)
prod = pd.read_csv(f"{RAW}/products/iowa_liquor_products_1029_rows.csv", dtype={"item_no": str},
                   usecols=["item_no", "proof"]).drop_duplicates("item_no")
b = b.merge(prod, on="item_no", how="left", validate="one_to_one").merge(border_share, on="item_no", how="left")
b["category_name"] = b.category_name.fillna("UNKNOWN")
b["proof"] = b.proof.where(b.proof > 0).fillna(b.groupby("category_name").proof.transform("median")).fillna(80)
b = b[(b.price > 0.5) & (b.bottles > 0)].copy()
b["nest"] = b.category_name.map(nest_of)
b["liters"] = b.bottles * b.ml / 1000
b["cost"] = b.price / 1.5
b["alc"] = b.ml / 1000 * b.proof / 200                                 # liters of pure alcohol per bottle
b["mup"] = MUP_PER_18ML * b.alc * 1000 / 18                            # HF 830 floor, $ per bottle (before markup)
b["price_per_l"] = b.price / (b.ml / 1000)
b["tier"] = pd.qcut(b.price_per_l, 4, labels=["Q1 cheapest/L", "Q2", "Q3", "Q4 priciest/L"])
cost, alc, mup, p0, q0 = (b[c].to_numpy() for c in ["cost", "alc", "mup", "price", "bottles"])
margin0 = (p0 - cost) @ q0
binds = mup > cost
print(f"Baseline: {len(b):,} items, {b.liters.sum()*12/1e6:.1f}M liters/yr, state margin ${margin0*12/1e6:.1f}M/yr; "
      f"HF 830 floor binds for {binds.mean():.0%} of items / {b.liters[binds].sum()/b.liters.sum():.0%} of liters", flush=True)

nc, nn = pd.factorize(b.nest)[0], b.nest.nunique()


def simulate(newprice, sigma, Mmult, own_elast):
    """Bottles at newprice from a nested logit calibrated to the baseline (log price utility)."""
    lam = 1 - sigma
    M = Mmult * b.liters.sum()
    s = b.liters.to_numpy() / M
    s0 = 1 - s.sum()
    s_g = np.bincount(nc, weights=s, minlength=nn)[nc]
    delta = np.log(s / s0) - sigma * np.log(s / s_g)                   # Berry nested-logit inversion
    own = 1 / lam - sigma / lam * s / s_g - s
    alpha = -own_elast / np.average(own, weights=b.liters)
    u = delta + alpha * np.log(p0) - alpha * np.log(newprice)
    e = np.exp(u / lam)
    D = np.bincount(nc, weights=e, minlength=nn)
    s1 = e / D[nc] * D[nc] ** lam / (1 + (D ** lam).sum())
    return s1 * M / (b.ml.to_numpy() / 1000)


def outcome(newprice, newcost, q1):
    return {"pure alcohol %": ((q1 @ alc) / (q0 @ alc) - 1) * 100,
            "state margin $M/yr": ((newprice - newcost) @ q1 - margin0) * 12 / 1e6,
            "supplier revenue $M/yr": (newcost @ q1 - cost @ q0) * 12 / 1e6,
            "store spending $M/yr": (newprice @ q1 - p0 @ q0) * 12 / 1e6}


p_mup = 1.5 * np.maximum(cost, mup)
cost_A2 = np.maximum(cost, mup)                                         # suppliers price up to the floor
rows = []
for el in ELASTICITIES:
    for sg in SIGMAS:
        for mm in MMULTS:
            q_mup = simulate(p_mup, sg, mm, el)
            rows.append({"policy": "A1 HF 830, suppliers keep prices", "elasticity": el, "sigma": sg, "M": mm, **outcome(p_mup, cost, q_mup)})
            rows.append({"policy": "A2 HF 830, suppliers price up to floor", "elasticity": el, "sigma": sg, "M": mm, **outcome(p_mup, cost_A2, q_mup)})
            t = brentq(lambda t: (cost + t * alc - cost) @ simulate(cost + t * alc, sg, mm, el) - margin0, 1, 500)
            q_b = simulate(cost + t * alc, sg, mm, el)
            rows.append({"policy": "B alcohol markup (rev.-neutral)", "elasticity": el, "sigma": sg, "M": mm,
                         "t $/L alcohol": t, **outcome(cost + t * alc, cost, q_b)})
full = pd.DataFrame(rows)
full.round(2).to_csv(os.path.join(OUT, "counterfactuals_full.csv"), index=False)
fan = (full.groupby(["policy", "elasticity"])[["pure alcohol %", "state margin $M/yr", "supplier revenue $M/yr", "store spending $M/yr"]]
       .agg(["min", "max"]).round(1))
fan.columns = [f"{a} [{b}]" for a, b in fan.columns]
print("\nRANGE over sigma x market size, by policy and elasticity:\n", fan.to_string(), flush=True)

# no-response upper bound for HF 830 state revenue (quantities fixed)
ub = ((p_mup - cost) @ q0 - margin0) * 12 / 1e6
ub_A2 = ((p_mup - cost_A2) @ q0 - margin0) * 12 / 1e6
# cross-border leakage: share of floor-bound volume sold in border counties that could leave the state
bound_border_margin = ((p_mup - cost)[binds] * q0[binds] * b.border_share.fillna(0).to_numpy()[binds]).sum() * 12 / 1e6
leak = pd.DataFrame({"leakage of floor-bound border volume": ["10%", "25%", "50%"],
                     "lost state margin $M/yr (A1)": [round(bound_border_margin * x, 1) for x in [0.1, 0.25, 0.5]]})
print(f"\nHF 830 state gain if quantities did not respond: A1 ${ub:.0f}M/yr, A2 ${ub_A2:.0f}M/yr (upper bounds)")
print(f"Floor-bound items: border-county share of their post-floor margin = ${bound_border_margin:.0f}M/yr\n", leak.to_string(index=False))

# who is hit (elasticity -0.63, sigma 0.5, M 2x)
q_mid = simulate(p_mup, 0.5, 2.0, -0.63)
hit = b.assign(new_price=p_mup, pct_price=(p_mup / p0 - 1) * 100, q1=q_mid)
summ = lambda g: pd.Series({"liters/yr (M)": g.liters.sum() * 12 / 1e6, "avg price change %": np.average(g.pct_price, weights=g.liters),
                            "liters change %": (g.q1 @ (g.ml / 1000) / g.liters.sum() - 1) * 100})
tiers = hit.groupby("tier", observed=True).apply(summ, include_groups=False).round(1)
nests = hit.groupby("nest").apply(summ, include_groups=False).round(1)
examples = hit.sort_values("liters", ascending=False).head(10)[["im_desc", "ml", "proof", "price", "new_price", "pct_price"]].round(2)
print("\nHF 830 by price tier (el -0.63, sigma .5, M 2x):\n", tiers.to_string(), "\n", examples.to_string(index=False))

with open(os.path.join(OUT, "counterfactuals.md"), "w", encoding="utf-8") as f:
    f.write("# Policy counterfactuals (auto-generated by code/09_counterfactuals.py, v2)\n\n")
    f.write(f"Baseline (Nov 2025-Oct 2026): state margin ${margin0*12/1e6:.0f}M/yr. HF 830 floor binds for "
            f"{binds.mean():.0%} of items and {b.liters[binds].sum()/b.liters.sum():.0%} of liters.\n\n")
    f.write("## Ranges over sigma {0,.5,.8} x market size {1.5,2,3}x, by policy and own-price elasticity\n\n" + fan.to_markdown() + "\n\n")
    f.write(f"**Upper bound (no quantity response):** HF 830 state gain ${ub:.0f}M/yr if suppliers keep prices (A1), "
            f"${ub_A2:.0f}M/yr if they price up to the floor (A2); the rest goes to suppliers.\n\n")
    f.write("## Cross-border leakage sensitivity\n\n" + leak.to_markdown(index=False) + "\n\n")
    f.write("## HF 830 incidence (elasticity -0.63, sigma 0.5, M 2x)\n\n" + tiers.to_markdown() + "\n\n" + nests.to_markdown() +
            "\n\nTop sellers:\n\n" + examples.to_markdown(index=False) + "\n\n'Store spending' = extra wholesale dollars paid by "
            "stores (proxy for buyers' cost), not consumer surplus. Price changes of +60-160% are far outside the estimation "
            "range: treat as extrapolation.\n")
print("Saved output/counterfactuals.md and counterfactuals_full.csv")
