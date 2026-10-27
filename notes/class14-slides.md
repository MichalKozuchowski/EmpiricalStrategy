# Class 14: Regression discontinuity, difference-in-differences, synthetic control (Oct 27, 2026)

Slides: `Session14_DiD_SyntheticControl.pdf` (Kevin Williams, 41 slides). Theme: **constructing comparisons to estimate causal effects.**
In-class data (Downloads): `rd_superfund.csv`, `did_markets.csv`, `synth_markets.csv`.

## Motivating applications (slide 2)
| Paper | Question | Method | Answer |
|---|---|---|---|
| Anderson & Magruder (2012), Yelp | Does an extra half-star bring customers? | RD at the rating-rounding cutoff | No 7 pm table: **+19 pp** |
| Blake, Nosko & Tadelis (2015), eBay | Are returns on search ads positive? | Turn non-brand search ads off in some regions | Short-run ROI **−63%** |
| Hall, Horton & Knoepfle (2017), Uber | Do higher fares raise hourly earnings? | Fare-change cities vs a weighted mix of others (synthetic control) | Initial gains fade |
| Ershov & Mitchell (2025), Instagram | Do disclosure rules reduce hidden ads? | Germany vs Spain, before/after (DiD) | Unlabeled posts are more often ads |

**Experiments vs quasi-experiments (slide 3).**
- **Experiment:** chance assigns treatment, which balances the other causes.
- **Quasi-experiment:** treatment was not randomized, so you use an assignment **rule or timing** to find a credible untreated comparison, and argue why other differences don't explain the change.
- Both need a credible comparison. The design determines **whose** effect you estimate.

## Regression discontinuity (RD), slides 4–14
- **Running variable** (score) + **cutoff** + treatment that switches on at the cutoff.
- **Yelp example:** underlying average 3.74 is shown as 3.5 stars; 3.76 is shown as 4 stars (cutoff 3.75). Outcome: is a table for four available at 7 pm, checked 36 hours ahead?
  - This measures demand; it is **not** revenue or total customers.
- **Logic:** units just below the cutoff estimate the missing untreated outcome just above it.
- **Assumption:** without treatment there would be **no jump** at the cutoff. Then the observed jump = the effect **at the cutoff** (a local effect).
- **Threats (slide 8):**

  | Threat | Example | What to check |
  |---|---|---|
  | Precise sorting | Restaurants buy reviews to cross 3.75 | Counts near the cutoff; earlier characteristics |
  | Another treatment at the same cutoff | A promotion also starts at that rating | The actual rules, timing, implementation |
  | Distant comparisons | Comparing 3.2-star with 4.7-star places | Narrower windows; curvature |

  Passing these checks **supports** the design; it doesn't **prove** it.
- **Regression (slide 9):**
  - Centre the score: x = X − c. Treatment dummy: D = 1{X ≥ c}.
  - Model: Y = (α + τD) + (β + γD)·x + u, using only units within **bandwidth h** of the cutoff.
  - Two intercepts and two slopes: α = baseline at the cutoff, β = slope below, γ = change in slope above, **τ = the jump = the effect**.
- **Yelp result:** a jump of about 20 points (reported **+19.2 pp**).
- **Superfund** (Greenstone & Gallagher 2008):
  - Cleanup eligibility if the 1982 hazard score ≥ **28.5**. Unit = waste site linked to its census tract. Outcome = 2000 median home value.
  - With h = 12 (90 below, 137 above), the gap is **−$5.9K (SE $16.8K)**, i.e. no significant effect.
  - Bandwidth trade-off: narrower = closer comparisons but fewer observations; wider = more observations but more risk from curvature.
- **Sharp vs fuzzy RD:**
  - **Sharp:** everyone above the cutoff is treated, no one below.
  - **Fuzzy:** crossing the cutoff only makes treatment *more likely*. (Superfund: `listed_by_2000` ≠ `above_cutoff` for some sites.)

## Difference-in-differences (DiD), slides 15–28
- **Example:** an online retailer stops paid search in **40 of 80 Connecticut towns**. Outcome = monthly revenue **per eligible shopper**, counting everyone, including people who buy nothing.
- **Counterfactual** = the treated group's outcome without treatment, which is unobserved. Use the control group's **change** in its place.
- **Arithmetic:**
  - Treated $10.00 → $9.60 (−0.40). Control $8.00 → $8.40 (+0.40).
  - **τ = (−0.40) − (+0.40) = −$0.80** per shopper per month.
