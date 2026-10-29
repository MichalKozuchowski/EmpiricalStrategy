# Class 15 slides: Supply, demand, and endogeneity (Thu Oct 29, 2026)

Source: `Supply_Demand_Endogeneity.html` (42 interactive slides, Kevin Williams). Data on Canvas:
`markets_demand.csv` (task 1), `markets_multi.csv` + a quality-change version (task 2).

## 1. The pizza market (slides 2–7)
- Demand `Qd = 120 − 2P`, supply `Qs = 20 + 3P`. Equilibrium: P = $20, Q = 80 units.
- **Moving along demand:** +$1 in price → −2 units (holding income, tastes, the product fixed).
- **Demand shock u** (e.g. a festival, not in the data): +20 units at every price.
  - The new equilibrium is P = 24, Q = 92. The shock raises **both** price and quantity.
- Solving the two equations: **P = 20 + u/5**. Price contains the unrecorded demand shock, so **price is endogenous**.
- Two observed points (A: $20/80, B: $24/92) can't tell you the demand curve.
  - If only demand shifted, they trace **supply**.
  - If both shifted, they trace **neither**.

## 2. Why OLS fails (slides 8–11)
- Demand equation: `Q = α + βP + u`. OLS needs price to be unrelated to u, but market clearing makes them correlated.
- If only demand shifts (supply fixed), regressing Q on P returns the **supply** slope (+3), not −2.
- **25 markets** with both curves shifting: OLS slope **+2.49**, so demand looks upward sloping. Every point is an equilibrium; demand slopes down in every market.
- **More data make the wrong slope more precise.** OLS converges to **+1.67**, not −2.
  - **Biased:** systematically misses.
  - **Inconsistent:** more data doesn't fix it.

## 3. Instrumental variables (slides 12–21)
- **Rule: to estimate one curve, find a shifter of the other curve.**
  - Supply shifts (flour costs) trace **demand**.
  - Demand shifts (income) trace **supply**.
- **Flour cost Z** contracts supply by 6Z. Price rises 1.2Z, quantity falls 2.4Z.
  - Points: A (Z = −1) $18.80/82.4; B (Z = 0) $20/80; C (Z = +1) $21.20/77.6.
- **Three requirements for an instrument:**
  - **Relevance:** flour moves price. A big first stage checks this.
  - **Exclusion:** flour has no other route to demand (quality, delivery…).
  - **Independence:** flour is unrelated to unrecorded demand factors u.
  - A strong first stage does **not** prove exclusion or independence.
- **IV as a ratio:** β_IV = (quantity response to Z) ÷ (price response to Z) = −2.4 / 1.2 = **−2**.
  - The quantity response is the **reduced form**; the price response is the **first stage**.
  - −2 is a slope, not an elasticity. Elasticity at B = −2 × 20/80 = **−0.5**.
- **2SLS = two regressions:**
  1. Regress P on Z; save the predicted price P̂ (= 20 + 1.2Z in the 15-market example).
  2. Regress Q on P̂. The slope is the IV demand response (−2; plain OLS on these 15 rows gives +2.46).
  - Markets with the same flour cost get the **same** predicted price, even if their observed prices differ (16 vs 24).
- **Why it works:** P = (20 + 1.2Z) [flour-driven] + 0.2u [demand-driven]. Keep the flour part, discard the demand part.
  - Substituting gives Q = 120 − 2P̂ + 0.6u. Demand shocks stay in quantity but no longer drive the price comparison.
- **Don't** report standard errors from the manual second stage. Use an IV routine.

## 4. Income as a control, and software (slides 22–26)
- Demand with income: `Q = 120 − 2P + 8W + u`. Income W is a **control** (it shifts demand directly), so it goes in **both stages**.
- One call does it:
  ```python
  from linearmodels.iv import IV2SLS
  fit = IV2SLS.from_formula("Q ~ 1 + W + [P ~ Z]", data=markets).fit()
  ```
  - `[P ~ Z]`: Z instruments P. Controls enter both stages automatically.
  - The companion script uses `cov_type="robust", debiased=True` (HC1).
  - Independent markets need no clustering.
