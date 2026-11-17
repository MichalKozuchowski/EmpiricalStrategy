# Class 20: Zappos demand estimation lab (Tue Nov 17, 2026)

In-class lab on the Zappos point-of-sale data. The data is the same as in Quan & Williams, "Product Variety, Across-Market Demand Heterogeneity, and the Value of Online Retail" (Cowles DP 2054R3); see `class12-reading-notes-product-variety.md`.

**Board rules:**
1. Don't prompt "estimate logit with these data"; think through the choices.
2. Don't reuse old Zappos (HW2) code.
3. Use the cluster or your own machine; the data link is on Canvas.

**Numbers below are from the full data run on the cluster.**

---

## Task 1: inspect the 5 files

| File | One row = | Size | Key contents | Issues |
|---|---|---|---|---|
| `POS.dta` (2.4 GB) | one pair sold (99.9% of transactions are 1 row) | 13,546,258 rows, 842 brands, 61,433 skus, 144,304 sku-colors, 63 "states", 35,935 zips | price paid, msrp, sale flag, discount, % off, brand, sku, colorid, styleid, state, zip, two timestamps | 2012-07-13 → 2013-08-15, so the **first and last months are partial**. Two clocks about 2 h apart (we use `sdate_*`). 4 blank states plus military codes (AA/AE). **Up to 3 skus share one styleid**, so the key is (sku, styleid). Avg price $86.26 (median $70.99); 30.8% of units sold on sale |
| `stock_chars.dta` | sku × color (`style_id`) | 117,493 rows, 50,050 skus | `orig_price`, `gender`, heel height, weight, materials, closures, toe style, occasion, color | Characteristics are **unlabeled codes**; many columns are mostly missing; **fixed over time**. 409 duplicate style_ids, but (sku, style_id) is unique |
| `brand_list.dta` | sku | 61,433 | brand (615 brands) | 100% of POS skus match |
| `categories.csv` | sku | 61,421 | `categ` 0–10 | Unlabeled. Alphabetical: 0 Boat, 1 Boots, 2 Climbing, 3 Clogs, 4 Flats, 5 Heels, 6 Loafers, 7 Oxfords, 8 Sandals, 9 Slippers, 10 Sneakers |
| `reviews.csv` | sku × month (2012–13) | 297,388 | `rev_cnt`, `overall`, `comfort`, `look` | **Cumulative** (counts only rise; ratings are running averages). Only 34.6% of POS skus have reviews (55% of product-weeks) |

**Product hierarchy:** brand ⊃ sku (a shoe model) ⊃ styleid (model × color) ⊃ size (not in the data).

