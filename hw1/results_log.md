# HW1 results log (verified outputs from the cluster)

Numbers here come from actual cluster runs of `analysis/hw1_nhamcs_analysis.py`, one question at
a time. They are the source for the write-up and slides. Charts are saved on the cluster in
`~/hw1_output/figures/` (download them via right-click > Download in JupyterLab).

## Methodology notes for the write-up
- **Data**: `~/esai_2026/data/NHAMCS/nhamcsed2015.csv` (CSV version of the NCHS public-use file).
- **Missing-value codes**: NCHS records missing answers as negative codes, not blanks:
  -9 = Blank, -8 = Unknown, -7 = Not applicable (source: codebook `docs/nhamcsed2015.pdf`, p.37
  onward for each item; p.116 lists PAYTYPER's -9/-8 rows). `df.isna()` misses them.
  **Verified** against the codebook's official nonresponse rates (p.15): LOV 7.0%, PAYTYPER
  8.7%, ETHUN 24.2%, IMMEDR 22.2% all match exactly; WAITTIME 15.2% vs 15.7% published (close).
  All statistics treat -9/-8 as missing, and -7 as "question did not apply".
- **Weights**: PATWT (visits represented per sampled record) for all totals and rates.

## Q1: Load and inspect (verified 2026-09-24)
- (a) **21,061 rows x 1,031 columns** (matches codebook's 21,061 records). Types: 570 float,
  408 int, 53 text.
- (b) `isna()`: 600 of 1,031 columns have true NaN. The top ones are 100% NaN: the drug
  category slots (RX29V2C4, RX30V3C4, ...), text columns that are empty unless a patient had
  29-30 medications. Coded missing (-9/-8): 118 columns >5%, 56 columns >20%. Top: MED30
  100%, MED19-29 ~99.5%, MRICONTRAST 99.5%, CAUSE3R 98.1% (structural: slots only filled
  if applicable).
- Homework variables (% -9 / % -8 / % -7):
  ETHUN 24.2/0/0 (hence use imputed ETHIM, 0% missing) | WAITTIME 15.2/0/3.4 |
  LOV 7.0/0/0 | PAYTYPER 1.9/6.8/0 | TOTCHRON 1.6/0/0 | INJPOISAD 0.2/3.7/0 |
  INTENT15 75.2/0.1/0 (blank mostly because the visit isn't an injury) | IMMEDR 2.3/19.9/0 |
  PAINSCALE 4.2/25.3/0 | HDSTAT 0.2/0.2/91.2 (-7 = not admitted, legitimately N/A) |
  AGE, SEX, ETHIM, VDAYR, ANYIMAGE, NUMMED, DIEDED, DOA, PATWT: 0% missing. ARRTIME 1.3% blank.
- **Missingness is NOT random (Class 4 MCAR/MAR/MNAR framing)**:
  - WAITTIME missing ~7-12% for triaged visits (levels 1-5), but 38-45% when triage is
    blank / no triage / ED doesn't triage. LOV follows the same pattern (34% when triage blank).
  - By region: WAITTIME missing 9.8% Midwest vs 19.7% Northeast / 19.4% West; PAYTYPER 5.0%
    South vs 13.5% Northeast.
  - Consistent with MAR (depends on observed ED/process characteristics). Implication:
    wait-time statistics describe EDs that record them, and may under-represent un-triaged
    (possibly less organised or lower-acuity) settings.
- Outlier check (after removing codes; describe with 0.5/99.5 pct):
  AGE 0-93 (93 = top-code "93+"), mean 37.6, median 34 |
  WAITTIME 0-1,305 min, median 19, 99.5% = 638 |
  LOV 0-5,732 min (~95 h), median 154, 99.5% = 1,891 (~31 h) -> long right tail, consider
  winsorizing at 99.5% (Class 4 method) for means |
  NUMMED 0-30, median 2 | TOTCHRON 0-12, median 0 | PATWT 117-42,002, mean 6,502.
- (c) **One row = one sampled ED visit** (one Patient Record Form), not a patient. No duplicate
  HOSPCODE+PATCODE pairs. 248 EDs in the sample; visits per ED: median 94 (min 3, max 163).
  Each row represents ~6,502 U.S. visits on average.

## Q2: Weighted totals and sample design (verified 2026-09-24)
- (a) **21,061 sampled visits** (unweighted; each row = one visit).
- (b) **136,943,181 estimated U.S. ED visits** (sum of PATWT), ~136.9M, exactly the codebook's
  published total (p.28, p.115); over 100M as the assignment expects.
- Weights are very unequal: PATWT min 117, 1% 298, median 5,232, mean 6,502, 99% 27,224,
  max 42,002. The top 10% of rows by weight = **28.7%** of all weighted visits.
- Region, sample vs weighted national share: Northeast 20.4% -> 17.3%, Midwest 26.8% -> 24.2%,
  South 33.3% -> 37.8%, West 19.4% -> 20.7%. The sample over-represents the Northeast/Midwest
  and under-represents the South, so unweighted stats would tilt toward Northeast/Midwest EDs.
- Figures: `q2_weight_distribution.png` (histogram of PATWT, median line),
  `q2_region_unweighted_vs_weighted.png` (grouped bars).

## Q3: Descriptive statistics (verified 2026-09-24)
Unweighted / weighted (rows used):
- (a) Age mean **37.6 / 37.0** yrs, median **34 / 34** (21,061). Age 93 = top-code "93+".
- (c) Wait to see provider, median **19 / 18 min** (17,153 rows; excludes -9 blank and
  -7 not seen). Mean 40.3 / 39.3 raw, 39.5 / 38.7 winsorized.
- (d) Length of visit, mean **221.9 / 213.7 min** raw (~3.6 h weighted), **216.5 / 209.8**
  winsorized at 99.5% (cap 1,891 min, 98 visits capped); median 154 / 154 (2.6 h) (19,581 rows).
  Wait winsorizing cap 638 min (86 visits capped).
- (b) Female **55.13% / 55.44%**, male 44.87 / 44.56 (matches codebook 55.436%).
  Hispanic **15.88% / 16.49%** (ETHIM imputed; matches codebook 16.493%).
- Age groups unweighted -> weighted: <15 18.65 -> 19.83, 15-24 15.07 -> 14.72,
  25-44 28.81 -> 28.58, 45-64 21.65 -> 21.26, 65-74 7.08 -> 7.15, 75+ 8.75 -> 8.45
  (weighted = codebook p.115 exactly).
- Interpretation notes: means far above medians (wait 39 vs 18; LOV 210 vs 154), so the
  distributions are right-skewed and a minority of very long waits/stays drives congestion.
  Weighting shifts toward children and the South and lowers mean LOV by ~8 min; medians
  don't move with weighting.
- Figures: `q3_wait_and_length_of_visit.png` (two weighted histograms, median/mean lines),
  `q3_age_groups_unweighted_vs_weighted.png`.

## Q4: Demand by day and hour (verified 2026-09-24)
- 20,779 of 21,061 visits have a usable arrival time (1.3% blank, dropped from the hour
  analysis). 2015 had 53 Thursdays and 52 of each other weekday, so days are compared as
  **average visits per day**.
- By day (total M / % / avg per day): Sun 18.00 / 13.14 / 346k | **Mon 22.45 / 16.40 / 432k** |
  Tue 20.57 / 15.02 / 396k | Wed 19.72 / 14.40 / 379k | Thu 18.74 / 13.69 / 354k |
  Fri 18.78 / 13.72 / 361k | Sat 18.67 / 13.64 / 359k. Busiest **Monday**, quietest **Sunday**
  (a 24.7% gap). Volume declines Mon through Thu, then is flat Thu-Sun.
- By hour (% of arrivals): trough 3-5am (1.3-1.4%); climbs from 7am (2.6%) and 9am (5.1%);
  **plateau 10am-8pm at ~5.5-6.3%**. Top hours: **18:00 (6.3%)**, 12:00 (6.1%), 10:00 (6.1%).
  Peak hour = 4.7x the quietest hour. 69.1% of arrivals are 10am-10pm; 11.5% midnight-7am.
  Avg U.S. arrivals per day in the peak hour: 23.5k (6pm) vs 5.0k (5am).
- Single busiest weekday-hour slot: **Monday 9:00-9:59** (28.5k visits on average). The heatmap
  is somewhat noisy cell by cell (~125 sample rows per cell), so read the broad pattern
  (Monday daytime darkest, overnight lightest) rather than single cells.
- Staffing implications: size staff to a daytime/evening plateau, not a single peak; add
  capacity Monday (esp. morning, catching up after the weekend when primary-care offices are
  closed); overnight 3-6am runs at ~1/4 of peak.
- Figures: `q4_visits_by_weekday.png`, `q4_arrivals_by_hour.png` (title corrected to the
  6pm-peak finding), `q4_weekday_hour_heatmap.png`.

## Q5: Payer mix (verified 2026-09-24)
- PAYTYPER = primary expected payer, NCHS hierarchy recode (one payer per visit).
- (a) Weighted % of ALL visits: Medicaid/CHIP **31.15**, Private **27.57**, Medicare **17.74**,
  Self-pay **9.03**, Unknown (-8) 8.30, All blank (-9) 2.47, Other 2.21, No charge/charity 0.83,
  Workers' comp 0.70. All five codebook checks (p.116) MATCH.
- (b) 89.2% of visits have a known payer. Share of known-payer visits: **Medicaid 34.9%,
  Private 30.9%, Medicare 19.9%, Self-pay 10.1%**. Public (Medicaid + Medicare) = **54.8%**;
  self-pay + no charge = **11.0%** (uncompensated-care risk).
- "Listed at all" (multiple payers allowed): Private 34.26%, Medicare 17.74%, Medicaid 34.75%,
  Self-pay 10.53%.
- Payer mix by age (known payer, %): <15 Medicaid 65.2 / Private 27.2; 15-24 Medicaid 40.8 /
  Private 37.7 / Self-pay 14.2; 25-44 Medicaid 34.9 / Private 34.7 / **Self-pay 17.5** (highest);
  45-64 Private 41.4 / Medicaid 26.0 / Medicare 18.0; 65-74 Medicare 78.3; 75+ Medicare 86.9.
- Financial implications: Medicaid (the largest payer) and Medicare reimburse below private
  rates. ~11% of visits are uninsured or charity, and EMTALA requires EDs to treat everyone
  regardless of ability to pay. Private insurance (~31%) cross-subsidizes. Young adults
  (25-44) are the main self-pay / bad-debt exposure.
- Figures: `q5_payer_mix.png` (ordered horizontal bars), `q5_payer_mix_by_age.png` (100%
  stacked bars; x-axis label added in the locked version).

## Q6: Chronic conditions (verified 2026-09-24)
- Section answered on 20,722 of 21,061 visits (1.6% blank, excluded). TOTCHRON = sum of the
  22 checkboxes on **100.0%** of answered visits (internal consistency check passed).
- (a) At least one chronic condition: **48.5% unweighted / 47.6% weighted**. None: 52.4%
  weighted (codebook p.4 reports 51.7%: close; small gap likely from denominator treatment
  of blank sections).
- Number of conditions (weighted %): 0 = 52.37, 1 = 21.14, 2 = 11.56, 3+ = **14.93**.
  Mean 1.05 per visit.
- (b) Prevalence (weighted %): **Hypertension 23.97**, Asthma 9.98, Depression 9.45,
  Hyperlipidemia 8.17, Substance abuse 6.65, CAD 6.08, Diabetes unspecified 5.77, COPD 5.37,
  **Diabetes type 2 4.70**, **Obesity 3.64**, Cancer 3.40, CHF 3.27, Stroke/TIA 2.96,
  Alcohol misuse 2.83, CKD 2.47, OSA 1.67, Alzheimer's 1.27, PE/DVT 1.14, Osteoporosis 0.83,
  Diabetes type 1 0.60, ESRD 0.56, HIV 0.42. Assignment's four: HTN 23.97, DM2 4.70,
  Obesity 3.64, Depression 9.45.
- **Any diabetes (type 1, 2 or unspecified combined): 10.68% unweighted / 11.06% weighted**,
  making it the #2 condition after hypertension (ahead of asthma 9.98). Splitting diabetes across
  three boxes understates it.
- By age (weighted): % with 1+ condition: <15 13.5, 15-24 28.2, 25-44 43.1, 45-64 68.9,
  65-74 86.2, 75+ **90.5**; mean # conditions 0.14 -> 2.66.
- Figures: `q6_chronic_condition_prevalence.png`, `q6_chronic_by_age.png`.

## Q7: Injuries and intent (verified 2026-09-24)
- INJPOISAD (weighted % of all visits): Injury/trauma **29.49**, Overdose/poisoning **1.38**,
  Adverse effect of medical care **2.22**, Not injury-related 62.67, Unknown 3.74,
  Questionable 0.29, Blank 0.22.
- (a) Injury, overdose or adverse effect: **33.4% unweighted / 33.1% weighted** of all
  visits (34.6% of visits with a clear yes/no answer).
- (b) Among those visits, INTENT15 (weighted): Unintentional 68.40%, Intentional 5.37%,
  Blank 25.74%, Unknown 0.49%. **Among visits with known intent: 7.3% intentional /
  92.7% unintentional.**
- Intent is never recorded for adverse effects of medical care (100% blank, i.e. the question
  isn't asked), so the intent split effectively covers injuries and overdoses. Injury/trauma:
  5.4% intentional, 72.8% unintentional, 21.2% blank. **Overdose/poisoning: 13.2%
  intentional**, 84.6% unintentional.
- % intentional (known intent) by age: <15 3.7, **15-24 12.1**, 25-44 10.1, 45-64 7.3,
  65-74 2.3, 75+ 0.4. By sex: female 8.1, male 6.5.
- Figure: `q7_injuries_and_intent.png` (two panels).

## Q8: Diagnostic services (verified 2026-09-24)
- Diagnostic section blank (DIAGSCRN = 2) on 1.1% of visits (weighted); rates are per ALL visits.
- (a) Imaging, % of all visits (unweighted / weighted): **Any imaging 45.54 / 47.05**, X-ray
  32.51 / 33.65, CT 15.75 / 16.50, Ultrasound 4.43 / 4.38, MRI 0.80 / 0.74, Other 0.93 / 0.90.
  Any imaging: injury visits 54.0% vs non-injury 44.4%. By age: <15 29.4, 15-24 40.0,
  25-44 44.3, 45-64 56.5, 65-74 65.9, 75+ **70.3**.
- (b) At least one blood test: **41.5% unweighted / 42.4% weighted**. Among blood-test visits
  (weighted %): **CBC 85.43**, CMP 55.31, Other blood test 46.11, BMP 25.18, Glucose 19.16,
  PT/INR 17.76, BUN/creatinine 15.72, Cardiac enzymes 9.79, LFT 9.71, Electrolytes 7.66,
  Blood culture 7.00, BNP 5.93, D-dimer 5.57, Blood alcohol 4.04, ABG 3.75, Lactate 3.08.
  Average 3.21 different blood tests per blood-test visit.
- Codebook p.4 checks all MATCH: BUN/creatinine 6.67% (6.7), electrolytes 3.25% (3.3),
  glucose 8.13% (8.1) of all visits.
- Note: panels (CMP/BMP) bundle glucose, BUN/creatinine and electrolytes, which is why the
  standalone boxes for those are low. The codebook notes their 2014 -> 2015 drop partly reflects
  form changes (BMP/CMP boxes added in 2015).
- Figures: `q8_imaging.png` ("Any imaging" highlighted in orange), `q8_blood_tests.png`.

## Q9: Medications (verified 2026-09-24)
- NUMMED = number of filled MED1-MED30 slots on **100.0%** of visits (consistency check).
- (a) Mean **2.54 unweighted / 2.49 weighted**; median **2 / 2**. Given in ED 1.62 vs
  prescribed at discharge 1.08 (weighted means). Form caps at 30 medications.
- Total U.S. drug mentions = sum(PATWT x NUMMED) = **340,550,921**, exactly codebook p.118.
- (b) Weighted: **none 20.94%, 1-2 41.91%, 3+ 37.15%** (unweighted 20.33 / 41.87 / 37.80);
  all MATCH codebook p.117.
- Mean meds by # chronic conditions: 0 -> 2.00, 1 -> 2.65, 2 -> 2.83, 3+ -> **3.77**.
  By age (mean / % with 3+): <15 1.60 / 21.5, 15-24 2.05 / 32.7, 25-44 2.61 / 42.4,
  45-64 **3.11 / 46.2**, 65-74 3.14 / 41.7, 75+ 2.80 / 37.5 (drops slightly for the oldest).
- Figures: `q9_medications_per_visit.png` (distribution 0-10+),
  `q9_meds_by_chronic_conditions.png`.

## Q10: Correlations (verified 2026-09-24)
- Method: ~20 cleaned variables (missing codes -> NaN, yes/no -> 0/1, wait/LOV winsorized at
  99.5% so outliers don't drive r). Weighted Pearson r on pairwise-complete rows, with a unit
  test: equal weights reproduce pandas `.corr()`. Admitted = ADMITHOS or OBSHOS.
- Rare outcomes (sample rows): died in ED **28**, DOA **7**, died in hospital **40 of 1,752**
  admitted. Weighted rates: died in ED 0.10%, DOA 0.04%, **admitted 9.0%**, in-hospital death
  among admitted 2.6%. Pearson r understates rare-outcome relationships, so use the rate tables.
- Top weighted correlations: age-Medicare **0.61** (mechanical: eligibility at 65), age-#chronic
  **0.55**, #chronic-Medicare 0.44, age-Medicaid -0.39, #blood tests-admitted **0.37**,
  #chronic-#blood tests 0.37, age-#blood tests 0.37, Medicaid-Medicare -0.37 (mutually
  exclusive primary payer), triage-#blood tests -0.35, #chronic-admitted 0.33, imaging-#blood
  tests 0.32, LOV-#blood tests 0.31, #blood tests-#meds 0.31, wait-LOV 0.28, ambulance-#chronic
  0.28, age-ambulance 0.27, age-admitted 0.27, triage-#chronic -0.27, age-imaging 0.26,
  age-triage -0.26.
- With admission: #blood tests 0.37, #chronic 0.33, age 0.27, Medicare 0.25, ambulance 0.24,
  triage -0.24, #meds 0.20, imaging 0.17; Medicaid -0.10. With in-hospital death: triage -0.21,
  ambulance 0.17. Sex, ethnicity and pain are ~0 with every outcome.
- By triage level (weighted %): admitted 33.3 / 25.0 / 11.4 / 2.3 / 2.5 (1 Immediate ->
  5 Nonurgent); **died in ED 6.43% for Immediate**, ~0 otherwise; died in hospital (admitted)
  30.7% Immediate, 2.7 Emergent, 1.1 Urgent; ambulance 40.8 -> 4.8; imaging 51.9 / 61.9 / 55.9 /
  39.4 / 24.1; mean meds 3.64 -> 1.92. **Median wait 14 / 18 / 20 / 19 / 18 min**: only the most
  urgent level is seen noticeably faster (sample rows 210 / 1,583 / 6,605 / 5,652 / 1,043).
- By age (weighted %): admitted 2.5 (<15) -> 29.1 (75+); died in ED 0.00 -> 0.34; ambulance
  4.8 -> 40.0; imaging 29.4 -> 70.3; in-hospital death among admitted ~1% (<45) vs ~3% (45+).
- Correlation is not causation: age drives chronic burden, payer and intensity together.
- Figures: `q10_correlation_heatmap.png` (|r| >= 0.2 labelled, undefined pairs grey "n/a"),
  `q10_triage_admission_and_wait.png`.
