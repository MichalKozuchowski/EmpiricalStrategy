# =============================================================================
# MGT 634 - Class 8, slide 16 "Application: Running experiments"
# =============================================================================
# Randomly give half of 200 customers a promotion; true effect = +$15 on a $50
# baseline. Regress purchase on a 0/1 treatment dummy: the slope estimates the
# treatment effect.
#
# NOTE - bug on the slide: it calls .fit() twice
#     model = sm.OLS(purchase, X).fit()
#     results = model.fit()        -> AttributeError: 'OLSResults' object has no attribute 'fit'
# Fixed below by building the model and fitting it once.
# Run:  uv run --with numpy --with statsmodels slide16_experiment.py
# Result (seed 42): effect 15.57 (SE 1.37, 95% CI 12.86-18.28), control mean 50.40.
# =============================================================================
import numpy as np
import statsmodels.api as sm

# Set seed
np.random.seed(42)

# Sample size
n = 200

# EXPERIMENT: Randomly assign treatment
treatment = np.random.binomial(1, 0.5, n)  # 50% get treatment

# Generate outcome: Purchase amount
# Control group average: $50
# Treatment effect: +$15
purchase = 50 + 15*treatment + np.random.normal(0, 10, n)

# Estimate with regression
X = sm.add_constant(treatment)
model = sm.OLS(purchase, X)      # FIX: build the model here...
results = model.fit()            # ...and fit it once here
# Print results
print(results.summary())

# Sanity check: with a single 0/1 regressor, OLS = difference in group means
control, treated = purchase[treatment == 0].mean(), purchase[treatment == 1].mean()
print(f"\nTreated: {treatment.sum()} of {n} | control mean ${control:.2f}, "
      f"treated mean ${treated:.2f}, difference ${treated - control:.2f}")
