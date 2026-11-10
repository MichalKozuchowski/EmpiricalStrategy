# Class 18 slides: discrete choice and logit demand (Tue Nov 10, 2026)

Sources:
- `Session18_Logit_Demand.html` (59 interactive slides, Kevin Williams).
- Companion guide `discrete_choice_guide.pdf` (50 pp., "Understanding Discrete Choice Models: From Binary Logit to Berry (1994)").
- Data: `data.zip`, 4 CSVs + README (see the bottom of this file).

All streaming data, prices and results are **invented teaching simulations**, not real Netflix/Disney+/Hulu plans or behavior.

## 1. Binary logit: subscribe to Netflix, yes or no? (slides 2–10)
- **One observation** = one household's one-month yes/no decision. **Keep both buyers and refusals.**
- **Utility explained by price:** V = β − αp = 2.1 − 0.10p. At $20, V = 0.1.
  - The units are utility, not dollars. A $1 increase lowers *utility* by 0.10, **not** the probability by 10 points.
- **Total utility:** U_N = V + ε_N (Netflix) vs U_0 = 0 + ε_0 (not subscribing). The household picks the higher one.
  - ε is a preference the analyst can't see (taste for the shows, other uses of free time). The household knows it.
  - **Same $20 offer, different choices:**
    - Household A: ε_N = −0.4, ε_0 = 0.2 → −0.3 < 0.2, so it declines.
    - Household B: ε_N = 0.4, ε_0 = −0.2 → 0.5 > −0.2, so it buys.
  - Setting the outside option's V to 0 is a **normalization** (a reference level); its ε stays.
- **The ε distribution:** Type I extreme value (Gumbel), one independent draw per option.
  - Its right tail is heavier than a normal's: >3 SD above the mean happens 1.19% of the time vs 0.13%.
  - The **difference of two Gumbels is logistic**, with heavier tails on both sides (0.86% vs 0.27% beyond 3 SD).
- **Buy if V > Δε** (Δε = ε_0 − ε_N). That gives the **logit formula**: s = e^V / (1 + e^V).
  - At V = 0.1, s = **52.5%**. At $0, s = 89.1%.
- **AI prompt (slide 8):** simulate 1,000 households with Gumbel draws; the share buying approaches 52.5%. The slide's seed gives 51.6%.
  - You don't need to simulate in practice: the formula integrates over the preferences for you.

## 2. Estimating by maximum likelihood (slides 11–15)
- **Likelihood** = the probability the model assigns to the choices actually observed: s for a buyer, (1 − s) for a refuser.
  - Multiply across households, or add the logs.
  - **Example** (β = 2.1, α = 0.10):
    - A bought at $10: s_A = 0.750.
    - B refused at $20: 1 − s_B = 0.475.
    - C bought at $30: s_C = 0.289.
    - L = 0.103, log L = −2.273.
- **One purchase can't pin down two coefficients.** (2.1, 0.10) and (4.1, 0.20) give the same V at $20.
  - You need purchases **and** refusals at **different prices**.
- **MLE** picks the β and α that maximize the log-likelihood.
  - On the real with-ads data (prices $10–35): β = 2.212, α = 0.1047, log L = −1799.6.
- **Why logit is convenient:**
  - closed-form probabilities, no simulation needed;
  - a **concave** log-likelihood (one peak, no local maxima);
  - **but** if the model perfectly separates buyers from non-buyers, the coefficients run off to infinity.

## 3. The ad-free feature, forecasts and willingness to pay (slides 16–20)
- **Adding the feature:** V = 2.1 − 0.10p + 0.6x (x = 1 if ad-free). At $20, take-up goes from 52.5% to **66.8%** (+14.3 points).
- **Estimated** (randomized prices and features):
  - V̂ = **2.193 − 0.1038p + 0.587x**;
  - price 95% CI [−0.1108, −0.0968];
  - ad-free 95% CI [0.475, 0.700].
