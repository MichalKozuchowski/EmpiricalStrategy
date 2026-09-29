# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "statsmodels", "matplotlib"]
# ///
# =============================================================================
# MGT 634 - Class 8 (Regression): "Your turn in Claude Code" exercises
# =============================================================================
# Five simulation experiments from the last slide. In each one we KNOW the true
# model (we generate the data ourselves), so we can see exactly when OLS gets
# the right answer and when it goes wrong.
#
# Method: Monte Carlo. We draw a fresh sample, run the regression, save the
# estimate, and repeat many times (REPS). The average of the saved estimates
# shows bias; how often the 95% confidence interval contains the truth
# ("coverage") shows whether the standard errors can be trusted (should be ~95%).
#
# Run from this folder with:   uv run class8_exercises.py
# (uv reads the package list at the top of this file and installs it for you.)
# =============================================================================

import numpy as np
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")                  # save charts to files without opening windows
import matplotlib.pyplot as plt

np.random.seed(42)                     # same seed as the lecture code -> reproducible
REPS = 2000                            # number of simulated samples per experiment
N = 200                                # observations per sample
TRUE_SLOPE = 2

# Chart style (same palette as HW1): blue, orange, aqua; grey for "truth" lines
BLUE, ORANGE, AQUA, INK, SOFT = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e"


def ols(y, X, robust=False):
    """Fit OLS with an intercept. robust=True uses heteroskedasticity-robust (HC1) SEs."""
    return sm.OLS(y, sm.add_constant(X)).fit(cov_type="HC1" if robust else "nonrobust")


def covers(fit, j, truth):
    """True if the 95% confidence interval for coefficient j contains the true value."""
    lo, hi = fit.conf_int()[j]
    return lo <= truth <= hi


def style(ax, title, xlabel, ylabel=""):
    ax.set_title(title, loc="left", fontsize=10.5, color=INK)
    ax.set_xlabel(xlabel, color=SOFT)
    ax.set_ylabel(ylabel, color=SOFT)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=SOFT, labelsize=8.5)
    ax.grid(color="#e6e5e1", linewidth=0.7)
    ax.set_axisbelow(True)


fig, axes = plt.subplots(2, 3, figsize=(15, 8.5))
axes = axes.ravel()

# =============================================================================
# EXERCISE 1 - Errors that are NOT normally distributed
# =============================================================================
# Truth: y = 3 + 2x + error. Three error types, all with mean 0 and SD 5:
#   normal; fat-tailed Student-t with 3 degrees of freedom; skewed (exponential, shifted).
print("=" * 72 + "\nEXERCISE 1 - non-normal errors (truth: slope = 2)\n" + "=" * 72)
error_draws = {
    "Normal":            lambda n: np.random.normal(0, 5, n),
    "Fat-tailed (t, 3 df)": lambda n: np.random.standard_t(3, n) * 5 / np.sqrt(3),
    "Skewed (exponential)": lambda n: np.random.exponential(5, n) - 5,
}
ex1 = {}
for name, draw in error_draws.items():
    slopes, cover = [], []
    for _ in range(REPS):
        x = np.random.uniform(0, 10, N)
        y = 3 + TRUE_SLOPE * x + draw(N)
        fit = ols(y, x)
        slopes.append(fit.params[1])
        cover.append(covers(fit, 1, TRUE_SLOPE))
    ex1[name] = np.array(slopes)
    print(f"{name:<22} mean slope {np.mean(slopes):.3f} | SD {np.std(slopes):.3f} | "
          f"95% CI covers truth {100 * np.mean(cover):.1f}% of the time")
print("-> OLS stays unbiased and the CIs still cover ~95%: normality is NOT needed for\n"
      "   unbiasedness, and with N = 200 the usual SEs work anyway (central limit theorem).")

ax = axes[0]
bins = np.linspace(1.4, 2.6, 50)
for (name, s), colour in zip(ex1.items(), [BLUE, ORANGE, AQUA]):
    ax.hist(s, bins=bins, histtype="step", linewidth=1.8, color=colour, label=name, density=True)
ax.axvline(TRUE_SLOPE, color=INK, linestyle="--", linewidth=1)
ax.legend(frameon=False, fontsize=8)
style(ax, "1. Non-normal errors: estimates still centre on the truth",
      "Estimated slope (truth = 2)", "Density")

# =============================================================================
# EXERCISE 2 - Omit x1, which is + correlated with x2 and - correlated with x3
# =============================================================================
# Truth: y = 1 + 2*x1 + 1*x2 + 1*x3 + error, with corr(x1,x2) = +0.6, corr(x1,x3) = -0.5,
# corr(x2,x3) = 0. The "short" regression leaves x1 out.
print("\n" + "=" * 72 + "\nEXERCISE 2 - omitted variable bias (truth: b2 = 1, b3 = 1)\n" + "=" * 72)
corr = np.array([[1.0, 0.6, -0.5], [0.6, 1.0, 0.0], [-0.5, 0.0, 1.0]])
full_b, short_b = [], []
for _ in range(REPS):
    x1, x2, x3 = np.random.multivariate_normal([0, 0, 0], corr, N).T
    y = 1 + 2 * x1 + 1 * x2 + 1 * x3 + np.random.normal(0, 2, N)
    full_b.append(ols(y, np.column_stack([x1, x2, x3])).params[2:4])   # b2, b3 with x1 included
    short_b.append(ols(y, np.column_stack([x2, x3])).params[1:3])      # b2, b3 with x1 omitted
