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

## First result: the 2019 single-malt Scotch tariff (`code/04_tariff_2019_scotch.py`)
- **Setup:** 101 single malts vs 589 control whiskies (blended Scotch, bourbon, Tennessee, Canadian, blended, rye); item + month fixed effects.
- **Price:** **no pre-trend.** Iowa prices of single malts rose **+3.4% (SE 1.1)** relative to the control whiskies while the tariff was on, and the effect builds gradually to about +5.5%.
- **Pass-through:** roughly 15–20% of a 25% tariff. Importers and suppliers absorbed most of it.
- **After removal (Mar 2021):** prices **stayed up**, +4.5% (SE 1.5): "rockets and feathers".
- **Quantity:** no detectable change (−1%, SE 4.6%).
- **For the design:** the price shift is small, so this tariff is a **weak price instrument** on its own. It's still a clean pass-through finding.

## What we observe vs what we don't
- **Observed:** what stores buy from the state and the price they pay. That's the **wholesale market the state controls**.
- **Not observed:** retail shelf prices. Stores set their own markups.
- **Interpretation:** we estimate demand faced by the state wholesaler (derived from consumer demand, through the stores). The state's pricing decision, the markup, acts exactly at this level, so it's the right level for the policy question.

## Natural experiments in the window (2018–2025)
| Event | Dates | Treated categories | Natural controls | Status |
|---|---|---|---|---|
| US 25% tariff on **single-malt Scotch** (Airbus dispute) | Imposed Oct 18, 2019; suspended Mar 4, 2021 (then a 5-year suspension) | Single malt Scotch | Blended Scotch (not covered), other whiskies | Dates confirmed in news coverage |
| 2025 tariffs: **10% on UK** goods (from about May 2025), **15% on EU** (from about Aug 2025) | 2025 | Imported vodka (EU), cognac/brandy, Scotch, Irish whiskey, imported liqueurs and gins | Tequila and bourbon (exempt under the US–Mexico–Canada agreement); Canadian whisky (status disputed) | Dates and rates by product **still to verify** with USTR/CBP |

## Open data questions (to check after the build)
- How many price changes per item per year, 2018–2025?
- Do price changes cluster in particular months (like Pennsylvania's quarterly renegotiation)?
- Can we map each category to a country of origin, to define tariff exposure?
- What does it mean when an item appears with several categories (e.g. "Temporary & Specialty Packages")?