- **Forecast for 500 households, with ads:**

  | Price | Share | Accounts | Fee revenue |
  |---|---|---|---|
  | $20 | 52.9% | 264.5 | $5,290 |
  | $24 | 42.6% | 212.9 | $5,109 |

  - This is **fee revenue, not profit**: no ad revenue, costs or renewals.
- **The price premium that offsets removing ads:** set the utilities equal → **Δp = γ/α = 0.5875/0.10384 = $5.66/month**.
  - Dividing by α converts utility into dollars.
- **Out-of-sample check:** fit on one sample, predict for the new households at the same prices, and compare.
  - Systematic gaps would mean a missing feature or the wrong price relationship.

## 4. Multinomial logit: choosing among services (slides 21–27)
- **The menu** (one paid subscription slot, or none): V_j = β_j − 0.10p_j + 0.6x_j.

  | | Netflix | Disney+ | Hulu | Not buying |
  |---|---|---|---|---|
  | β | 2.10 | 0.85 | 0.25 | — |
  | Price | $20 | $15 | $10 | — |
  | Ad-free | no | yes | no | — |
  | V | +0.10 | −0.05 | −0.75 | 0 |

- **Probabilities:** exponentiate each V, add them up (the outside option contributes **e⁰ = 1**), then divide.
  - D = 1.105 + 0.951 + 0.472 + 1 = 3.529.
  - Netflix **31.3%**, Disney+ 27.0%, Hulu 13.4%, not buying 28.3%.
- **The formula:** s_j = e^{V_j} / (1 + Σ_k e^{V_k}) and s_0 = 1 / (1 + Σ_k e^{V_k}).
- **This is the same softmax language models use** for next-token probabilities. Adding Gumbel noise and taking the largest = sampling from softmax (the Gumbel-max trick).
- **Unchosen offers matter:** removing Hulu raises Netflix's probability to 36.2%.
  - The data **must** keep every offered alternative: one row per household per alternative, exactly one chosen, plus the outside option.
  - **Never** estimate separate binary logits per provider.
- **MLE on `streaming_choices.csv`:**

  | Coefficient | Estimate | 95% CI |
  |---|---|---|
  | Netflix FE | 2.3372 | [2.074, 2.600] |
  | Disney+ FE | 1.0262 | [0.819, 1.234] |
  | Hulu FE | 0.4640 | [0.307, 0.621] |
  | Price (−α) | −0.1139 | [−0.1266, −0.1013] |
  | Ad-free | 0.6494 | [0.561, 0.738] |

## 5. Substitution, elasticities and IIA (slides 28–34)
- **Raising Netflix's price reallocates accounts across *all* options**, the outside one included.
  - **$20 → $15:** Netflix +11.6 pts, Disney+ −4.6, Hulu −2.3, not buying −4.8.
  - **$20 → $21:** Netflix −2.1 pts; Disney+ +0.8, Hulu +0.4, not buying +0.9.
- **Own-price elasticity:** E_j = −α p_j (1 − s_j). It is **not constant**:
  - $15 → −0.86;
  - $20 → −1.37;
  - $30 → −2.57.
- **Cross-price elasticity:** E_jk = α p_k s_k. It is the **same for every rival** when k's price changes.
- **The elasticity matrix** (rows = whose demand, columns = whose price):

  | | Netflix price | Disney+ price | Hulu price |
  |---|---|---|---|
  | Netflix demand | −1.37 | +0.40 | +0.13 |
  | Disney+ demand | +0.63 | −1.10 | +0.13 |
  | Hulu demand | +0.63 | +0.40 | −0.87 |

  - Cross values **repeat down each column**. That is logit's strong restriction.
- **AI prompt (slide 30):** build this matrix, plot the demand curves, and check it with tiny numerical price changes.
- **IIA (independence of irrelevant alternatives):** s_N/s_D = e^{V_N − V_D} = 1.162, *whatever* happens to Hulu.
  - Lost customers spread **in proportion to current shares**.