- **2,000-market data:** OLS **+1.701** vs IV **−2.107** (true −2). The IV interval is wider: less (but credible) price variation.

## 5. Good vs bad instruments (slides 25, 27–28)
| | Estimate demand | Estimate supply |
|---|---|---|
| Good | Flour cost change (quality fixed) | Household cash transfer (costs fixed) |
| Bad | Premium flour (raises cost **and** taste) | Local jobs boom (raises income **and** supplier wages) |
- Published demand IVs:
  - Barahona, Otero & Otero (2023, *Econometrica*): Chilean cereal, using recipe-weighted corn/wheat/oat prices.
  - Angrist, Graddy & Imbens (2000, *REStud*): Fulton fish market, using offshore wind and waves.
- **Second instrument (oven energy costs):**
  - Valid extra variation → tighter estimates (−1.99 vs −1.98, narrower spread).
  - If energy also changes crust quality (+3 per unit of demand), estimates cluster around **−0.80** (precise but wrong).
  - A copied instrument adds nothing. An invalid one adds a misleading comparison.

## 6. Weak instruments (slide 30)
- **Strong** (price +$1.20 per $1 of flour): estimates stay near −2.
- **Weak** (+$0.05): the first 12 samples range from −16.5 to +4.5. Across 100 samples, 43 are **positive** and the range is −258 to +653.
- A noisy denominator makes the ratio unstable, and the sign and significance tests mislead.
- More data help only a nonzero first stage. They can't fix a zero response or an invalid instrument.

## 7. Estimating supply (slides 31–34)
- Income shifts demand. W = −1, 0, +1 gives (18.4, 75.2), (20, 80), (21.6, 84.8), so slope 9.6/3.2 = **3**.
- Supply: `Q = a + bP + cZ + v`. Here **flour is the control** (it shifts supply directly) and **income is the instrument**.
  - The first stage is the same (P on W and Z); the second stage changes (Q on P̂ and Z).
- 2,000 markets: OLS **+2.657** (SE 0.030) vs IV **+3.017** (SE 0.060, 95% CI [2.90, 3.14]). Truth = 3.
- Published supply IVs:
  - Sommer & Sullivan (2018, *AER*): housing construction, with real disposable income as the instrument (elasticity 0.90).
  - Shea (1993, *QJE*): cement, using builders' construction activity as the instrument.
- **Uses:** estimate each curve with its own excluded shifter; predict responses to cost or demand changes. These are market-level curves, not a firm's elasticity.

## 8. Your turn (slides 36–41)
1. **Estimate demand and supply** (`markets_demand.csv`, 2,000 rows).
   - OLS vs IV for each curve: slope per $1 plus uncertainty.
   - Choose the control and the excluded instrument for each curve.
   - Check both IV slopes another way.
   - Return code, results and validity arguments.
2. **Does a second instrument help?** Two files with flour + oven energy: a **cost-only** file and a **quality-change** file (energy also changes crust quality).
   - Compare demand IV using flour only, energy only, then both.
   - Keep the same rows and the income control.
   - Judge on the economic channel, not fit.
3. **Build your own simulated market** with AI: sample size, coefficients, shocks, instruments, adjustable seed.
   - Solve jointly for P and Q.
   - Verify the code first, then add an HTML dashboard.
   - Experiments:
     1. OLS vs IV recovers the truth?
     2. Strong vs weak valid instruments.
     3. Strong valid + weak invalid.
     4. Weak valid + strong invalid (a strong first stage with a wrong answer?).
     5. A few vs many weak instruments (bias toward OLS).
     6. An instrument excluded from demand but correlated with u (exclusion ≠ independence).
     7. A fixed violation + growing n: precise ≠ accurate.

## References
- Angrist & Krueger (2001), *Instrumental Variables and the Search for Identification*.
- Murray (2006), *Avoiding Invalid Instruments and Coping with Weak Instruments*.
- Bound, Jaeger & Baker (1995): weak instruments.
- linearmodels IV2SLS docs.
