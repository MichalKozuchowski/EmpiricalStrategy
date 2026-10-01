# Class 9 — Free-delivery experiment (Harvest Lane Markets)
**Thu, Oct 1, 2026** — Kevin Williams. Applied exercise after the Class 8 regression deck
([class8-slides.md](class8-slides.md)): omitted variable bias and fixed effects on real-looking data.
Code: [class9_free_delivery/free_delivery_pipeline.py](class9_free_delivery/free_delivery_pipeline.py).

## The task
CEO Dana Whitfield's email (`ceo_email.md`): some loyalty members were offered free home delivery
for four weeks, the rest were not. She wants
1. **one number**: how many dollars the offer raised a customer's four-week spending, and
2. **a yes or no**: roll it out to every loyalty member? Finance says it only pays for itself at
   **+$15 per customer or more**.

She warns the export is "a little rough" and says she'll ask us to defend the number.

The professor's hints: (1) **do not adjust the raw data**, (2) look at the data and report back,
(3) take notes, (4) **automate** it and answer the email. He also said the data has **omitted
variable bias** to deal with.

## Answer (wave 1; wave 2 and pooled results in section 7)
**About +$8 per customer (95% range $6.55 to $9.92). No: don't roll it out.** Even the top of the
range is well below $15.

## 1. Don't adjust the raw data
- The raw CSV is only ever *read*. Every fix happens in code, on a copy in memory, and the
  cleaned sample is written to a new file (`output/clean_data.csv`).
- Why: anyone can re-run the pipeline from the original file and get the same answer. Nothing is
  lost or hidden. If a cleaning decision turns out wrong, you change one line of code instead of
  trying to reconstruct an edited spreadsheet.
- The pipeline proves it by taking a SHA-256 "fingerprint" of the raw file before and after the
  run. If one byte changed, the fingerprints would differ and the script would stop.

## 2. What is in the data (and why it's "rough")
5,805 rows × 7 columns: `customer_id, store, offer_group, household_size, tenure_months, app_user,
spend_4wk`. One row should equal one customer. There are no blank cells; the problems are hidden
in the values:

