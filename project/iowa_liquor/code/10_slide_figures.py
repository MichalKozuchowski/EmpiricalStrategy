"""
10_slide_figures.py: presentation figures built from the counterfactual results (no data download needed).
Reads output/counterfactuals_full.csv (written by 09) and saves:
  fig_hf830_who_gets_money.png : state vs supplier gain per policy (range over sigma x market size; dot = sigma .5, M 2x)
  fig_policy_alcohol.png       : change in pure alcohol bought per policy, by own-price elasticity

Run:  uv run --with pandas --with matplotlib python code/10_slide_figures.py
"""
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
try:                                                    # house plot style (NYT Upshot look), if available
    sys.path.insert(0, os.path.abspath(os.path.join(OUT, "..", "..", "..", "..")))
    import upshot_style as us
    us.use_style()
except Exception:
    pass

cf = pd.read_csv(os.path.join(OUT, "counterfactuals_full.csv"))
LAB = {"A1 HF 830, suppliers keep prices": "HF 830, suppliers\nkeep their prices",
       "A2 HF 830, suppliers price up to floor": "HF 830, suppliers raise\nprices to the floor",
       "B alcohol markup (rev.-neutral)": "Alcohol-content markup\n(revenue-neutral)"}
POL = list(LAB)

# ---------- Figure 1: who gets the money (elasticity -0.63) ----------
base = cf[cf.elasticity == -0.63]
fig, ax = plt.subplots(figsize=(9, 5.2))
for j, (col, name, c, off) in enumerate([("state margin $M/yr", "Iowa (state margin)", "#2b6cb0", 0.17),
                                         ("supplier revenue $M/yr", "Suppliers (revenue)", "#993f2a", -0.17)]):
    for i, p in enumerate(POL):
        s = base[base.policy == p][col]
        mid = base[(base.policy == p) & (base.sigma == 0.5) & (base.M == 2.0)][col].iloc[0]
        y = len(POL) - 1 - i + off
        ax.plot([s.min(), s.max()], [y, y], color=c, lw=7, alpha=0.35, solid_capstyle="butt")   # range
        ax.plot(mid, y, "o", color=c, ms=7, label=name if i == 0 else None)                       # central case
        D = "\\$"                                                   # escaped dollar sign (plain "$" starts math text)
        money = lambda v: f"-{D}{-v:.0f}M" if v < -0.5 else f"{D}{max(v, 0):.0f}M"
        txt = f"{D}0 (by design)" if s.abs().max() < 0.5 else f"{money(s.min())} to {money(s.max())}"
        ax.text(s.max() + 1.5, y, txt, va="center", fontsize=8.5, color=c)
ax.axvline(0, color="#999999", lw=1)
ax.set_yticks(range(len(POL))); ax.set_yticklabels([LAB[p] for p in POL][::-1])
ax.set_xlabel("Gain per year, $ millions (bar = range over nesting and market-size assumptions; dot = central case)")
ax.set_title("HF 830's money goes to the state only if suppliers don't raise their prices", loc="left")
ax.legend(loc="lower right", fontsize=8.5); ax.set_xlim(left=min(-6, base[["state margin $M/yr", "supplier revenue $M/yr"]].min().min() - 2))
ax.tick_params(labelbottom=True, labelleft=True)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_hf830_who_gets_money.png"), dpi=150)

# ---------- Figure 2: pure alcohol change by policy and elasticity ----------
fig, ax = plt.subplots(figsize=(9, 5.0))
cols = {-0.4: "#bbbbbb", -0.63: "#121212", -1.0: "#993f2a"}
pols = ["A1 HF 830, suppliers keep prices", "B alcohol markup (rev.-neutral)"]   # A2 has the same quantities as A1
labs = {pols[0]: "HF 830 minimum unit price", pols[1]: "Alcohol-content markup\n(revenue-neutral)"}
for i, p in enumerate(pols):
    for k, (e, c) in enumerate(cols.items()):
        s = cf[(cf.policy == p) & (cf.elasticity == e)]["pure alcohol %"]
        y = len(pols) - 1 - i + (k - 1) * 0.2
        ax.plot([s.min(), s.max()], [y, y], color=c, lw=6, solid_capstyle="butt",
                label=f"elasticity {e}" if i == 0 else None)
ax.axvline(-3, color="#2b6cb0", lw=1, ls="--")
ax.text(-3.15, 0.5, "Scotland's minimum price:\nsales about -3% (PHS 2023)", color="#2b6cb0", fontsize=8, ha="right", va="center")
ax.axvline(0, color="#999999", lw=1)
ax.set_yticks(range(len(pols))); ax.set_yticklabels([labs[p] for p in pols][::-1])
ax.set_xlabel("Change in pure alcohol bought, % per year (range over nesting and market-size assumptions)")
ax.set_title("Both policies cut drinking by a few percent, in line with Scotland's experience", loc="left")
ax.legend(loc="lower left", fontsize=8); ax.tick_params(labelbottom=True, labelleft=True)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_policy_alcohol.png"), dpi=150)
print("Saved fig_hf830_who_gets_money.png and fig_policy_alcohol.png")
