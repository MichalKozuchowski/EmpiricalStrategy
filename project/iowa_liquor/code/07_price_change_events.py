"""
07_price_change_events.py: what happens to an item's sales around its OWN posted-price changes?
An event-study check on the logit elasticity (05) in the spirit of Seim & Waldfogel's "days around price changes" design.

Events: an item's posted price moves by >= 3% (up or down) from month t-1 to t, and the new price holds for >= 2 more months
        (filters out one-month promotions); the item must be sold in each of months t-6..t+6 (balanced window).
Outcome: log bottles. Each event is compared with up to 20 items in the same spirit-type nest with no price change in
         the window (stacked design: event x item fixed effects + event x calendar-month fixed effects), so seasonality and
         nest-wide trends net out. |log price change| <= 0.5 (larger "changes" are item-number reuse / errors).
         SE clustered by ITEM (the same items reappear across events and as controls).
Reading: increases are the cleaner estimate; price CUTS follow falling sales (pre-trend), i.e. cuts respond to demand.
Reports the event-time path separately for increases and decreases, normalized to t-2 (so t-1 shows stocking-up),
and an implied elasticity = (avg log-q change, months t..t+5 vs t-6..t-2) / (log price change).

Run:  uv run --with duckdb --with pandas --with numpy --with matplotlib --with tabulate python code/07_price_change_events.py
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
W = 6

d = duckdb.sql(f"""SELECT m.item_no, m.month, m.bottles, m.price_posted AS price, i.category_name
                   FROM '{B}/item_month.parquet' m JOIN '{B}/items.parquet' i USING (item_no)
                   WHERE m.month BETWEEN '2018-01-01' AND '2026-10-01' AND m.price_posted BETWEEN 1 AND 150""").df()
d["category_name"] = d["category_name"].fillna("UNKNOWN")
d["nest"] = d.category_name.map(nest_of)
d["t"] = (d.month.dt.year - 2018) * 12 + d.month.dt.month - 1
d = d.sort_values(["item_no", "t"])
d["lp"], d["lq"] = np.log(d.price), np.log(d.bottles)
g = d.groupby("item_no")
d["dlp"] = d.lp - g.lp.shift(1)
d["gap"] = d.t - g.t.shift(1)
d["hold1"] = (g.lp.shift(-1) - d.lp).abs() < 0.01
d["hold2"] = (g.lp.shift(-2) - d.lp).abs() < 0.01
ev = d[(d.gap == 1) & (d.dlp.abs() >= np.log(1.03)) & (d.dlp.abs() <= 0.5) & d.hold1 & d.hold2][["item_no", "t", "dlp", "nest"]].copy()

# balanced window: item sold in every month t-6..t+6
have = set(zip(d.item_no, d.t))
ev = ev[[all((i, t + k) in have for k in range(-W, W + 1)) for i, t in zip(ev.item_no, ev.t)]]
ev["event_id"] = np.arange(len(ev))
ev["dir"] = np.where(ev.dlp > 0, "increase", "decrease")
print(f"Events: {len(ev):,} ({(ev.dir == 'increase').sum():,} increases, {(ev.dir == 'decrease').sum():,} decreases); "
      f"median |dlog p| = {ev.dlp.abs().median():.3f}", flush=True)

# stacked panel: each event's own item (treated) + same-nest items with NO price change in the window (controls)
d_idx = d.set_index(["item_no", "t"])
stable = d.assign(chg=(d.dlp.abs() > 0.005).astype(int)).groupby("item_no")
rows = []
nest_items = d.groupby("nest").item_no.unique().to_dict()
rng = np.random.default_rng(634)
for e in ev.itertuples():
    win = range(e.t - W, e.t + W + 1)
    tr = d_idx.loc[[(e.item_no, k) for k in win]].reset_index()
    tr["treated"] = 1
    # up to 20 control items from the same nest, observed all window months, no price change in the window
    cands = [i for i in rng.permutation(nest_items[e.nest]) if i != e.item_no][:400]
    ctl = []
    for i in cands:
        keys = [(i, k) for k in win]
        if all(kk in have for kk in keys):
            sub = d_idx.loc[keys]
            if (sub.dlp.abs().fillna(0) < 0.005).all():
                ctl.append(sub.reset_index())
        if len(ctl) == 20:
            break
    if not ctl:
        continue
    c = pd.concat(ctl); c["treated"] = 0
    blk = pd.concat([tr, c]); blk["event_id"] = e.event_id; blk["rel"] = blk.t - e.t
    blk["dir"] = e.dir; blk["dlp_event"] = e.dlp
    rows.append(blk)
st = pd.concat(rows, ignore_index=True)
st["unit"] = st.event_id.astype(str) + "_" + st.item_no.astype(str)
st["ev_month"] = st.event_id.astype(str) + "_" + st.t.astype(str)          # event x calendar month FE (controls)
print(f"Stacked panel: {len(st):,} rows, {st.event_id.nunique():,} events with controls", flush=True)

paths, elas = {}, {}
for dr in ["increase", "decrease"]:
    s = st[st.dir == dr].copy()
    rels = [k for k in range(-W, W + 1) if k != -2]
    for k in rels:
        s[f"r{k}"] = ((s.rel == k) & (s.treated == 1)).astype(float)
    cols = [f"r{k}" for k in rels]
    dm, keep, dums = absorb(s, ["unit"], ["lq"] + cols, dummy_cols=[])
    # event x month fixed effects via second demeaning step: residualize on ev_month by group means of the demeaned data
    em = s.loc[keep, "ev_month"].to_numpy()
    dm = dm - dm.groupby(em).transform("mean")
    r = tsls(dm, "lq", exog=cols, clusters=s.loc[keep, "item_no"].to_numpy())
    t = r["table"]; t["k"] = rels
    t = pd.concat([t, pd.DataFrame({"coef": [0.0], "se": [0.0], "k": [-2]})]).sort_values("k")
    paths[dr] = t
    post = t[(t.k >= 0) & (t.k <= 5)].coef.mean(); pre = t[(t.k >= -6) & (t.k <= -3)].coef.mean()
    dlp = s.loc[s.treated == 1].groupby("event_id").dlp_event.first().mean()
    elas[dr] = {"avg dlog p": round(dlp, 3), "dlog q (t..t+5 vs t-6..t-3)": round(post - pre, 3),
                "t-1 stocking (dlog q)": round(t.loc[t.k == -1, "coef"].iloc[0], 3),
                "pre-trend (t-6..t-3 vs t-2)": round(pre, 3),
                "elasticity vs t-6..t-3": round((post - pre) / dlp, 2),
                "elasticity vs t-2": round(post / dlp, 2)}
print(pd.DataFrame(elas).T.to_string(), flush=True)

fig, ax = plt.subplots(figsize=(9.5, 4.4))
ax.axhline(0, color="#999999", lw=1); ax.axvline(-0.5, color="#121212", lw=1, ls="--")
for dr, c in [("increase", "#993f2a"), ("decrease", "#2b6cb0")]:
    p = paths[dr]
    ax.errorbar(p.k + (0.08 if dr == "increase" else -0.08), p.coef, yerr=1.96 * p.se, fmt="o-", color=c, ms=4,
                capsize=0, lw=1.4, label=f"price {dr} (n={elas[dr]['avg dlog p']:+.3f} avg log change)")
ax.set_xlabel("Months relative to the item's posted-price change (normalized to t-2)")
ax.set_ylabel("Log bottles vs same-nest items")
ax.set_title("Iowa stores stock up right before a price increase, then buy less", loc="left")
ax.legend(fontsize=8); ax.tick_params(labelbottom=True, labelleft=True)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_price_change_events.png"), dpi=150)
with open(os.path.join(OUT, "price_change_events.md"), "w", encoding="utf-8") as f:
    f.write("# Own posted-price changes: event study (auto-generated by code/07_price_change_events.py)\n\n")
    f.write(f"Events: posted price moves >= 3% and holds >= 2 more months; item sold in all months t-6..t+6. "
            f"{st.event_id.nunique():,} events, each with up to 20 same-nest controls with no price change. "
            "FE: event x item + event x month. |dlog p| <= 0.5. SE clustered by item.\n\n")
    f.write(pd.DataFrame(elas).T.to_markdown())
