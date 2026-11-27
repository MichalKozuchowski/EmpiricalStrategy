# Data notes (verified facts, Nov 27, 2026)

## Source
**Iowa Liquor Sales**, Iowa Department of Revenue, Alcoholic Beverages Division (ABD), CC BY 4.0.
- **Coverage:** every spirits order by every Class E licensee (private liquor stores, groceries, convenience stores) from the state wholesaler, 2012 to now.
- **Download:** one dataset per year at `https://idh-be.iowa.gov/api/v1/datasets/<id>/rows.csv`. It returns a **ZIP of part CSVs** (about 550 MB per year; it downloads in seconds). `code/01_download.py` has the year → id map.
- **Size:** about 2.4–2.6M order lines per year, about 2,100 stores, about 5,200 items, 44 categories.

**Columns:** `invoice_id, ordered_on, store_no, store_name, store_address, store_city, store_zip_code, county_fips_code, county_name, category_code, category_name, vendor_number, vendor_name, item_no, im_desc, pack, bottle_volume_ml, state_bottle_cost, state_bottle_retail, sales_bottles, sales_dollars, sales_liters, sales_gallons`

## Facts that drive the design
| Fact | Evidence | Implication |
|---|---|---|
| **`state_bottle_cost` and `state_bottle_retail` are blank in every row** on the new portal | 100% missing in 2019, 2023 and 2024 | Price per bottle = `sales_dollars / sales_bottles` (what the store paid the state) |
| **State price = 1.5 × supplier cost** | Current product list (dataset 1029, 14,040 items, as of 2026-11-01): retail/cost = 1.500 for 99.9% | Cost = price / 1.5. The state's margin = price / 3. That's Iowa Code §123.24's 50% markup |
| **Prices are uniform statewide** | Same item, same day, different stores → different unit price in only **0.03%** of item-days (2024) | Geography gives no price variation; the price effect is identified from **changes over time** (as at Zappos and in Pennsylvania) |
| **Prices change rarely** | In 2024, only **15%** of items (≥ 50 orders) changed price; 1.16 distinct prices per item. Top sellers (e.g. Black Velvet 1.75L at $6.45 → $6.54 in Oct) were flat most of the year | We need several years, and identification will lean on discrete list-price changes plus tariff shocks |
| **The product list has characteristics** | Dataset 1029: `proof, age, bottle_volume_ml, pack, list_on, upc, state_bottle_cost, state_bottle_retail` (current snapshot only) | Characteristics for rival-product instruments and controls. Discontinued items are missing from the current list |

## Data problems found and fixed (Nov 27)
- **Duplicate rows.** The portal files repeat exact copies of order lines.
  - **2025:** about 518k duplicates in Jul–Oct; every Aug 2025 line appears twice. That made Aug–Sep 2025 look like 2× normal volume.
  - **2020–2022:** about 0.5M duplicates a year. That inflated the "COVID spike" from about +11% to +34%.
  - **Fix:** `02_build_panel.py` drops exact duplicate rows (`SELECT DISTINCT`). Before Jul 2025, `invoice_id` is unique per line, so an exact duplicate can't be a real order.
- **New ordering system from about Sep–Oct 2025.**
  - `invoice_id` becomes one ID per order (not per line), and `store_no` changes format (e.g. `010622`).
  - From Nov 2025 a few odd adjustment lines (e.g. 1 bottle at $1.00) create extra unit prices.
  - The **posted price** (the price with the most bottles in the month) is unaffected.
  - The first-pass demand model stops at Oct 2025; store-level work would need an old → new store ID crosswalk.
- **After cleaning:** 25–31M bottles and $334–448M a year to the state (state margin $111–149M a year). 2020 is +11% over 2019 (COVID at-home drinking).

## Price-change facts (2018–2025, `output/descriptives.md`)
- **Frequency:** about **3% of items change posted price in a given month** (about 8,300 changes in 8 years).
  - **2018–2023:** increases outnumber decreases (2022–23: 2.6% up vs 0.5% down; inflation).
  - **2024:** balanced.
- **Size:** the median change is +0.7%; the 10th–90th percentile is −13% to +14%.
- **Timing:** changes cluster in Jan, Apr–May, Jul–Aug and Oct, with very few in Mar/Jun/Sep. That looks like a quarterly cost-review cycle, as in Pennsylvania. Nov 2025 (11%) is the system change.