- **Parallel trends:** without treatment, both groups would have had the **same average change**. Levels can differ.
- **Pre-trends:** earlier similarity helps but **does not prove** the assumption. Example: a demand shock hits only the controls after treatment, and DiD comes out at +$0.18.
- **Three ways it fails:**
  - **Anticipation:** the effect starts before the recorded date.
  - **Spillover:** the controls are affected too.
  - **Concurrent shock:** another change happens at the same time.
- **TWFE (two-way fixed effects):** R_it = α_i (town FE) + δ_t (month FE) + τ·D_it + u_it. D = 1 for ads-off towns after the stop.
  - Same answer as the four-means DiD here (**−$0.820**) when the conditions hold: same towns every month, equal weights, one start date, no extra controls.
- **Event study:** a separate coefficient per month shows whether the effect **grows over time**. A single average can hide a loss that grows.
- **Unequal trends cause bias:** **bias = 18 × the extra monthly trend**, since 18 months separate the average pre and post observations.
  - Example: an extra +0.025/month turns a true −0.80 into an estimated −0.37.

## Synthetic control (SC), slides 29–36
- **Use case:** one treated market, where no single control (or simple average) matches its history. Here: New Haven stops ads in Jan 2025; 12 other CT towns keep them.
- **SC = a weighted average of untreated towns:**
  - weights are **nonnegative and sum to 100%**;
  - weights are fitted on **pre-treatment outcomes only**, by minimizing the mean squared gap;
  - then held fixed for the post period.
- **Result:**
  - Weights: Branford **59.2%**, Cheshire 20.6%, East Haven 15.6%, others 4.6% (West Haven 3.2%, Wallingford 1.4%).
  - Pre-treatment gap $0.031; average squared gap 0.001511.
  - **Effect −$0.827** per shopper per month (DiD on the same data: −$0.601).
- **The assumption changes:** DiD assumes equal average changes; SC assumes **a fixed weighted mix keeps tracking** the treated unit's untreated outcome.
  - It needs enough pre-periods and suitable controls.
  - Both methods still need: controls unaffected by the treatment, and no other treated-only change.
- **Robustness: drop the largest contributor** (Branford).
  - The pre-fit worsens (gap $0.190), and the effect becomes **−$0.668**.
  - The conclusion depends on Branford being a credible control.
- **Placebo (in-space) test:** pretend each untreated town stopped ads in Jan 2025 and fit its own SC.
  - Their gaps range from −0.11 to +0.31, vs **−0.827** for New Haven, so New Haven's gap stands out.

## Your turn (slides 38–40)
1. **RD (rd_superfund.csv):** estimate the jump at 28.5 separately for 1980, 1990 and 2000 home values. Plot the three fits and interpret.
   - Same bandwidth across years, then check another window. Separate slopes on each side.
   - **1980 is a pre-policy check and a mean; 1990 and 2000 are medians.**
2. **DiD (did_markets.csv):** 40 of 80 towns stop ads in Jan 2025.
   - Plot the comparison, estimate with **town + month fixed effects**, and interpret.
   - Inspect earlier trends first.
3. **SC (synth_markets.csv):** New Haven vs 12 controls.
   - Estimate the average 2025 effect; show the weights and both revenue paths.
   - Drop the largest contributor, refit, and assess whether the conclusion changes.
   - Weights nonnegative, summing to 1, fitted on pre-2025 only, then held fixed.

## Data files
- `rd_superfund.csv`, ~487 sites:
  - `site_id, tract_id, hazard_score, house_value_1980, house_value_1990, house_value_2000, listed_by_2000, above_cutoff`
  - Duplicate tract IDs are possible: several sites can share one tract.
- `did_markets.csv`, 2,880 rows (80 towns × 36 months, Jan 2023–Dec 2025):
  - `market, month, month_index, treated, post, shutdown, revenue`
- `synth_markets.csv`, 780 rows (13 towns × 60 months, Jan 2021–Dec 2025):
  - `market, month, month_index, treated, post, revenue`
  - Treated = New Haven; post = 2025.
