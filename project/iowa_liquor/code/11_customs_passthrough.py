"""
11_customs_passthrough.py: turn the 2019 Iowa price effect (04) into an exact pass-through rate, using US customs data.

The 25% Airbus tariff was charged on the CUSTOMS value (the importer's declared price at the border), which is only part
of what Iowa pays the supplier. To know what share of the tariff reached Iowa we need that customs value.

Source: US Census Bureau International Trade API, imports by HS10 x country x month x RATE PROVISION.
  * HS 2208.30.3030 = Scotch & Irish whisky, containers <= 4 L (single malt is not a separate code), from the UK.
    Only single malt paid the tariff, so the DUTIABLE lines (rate provision 69 = Chapter 99 duty) ARE the single malts:
    their value / proof liters = customs value per proof liter of single malt; duty / value = the effective tariff rate.
  * HS 2208.70.0030 = liqueurs & cordials, containers <= 4 L, from Germany, Ireland, Italy, Spain, UK.
  Quantities are in proof liters (PFL: 1 liter at 100 US proof = 0.5 liter of pure alcohol).

Pass-through (in dollars per proof liter, tariff period Nov 2019-Feb 2021):
  duty per PFL          = tariff rate x customs value per PFL
  Iowa supplier cost    = Iowa price / 1.5, per PFL of the treated items (pre-period, $-weighted)
  rise in supplier cost = (exp(beta) - 1) x supplier cost      (beta = 'on' estimate from 04, $-weighted)
  pass-through          = rise in supplier cost / duty per PFL
Iowa's 50% markup then multiplies the cost rise by 1.5 for the price buyers pay.

API key: env var CENSUS_API_KEY, or a text file census_api_key.txt in IOWA_DATA_DIR (kept OUT of git).
Run:  uv run --with duckdb --with pandas --with numpy --with matplotlib --with requests --with tabulate python code/11_customs_passthrough.py
"""
import os
import sys
import json
import duckdb
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nests import COVERED_LIQUEUR_BRANDS

DATA_DIR = os.environ.get("IOWA_DATA_DIR", os.path.expanduser("~/mgt634_data/iowa_liquor"))
B = os.path.join(DATA_DIR, "build").replace("\\", "/")
RAW = os.path.join(DATA_DIR, "raw").replace("\\", "/")
CACHE = os.path.join(DATA_DIR, "census"); os.makedirs(CACHE, exist_ok=True)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
try:
    sys.path.insert(0, os.path.abspath(os.path.join(OUT, "..", "..", "..", "..")))
    import upshot_style as us
    us.use_style()
except Exception:
    pass

ON0, ON1 = "2019-11", "2021-02"                      # tariff in force (first full month .. last full month)
COUNTRIES = {"4120": "United Kingdom", "4280": "Germany", "4190": "Ireland", "4759": "Italy", "4700": "Spain"}
PFL_PER_750_86 = 0.75 * 0.86                          # proof liters in a 750 ml bottle at 86 proof (43% ABV)


def census_key():
    k = os.environ.get("CENSUS_API_KEY")
    p = os.path.join(DATA_DIR, "census_api_key.txt")
    if not k and os.path.exists(p):
        k = open(p).read().strip()
    if not k:
        print("No Census API key (set CENSUS_API_KEY or put it in " + p + "); skipping step 11.")
        sys.exit(0)
    return k


def pull(hs, cty):
    """Monthly imports for one HS10 code and country, Jul 2018-Dec 2021, split by rate provision (cached)."""
    path = os.path.join(CACHE, f"imports_{hs}_{cty}.csv")
    if os.path.exists(path):
        return pd.read_csv(path, dtype={"RP": str, "time": str})
    url = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
    params = {"get": "CTY_NAME,RP,CON_VAL_MO,CON_QY1_MO,UNIT_QY1,DUT_VAL_MO,CAL_DUT_MO", "COMM_LVL": "HS10",
              "I_COMMODITY": hs, "CTY_CODE": cty, "time": "from 2018-07 to 2021-12", "key": census_key()}
    r = requests.get(url, params=params, timeout=180, allow_redirects=False)
    if r.status_code == 204:
        return pd.DataFrame()
    r.raise_for_status()
    rows = r.json()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df = df.loc[:, ~df.columns.duplicated()]
    for c in ["CON_VAL_MO", "CON_QY1_MO", "DUT_VAL_MO", "CAL_DUT_MO"]:
        df[c] = pd.to_numeric(df[c])
    df.to_csv(path, index=False)
    return df