**Gender codes** (decoded from item names; Stata's `encode` = alphabetical):

| Code | Label | Evidence |
|---|---|---|
| 1 | Boys | 99% of item names contain kids' words |
| 2 | Girls | 100% |
| 3 | Men | 2% |
| 4 | Unisex | 195 skus |
| 5 | Women | 1%; the biggest group |

Shares of units: Women 53%, Men 26%, Boys 8.3%, Girls 7.3%, Unisex 0.7%, no characteristics match 4.7%.

## Task 2: market (m) and product (j) definitions

**Where does price vary?**

| Dimension | Finding | Meaning |
|---|---|---|
| Across space (same style, same day, different states) | Prices differ only **0.8%** of the time | **Prices are national.** Geography adds no price variation |
| Over time | **71%** of styles change price at least once; 2.43 distinct prices per style (3.09 distinct weekly prices per product) | Markdowns over time = **the identifying variation** |
| Across colors (same sku, same day) | **30%** of sku-days have colors at different prices | Pooling colors into "sku" mixes different prices |
| Within a day | 0.3% change | A day or week is effectively one price |
| Characteristics | Never change | Absorbed by product fixed effects |

**Sparsity (share of possible product × market cells with any sale):**

| Market × product | Cells with sales | Median units |
|---|---|---|
| National × week, brand | 79% | 89 |
| National × week, sku | 32% | 4 |
| National × week, sku-color | 27% | 3 |
| National × month, sku-color | 38% | 7 |
| State × month, sku-color | 5% | 1 |
| Zip × month, sku-color | **0.03%** | 1 |

**Decisions:**
- **j = sku × color (sku, styleid).**
  - That's where prices are set (colors are priced differently 30% of the time).
  - It's also the key that links to the characteristics.
- **m = national × week, separately by segment (women / men / girls / boys).**
  - Prices are national, so geography only adds zeros (you can't take the log of a zero share).
  - Weekly keeps markdown timing: monthly averaging cut the elasticity from −1.0 to −0.6.
  - Segments are separate markets: a women's heel doesn't compete with a toddler's sneaker.
  - The paper-spec model uses national × month for comparability with the paper.
- **Price of j in m** = the average price paid that week (the paper spec uses the monthly median).

**"If j is brand, what is Nike's price?"**
- There is none: Nike sells hundreds of shoes, so a "Nike price" is an average over whatever sold that week.
- In the data, the units-weighted "Nike price" drifts **$74.76 → $76.35**, and the median product price jumps **$72 → $75**, **with no Nike price change**. It just reflects which shoes sold.
- A demand model would wrongly read that as a price change. So brand is the wrong j.

## Merging the data at (j, m)

Every merge printed row counts before and after (the class 7 rule), and every merge was **×1.000**:

| Merge | Key | Result |
|---|---|---|
| Category | sku | 100% matched |
| Characteristics | (sku, styleid) | 93.3% of cells |
| Reviews | sku × **previous month** | 55.4% of cells. Shoppers only see reviews written before the purchase (no look-ahead) |

The final product-week dataset has **2,235,875 rows** (about 40,000 products and 238,000 units per week). The partial first and last weeks are dropped.

## Market size (the professor's prompt)

"How many people did *not* buy?" This is an assumption you fix. Following Quan & Williams: **each person considers buying one pair of shoes per year**, by segment, so weekly M = population ÷ 52.

| Segment | US population (2013, approx.) | M per week | Inside share |
|---|---|---|---|
| Women | 124M | 2.38M | 5.3% |
| Men | 118M | 2.27M | 2.7% |
| Girls | 36M | 0.69M | 2.5% |
| Boys | 37.6M | 0.72M | 2.8% |

- The outside share is 93–99%.
- **With segment × week fixed effects, log(s₀) is constant within each market and gets absorbed, so M does not change α.** We confirmed this: the estimates were identical before and after changing M.
- M matters for share levels, consumer surplus and diversion to the outside option.

## Estimation 1: Berry (1994) logit with ξ: what identifies the price effect?

Outcome: ln(s_j) − ln(s_0). Product + week fixed effects mean the price effect comes only from each shoe's own price changes over time.

| Specification | α (per $) | Own elasticity |
|---|---|---|
| OLS, no FE | 0.0020 | −0.19 |
| OLS, product + week FE, all products | 0.0030 | −0.29 |
| OLS, product + week FE, **steady sellers** (sold in ≥ 90% of weeks; 4,889 products) | **0.0117** | **−1.02** |
| OLS + FE, monthly, steady sellers | 0.0059 | −0.59 |
| 2SLS, "brand's other skus on sale" instrument | **negative** (wrong sign) | +0.3 to +2.9 |
| **2SLS, vendor MSRP instrument**, steady sellers (first-stage F = 303) | **0.0203** (SE 0.0022) | **−1.76** |

**Lessons:**
1. **Zero-sale selection.** Thin cells hide the weeks a shoe didn't sell, so α was biased toward 0. Steady sellers made α 4× larger.
2. **The brand-markdown instrument is strong (F ≈ 10,000) but invalid.** Brand-wide sales are promoted, so they also drive traffic: that breaks the exclusion restriction (the class 15 lesson).
3. **MSRP (vendor list-price) changes:**
   - They move Zappos' price and are vendor-driven, and the IV comes out *more* elastic than OLS. That's consistent with markdowns happening when demand is weak.
   - **Risk:** the "was $X" reference price shown to shoppers may affect demand directly.

**By segment (2SLS, MSRP instrument):**

| Segment | α (SE) | Own elasticity |
|---|---|---|
| Boys | 0.0396 (0.012) | −1.76 |
| Girls | 0.0476 (0.012) | −2.11 |
| Men | 0.0188 (0.003) | −1.82 |
| Women | 0.0198 (0.003) | −1.82 |

**Kids are about 2× more price-sensitive per dollar.** Elasticities are similar (−1.8 to −2.1) because kids' shoes are cheaper.

**Our own nested-logit attempt** (nests = gender × category, with simple instruments) gave σ ≈ −1.5. That's outside [0, 1), so it's rejected. Those instruments don't vary enough within a product over time.

## Estimation 2: maximum likelihood, no ξ (no Berry, no instruments)

- **Setup:** each potential buyer in a segment-week market picks one product or the outside option.
- **Controls:** price, log(1 + reviews), rating, has-reviews, segment intercepts, category and month dummies. **No product fixed effects and no ξ.**
- **Data:** 2,073,931 product-weeks, 224 markets.

| Variable | Coefficient | SE |
|---|---|---|
| Price (per $100) | −0.2574 | 0.0006 |
| log(1 + reviews) | +0.294 | 0.0002 |
| Rating | +0.062 | 0.0007 |
| Has reviews | −0.442 | 0.0010 |

- **α = 0.0026 per $, mean elasticity −0.25.**
  - Without ξ the model compares different shoes, and expensive shoes are better shoes, so price looks harmless.
  - The tiny SEs are precision around the wrong number: more data doesn't fix endogeneity.
- **Nested-logit maximum-likelihood profile:**

  | σ | Log-likelihood |
  |---|---|
  | 0 | **−170,427,385** (converged; matches the logit exactly, which checks the code) |
  | 0.4 | −170,878,263 |
  | 0.8 | −172,115,679 |

  - The no-ξ model prefers **σ ≈ 0**. The σ > 0 fits hit a 200-iteration cap, but the gaps are large.

## Estimation 3: the paper's national nested logit (Berry inversion + IV + GMM; professor's spec)

**Setup:**
- j = sku × color; m = national × month (Aug 2012 – Jul 2013); **men and women separately**; nests = shoe category.
- **Choice set:** each product is available from its first to its last month with a sale. Zero-sale months get 0.17 units (approximating Gandhi–Lu–Shi); 5.8% of rows are zeros (paper: about 6%).
- **Price** = the monthly median price paid; zero-sale months use the nearest observed price.
- **Market size:** adult population, one decision per person per month.

**Equation:** ln s_jt − ln s_0t = xβ − αp_jt + λ ln s_{j|g,t} + ξ_jt. **Endogenous:** price and ln s_{j|g}.

**Controls (x):**
- overall, look and comfort ratings, plus a no-reviews dummy;
- category × cold-season dummies (Boots and Sandals, Sep 2012 – Feb 2013);
- **brand fixed effects by demeaning:** brands averaging at least 50 units/month get their own group; the rest are pooled.
- **No month fixed effects:** λ is identified from category × month variation.

**7 instruments:**
1. The number of colorways of the same sku available that month.
2. The **sums and averages of rival brands'** overall, look and comfort ratings within the same category-month (6 instruments).

| | Price coef. | λ | Mean elasticity (sd) | N |
|---|---|---|---|---|
| Men, paper | −0.0060 | 0.814 | −3.64 (2.74) | 173,304 |
| Men, ours, GMM | −0.0068 (0.0004) | 0.866 (0.005) | −5.74 (4.24) | 176,072 |
| Men, ours, 2SLS | −0.0099 (0.0006) | 0.783 (0.008) | −5.13 (3.79) | 176,072 |
| Women, paper | −0.0154 | 0.370 | −3.06 (2.67) | 362,184 |
| Women, ours, GMM | −0.0115 (0.0004) | 0.489 (0.006) | −2.69 (2.29) | 378,733 |
| Women, ours, 2SLS | −0.0110 (0.0004) | 0.467 (0.006) | −2.48 (2.11) | 378,733 |

- All estimates are valid: the price coefficient is negative and λ is in [0, 1).
- **Women replicate closely. Men are more elastic** (higher λ → larger 1/(1−λ)), which matches the spec's expected rebuild (−5.7).
- **Men substitute within category much more** (λ ≈ 0.8–0.87) than women (λ ≈ 0.47–0.49).
- **First stage:** partial R² is only 0.24–0.55% for price and 2–4% for the within-nest share. F is in the thousands only because N is huge, so report both.
- **Missing from the lab data:** the inventory choice set and the photo-based color dummies.

## The big picture

| Method | ξ? | Identification | Own elasticity |
|---|---|---|---|
| Maximum-likelihood logit / nested logit | No | Compares different shoes | −0.25 |
| Berry logit, product + week FE (OLS) | Yes | Own markdowns | −1.0 |
| Berry logit, 2SLS with MSRP | Yes | Vendor list-price changes | −1.8 (adults), −1.8 to −2.1 (kids) |
| **Berry nested logit, rival-brand instruments + GMM (paper)** | Yes | Rival ratings, style count | **−2.7 (women), −5.7 (men)** |

**Takeaway:**
- Ignoring unobserved quality (ξ) makes shoe demand look about 10× too inelastic.
- Allowing ξ, instrumenting price, and letting shoes within a category be closer substitutes gives elasticities of −2 to −6, in line with the paper's −3.
- **The market definition, the treatment of zero-sale cells, and the choice of instrument each move the answer a lot:** that's the empirical-strategy lesson of the day.
