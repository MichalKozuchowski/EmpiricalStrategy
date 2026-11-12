# Class 19 slides: logit and nested logit demand (Thu Nov 12, 2026)

Source: `Nested_Logit_Demand.html` (56 interactive slides, Kevin Williams).
- Builds on class 18 (`class18-slides.md`). The class 18 deck stopped at household types, so the share inversion, ξ and BLP are re-taught here, using **cars** instead of streaming.
- Reading posted alongside: the Netflix recommendations paper (`class18-reading-notes-netflix.md`).

## 1. Logit review with four cars (slides 2–4)
- U_ij = β_j − αp_j + ε_ij; not buying has V = 0 but keeps its own ε.
- **Worked example** (α = 0.00005 per $):

  | Car | Price | β | V | e^V |
  |---|---|---|---|---|
  | BMW | $50,000 | 1.51917 | −0.98083 | 0.375 |
  | Mercedes | $50,000 | 1.51917 | −0.98083 | 0.375 |
  | Mazda | $25,000 | 0.26917 | −0.98083 | 0.375 |
  | Toyota | $25,000 | 0.26917 | −0.98083 | 0.375 |

  - Denominator = 1 + 4(0.375) = **2.5** → each car **15%**, not buying **40%**.
- **Estimation:** log L = Σ log s_(i, chosen); pick the coefficients with the highest log-likelihood.
- A constant price coefficient does **not** mean constant elasticity, and plain logit gives every rival the **same % gain**.

## 2. Maximum likelihood with 10 coin flips (slide 5)
- Sequence H T H H T H H T H H: L(θ) = θ⁷(1−θ)³.
- log L = 7 log θ + 3 log(1−θ). Loss = −log L.
- **MLE θ̂ = 7/10 = 0.70** (log L = −6.109). Logs turn products into sums without changing the best θ.
- Back to logit: each observed choice contributes its model probability, and the coefficients replace θ.

## 3. Consumer surplus and profits (slides 6–11)
- **CS per household** = log(1 + Σ e^{V_j}) / α. Total CS = N × that. Compare scenarios with ΔCS = new − current.
- **BMW price $50k → $55k** (N = 10,000, other prices fixed):
  - Total CS **$183.26m → $176.51m (−$6.75m, −$675 per household)**.
  - Shares: BMW 15% → 12.08%; each rival 15.52%; not buying 41.37%.
  - The alternatives soften the loss.
- **Each car's demand area** = its value relative to the menu *without* it: −(N/α) log(1 − s_j).
  - BMW's area shrinks ($32.50m → $25.76m) and each rival's grows by $1.22m.
  - **Don't add the areas**: each is measured against a different remaining menu.
- **Profit** π = (p − mc) × N × s. BMW with mc = $20k:

  | BMW price | Sales | Profit |
  |---|---|---|
  | $50k | 1,500 | $45.0m |
  | $55k | 1,208 | $42.3m |

  - The same +$5k with **mc = $40k: profit +20.8%** (sales −19.4%). Fewer sales don't necessarily mean less profit; it depends on the margin.
- **AI prompt (slide 7):** plot total CS as BMW's price rises $0–5k, plus each car's own-price demand area.

## 4. Demand from market shares (slides 12–24)
- **Law of large numbers:** with 100,000 households, BMW gets 14,899 and not buying 40,134.
- **Utility with unobserved appeal:** U_ij = β + x_j'γ − αp_j + **ξ_j** + ε_ij.
  - ξ = appeal everyone sees but our data miss (e.g. a styling redesign).
  - ε averages out over many households. **ξ doesn't.**
- **Berry inversion:** s_j/s_0 = e^{V_j} → **log(s_j) − log(s_0) = V_j**.
  - Example: log(0.14899/0.40134) = **−0.991** (true −0.981).
- **Linear estimating equation:** log(s_jm) − log(s_0m) = β + x_jm'γ − αp_jm + ξ_jm. One observation = one car model in one year.
  - **Outside share:** use all potential households, not just buyers. Zero shares can't be logged.