full_b, short_b = np.mean(full_b, axis=0), np.mean(short_b, axis=0)
# Omitted variable bias formula: short b = true b + (effect of x1) x (slope of x1 on that x)
theory = [1 + 2 * 0.6, 1 + 2 * (-0.5)]
print(f"x1 included: b2 = {full_b[0]:.3f}, b3 = {full_b[1]:.3f}   (unbiased)")
print(f"x1 omitted:  b2 = {short_b[0]:.3f}, b3 = {short_b[1]:.3f}   "
      f"(theory: {theory[0]:.2f} and {theory[1]:.2f})")
print("-> x2 soaks up x1's positive effect and is overstated (1 -> 2.2); x3 soaks up the\n"
      "   negative link and its real effect of 1 disappears to ~0. Bias direction = sign of\n"
      "   (x1's effect) x (x1's correlation with the included variable).")

ax = axes[1]
pos = np.arange(2)
b1 = ax.bar(pos - 0.2, full_b, 0.38, color=BLUE, label="x1 included")
b2 = ax.bar(pos + 0.2, short_b, 0.38, color=ORANGE, label="x1 omitted")
ax.bar_label(b1, fmt="%.2f", fontsize=8, color=SOFT, padding=2)
ax.bar_label(b2, fmt="%.2f", fontsize=8, color=SOFT, padding=2)
ax.axhline(1, color=INK, linestyle="--", linewidth=1)
ax.set_xticks(pos)
ax.set_xticklabels(["b2 (x2, corr +0.6 with x1)", "b3 (x3, corr -0.5 with x1)"], fontsize=8.5)
ax.set_ylim(0, 2.6)
ax.legend(frameon=False, fontsize=8)
style(ax, "2. Omitting x1 biases x2 up and x3 down", "", "Average estimate (truth = 1)")