# ---------------- 1. Customs data ----------------
scotch = pull("2208303030", "4120")
liq = pd.concat([pull("2208700030", c).assign(cty=c) for c in COUNTRIES], ignore_index=True)
for df in (scotch, liq):
    df["month"] = df.time.str[:7]
    df.drop(df[df.RP == "-"].index, inplace=True)                     # "-" = total over rate provisions (avoid double count)


def customs_stats(df, label):
    on = df[(df.month >= ON0) & (df.month <= ON1)]
    dut = on[on.RP == "69"]                                           # dutiable under Chapter 99 (the 2019 tariff)
    val, pfl, duty, dval = dut.CON_VAL_MO.sum(), dut.CON_QY1_MO.sum(), dut.CAL_DUT_MO.sum(), dut.DUT_VAL_MO.sum()
    monthly = dut.groupby("month").agg(v=("CON_VAL_MO", "sum"), q=("CON_QY1_MO", "sum"))
    uv_m = (monthly.v / monthly.q)[monthly.q > 1000]
    return {"group": label, "dutiable imports $M (tariff period)": round(val / 1e6, 1),
            "proof liters (M)": round(pfl / 1e6, 2), "effective tariff rate": round(duty / dval, 3),
            "customs value $/proof liter": round(val / pfl, 2),
            "monthly range $/PFL": f"{uv_m.min():.1f}-{uv_m.max():.1f}",
            "customs value per 750ml 86-proof bottle $": round(val / pfl * PFL_PER_750_86, 2)}


cs = pd.DataFrame([customs_stats(scotch, "Single-malt Scotch"), customs_stats(liq, "Covered EU/UK liqueurs")]).set_index("group")
print("Customs data (dutiable lines, Nov 2019-Feb 2021):\n", cs.T.to_string(), flush=True)

# ---------------- 2. Iowa supplier cost per proof liter, treated items, pre-period ----------------
d = duckdb.sql(f"""SELECT m.item_no, m.month, m.bottles, m.dollars, m.price_posted, i.category_name, i.im_desc, i.ml
                   FROM '{B}/item_month.parquet' m JOIN '{B}/items.parquet' i USING (item_no)
                   WHERE m.month BETWEEN '2018-10-01' AND '2019-10-01' AND m.price_posted BETWEEN 1 AND 150""").df()
prod = pd.read_csv(f"{RAW}/products/iowa_liquor_products_1029_rows.csv", dtype={"item_no": str},
                   usecols=["item_no", "proof"]).drop_duplicates("item_no")
d["item_no"] = d.item_no.astype(str)
n0 = len(d); d = d.merge(prod, on="item_no", how="left", validate="many_to_one"); assert len(d) == n0
d["im_desc"] = d.im_desc.fillna("")
d["grp"] = np.select([d.category_name == "SINGLE MALT SCOTCH",
                      d.im_desc.str.upper().str.contains("|".join(COVERED_LIQUEUR_BRANDS))],
                     ["Single-malt Scotch", "Covered EU/UK liqueurs"], "x")
d = d[d.grp != "x"].copy()
print("Proof from the price list for", d.groupby("grp").proof.apply(lambda s: f"{s.notna().mean():.0%}").to_dict(),
      "of item-months; rest = group median", flush=True)
d["proof"] = d.proof.where(d.proof > 0).fillna(d.groupby("grp").proof.transform("median"))
d["pfl"] = d.bottles * d.ml / 1000 * d.proof / 100                      # proof liters bought
iowa = d.groupby("grp").agg(dollars=("dollars", "sum"), pfl=("pfl", "sum"))
iowa["Iowa supplier cost $/proof liter"] = iowa.dollars / 1.5 / iowa.pfl