- **Endogeneity:** appeal ξ raises both demand and price → Corr(p, ξ) ≠ 0 → use IV/2SLS. A cost shifter is valid only if it doesn't change appeal.
- **BLP (1995) cars** (1971–1990, 2,217 model-years):
  - **Outside option:** not buying a listed new car.
  - **Instruments:** other cars' numbers and features.

  | | OLS | IV |
  |---|---|---|
  | Price coefficient (per $1k, 1983 dollars) | −0.089 | **−0.216** |
  | Inelastic model-years | 1,494 | 22 |

- **Counterfactual: BMW 325i $18,860 → $23,860:** V_BMW falls by 0.000216 × 5,000 = **1.08**. Recompute every share with the new denominator.
- **Tariff on both German cars:** change both exponential terms in the denominator. Each loses less than if it alone raised its price.

## 5. Logit's substitution problem (slides 25–26)
- **Elasticity matrix** (α = 0.05 per $1k):

  | Demand ↓ / price → | BMW | Mercedes | Mazda | Toyota |
  |---|---|---|---|---|
  | BMW | −2.125 | +0.375 | +0.188 | +0.188 |
  | Mercedes | +0.375 | −2.125 | +0.188 | +0.188 |
  | Mazda | +0.375 | +0.375 | −1.062 | +0.188 |
  | Toyota | +0.375 | +0.375 | +0.188 | −1.062 |

  - **Mercedes gets no extra gain for being more similar to BMW** (red bus / blue bus).
- **BMW +1%:** BMW sales −2.106%; every rival **+0.372%** (approximation 0.375%).
  - Lost BMW sales go 17.6% to each car and **47.1% to not buying**, i.e. in proportion to starting shares, at every price step.

## 6. Nested logit (slides 27–40)
- **The manager chooses the groups ("nests"); the data estimate σ:**
  - Germany: BMW, Mercedes.
  - Japan: Mazda, Toyota.
  - Not buying: alone.
- **σ (0 ≤ σ < 1):**
  - σ = 0 is plain logit.
  - A larger σ makes same-nest cars closer substitutes.
  - **Example (BMW +10%):** the share of BMW's lost sales going to Mercedes rises from 17.6% (σ = 0) to 23.0%.
- **Preference shock:** ε^NL_ij = **ζ_ig** (shared by every car in nest g for household i) + **(1 − σ)ε_ij** (car-specific).
  - The total is still standard Gumbel; only how cars **move together** changes.
  - Within-nest correlation = 1 − (1 − σ)². It's zero across nests. **σ itself is not the correlation.**
- **Shares factor into two parts:** s_j = s_g (group share) × s_(j|g) (share within the group).
  - **Within-group share:** s_(j|g) = exp(V_j/(1−σ)) / D_g, where D_g = Σ_(k∈g) exp(V_k/(1−σ)).
  - **Group share:** s_g = D_g^(1−σ) / (1 + Σ_h D_h^(1−σ)); s_0 = 1 / (same denominator).
  - **Example** (σ = 0.6, V = −0.56494):
    - exp(V/0.4) = 0.24357, so D_g = 0.48714 and D_g^0.4 = 0.75.
    - s_Germany = 0.75/2.5 = **0.30**.
    - s_BMW = 0.30 × 0.50 = **0.15**.
