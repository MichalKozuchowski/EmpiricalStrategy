"""
09_counterfactuals.py: policy counterfactuals for Iowa's liquor pricing, from a calibrated nested logit.

Policies (Iowa Code 123.24 today: state price = manufacturer's price x 1.5):
  (A) HF 830 (2025, died in committee): MINIMUM UNIT PRICE of $0.50 per 18 ml of alcohol; the 50% markup applies to the
      greater of the manufacturer's price and that floor -> new state price = 1.5 x max(cost, MUP).
  (B) Revenue-neutral ALCOHOL-BASED markup: replace the 50% ad-valorem markup with $t per liter of pure alcohol, t chosen
      so the state's margin is unchanged (taxes alcohol, not price; same money for the state).
  (C) For reference: uniform markups of 30%, 70%.

Demand model (calibrated, see docs): nested logit with log price, nests = spirit type, Iowa x month market.
  * own-price elasticity fixed at the within-item estimate (code/05: -0.63; event study code/07: -0.3 to -0.6)
  * sigma (within-nest correlation) is NOT credibly identified in our data (08: invalid), so every result is shown for
    sigma in {0, 0.5, 0.8}, and market size M in {1.5x, 2x, 3x observed liters} (outside share 0.33-0.67)
  * baseline = average month Nov 2025 - Oct 2026; base utilities are inverted from observed liter shares
Outcomes: liters, pure-alcohol liters, state margin ($/yr), supplier revenue, consumer cost (rule-of-half), by nest and
price tier.

Run:  uv run --with duckdb --with pandas --with numpy --with tabulate python code/09_counterfactuals.py
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
OWN_ELAST = -0.63
MUP_PER_18ML = 0.50

# ---------- baseline: average month over the last 12 months ----------
b = duckdb.sql(f"""SELECT m.item_no, SUM(m.bottles)/12 AS bottles, SUM(m.dollars)/SUM(m.bottles) AS price,
                          ANY_VALUE(i.category_name) AS category_name, ANY_VALUE(i.im_desc) AS im_desc, ANY_VALUE(i.ml) AS ml
                   FROM '{B}/item_month.parquet' m JOIN '{B}/items.parquet' i USING (item_no)
                   WHERE m.month BETWEEN '2025-11-01' AND '2026-10-01' AND i.ml > 0
                   GROUP BY 1""").df()
b["item_no"] = b.item_no.astype(str)
prod = pd.read_csv(f"{RAW}/products/iowa_liquor_products_1029_rows.csv", dtype={"item_no": str},
                   usecols=["item_no", "proof"]).drop_duplicates("item_no")
b = b.merge(prod, on="item_no", how="left", validate="one_to_one")
b["category_name"] = b.category_name.fillna("UNKNOWN")
b["proof"] = b.proof.where(b.proof > 0).fillna(b.groupby("category_name").proof.transform("median")).fillna(80)
b = b[(b.price > 0.5) & (b.bottles > 0)].copy()
b["nest"] = b.category_name.map(nest_of)
b["liters"] = b.bottles * b.ml / 1000
b["cost"] = b.price / 1.5                                               # Iowa: price = 1.5 x manufacturer's price
b["alc_l_per_bottle"] = b.ml / 1000 * b.proof / 200                     # liters of pure alcohol per bottle
b["mup"] = MUP_PER_18ML * (b.alc_l_per_bottle * 1000 / 18)              # HF 830 floor on the base, $ per bottle
b["price_per_l"] = b.price / (b.ml / 1000)
b["tier"] = pd.qcut(b.price_per_l, 4, labels=["Q1 cheapest/L", "Q2", "Q3", "Q4 priciest/L"])
print(f"Baseline month: {len(b):,} items, {b.liters.sum():,.0f} liters, state margin ${(b.price - b.cost).mul(b.bottles).sum()*12/1e6:,.1f}M/yr; "
      f"HF 830 floor binds for {(b.mup > b.cost).mean():.0%} of items / {b.loc[b.mup > b.cost, 'liters'].sum() / b.liters.sum():.0%} of liters", flush=True)


def shares(delta, nest_codes, sigma, n_nests):
    """Nested logit shares (liters) given mean utilities delta."""
    lam = 1 - sigma
    e = np.exp(delta / lam)
    D = np.bincount(nest_codes, weights=e, minlength=n_nests)
    denom = 1 + (D ** lam).sum()
    return e / D[nest_codes] * D[nest_codes] ** lam / denom, D


def simulate(newprice, sigma, Mmult):
    """Return outcomes at newprice for a model calibrated to the baseline with given sigma and market size."""
    nc, nn = pd.factorize(b.nest)[0], b.nest.nunique()
    M = Mmult * b.liters.sum()
    s = b.liters.to_numpy() / M
    s0 = 1 - s.sum()
    s_g = np.bincount(nc, weights=s, minlength=nn)[nc]
    delta = np.log(s / s0) - sigma * np.log(s / s_g)                    # Berry nested-logit inversion
    own = (1 / (1 - sigma) - sigma / (1 - sigma) * s / s_g - s)
    alpha = -OWN_ELAST / np.average(own, weights=b.liters)              # matches the estimated own elasticity
    base_utility = delta + alpha * np.log(b.price.to_numpy())
    s1, _ = shares(base_utility - alpha * np.log(newprice), nc, sigma, nn)
    liters1 = s1 * M
    bottles1 = liters1 / (b.ml.to_numpy() / 1000)
    return bottles1


def outcomes(name, newprice, newcost, sigma, Mmult):
    q0, p0, c0 = b.bottles.to_numpy(), b.price.to_numpy(), b.cost.to_numpy()
    q1 = simulate(newprice, sigma, Mmult)
    alc = b.alc_l_per_bottle.to_numpy()
    return {"policy": name, "sigma": sigma, "M (x liters)": Mmult,
            "liters %": (q1 @ (b.ml / 1000) / (q0 @ (b.ml / 1000)) - 1) * 100,
            "pure alcohol %": ((q1 @ alc) / (q0 @ alc) - 1) * 100,
            "state margin $M/yr": ((newprice - newcost) @ q1 - (p0 - c0) @ q0) * 12 / 1e6,
            "supplier revenue $M/yr": (newcost @ q1 - c0 @ q0) * 12 / 1e6,
            "buyer cost $M/yr (rule of half)": (0.5 * (q0 + q1) @ (newprice - p0)) * 12 / 1e6}


cost = b.cost.to_numpy()
margin0 = ((b.price - b.cost) * b.bottles).sum()
rows = []
for sigma in [0.0, 0.5, 0.8]:
    for Mmult in [1.5, 2.0, 3.0]:
        # (A) HF 830 minimum unit price
        base = np.maximum(cost, b.mup.to_numpy())
        rows.append(outcomes("A: HF 830 min. unit price", 1.5 * base, cost, sigma, Mmult))
        # (B) revenue-neutral alcohol-based markup: price = cost + t * alcohol liters; solve t so the margin is unchanged
        alc = b.alc_l_per_bottle.to_numpy()

        def gap(t):
            p = cost + t * alc
            q1 = simulate(p, sigma, Mmult)
            return (p - cost) @ q1 - margin0
        t = brentq(gap, 1, 500)
        r = outcomes(f"B: alcohol markup (${t:.0f}/L pure alcohol)", cost + t * alc, cost, sigma, Mmult)
        rows.append(r)
        for m in [0.3, 0.7]:
            rows.append(outcomes(f"C: uniform {int(m*100)}% markup", (1 + m) * cost, cost, sigma, Mmult))
res = pd.DataFrame(rows).round(1)
print(res.to_string(index=False), flush=True)

# who is hit by HF 830 (sigma 0.5, M 2x): price change by tier and nest
base = np.maximum(cost, b.mup.to_numpy())
newp = 1.5 * base
q1 = simulate(newp, 0.5, 2.0)
hit = b.assign(new_price=newp, pct_price=(newp / b.price - 1) * 100, q1=q1)
by = lambda col: hit.groupby(col, observed=True).apply(lambda g: pd.Series({
    "baseline liters/yr (k)": g.liters.sum() * 12 / 1e3,
    "avg price change %": np.average(g.pct_price, weights=g.liters),
    "liters change %": (g.q1 @ (g.ml / 1000) / g.liters.sum() - 1) * 100}), include_groups=False).round(1)
tiers, nests = by("tier"), by("nest")
print("\nHF 830 (sigma=0.5, M=2x) by price tier:\n", tiers.to_string(), "\n\nby spirit type:\n", nests.to_string())
examples = hit.sort_values("liters", ascending=False).head(12)[["im_desc", "ml", "proof", "price", "new_price", "pct_price"]].round(2)
print("\nTop sellers under HF 830:\n", examples.to_string(index=False))

with open(os.path.join(OUT, "counterfactuals.md"), "w", encoding="utf-8") as f:
    f.write("# Policy counterfactuals (auto-generated by code/09_counterfactuals.py)\n\n")
    f.write("Calibrated nested logit: own-price elasticity -0.63 (code/05), sigma and market size varied (not identified). "
            "Baseline = average month Nov 2025-Oct 2026, annualized. Buyer cost uses the rule of half.\n\n")
    f.write(res.to_markdown(index=False))
    f.write("\n\n## HF 830 incidence (sigma = 0.5, M = 2x)\n\nBy price tier (price per liter quartiles):\n\n" + tiers.to_markdown())
    f.write("\n\nBy spirit type:\n\n" + nests.to_markdown() + "\n\nTop sellers:\n\n" + examples.to_markdown(index=False))
print("Saved output/counterfactuals.md")