# ---------------- 3. Pass-through ----------------
est = json.load(open(os.path.join(OUT, "tariff2019_estimates.json")))
rows = []
for g in cs.index:
    b, se = est[f"{g}|on|log_p|$-weighted"]["coef"], est[f"{g}|on|log_p|$-weighted"]["se"]
    cost = iowa.loc[g, "Iowa supplier cost $/proof liter"]
    duty = cs.loc[g, "effective tariff rate"] * cs.loc[g, "customs value $/proof liter"]
    rise = np.expm1(b) * cost
    pt = rise / duty
    pt_se = np.exp(b) * se * cost / duty                                   # delta method (beta uncertainty only)
    lo, hi = [float(x) for x in cs.loc[g, "monthly range $/PFL"].split("-")]
    tau = cs.loc[g, "effective tariff rate"]
    rows.append({"group": g, "Iowa price effect (beta)": f"{b:.3f} ({se:.3f})",
                 "customs share of Iowa supplier cost": round(cs.loc[g, "customs value $/proof liter"] / cost, 2),
                 "duty $/PFL": round(duty, 2), "Iowa supplier cost rise $/PFL": round(rise, 2),
                 "pass-through %": round(100 * pt), "95% CI %": f"{100 * (pt - 1.96 * pt_se):.0f}-{100 * (pt + 1.96 * pt_se):.0f}",
                 "range over monthly customs values %": f"{100 * rise / (tau * hi):.0f}-{100 * rise / (tau * lo):.0f}",
                 "per 750ml bottle: duty $": round(duty * PFL_PER_750_86, 2),
                 "per bottle: Iowa supplier cost +$": round(rise * PFL_PER_750_86, 2),
                 "per bottle: Iowa price +$": round(1.5 * rise * PFL_PER_750_86, 2)})
pt = pd.DataFrame(rows).set_index("group")
print("\nPass-through of the 2019 tariff to Iowa:\n", pt.T.to_string(), flush=True)

# ---------------- 4. Figure: UK Scotch imports by month; the dutiable part = single malt ----------------
m = scotch.assign(dutiable=scotch.RP == "69").groupby(["month", "dutiable"]).CON_VAL_MO.sum().unstack(fill_value=0) / 1e6
m = m.reindex(columns=[False, True], fill_value=0)
fig, ax = plt.subplots(figsize=(10, 4))
x = pd.to_datetime(m.index)
ax.bar(x, m[False], width=25, color="#bbbbbb", label="duty-free (all Scotch before the tariff; blended during it)")
ax.bar(x, m[True], width=25, bottom=m[False], color="#993f2a", label="paid the 25% tariff (single malt)")
ax.axvspan(pd.Timestamp("2019-10-18"), pd.Timestamp("2021-03-04"), color="#fbebb7", alpha=0.5, zorder=0)
ax.set_ylabel("US imports from the UK, $M per month")
ax.set_title("Only single malt paid the 25% tariff, so its duty records reveal its customs value", loc="left")
ax.legend(loc="upper right", fontsize=8); ax.tick_params(labelbottom=True, labelleft=True)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_customs_scotch.png"), dpi=150)

with open(os.path.join(OUT, "customs_passthrough.md"), "w", encoding="utf-8") as f:
    f.write("# 2019 tariff pass-through using US customs values (auto-generated by code/11_customs_passthrough.py)\n\n"
            "Census International Trade API, HS10 x country x month x rate provision; dutiable lines (rate provision 69) "
            f"in the tariff period ({ON0} to {ON1}). Iowa supplier cost = Iowa price / 1.5 per proof liter, treated items, "
            "Oct 2018-Oct 2019, $-weighted. Beta = $-weighted 'on' estimate from 04.\n\n## Customs data\n\n"
            + cs.to_markdown() + "\n\n## Pass-through\n\n" + pt.to_markdown() +
            "\n\nCaveat: customs values are the US-wide average of dutiable imports; Iowa's mix of single malts may differ. "
            "The CI reflects uncertainty in beta only.\n")
print("Saved output/customs_passthrough.md and fig_customs_scotch.png")
