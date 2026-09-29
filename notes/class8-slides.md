# Class 8 — Slide Deck: "Regression"
**Kevin Williams, MGT 634: ESAI, Tue Sep 29, 2026.** In-class exercise worked in
[class8_regression/](class8_regression/) (simulations run locally with uv, not on the cluster).

## Plan (slide 2)
1. Regression details and how to estimate a regression in Python
2. Extensions: multiple linear regression, fixed effects (regression discontinuity and
   difference-in-differences come later)
3. Tips and warnings: endogeneity, omitted variable bias, perfect multicollinearity

## Simple linear regression (slides 3–4)
- Model: `y_i = a + b x_i + u_i`; `y` = outcome/dependent variable, `x` = control/exogenous
  variable, `u` = unobserved factors (error term). The more `x` explains `y`, the less `u` matters.
- "Simple" = one control; several controls = multiple linear regression.
- "Linear" = **linear in the parameters**, not a straight line. Not linear: `y = a·b·x + u`,
  `y = a + b·x·u`. Linear: `y = a + b·x1·x2 + u`, `y = a + b·x + c·x² + u`.

## What estimating a regression does (slides 5–7)
- Choose `a, b` that best explain `y`, i.e. minimize the role of `u`. Estimates: `â, b̂`.
- Fitted `ŷ = â + b̂x`; residual `û = y − ŷ`. OLS minimizes `Σ û²` (squared loss, "SSE").
- SST = `Σ(y − ȳ)²`, SSR = `Σ(ŷ − ȳ)²`, **R² = SSR/SST = 1 − SSE/SST**.
- OLS vs least absolute deviations (LAD): LAD minimizes `Σ|û|`. OLS is the default because of
  its nice properties (and a closed-form solution).

## Example code (slide 11) — the professor's baseline
```python
import numpy as np
import statsmodels.api as sm
np.random.seed(42)
n = 100
X = np.random.uniform(0, 10, n)
y = 3 + 2*X + np.random.normal(0, 5, n)
X_const = sm.add_constant(X)
model = sm.OLS(y, X_const)
results = model.fit()
print(results.summary())
```
Output shown: const 4.0755 (SE 0.851), x1 1.7701 (SE 0.153), R² 0.577, N = 100.
Slide 12: best fit (R² 0.577) beats a "not best fit" line (R² 0.553); fitted vs true line differ
because we only see a sample.

## Nice properties (slides 13–15)
- **Consistent**: as N grows, `β̂` converges to the truth (slope 2, intercept 3 in the demo).
- **Precision**: standard errors shrink roughly like `1/√N`. Significant at 5% if |t| > 1.96
  (N = 5 demo: slope 1.87, SE 0.809, t = 2.3 significant; intercept t = 0.3 not).
- **Unbiased**: re-running the study many times, the estimates centre on the truth.

## Application: experiments (slide 16)
Randomly assign a promotion; `Purchase = β0 + β1·Treatment + ε`. With random assignment, `β̂1`
estimates the treatment effect (+$15 in the simulated example, n = 200, control mean $50).

## Multiple regression and omitted variable bias (slides 17–21)
- `y = β0 + β1x1 + … + βkxk + ε`; each β is a marginal effect holding the others constant.
  Controls help isolate causal/managerial insights (shoe demand: control for brand and price,
  because brand is correlated with price).
- Example: `y = 2 + 3·X1 + 1.5·X2 + noise`, corr(X1, X2) = 0.7.
- **Omitted variable bias**: leave out a variable that is correlated with an included one and
  the included one becomes correlated with the error term → the **endogeneity problem**.
  Demo: full model β1 = 2.81; X1 only β1 = 3.91 (biased); theory `3 + 1.5ρ`. If ρ = 0, omitting
  X2 does no harm.

## Fixed effects (slides 22–27)
- Categorical variables → dummy variables; estimate (#categories − 1) because the last one is
  absorbed by the intercept (otherwise **perfect multicollinearity**: the 24 hour-of-day dummies
  sum to the constant column).
- Applications: 311 (time to resolve ~ neighborhood FE), Yelp (rating ~ cuisine FE), TSA
  (checkpoint totals ~ time-of-day FE + airport FE): `y = Xβ + τ(hour) + τ(apt) + ε`.
- FE can be estimated (dummies: `pd.get_dummies(..., drop_first=True)`) or **absorbed** with the
  within estimator (demean by group: `df.groupby('firm').transform(lambda x: x - x.mean())`,
  no constant needed) — same slope, but you don't get the FE estimates back.
- Demo (20 firms × 5 years, true β = 2): pooled OLS 2.05, FE 2.03.

## Your turn in Claude Code (slide 28) — in-class exercise
1. What if the true errors are not normally distributed?
2. Multiple regression where x1 is positively correlated with x2 and negatively with x3, and we
   exclude x1?
3. What if we measure x1 with error in a simple linear model?
4. What if the error variance grows with x1 (heteroskedasticity)?
5. Simulate selection: we only observe complete data where y is above a threshold.
