"""
08_nested_logit.py: nested logit demand following the professor's class-20 spec (Quan & Williams national NL),
adapted to Iowa (notes/class20-zappos-lab-2026-11-17.md, "Estimation 3"):

  j = item (product x size); m = Iowa x month (prices are uniform statewide); 2019-01 .. 2026-10
  Shares in LITERS (so 50 ml nips do not dominate); market size M = ADULTS_21 x L_PER_ADULT liters/month (assumption,
      reported with a robustness grid)
  Choice set: an item is available from its first to its last month with a sale; zero months get 0.17 bottles
  Nests g = spirit type (nests.nest_of); outside good = its own nest
  ln s_j - ln s_0 = x b + alpha * price_per_liter + lambda * ln s_{j|g} + xi
  Endogenous: price per liter, ln s_{j|g}
  x: proof, imported, flavored, bottle-size class, nest x cold-season (Sep-Feb) dummies
  Brand(vendor)-group fixed effects by demeaning (vendors with >= 20k liters/month get their own group, rest pooled);
      NO month FE (spec pitfall: month / nest x month FE wipe out the variation that identifies lambda)
  Instruments (BLP-style, vary at nest-month): own-vendor # of items in the nest; RIVAL-vendor sums and averages of
      characteristics (proof, imported, size) and counts in the nest-month
Checks: price coefficient < 0, 0 <= lambda < 1, first-stage partial F (homoskedastic and cluster-robust) and partial R2.

Run:  uv run --with duckdb --with pandas --with numpy --with tabulate python code/08_nested_logit.py
"""
import os
import re
import sys
import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from econ import absorb, tsls, cluster_F
from nests import nest_of, origin_of

DATA_DIR = os.environ.get("IOWA_DATA_DIR", os.path.expanduser("~/mgt634_data/iowa_liquor"))
B = os.path.join(DATA_DIR, "build").replace("\\", "/")
RAW = os.path.join(DATA_DIR, "raw").replace("\\", "/")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
ADULTS_21 = 2.35e6                 # Iowa population 21+ (approx., ~73% of 3.2M); assumption
L_PER_ADULT = 2.0                  # potential liters per adult per month -> inside share ~0.4-0.5
ZERO_BOTTLES = 0.17

# ---------- data ----------
d = duckdb.sql(f"""SELECT m.item_no, m.month, m.bottles, m.liters, m.price_posted AS price, i.category_name, i.vendor_name,
                          i.im_desc, i.ml
                   FROM '{B}/item_month.parquet' m JOIN '{B}/items.parquet' i USING (item_no)
                   WHERE m.month BETWEEN '2019-01-01' AND '2026-10-01' AND i.ml > 0""").df()
d["category_name"] = d.category_name.fillna("UNKNOWN")
d["vendor_name"] = d.vendor_name.fillna("UNKNOWN")                       # blank vendors would become NaN groups
d["im_desc"] = d.im_desc.fillna("")
d = d[~d.category_name.isin(["TEMPORARY & SPECIALTY PACKAGES", "SPECIAL ORDER ITEMS", "DELISTED / SPECIAL ORDER ITEMS"])]
d["ppl"] = d.price / (d.ml / 1000)                                         # price per liter
d = d[(d.price.between(1, 150)) & (d.ppl.between(2, 400))].copy()

# characteristics: proof from the state price list (current snapshot); missing -> category median
prod = pd.read_csv(f"{RAW}/products/iowa_liquor_products_1029_rows.csv", dtype={"item_no": str},
                   usecols=["item_no", "proof", "age"]).drop_duplicates("item_no")
d["item_no"] = d.item_no.astype(str)
d = d.merge(prod, on="item_no", how="left", validate="many_to_one")
print(f"Proof from price list for {d.proof.notna().mean():.0%} of item-months "
      f"({d.loc[d.proof.notna(), 'liters'].sum() / d.liters.sum():.0%} of liters); rest = category median", flush=True)
d["proof"] = d.proof.where(d.proof > 0).fillna(d.groupby("category_name").proof.transform("median")).fillna(80)
items = d.drop_duplicates("item_no")[["item_no", "category_name", "vendor_name", "im_desc", "ml", "proof"]].copy()
items["nest"] = items.category_name.map(nest_of)
items["imported"] = [int(origin_of(a, c) in ("UK", "EU", "Other")) for a, c in zip(items.im_desc, items.category_name)]
items["flavored"] = (items.category_name.str.contains("FLAVORED") | items.im_desc.str.contains(
    r"FLAVOR|CHERRY|PEACH|APPLE|VANILLA|CINNAMON|HONEY|BERRY|LIME|LEMON|MANGO|COCONUT", regex=True, na=False)).astype(int)
items["size"] = pd.cut(items.ml, [0, 200, 400, 800, 1100, 1e9], labels=["mini", "375", "750", "1L", "1.75L"]).astype(str)

# ---------- choice set: first -> last month with a sale; fill zero months ----------
span = d.groupby("item_no").month.agg(["min", "max"])
months = pd.date_range("2019-01-01", "2026-10-01", freq="MS")
grid = span.reset_index().merge(pd.DataFrame({"month": months}), how="cross")
grid = grid[(grid.month >= grid["min"]) & (grid.month <= grid["max"])][["item_no", "month"]]
p = grid.merge(d[["item_no", "month", "liters", "price", "ppl"]], on=["item_no", "month"], how="left").merge(items, on="item_no")
zero = p.liters.isna()
p["liters"] = p.liters.fillna(ZERO_BOTTLES * p.ml / 1000)
p = p.sort_values(["item_no", "month"])
for c in ["price", "ppl"]:
    p[c] = p.groupby("item_no")[c].ffill(); p[c] = p.groupby("item_no")[c].bfill()