## Results (v2, after the independent review; see `review_log.md`)
**2019 Airbus tariffs** (`04`; item + month FE, $-weighted, regular-price items):
- **Single malts (97 items vs 582 untariffed whiskies):** Iowa price **+5.3% (SE 0.9)** while the tariff was on, and **+5.8% after the suspension**.
- **Covered DE/IE/IT/ES/UK liqueurs (61 items vs 235 US liqueurs):** **+6.3% (SE 2.3)** on, **+7.6%** after.
- **Pre-trends are flat.** The jump comes one quarter after Oct 2019, matching the quarterly price-review lag.
- **Pass-through:** about 36–72% if customs value is 30–60% of the supplier price; 22% only if the tariff applied to the whole price. Needs Census customs unit values.
- **Bottles:** no detectable change.

**2025–26 UK/EU tariffs** (`06`; origin by brand, base Apr 2024 – Mar 2025, items sold before and after):
- **Panel:** 2,611 items.
- **Price effect vs US + Mexico/Canada spirits:**
  - UK whisky: −0.4%.
  - UK gin: +0.5% to +0.9%.
  - EU: −0.9% to −1.6%.
  - The same holds across all regimes: 10%, 15%, back to 10%, and UK whisky at 0%.
- **No pass-through through Oct 2026.** New 700 ml SKUs are only 0.5% of treated dollars.
- **Liters:**
  - UK whisky: −5.7% (SE 2.5, $-weighted) during the 10% period.
  - EU: no consistent effect.
  - EU vodka gained share within vodka.

**Own price changes** (`07`):
- 2,837 changes of at least 3% that held at least 2 months, with up to 20 same-nest controls each.
- Implied elasticity **−0.31** for increases and **−0.59** for decreases.
- Bottles are **+2.6% in the month before an increase** (stores stock up ahead of announced increases).

**Demand:**
- **Logit (item + month + nest × season FE, log price):** elasticity **−0.63** (`05`).
- **Nested logit is invalid in both versions:**
  - our nest-count instruments (σ > 1, `05`);
  - the class-20 spec with rival-vendor instruments, liter shares and zero months filled (price coefficient > 0, λ = 0.94, partial R² ≤ 0.8%, `08`).

**Counterfactuals** (`09`; calibrated nested logit, elasticity −0.63, σ ∈ {0, .5, .8}, M ∈ {1.5, 2, 3} × liters):
- **HF 830 minimum unit price:**
  - binds on 48% of liters;
  - pure alcohol **−2% to −11%**;
  - state margin **+$44–60M/yr** (on $139M);
  - buyers **+$57–60M/yr**.
- **Revenue-neutral alcohol markup** (about $18 per liter of pure alcohol): pure alcohol **−1% to −7%** at the same state revenue.
## What we observe vs what we don't
- **Observed:** what stores buy from the state and the price they pay. That's the **wholesale market the state controls**.
- **Not observed:** retail shelf prices. Stores set their own markups.
- **Interpretation:** we estimate demand faced by the state wholesaler (derived from consumer demand, through the stores). The state's pricing decision, the markup, acts exactly at this level, so it's the right level for the policy question.

## Natural experiments in the window: verified tariff timeline (CBP CSMS, EOs 14257/14326/14345, USTR, Fed. Reg.)
| Origin / product | Rate path | Notes |
|---|---|---|
| **2019 Airbus (Section 301):** UK single malt Scotch (+ N. Irish single malt); liqueurs/cordials from UK, DE, IE, IT, ES | 25% from **Oct 18 2019**; suspended **Mar 4 2021** (UK) / **Mar 11 2021** (EU); 5-year suspension from Jul 2021 | Republic of Ireland whiskey and French liqueurs **not** covered; French/German cognac 25% only Jan 12 – Mar 11 2021 |
| **EU** spirits | 10% from **Apr 5 2025** (EO 14257) → 15% all-in from **Aug 7 2025** (EO 14326) → 10% Section 122 from **Feb 24 2026** → 10% Section 301 from **Jul 24 2026** | No wine/spirits carve-out. The Supreme Court (*Learning Resources v. Trump*, Feb 20 2026) struck down the IEEPA tariffs, so refunds are possible |
| **UK** spirits | 10% from Apr 5 2025 (the May 8 2025 deal left spirits at 10%) → 10% (Section 122) Feb 24 2026 → **whisky 0%**, gin 10% from **Jul 24 2026** | |
| **Mexico, Canada** | 25% IEEPA from Mar 4 2025, but **USMCA-qualifying goods exempt from Mar 7 2025** | Tequila and Canadian whisky effectively tariff-free → control group |
| Japan, other | 10% → 15% (Japan from Aug 7 2025) | Small in Iowa; excluded |
## Open data questions
- Customs unit values (Census International Trade API, free key) to convert the 2019 price effect into exact pass-through.
- Border counties: is demand more elastic near Illinois/Missouri/Nebraska/Minnesota/Wisconsin/South Dakota (cross-border leakage would cap any markup)?