- **A duplicate listing** of the same Hulu plan, treated as independent, inflates Hulu's combined share from 13.4% to 23.6%. That's a misspecification; deduplicate.
- **Red bus / blue bus (Train):**
  - Car vs blue bus is 50/50. Add an identical red bus → logit says 33⅓% each.
  - Reality: car 50%, and the two buses split 25/25.
  - The problem is **correlated preferences** for similar options.

## 6. Household types and consumer surplus (slides 35–39)
- **Two types**, half the market each:
  - type A is price-sensitive (−0.15);
  - type B much less so (−0.05).
  - Average their probabilities to get the market share (a finite mixture of logits).
- **Netflix $20 → $24, from the same starting shares:**

  | Change in share | Netflix | Disney+ | Hulu | Not buying |
  |---|---|---|---|---|
  | Common coefficients | −7.91 | +3.10 | +1.54 | +3.26 |
  | Two types | −8.32 | +2.22 | +2.27 | +3.83 |

  - Mixtures relax IIA in the aggregate, but each type still has IIA.
- **Consumer surplus per person:** CS = log(1 + Σ e^{V_j}) / α (the "logsum").
  - ΔCS = CS_new − CS_current, for a price change, a new service or a removed option.
  - **For types:** compute each type's CS with its own α, then average.
- **Binary example** (β = 2.1, α = 0.10): CS(p) = ∫_p^∞ s(z) dz = log(1 + e^{2.1 − 0.1p}) / 0.1.
  - CS = **$13.87** at $10, **$7.44** at $20, **$3.41** at $30 per person. That's buyers *and* non-buyers, and not revenue or profit.
- **AI prompt (slide 38):** shade CS under the demand curve and check the integral against logsum/α.

## 7. Demand from market shares: Berry (1994) (slides 40–50)
- **Law of large numbers:** with more households, observed shares approach the probabilities.
  - With 100,000 households: Netflix 30,953 (31.0%), not buying 28,577. log(s_N/s_0) = 0.080 (the true V is 0.1).
- **Utility with an unobserved product appeal ξ:** U_ij = δ_j + ε_ij, where δ_j = β − αp_j + γx_j + **ξ_j**.
  - ξ = appeal shared by everyone but **missing from our data**, e.g. a hit series popular in New Haven.
  - ε varies by person and averages out in shares. **ξ doesn't average out**, however many households you have.
- **Berry's inversion:** s_j/s_0 = e^{δ_j}, so **log(s_j) − log(s_0) = β − αp_j + γx_j + ξ_j**.
  - That's a **linear regression on market shares**; no individual purchase records are needed.
  - **With many markets m:** log(s_jm) − log(s_0m) = β_j − αp_jm + γx_jm + ξ_jm, with product fixed effects β_j.
  - You can't log a zero share; don't silently add a constant.
- **Price endogeneity:** firms raise prices when appeal (ξ) is high, so Corr(p, ξ) ≠ 0 and OLS is biased.
  - **Fix with an instrument:** the **hosting-cost shock**.
    - It must move price.
    - It must be unrelated to ξ.
    - It must leave quality and catalog unchanged. **Bad** if it's spending that improves streaming quality.
  - Use 2SLS on the log-share equation: provider dummies and ad-free are controls in both stages.
- **Streaming market data** (truth −0.10):

  | | Price coefficient |
  |---|---|
  | OLS | **+0.0231** (wrong sign) |
  | 2SLS with cost instrument | **−0.0866** |

  - Standard errors are market-clustered.

## 8. Applications (slides 51–53)
- **Cars: BLP (1995) Table III**, model-year data 1971–1990 (2,217 observations).
  - Car features: horsepower/weight, air conditioning, miles per dollar, size.
  - **The outside option:** not buying a new car.

  | | OLS logit | IV logit |
  |---|---|---|
  | Price coefficient | −0.089 (SE 0.004) | −0.216 (0.123) |
  | Inelastic model-years (nonsense for profit-maximizers) | 1,494 | 22 |

  - Instruments: features and counts of the firm's other cars and of rivals' cars.