print(f"Choice set: {len(p):,} item-months, {p.item_no.nunique():,} items; zero-sale months {zero.mean():.1%}", flush=True)

# ---------- shares ----------
M = ADULTS_21 * L_PER_ADULT
p["s"] = p.liters / M
p["s0"] = 1 - p.groupby("month").liters.transform("sum") / M
p["s_g"] = p.groupby(["month", "nest"]).s.transform("sum")
p["y"] = np.log(p.s) - np.log(p.s0)
p["ln_s_jg"] = np.log(p.s / p.s_g)
print(f"Market size M = {M:,.0f} liters/month; outside share {p.s0.min():.2f}-{p.s0.max():.2f}", flush=True)

# ---------- instruments (vary at nest x month): own-vendor count, rival-vendor sums/averages ----------
gm, gv = p.groupby(["month", "nest"]), p.groupby(["month", "nest", "vendor_name"])
n_all, n_own = gm.item_no.transform("size"), gv.item_no.transform("size")
p["z_own_cnt"] = n_own
p["z_rival_cnt"] = n_all - n_own
Z = ["z_own_cnt", "z_rival_cnt"]
for c in ["proof", "imported", "ml"]:
    p[f"z_rival_sum_{c}"] = gm[c].transform("sum") - gv[c].transform("sum")
    p[f"z_rival_avg_{c}"] = p[f"z_rival_sum_{c}"] / p.z_rival_cnt.clip(lower=1)
    Z += [f"z_rival_sum_{c}", f"z_rival_avg_{c}"]

# ---------- controls ----------
p["cold"] = p.month.dt.month.isin([9, 10, 11, 12, 1, 2]).astype(int)
p["nest_cold"] = p.nest + "_" + p.cold.astype(str)
big = p.groupby("vendor_name").liters.sum() / p.month.nunique() >= 20000
p["brand_grp"] = np.where(p.vendor_name.map(big), p.vendor_name, "SMALL")
X = ["proof", "imported", "flavored"]
bad = {c: int(p[c].isna().sum() + np.isinf(p[c]).sum()) for c in ["y", "ppl", "ln_s_jg"] + X + Z}
bad = {k: v for k, v in bad.items() if v}
if bad:
    print("Dropping rows with missing/inf values:", bad, flush=True)
    p = p.replace([np.inf, -np.inf], np.nan).dropna(subset=["y", "ppl", "ln_s_jg"] + X + Z).reset_index(drop=True)
dm, keep, dums = absorb(p, ["brand_grp"], ["y", "ppl", "ln_s_jg"] + X + Z, dummy_cols=["size", "nest_cold"], drop_singletons=False)
kept = p[keep].reset_index(drop=True)
cl = kept.item_no.to_numpy()

out = []
for name, kw in [("Nested OLS", dict(exog=["ppl", "ln_s_jg"] + X)),
                 ("Nested 2SLS (rival-vendor IVs)", dict(exog=X, endog=["ppl", "ln_s_jg"], instruments=Z))]:
    r = tsls(dm, "y", clusters=cl, controls=dums, **kw)
    t = r["table"]
    a, lam = t.loc["ppl", "coef"], t.loc["ln_s_jg", "coef"]
    e = a * kept.ppl * (1 / (1 - lam) - lam / (1 - lam) * kept.s / kept.s_g - kept.s)
    row = {"model": name, "price/liter coef": round(a, 4), "SE": round(t.loc["ppl", "se"], 4), "lambda": round(lam, 3),
           "lambda SE": round(t.loc["ln_s_jg", "se"], 3), "elasticity mean": round(e.mean(), 2),
           "elasticity median": round(e.median(), 2), "N": r["n"], "brand groups": kept.brand_grp.nunique()}
    if "endog" in kw:
        fs = r["first_stage"]
        row["partial R2 (price, nest)"] = f"{fs.loc['ppl', 'partial_R2']:.3f}, {fs.loc['ln_s_jg', 'partial_R2']:.3f}"
        row["F homosk. (price, nest)"] = f"{fs.loc['ppl', 'partial_F']:.0f}, {fs.loc['ln_s_jg', 'partial_F']:.0f}"
        cl_nm = (kept.month.astype(str) + kept.nest).to_numpy()            # instruments vary at nest-month
        row["F cluster nest-month (price, nest)"] = (f"{cluster_F(dm, 'ppl', Z, X + dums, cl_nm):.1f}, "
                                                    f"{cluster_F(dm, 'ln_s_jg', Z, X + dums, cl_nm):.1f}")
    out.append(row); print(row, flush=True)
res = pd.DataFrame(out)
valid = (res["price/liter coef"] < 0) & (res["lambda"] >= 0) & (res["lambda"] < 1)
res["valid (alpha<0, 0<=lambda<1)"] = valid
print("\n" + res.to_string(index=False))
with open(os.path.join(OUT, "nested_logit.md"), "w", encoding="utf-8") as f:
    f.write("# Nested logit, professor's class-20 spec adapted to Iowa (auto-generated by code/08_nested_logit.py)\n\n")
    f.write(f"Iowa x month markets 2019-01..2026-10; liters shares, M = {M:,.0f} liters/month; choice set first-to-last sale with "
            f"0.17-bottle zeros ({zero.mean():.1%} of item-months); brand(vendor)-group demeaning; size and nest x cold dummies; "
            "no month FE. Instruments: own-vendor item count and rival-vendor counts, sums and averages of proof/imported/size "
            "within nest-month. SE clustered by item.\n\n")
    f.write(res.to_markdown(index=False))
