# =============================================================================
# MGT 634 - Class 8, slide 11 "Example": plot the data with the fitted OLS line
# =============================================================================
# Same simulation and regression as the professor's slide (seed 42, n = 100),
# drawn in Michal's Upshot plotting style (skill: upshot-plot-style).
# Run from the "Second Year" folder (the uv project that holds the style files):
#   uv run --with statsmodels EmpiricalStrategy/notes/class8_regression/slide11_fit_plot.py
# =============================================================================
import sys
from pathlib import Path

import numpy as np
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")                         # save to file, no pop-up window
import matplotlib.pyplot as plt

# The style module lives in the "Second Year" folder, three levels up from this script
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import upshot_style as us

# ---- 1. The professor's code: simulate and estimate -----------------------------
np.random.seed(42)
n = 100
X = np.random.uniform(0, 10, n)
y = 3 + 2*X + np.random.normal(0, 5, n)
results = sm.OLS(y, sm.add_constant(X)).fit()
a_hat, b_hat = results.params                 # intercept 4.0755, slope 1.7701
print(results.params.round(4), "R2 =", round(results.rsquared, 3))

# ---- 2. Plot in the Upshot style ------------------------------------------------
us.use_style()                                # ALWAYS first: font, colors, grid
fig, ax = plt.subplots(figsize=us.FIGSIZE)

# Data: ordinary sage dots (no point is "key" here, so none get the black ring)
us.dots(ax, X, y, us.SAGE)

# Lines across the observed range of X
grid = np.array([0, 10])
ax.plot(grid, 3 + 2 * grid, color=us.AXIS_LINE, linewidth=1.5, linestyle="--", zorder=2)
ax.plot(grid, a_hat + b_hat * grid, color=us.DARK_GREEN, linewidth=2.2, zorder=4)

# Direct labels at the line ends instead of a legend. The two lines end only
# ~1 unit apart, so nudge the labels apart vertically (points) to stop them overlapping.
fitted = us.label(ax, 10, a_hat + b_hat * 10, f"Fitted OLS line\ny = {a_hat:.2f} + {b_hat:.2f}x")
fitted.xyann = (9, -16)                       # below the end of the fitted line
truth = us.label(ax, 10, 3 + 2 * 10, "True line\ny = 3 + 2x")
truth.xyann = (9, 16)                         # above the end of the true line

# A regression plot needs real numbers on the axes (per the skill's "adapting" rules)
ax.set_xlim(0, 10)
ax.set_ylim(-5, 32)
ax.tick_params(labelbottom=True, labelleft=True, colors="#666666", labelsize=9, length=0)
for spine in ax.spines.values():
    spine.set_color(us.GRID)
    spine.set_linewidth(0.75)

us.axis_box(ax, "X", "bottom")
us.axis_box(ax, "Y", "left")
us.corner_note(ax, f"R² = {results.rsquared:.3f}\nN = {n} simulated points", "top left")
ax.set_title("OLS recovers the true line closely from one noisy sample", loc="left")

fig.savefig(Path(__file__).with_name("slide11_fit_plot.png"))
print("saved slide11_fit_plot.png")