| Problem | Rows | Fix |
|---|---|---|
| `offer_group` spelled 10 ways (`treatment`, `Treatment`, `treat`, `T`, `1`, `control`, `Control`, `ctrl`, `C`, `0`) | all | map to 1/0; `1`/`0` average like treatment/control, which confirms the mapping |
| `store` codes inconsistent (`s09` vs `S09`, `S06 ` with a trailing space): 120 codes for 40 stores | 507 | trim + upper-case |
| `TEST1001`–`TEST1025` fake test accounts: **all in treatment**, household 1, tenure 1 month, app users, spending only $0.01 / $1 / $5 (real customers spend ~$200) | 25 | drop; kept, they would drag the treatment effect **down** |
| exact duplicate rows | 120 | keep one copy |
| customers recorded in **both** groups (otherwise identical rows) | 60 customers | drop: we can't know their real group |
| `spend_4wk = -999`, a missing-value code (like NHAMCS's -9 in HW1) | 112 | drop; similar share in both groups (2.2% vs 1.7%) |
| impossible spends ($6,480 / $9,125.50 / $14,890.25; normal max ≈ $394), all treated | 3 | drop, and show the effect with them kept |
| tenure up to 155 months | 21 > 120 | keep: plausible, and only a control |

After cleaning: **5,425 customers**, each appearing once. Row counts are printed after every step
(the Class 3 habit).

## 3. The omitted variable: the store
- **Simple comparison** (treated mean − control mean): **+$26.01**. Taken at face value, that says
  "roll it out."
- The offer went to **15% of customers in some stores and 90% in others**, and the stores that
  offered it to more customers are stores where customers **already spend more**. The correlation
  between a store's treated share and its control customers' average spend is **0.77**.
- In slide 19's terms: X1 = treatment, X2 = store. Store affects spending **and** is correlated with
  treatment, so leaving it out puts it into the error term. The treatment variable is then
  correlated with the error: the **endogeneity problem**. Both links are positive, so the bias is
  **upward** (like slide 20's 3.91 vs 3).
- **Fix: store fixed effects** (Class 8 slides 22–27). Store is categorical with 40 values, so add
  39 store dummies (J − 1, to avoid perfect multicollinearity). That compares offered vs not-offered
  customers **within the same store**: **+$7.36**, or **+$8.23** with customer controls.
- So roughly **$18 of the naive $26 was bias**: store differences credited to the offer.
- Customer controls (household size, tenure, app use) barely move the estimate. They are not
  correlated with treatment, and slide 21 shows that omitting an uncorrelated variable does no harm.

## 4. Is the within-store comparison believable?
- **Balance within stores**: holding the store fixed, treated and control customers have the same
  household size, tenure and app use (differences −0.04, +0.46 months, +0.007; p > 0.4).
  This is what you'd expect if the offer was **randomized within each store, at different rates
  per store**. That's the setting where store fixed effects recover the true effect.
- **Stable across store types**: +$8.39 in stores that treated under 50% of customers, +$8.08 in
  stores that treated more.
- **Standard errors are clustered by store**: customers in the same store share local shocks, so
  treating them as independent would overstate precision (the Class 8 heteroskedasticity lesson,
  one level up).

## 5. Why the cleaning matters
| Version | Effect |
|---|---|
| Raw file, store FE, **no cleaning** | +$5.59 (95%: −$4.23 to +$15.42): -999s and duplicates drown the signal |
| Cleaned, store FE, **3 extreme spends kept** | +$14.03 (95%: $5.73 to $22.32): three rows nearly double the estimate |
| Cleaned, **no store FE** | +$26.01: omitted variable bias |
| **Cleaned + store FE + controls** | **+$8.23 (95%: $6.55 to $9.92)** |

Each shortcut gives a different, wrong number, and two of them would flip the decision to "yes".

## 6. Automation
`free_delivery_pipeline.py` runs everything with one command
(`uv run free_delivery_pipeline.py path/to/experiment_wave1.csv`, or plain `python` on the
cluster). It writes `output/`:
- `data_report.md`: what is in the raw file and every problem found
- `results.md`: cleaning log, all estimates, validity checks, decision
- `reply_email.md`: the answer to Dana, generated from the numbers (the decision rule:
  yes if the low end of the 95% range ≥ $15, no if the high end < $15, otherwise inconclusive)
- `effect_chart.png`: naive vs within-store estimate against the $15 line (Upshot style); the
  title is built from the results
- `clean_data.csv`: the analysis sample (a new file)

If a "wave 2" export arrives, the same command produces a new answer. Every number in the email
is computed, not typed.

## 7. Wave 2 (second part of the experiment, posted in class)
`experiment_wave2.csv`: 6,105 rows, same 7 columns, **new customers** (no ids overlap with wave 1).
- **Same problems** as wave 1: 25 TEST accounts, 120 duplicate rows, 60 customers in both groups,
  118 rows of `-999`, 2 impossible spends ($7,310 and $11,240.75), tenure up to 180 months.
  5,720 customers left after cleaning.
- **New problem: two new group labels, `Offer` (1,050) and `Holdout` (1,059).** The pipeline
  *stopped* on them, which is what it should do: an unknown label must never be guessed silently.
  Before mapping we checked that they appear in every store (~a third of each store's rows), that
  those customers look like everyone else, and that `Offer` spends like treatment ($219) and
  `Holdout` like control ($197). So: Offer = treatment, Holdout = control. The pipeline now
  re-checks this every run by estimating the effect separately for each label scheme:
  **$7.33** (Offer/Holdout) vs **$8.21** (original labels). They agree, so the mapping holds.
- **Same omitted variable bias**: the simple comparison gives $27.72; store FE + controls give
  **$8.02** (95% range $6.10 to $9.94). Decision: **NO**.
- **Both waves pooled** (store + wave fixed effects, 11,145 customers): **$8.08** (95% range
  $6.67 to $9.49). The effect did **not** change between waves (difference +$0.55, p = 0.61).
- **No customer group clears $15**: by app use $7.78–$8.38; by household size $7.36–$9.05; by
  tenure $7.12–$10.17 (members of 3+ years respond most, but even their range tops out at $12.87).
  A targeted rollout wouldn't pay off either.
- **What wave 2 taught us about automation**: the same command answered a new file in seconds, but
  only because the code had **guardrails** (assert every label is known, count rows at every step,
  fingerprint the raw file, re-check the label mapping). Text in the outputs was also made fully
  data-driven (e.g. "2 impossible spending values", not a typed "three").

## 8. Caveats to say out loud
- Four weeks only: long-run effects (habit, cannibalization of in-store trips) are unknown.
- The data team's note on how the test was run wasn't in the materials we had. "Randomized within
  each store" is inferred from the balance checks and should be confirmed against that note.
- The break-even is in spending; it assumes Finance's $15 already accounts for delivery costs
  and margins.
