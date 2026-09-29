# =============================================================================
# MGT 634 - Class 8, slide 13 "Nice Property #1: OLS can be consistent"
# =============================================================================
# Truth: y = 3 + 2x + noise. We draw 10,000 points once, then pretend data
# arrive gradually: re-run OLS on the first N points for N = 5 ... 10,000.
# Consistency = as N grows, the estimates home in on the truth (3 and 2) and
# the +/- 2 SE band around them shrinks toward zero.
# Run from the "Second Year" folder:
#   uv run --with statsmodels EmpiricalStrategy/notes/class8_regression/slide13_consistency.py
# =============================================================================
import sys
from pathlib import Path

import numpy as np
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # "Second Year" folder
import upshot_style as us

# ---- 1. Simulate one big sample (same setup as the slide 11 example) -------------
np.random.seed(42)
N_MAX = 10_000
x_all = np.random.uniform(0, 10, N_MAX)
y_all = 3 + 2 * x_all + np.random.normal(0, 5, N_MAX)

# ---- 2. Re-estimate on the first N points, for N from 5 to 10,000 -----------------
sizes = np.unique(np.round(np.logspace(np.log10(5), np.log10(N_MAX), 40)).astype(int))
est = {"b0": [], "b1": [], "se0": [], "se1": []}
for n in sizes:
    fit = sm.OLS(y_all[:n], sm.add_constant(x_all[:n])).fit()
    est["b0"].append(fit.params[0]); est["b1"].append(fit.params[1])
    est["se0"].append(fit.bse[0]);   est["se1"].append(fit.bse[1])
est = {k: np.array(v) for k, v in est.items()}

print(" N      intercept (SE)      slope (SE)")
for n in [5, 10, 50, 100, 1000, 10000]:
    i = np.where(sizes == n)[0]
    if len(i) == 0:                                     # size not on the grid: fit directly
        fit = sm.OLS(y_all[:n], sm.add_constant(x_all[:n])).fit()
        b0, b1, s0, s1 = *fit.params, *fit.bse
    else:
        i = i[0]; b0, b1, s0, s1 = est["b0"][i], est["b1"][i], est["se0"][i], est["se1"][i]
    print(f"{n:>6}   {b0:6.2f} ({s0:5.2f})     {b1:5.2f} ({s1:5.3f})")

# ---- 3. Plot: left = the N = 5 fit; right = estimates vs N ------------------------
us.use_style()
fig = plt.figure(figsize=(12, 5.2))
gs = fig.add_gridspec(2, 2, width_ratios=[1.05, 1], hspace=0.55, wspace=0.28)
ax_fit = fig.add_subplot(gs[:, 0])
ax_b1 = fig.add_subplot(gs[0, 1])
ax_b0 = fig.add_subplot(gs[1, 1])


def numeric_axes(ax):
    """Real tick numbers (a regression plot needs them), light frame, no tick marks."""
    ax.tick_params(labelbottom=True, labelleft=True, colors="#666666", labelsize=9, length=0)
    for spine in ax.spines.values():
        spine.set_color(us.GRID)
        spine.set_linewidth(0.75)


# Left: the five points we see at N = 5 (key points -> black ring), their OLS line,
# the N = 10,000 line and the truth
grid = np.array([0, 10])
fit5 = sm.OLS(y_all[:5], sm.add_constant(x_all[:5])).fit()
fitN = sm.OLS(y_all, sm.add_constant(x_all)).fit()
ax_fit.scatter(x_all[:400], y_all[:400], s=14, color="#e4e4e4", zorder=1)   # context only
ax_fit.plot(grid, 3 + 2 * grid, color=us.AXIS_LINE, linewidth=1.5, linestyle="--", zorder=2)
ax_fit.plot(grid, fit5.params[0] + fit5.params[1] * grid, color=us.SALMON, linewidth=2.2, zorder=3)
ax_fit.plot(grid, fitN.params[0] + fitN.params[1] * grid, color=us.DARK_GREEN, linewidth=2.2, zorder=3)
us.dots(ax_fit, x_all[:5], y_all[:5], us.SALMON, highlight=True)
lab5 = us.label(ax_fit, 10, fit5.params[0] + fit5.params[1] * 10,
                f"OLS on N = 5\nslope {fit5.params[1]:.2f}")
# The N = 10,000 line sits on top of the truth (that is the point), so one label covers both
labN = us.label(ax_fit, 10, fitN.params[0] + fitN.params[1] * 10,
                f"OLS on N = 10,000\nslope {fitN.params[1]:.2f}\n(truth: 2, dashed)")
ax_fit.set_xlim(0, 10); ax_fit.set_ylim(-10, 40)
numeric_axes(ax_fit)
us.axis_box(ax_fit, "X", "bottom"); us.axis_box(ax_fit, "Y", "left")
us.corner_note(ax_fit, "Grey dots: more data\nwe have not seen yet", "top left")
ax_fit.set_title("Five points can mislead; 10,000 do not", loc="left", fontsize=11.5)


def track(ax, key, se_key, truth, title, ylim):
    """Estimate vs sample size (log scale) with a +/- 2 SE band and the true value."""
    b, se = est[key], est[se_key]
    ax.fill_between(sizes, b - 2 * se, b + 2 * se, color=us.SAGE, alpha=0.45, linewidth=0, zorder=1)
    ax.plot(sizes, b, color=us.DARK_GREEN, linewidth=2, zorder=3)
    ax.axhline(truth, color=us.AXIS_LINE, linewidth=1.2, linestyle="--", zorder=2)
    ax.set_xscale("log")
    ax.set_xlim(5, N_MAX); ax.set_ylim(*ylim)
    ax.set_xticks([5, 10, 100, 1000, 10000])
    ax.set_xticklabels(["5", "10", "100", "1,000", "10,000"])
    numeric_axes(ax)
    ax.minorticks_off()
    us.label(ax, N_MAX, b[-1], f"{b[-1]:.2f}")
    ax.set_title(title, loc="left", fontsize=11)


track(ax_b1, "b1", "se1", 2, "Estimated slope (truth = 2): band = ±2 SE", (-1, 5))
track(ax_b0, "b0", "se0", 3, "Estimated intercept (truth = 3)", (-15, 20))
ax_b0.set_xlabel("SAMPLE SIZE N (LOG SCALE)", fontsize=9.5, color="#666666", fontweight="medium")

fig.suptitle("OLS is consistent: more data pulls the estimates onto the truth",
             x=0.06, ha="left", fontsize=14, fontweight="bold", color=us.INK)
fig.savefig(Path(__file__).with_name("slide13_consistency.png"))
print("saved slide13_consistency.png")