- **Netflix M001, $19.82 → $23.82** (starting from observed shares):
  - **OLS** predicts accounts **+28.1%** (the wrong sign).
  - **IV** predicts **−6.9%** (95% [−11.5%, −2.1%]).
  - Starting accounts 1,254; fee revenue $24,854.

## 9. What logit gives you vs what you must establish (slide 54)
| Logit gives | The analyst must establish |
|---|---|
| Probabilities sum to 1; sales = share × eligible population | Is one subscription the real decision, or do households buy bundles? |
| Fast closed-form predictions | Are the coefficients and population stable? |
| Price and feature tradeoffs | What identifies a causal price or feature effect? |
| One price change updates all options | Is proportional substitution (IIA) plausible? Do types differ? |

**Next:** nested logit (shared appeal within groups). It does **not** fix price endogeneity.

## 10. Your turn (slides 55–58)
1. **Subscription and the value of ad-free** (`streaming_quotes.csv`, check on `streaming_new_households.csv`):
   - Binary logit, keeping the refusals. Report the coefficients and their uncertainty.
   - Predict accounts and fee revenue at $20 vs $24 (with ads) for 500 households.
   - Compute the ad-free offsetting premium γ/α.
   - Check predicted vs observed rates on the new households.
   - Explain what the model can't establish (profit, renewals).
2. **A dashboard for competing offers** (`streaming_choices.csv`):
   - Estimate the multinomial logit (outside option included).
   - Build an interactive dashboard: each provider's price, ad-free and availability → all probabilities and accounts.
   - Show where Netflix's lost accounts go.
   - Compare a new provider with a duplicate listing.
   - Try two assumed household types from the same starting shares.
3. **Endogenous prices** (`streaming_markets.csv`):
   - Build provider and outside shares.
   - Estimate the log-share equation by OLS and by IV with the hosting-cost shock.
   - Recompute all shares for a +$4 Netflix price in M001, and compare fee revenue.
   - Argue the instrument's validity, and how it fails if cost also changes service quality.
   - **Check:** a zero price change must reproduce the original shares.

## Data (`data.zip`)
| File | Rows | Contents |
|---|---|---|
| `streaming_quotes.csv` | 6,000 households | household_id, price_monthly ($10/15/20/25/30/35), ad_free, subscribed |
| `streaming_new_households.csv` | 1,500 | Same fields; a holdout for checking predictions |
| `streaming_choices.csv` | 16,000 = 4,000 households × 4 options | household_id, provider (Netflix/Disney+/Hulu/No paid service), price_monthly (outside = 0), ad_free, chosen (one per household) |
| `streaming_markets.csv` | 720 = 240 markets × 3 services | market_id, provider, price_monthly, ad_free, accounts, eligible_households (repeated per row; **don't sum it**), hosting_cost_shock |

- **Outside count** = eligible − sum of the 3 account counts.
  - Check unique keys, a common population within each market, and positive shares before taking logs.
- **Example, M001:**

  | Eligible | Netflix | Disney+ | Hulu | No paid service |
  |---|---|---|---|---|
  | 4,222 | 1,254 | 1,109 | 571 | 1,288 |

## Companion guide (`discrete_choice_guide.pdf`)
An intuition-first walk-through:
1. binary logit, MLE, odds and marginal effects;
2. multinomial logit, the outside option, IIA, elasticities;
3. Berry (1994): ξ, the inversion, IV/2SLS, the outside share, MLE vs Berry, a cereal example;
4. a glossary, math supplement (Gumbel, MLE first-order conditions, GMM);
5. Python code (binary logit, shares, inversion, OLS vs IV, elasticities, plots) and tips for AI coding assistants.

## References
- Train, *Discrete Choice Methods with Simulation*, chapter 3 (logit) and chapter 13 (endogeneity).
- Berry (1994), *RAND Journal of Economics*.
- Berry, Levinsohn & Pakes (1995), *Econometrica*.
- statsmodels Logit.
- NIST Gumbel.
- Vaswani et al. (2017).
- Jang, Gu & Poole (2017).
