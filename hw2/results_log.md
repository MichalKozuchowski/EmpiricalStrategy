# HW2 results log (Zappos): verified outputs and data notes

Numbers below come from `analysis/hw2_zappos_analysis.py` / `.ipynb`, run locally on the course
files (uv, Python 3.12) and re-run under Python 3.9 + pandas 2.3.3 (the cluster's versions) with
identical output. The notebook's final cell re-checks 13 of these values and the raw-file
fingerprints.

## Step 0: data inventory and cleaning

| File | Rows | One row = |
|---|---|---|
| POS.dta (2.60 GB) | 13,546,258 | one unit sold (no quantity column) |
| brand_list.dta | 61,433 | one sku (unique), 615 parent brands |
| categories.csv | 61,421 | one sku (unique), `categ` codes 0–10 |
| stock_chars.dta | 117,493 | one sku × color (`style_id`); 50,050 skus, ≈2.35 colors per sku |
| reviews.csv | 297,388 | one sku × month: 21,242 skus × 14 months (Jul 2012 – Aug 2013), balanced |

- POS converted once to Parquet (309 MB, zstd) in 1M-row chunks (113 s on the cluster). `timestamp`
  dropped (float32, too coarse). Large queries run in DuckDB on the Parquet file (Class 7: >10M rows).
- **All 13.5M rows pass**: price ≤ 0: 0; price > msrp: 0; discount ≠ msrp − price: 0; sale flag ≠
  (discount > 0): 0; `mdy` ≠ `date_*` day: 0. Blank state: 4 rows.
- **No exact duplicate rows** (compared on every column inside the ~8,500 order ids with >1 row).
  Rows sharing an order id, product and time can ship to different addresses: real sales, kept.
- `date_*` = purchase time (matches `mdy`). `sdate_*` is 2–3 hours later. Times are local US time
  with daylight saving (Mar 10 2013 has no 2 am hour).
- 63 state codes: 50 states + DC + PR, VI, GU, MP, AS, FM, PW, MH, military AA/AE/AP, blank.
  Non-states = 93,986 units (0.69%): kept in national totals, excluded from state/region analysis.
- Sales: 2012-07-13 14:51 to 2013-08-15 10:16, 399 days, no missing days. First/last day partial.
- **Recording gaps** (days with missing hours): 2012-10-15 (20 h), 2013-01-04 (22), 2013-01-05 (23,
  only 10,774 units), 2013-01-06, 2013-01-09, 2013-04-19 (23), 2013-07-14 (22), 2013-07-15 (14),
  2013-08-07 (10 h, 3,035 units). Excluded from moving averages and time-of-day regressions.

## Q1. Brands
- Distinct brands: **615** parent brands (brand_list); **842** brand names in POS (sub-lines such as
  "Nike Kids", "adidas Originals").
- Top 10 by SKUs: Nike 1,256; adidas 1,237; SKECHERS 1,150; PUMA 1,108; Steve Madden 952; Stuart
  Weitzman 893; Primigi Kids 758; New Balance 688; Kenneth Cole 661; UGG 659.
- Merge POS → brand_list on sku (m:1): rows 13,546,258 before and after; **100% of rows and all
  61,433 skus match**. Names agree on 76.6% of rows; 239 POS names roll up into 158 parents
  (Nike Kids → Nike 286,004 units; Sperry Top-Sider → Sperry 272,073; Madden Girl → Steve Madden).
  5 POS names map to 2 parents (Gabriella Rocha, NoSoX/NO SOX, Rose Petals, Truth or Dare).

## Q2. Product characteristics
- Key: stock_chars is sku × color; POS has `styleid`, so merge on **sku + styleid**: 95.2% of sales
  rows match (97.8% on sku only). 305 skus disagree on gender across colors, 2,601 on list price.
- Completeness: gender, orig_price, color 100%; occasion 98.0%; closures 97.2%; weight 93.7%;
  materials 93.2%; most others <50%.
- **Chosen features: gender** (Women/Men/Kids/Unisex), **occasion** (Casual/Dress/Athletic/
  Outdoor/Work/Other), **material** (Leather/Suede/Synthetic/Fabric/Other). Unmatched colors use the
  product's most common value. After merge: rows unchanged; gender 97.8%, occasion 96.0%,
  material 92.7% of sales filled.
- Prices per unit: msrp mean $93.77, median $79.95, SD $62.81, min $10, max $3,150; price paid mean
  **$86.26**, median **$70.99**, SD $56.00, min $8.49, max $3,150.
- Discounts by gender (share of units discounted / avg % off when discounted): Women 32.8% / 22.7%;
  Men 27.9% / 20.8%; Unisex 25.2% / 17.9%; Kids 24.0% / 15.8%.
- Highest avg msrp (20+ skus): Roberto Cavalli $966, Giuseppe Zanotti $919, Alexander McQueen $900,
  Sergio Rossi $882, Bottega Veneta $786: all women's luxury/designer (dress and casual leather).

## Q3. Reviews
- `rev_cnt` is cumulative (never falls); ratings are running averages. Products with any review:
  12,963 (Jul 2012) → 21,242 (Jul 2013), flat from Jan 2013. Products with a new review: 6–8k/month
  Aug–Dec 2012, 2.6–3.0k Feb–May 2013, 391 in Jul 2013 (review coverage fades: data caveat).
- Average over all product-months: overall 4.301, comfort 4.293, **look 4.668 (highest)**.
- Reviews vs rating (21,242 products, latest month): overall = 4.13 + 0.085 × ln(reviews), SE 0.003
  (HC1), R² 0.026 → +0.06 stars per doubling; spread shrinks from SD 1.11 (1 review) to 0.22 (100+).
- Trend: running average 4.388 → 4.284 (newly reviewed products enter lower); ratings of new reviews
  flat at ~4.3–4.4 (trend −0.002 stars/month, SE 0.008): **no improvement or decline**.

## Q4. Ratings × characteristics
- reviews (297,388) merged m:1 with product features: rows unchanged; **95.9%** of review rows
  matched (95.5% of rated rows); 20,361 of 21,242 products.
- Overall / comfort by group (products): Women 4.22 / 4.15; Men 4.36 / 4.39; Kids 4.39 / 4.55.
  Dress 4.14 / 4.00 (lowest); Athletic 4.41 / 4.47; Outdoor 4.41 / 4.44. Synthetic 4.18;
  Suede 4.26; Leather 4.31; Fabric 4.33. Look is 4.6–4.8 everywhere.

## Q5. Transactions
- **13,546,258 transactions** (units); 13,537,721 order ids; 2012-07-13 to 2013-08-15.
- Top states (units): CA 1.92M (14%), NY 1.53M (11%), IL 0.72M, NJ 0.67M, TX 0.63M, FL 0.61M,
  PA 0.58M, MA 0.53M, VA 0.44M, WA 0.36M, OH 0.36M, MD 0.35M, GA 0.33M, MI 0.33M, NC 0.30M.
- Avg price paid by state: national $86.29; highest DC $91.60, VT $91.06, MT $90.99, OR $90.80,
  CO $90.79; lowest FL $80.46, HI $81.68, NE $82.49, AZ $82.87, IA $83.18.
- Share discounted by Census region: Northeast 29.7%, Midwest 30.9%, South 31.0%, West 32.0%.
- Rating by list-price tier (products / % reviewed / overall): <$50 9,513 / 33% / 4.32;
  $50–100 24,989 / 33% / **4.24 (lowest)**; $100–200 17,232 / 40% / 4.30; $200+ 9,699 / 29% / 4.34.
- Ratings → sales, sku × month panel (232,895 obs, 19,948 products), y = log(1 + units), x = last
  month's rating, SE clustered by product: (1) naive **+0.261** (0.010); (2) + controls & month FE
  +0.056 (0.008); (3) **product FE + month FE −0.043 (0.024), not significant** (dof-corrected).
  Within-product SD of rating 0.164 vs 0.775 across products. Log reviews: +0.60 in (2), −0.42 in
  (3) (product ageing: reviews pile up as sales fade).

## Q6. Brands
- Total revenue (sum of prices paid) **$1,168.4M**, 615 brands.
- Top 10 by units: Nike 983,646; UGG 546,079; New Balance 459,610; ASICS 398,158; adidas 337,009;
  Keen 336,667; Sperry 316,227; Clarks 312,724; Merrell 311,711; Converse 296,767.
- Top by revenue: UGG $75.9M (6.5%), Nike $65.3M (5.6%), Frye $44.4M (3.8%, avg $262), ASICS $35.1M,
  New Balance $33.7M, Clarks $29.1M, Merrell $29.0M, Keen $26.9M, Cole Haan $25.9M, Sperry $24.0M.
- Concentration: top 10 = 33.3% of revenue; top 50 = 66.4%; **99 of 615 brands = 80%**.

## Q7. Time patterns
- Median day 33,541 units; busiest **Cyber Monday 2012-11-26: 57,736 units, $5.54M, 42.8%
  discounted**; next: Mon Aug 20, Mon Sep 3 (Labor Day), Mon Dec 10, Mon Dec 17.
- Day of week (avg units): Mon 37,064 (highest), Tue 36,103, Sun 35,338, Wed 34,928, Thu 33,888,
  Fri 30,894, Sat 30,186 (lowest). Daily units vs share discounted: correlation −0.29.
- Smoothed: avg daily revenue Jul 13–Nov 15 2012 $3.21M vs Feb–Jul 2013 $2.61M (−19%); units
  36,450 vs 32,381. STL: weekly pattern ≈31% of day-to-day variation.
- Category codes (inferred from best sellers and features): 0 Boat shoes, 1 Boots, 2 Climbing
  shoes, 3 Clogs & mules, 4 Flats, 5 Heels & pumps, 6 Loafers & moccasins, 7 Oxfords & dress
  lace-ups, 8 Sandals, 9 Slippers, 10 Sneakers & athletic.
- Seasonality (index, category's average month = 100): Boots 24–33 in summer → 256–261 Nov–Dec;
  Sandals 22–29 Oct–Jan → 202 May–Jun; Sneakers 87–144 (steady; back-to-school peak Aug 2012).
- Hourly units (388 complete days × 24): R² time of day **0.856**, day of week 0.017, month 0.021;
  all three 0.895. Daily totals: R² day of week 0.228, month 0.275.

## Q8 support: segment scorecard (unit-weighted)
| Segment | Units | Revenue | Avg price | Discounted | Rating / comfort |
|---|---|---|---|---|---|
| Women | 55.2% | 62.7% | $98.43 | 32.8% | 4.38 / 4.33 |
| Men | 27.4% | 27.6% | $87.37 | 27.9% | 4.51 / 4.50 |
| Kids | 16.6% | 9.1% | $47.80 | 24.0% | 4.54 / 4.67 |
| Sneakers & athletic | 34.5% | 28.0% | $70.01 | 30.1% | 4.50 / 4.51 |
| Boots | 16.0% | 25.6% | $137.87 | 33.0% | 4.41 / 4.41 |
| Sandals | 18.0% | 14.2% | $68.05 | 30.2% | 4.51 / 4.52 |
| Heels & pumps | 9.1% | 9.9% | $94.43 | **40.5%** | **4.21 / 4.00** |
| Flats | 6.7% | 5.9% | $75.31 | 34.9% | 4.20 / 4.17 |