# =============================================================================
# EXERCISE 3 - x measured with error
# =============================================================================
# Truth: y = 3 + 2*x_true + error. We only observe x_obs = x_true + noise.
# Theory ("attenuation bias"): slope -> 2 x Var(x) / (Var(x) + Var(noise)).
print("\n" + "=" * 72 + "\nEXERCISE 3 - measurement error in x (truth: slope = 2)\n" + "=" * 72)
noise_sds = np.linspace(0, 3, 13)
ex3 = []
for sd in noise_sds:
    slopes = []
    for _ in range(REPS // 4):                  # 500 samples per noise level is plenty
        x_true = np.random.normal(5, 2, N)      # Var(x) = 4
        y = 3 + TRUE_SLOPE * x_true + np.random.normal(0, 2, N)
        x_obs = x_true + np.random.normal(0, sd, N)
        slopes.append(ols(y, x_obs).params[1])
    ex3.append(np.mean(slopes))
theory3 = TRUE_SLOPE * 4 / (4 + noise_sds ** 2)
for sd, est, th in zip(noise_sds[::4], ex3[::4], theory3[::4]):
    print(f"noise SD {sd:.2f}: mean slope {est:.3f} (theory {th:.3f})")
print("-> Noise in x biases the slope TOWARD ZERO (attenuation); more noise, more bias.\n"
      "   A bigger sample does not fix it. (Noise in y only adds imprecision, not bias.)")

ax = axes[2]
ax.plot(noise_sds, ex3, "o", color=BLUE, markersize=6, label="Simulated average")
ax.plot(noise_sds, theory3, color=ORANGE, linewidth=1.8, label="Theory: 2 x 4 / (4 + noise var)")
ax.axhline(TRUE_SLOPE, color=INK, linestyle="--", linewidth=1)
ax.set_ylim(0, 2.3)
ax.legend(frameon=False, fontsize=8)
style(ax, "3. Measurement error in x shrinks the slope", "SD of measurement noise (SD of x = 2)",
      "Average estimated slope (truth = 2)")

# =============================================================================
# EXERCISE 4 - Error variance grows with x (heteroskedasticity)
# =============================================================================
# Truth: y = 3 + 2x + error, error SD = 0.5 * x^2 (spread fans out sharply as x grows).
print("\n" + "=" * 72 + "\nEXERCISE 4 - heteroskedasticity (truth: slope = 2)\n" + "=" * 72)
slopes, se_default, se_robust, cover_default, cover_robust = [], [], [], [], []
for _ in range(REPS):
    x = np.random.uniform(0, 10, N)
    y = 3 + TRUE_SLOPE * x + np.random.normal(0, 0.5 * x ** 2, N)
    fit_default, fit_robust = ols(y, x), ols(y, x, robust=True)
    slopes.append(fit_default.params[1])
    se_default.append(fit_default.bse[1])
    se_robust.append(fit_robust.bse[1])
    cover_default.append(covers(fit_default, 1, TRUE_SLOPE))
    cover_robust.append(covers(fit_robust, 1, TRUE_SLOPE))
cov4 = [100 * np.mean(cover_default), 100 * np.mean(cover_robust)]
print(f"mean slope {np.mean(slopes):.3f} (still unbiased)")
print(f"actual spread of the slope estimates (SD across samples): {np.std(slopes):.3f}")
print(f"average reported SE: default {np.mean(se_default):.3f} | robust {np.mean(se_robust):.3f}")
print(f"95% CI coverage: default SEs {cov4[0]:.1f}% | robust (HC1) SEs {cov4[1]:.1f}%")
print("-> The estimate is fine, but default SEs are too small, so '95%' intervals miss\n"
      "   more often than 5% -> overconfident significance. Robust SEs fix it:\n"
      "   sm.OLS(...).fit(cov_type='HC1').")

ax = axes[3]
miss = [100 - c for c in cov4]          # how often a "95%" CI misses the truth (should be 5%)
bars = ax.bar(["Default SEs", "Robust (HC1) SEs"], miss, color=[ORANGE, BLUE], width=0.55)
ax.bar_label(bars, fmt="%.1f%%", fontsize=9, color=SOFT, padding=2)
ax.axhline(5, color=INK, linestyle="--", linewidth=1)
ax.text(-0.3, 5.3, "should miss 5%", fontsize=8, color=SOFT)
ax.set_ylim(0, 14)                      # bars start at zero (Class 5 rule)
style(ax, "4. Heteroskedasticity: default '95%' CIs miss twice as often", "",
      "% of 95% CIs that MISS the true slope")

# =============================================================================
# EXERCISE 5 - Selection: we only see observations where y is above a threshold
# =============================================================================
# Truth: y = 3 + 2x + error (SD 5). We keep only rows with y > 15.
print("\n" + "=" * 72 + "\nEXERCISE 5 - selection on y (truth: slope = 2)\n" + "=" * 72)
THRESH = 15
slopes_all, slopes_sel, kept = [], [], []
for _ in range(REPS):
    x = np.random.uniform(0, 10, N)
    y = 3 + TRUE_SLOPE * x + np.random.normal(0, 5, N)
    keep = y > THRESH
    slopes_all.append(ols(y, x).params[1])
    slopes_sel.append(ols(y[keep], x[keep]).params[1])
    kept.append(keep.mean())
print(f"all data:         mean slope {np.mean(slopes_all):.3f}")
print(f"only y > {THRESH}:     mean slope {np.mean(slopes_sel):.3f}  "
      f"(kept {100 * np.mean(kept):.0f}% of rows)")
print("-> Selecting on the OUTCOME biases the slope toward zero: at low x, only units with\n"
      "   big positive errors make the cut, so the error is no longer independent of x.\n"
      "   (Selecting on x instead would not bias the slope.)")

ax = axes[4]
np.random.seed(7)                                    # one illustrative sample
x = np.random.uniform(0, 10, 300)
y = 3 + TRUE_SLOPE * x + np.random.normal(0, 5, 300)
keep = y > THRESH
ax.scatter(x[~keep], y[~keep], s=10, color="#c9c8c3", label="Not observed")
ax.scatter(x[keep], y[keep], s=10, color=BLUE, label=f"Observed (y > {THRESH})")
grid = np.array([0, 10])
b_all, b_sel = ols(y, x).params, ols(y[keep], x[keep]).params
ax.plot(grid, 3 + 2 * grid, color=INK, linestyle="--", linewidth=1, label="Truth (slope 2)")
ax.plot(grid, b_sel[0] + b_sel[1] * grid, color=ORANGE, linewidth=2,
        label=f"OLS on observed (slope {b_sel[1]:.2f})")
ax.axhline(THRESH, color=SOFT, linewidth=0.6)
ax.legend(frameon=False, fontsize=7.5, loc="upper left")
style(ax, "5. Selecting on y flattens the slope", "x", "y")

# ---- Panel 6: summary text -----------------------------------------------------
ax = axes[5]
ax.axis("off")
summary = [
    ("Biased estimate?", INK, True),
    ("1. Non-normal errors: no", SOFT, False),
    ("2. Omitted correlated x1: yes (sign depends on correlations)", SOFT, False),
    ("3. Measurement error in x: yes, toward zero", SOFT, False),
    ("4. Heteroskedasticity: no, but default SEs are wrong", SOFT, False),
    ("5. Selection on y: yes, toward zero", SOFT, False),
]
for i, (t, c, b) in enumerate(summary):
    ax.text(0.02, 0.9 - i * 0.14, t, fontsize=10.5, color=c, fontweight="bold" if b else "normal",
            transform=ax.transAxes)

fig.suptitle(f"When does OLS go wrong? {REPS:,} simulated samples of N = {N} per experiment",
             x=0.01, ha="left", fontsize=13, color=INK)
fig.tight_layout()
fig.savefig("class8_exercises.png", dpi=170)
print("\nSaved chart: class8_exercises.png")