- **Inversion (Berry 1994):** **log(s_j) − log(s_0) = V_j + σ log(s_(j|g))**.
- **Estimating equation:** log(s_jm/s_0m) = β + x'γ − αp + **σ log(s_(j|g,m))** + ξ.
  - **Two endogenous regressors:** price **and** the within-nest share (ξ raises a car's own within-nest share).
  - **You need at least 2 instruments.** Within-nest counts and sums of characteristics are the typical choice.
- **AI prompt (slide 39):** vary ξ_BMW from −1 to 1 with σ = 0.6 and fixed prices.
  - The within-group share moves: ξ = −1 gives 7.6% (log −2.579); ξ = +1 gives 92.4%.
  - So it needs an instrument even when price is fixed.
- **AI prompt (slide 31):** use the supplied `nested_logit_shock_sampler.py` to draw 3,000 households at σ = 0, 0.4, 0.8.
  - Plot the shared part, the car-specific part and the total.
  - Compare the BMW/Mercedes and BMW/Mazda scatterplots.

## 7. Nested logit on the BLP cars (slides 41–47)
- **Origin nests:** US, Europe, Japan, plus not buying.
- **Instruments:** other own-firm and rival characteristics, plus within-origin counts and sums.
  - **Failure case:** firms add European models because they foresee a surge in European demand, so the instruments move with ξ.
- **Estimates** (2SLS, clustered by model):

  | | Estimate | 95% interval |
  |---|---|---|
  | α (per $1k) | **0.174** | 0.140–0.208 |
  | σ | **0.163** | 0.030–0.295 |

  - This is the professor's extension, not published in BLP.
- **BMW 325i +$5k (1990): where BMW's lost sales go**

  | | Other European | US | Japanese | Not buying |
  |---|---|---|---|---|
  | Logit | 0.4% | 6.3% | 2.5% | 90.8% |
  | Nested logit | **15.8%** | 5.3% | 2.1% | 76.7% |

- **Profit** (N = 100m, mc = $12k):

  | Model | 325i sales | 325i profit |
  |---|---|---|
  | Logit | −66.0% | −$86.5m |
  | Nested logit | −64.4% | −$80.5m |

  - **Cannibalization:** BMW's 535i and 735i gain +0.86% each (+$1.9m, +$1.1m), so **BMW's total profit change is −$77.4m**.
- **The choice of nests changes the answer:**

  | Nests | α | σ | BMW profit change |
  |---|---|---|---|
  | US/Europe/Japan | 0.174 | 0.163 | −$77.4m |
  | US/imported | 0.132 | 0.505 | **−$112.1m** |
  | Small/medium/large | 0.084 | 0.494 | −$51.2m |

  - **Don't pick nests to get the answer you want.** Use switching data or held-out price changes to check them.
- **IIA still holds within a nest:** s_BMW/s_Mercedes doesn't change when Mazda's price changes. Each car belongs to only one nest.
  - Random-coefficients (mixed) logit is the richer alternative.
- **Nested logit adds** flexible within- vs across-group substitution and better cannibalization and CS predictions.
  - It **keeps** closed-form shares and a linear inversion.
  - It **costs** an extra endogenous regressor and a partition you have to defend.

## 8. Your turn (slides 50–55)
1. **Simulate and estimate binary logit:**
   - **Setup:** N = 2,000, seed 634, price uniform $20k–60k, β = 2.1, α = 0.00005, Gumbel(0,1) shocks on **both** choices.
   - Fit a logit with an intercept and compare with the truth. Plot the true vs fitted probability curves.
   - **(a)** U_out = 2 + ε → the intercept becomes β − 2 = 0.1, and α is unchanged. Subtracting 2 from **both** utilities changes nothing. That's what normalization means.
   - **(b)** Normal(0,1) errors instead → logit is misspecified but may still approximate the probabilities. The true probability is Φ((2.1 − 0.00005p)/√2).
   - **(c)** Probit on the normal data: its coefficients are the utility coefficients divided by √2.
2. **Logit dashboard (HTML):** the 4 cars at $50k/$50k/$25k/$25k, N = 10,000.
   - Each car gets a price control and an available/unavailable switch.
   - Show shares, quantities, % changes, CS per person and in total, and a Reset button.
   - **Scenarios** (each against the original market):
     - **(a)** BMW → $55k: BMW −19.45%, rivals +3.43% each, CS −$6.75m.
     - **(b)** all four prices +3% ($51,500 and $25,750).
     - **(c)** BMW removed: each remaining car 0.15/0.85, not buying 0.40/0.85, and CS falls.
3. **Nested logit dashboard:**
   - Germany = BMW/Mercedes, Japan = Mazda/Toyota, not buying alone.
   - Start every car at 15% and not buying at 40%. Recalibrate V_j0 = ln(0.15/0.40) − σ ln(0.5) for each σ ∈ {0, 0.4, 0.8}.
   - Raise BMW's price by $0–5k; plot the Mercedes and Mazda % gains against σ.
   - **Check:** σ = 0 must reproduce plain logit.

## References
- Berry (1994).
- Berry, Levinsohn & Pakes (1995).
- Train, chapters 3 (logit), 4 (nested logit/GEV) and 13 (endogeneity).
- PyBLP docs (automobile data; logit and nested-logit estimation).
