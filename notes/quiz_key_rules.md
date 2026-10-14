# MGT 634 quiz: the key rules (one line each)

## Answering
- **Circle the trap word:** *always, never, must, definitely, proves*. It's usually what makes the statement False.
- **T/F/U answer = label + the term + one-line why + the fix.** Uncertain is fine if you state what it depends on.
- **Section 3 template:** **A** = problem → *symptom* · **B** = change → *principle* · **C** = suspect → *check*. Put each on its own line.

## Coefficients & units
- **Rescaling:** say the sentence with the new unit, then convert back to check.
  - x in a bigger unit → β bigger.
  - y in a bigger unit → β smaller.
- **"Linear" = linear in the β's.** x² is just another column.
- **Dummy = intercept shift. Interaction (x × d) = slope difference.**
- **The log goes where the percent goes:**
  - log(y) on x → β×100 %.
  - y on log(x) → β/100 units.
  - log on both sides → % for % (elasticity).
- **R² measures fit, not effect size.**
  - Adding a variable never lowers R² on the same sample (adjusted R² can fall).
  - R² from different samples isn't comparable.
- **Correlation 0 = no *straight-line* relationship**, not no relationship (U-shapes exist).
- **Prediction: multiply and add.** Plug the numbers into the equation.

## Uncertainty
- **t = β / SE.** Significant at 5% if |t| > 1.96 (one-tailed: 1.645).
- **CI = β ± 1.96·SE** → "95% confident the true effect is in this range."
- **Significant ≠ causal ≠ important.** A big n makes tiny effects significant, so compare with cost.
- **Not significant ≠ no effect.** It means not enough evidence. Main fix: more data.
- **A bigger sample = a steadier hand, not better aim.** It reduces noise, not bias.
- **Heteroskedasticity = the errors *spread* more at some x.** Coefficient fine, SEs wrong → robust SEs.
- **Repeated rows from the same unit aren't new information → cluster SEs by the unit.** Treatment assigned per school → real n ≈ number of schools.

## Bias
- **Endogeneity = a "cheating x":** correlated with the error, so biased.
- **Multicollinearity = look-alike x's:** just blurry (bigger SEs). Don't drop one to fix it, or you create OVB.
- **OVB needs both:** the omitted variable affects y **and** is related to x.
  - **Sign = (effect on y) × (relation with x)**: + × + = too high; + × − = too low.
  - Write the words **"too high" / "too low"**.
- **Noisy x flattens the slope toward 0 (attenuation)**, and more data doesn't fix it. Noisy y just blurs.
- **Reverse causality / simultaneity:** police ↔ crime, price ↔ demand.
- **To see one curve, wiggle the other:** a supply-shifter traces demand.
- **Bad controls:** never control for something the treatment itself changes (training → job title).
- **Survivorship / selection on the outcome:** you need the failures too.
- **Regression to the mean:** groups picked for being unusually low bounce back on their own → need a control group.
- **Compare the groups the coin made, not the groups people chose.**
  - That's intention-to-treat.
  - Effect per person who took it ≈ effect ÷ take-up rate.
- **A good predictor isn't a cause** (service calls predict cancelling; they don't cause it).

## Fixed effects & experiments
- **Fixed effects = "compare only within the same ___"** (store / school / week).
  - Removes everything constant within the group, **even unmeasured things**.
  - **Doesn't** remove differences *inside* the group (e.g. weak students placed in small classes).
  - **Can't** estimate something that never changes within the group (state minimum wage with state FE).
  - **Can** use a treatment that switches on partway through: before vs after within the same unit.
  - Add **time FE** for shocks that hit everyone at once. Watch for things that change at the same time as the treatment.
- **Randomization = the coin can't cheat.**
  - The difference in means is the effect.
  - Controls add precision, not unbiasedness.
- **Balance check:** compare pre-treatment traits. A big imbalance → suspect broken assignment, and control for the trait.
- **Choices depend on differences.**
  - A change that hits every option equally doesn't re-sort people.
  - It only changes the comparison with the **outside option**.
- **WTP from a table:** scale linearly ("per 10%" → 5% = half), add up the pieces, write the number.

## Messy data
- **Missing data:**
  - **MCAR** = coffee spill (harmless).
  - **MAR** = depends on something you *see* → control or reweight.
  - **MNAR** = depends on the missing value itself (burned-out people skip the burnout survey) → biased, can't fix from the data.
- **Disguised missing values:** 0, −9, 999, "$0.00", 1900/2099 dates, placeholders. Treat as missing and report how many.
- **Outliers: typo or Bezos?**
  - Fix typos.
  - For real extremes: winsorize (**caps** values, keeps rows), use the median or logs, and run it **both ways**.
- **Mean vs median far apart** → a few extreme or bad rows are driving the mean.
- **Always report n** next to an average; tiny n = noisy.
- **Bars start at zero; dots and lines may zoom.** No pies, no 3D.

## Merges
- **A merge adds columns, not rows.**
- **Rows multiply only when a key appears more than once on the lookup side.**
- **Left merge:**
  - Unmatched rows stay, with **blanks**.
  - Extra rows can only come from **duplicates on the right**.
- **Same row count ≠ everything matched.** Count the blanks.
- **Checklist:** key unique? same key type (leading zeros)? rows before/after? `validate`? who didn't match, and are they different?
- **Pick the left table by who you need to count** (customers who never ordered need customers on the left).
- **Roll-ups:** add up the counts, then divide. Don't average percentages.

## Big data workflow
- **Size it → peek → pick columns → filter → clean → shrink → join safely → report n.**
  - Pandas is fine under ~10M rows and a file under ~1/5 of RAM.
  - Otherwise use DuckDB/Polars.
- **Shrink before you join. Never load what you can shrink.**
  - Aggregate per unit first.
  - Remove duplicate addresses before looking them up.
  - Convert units at the end.
- **CSV = read the whole book to find one word. Parquet = jump to the right chapter** (columnar, compressed).
- **Memory:** a merge or `df = df…` briefly makes about **2×** copies; a new column adds memory, not rows.
- **More cooks help only until they wait for the same grill.** multiprocessing works for independent jobs; tune 4 → 8 → 16.
- **glob builds the whole list in memory → use a lazy version for millions of files.**
- **Reproducible:** no hard-coded personal paths; a setting at the top; runs on any computer.

## Web data (classes 11–12)
- **File → API → hidden API → robot browser.** Use the highest one that works.
- **API gotchas:** keys, rate limits (429), **pagination** (a round row count → is there a page 2?), numbers arriving as text.
- **Status 200 = the waiter brought *a* plate, not your full order.** "No errors" ≠ correct data, so monitor runs.
- **Look for embedded JSON before parsing HTML.** Regex for patterns.
- **Look at the file before converting it** (PDF formats change). Ask: what's the best tool?
- **Cleaning = fixing the data. Checking = proving the conversion is right** (row counts, totals vs an independent source, random spot checks).
- **Blank cells in a report can mean "same as above" → fill down.**
- **Irregular snapshots → a regular panel:**
  - Use the last observation **at or before** each slot.
  - **Never a future one** (look-ahead).
  - Flag the filled rows.
- **Values can go backwards** (withdrawn pledges). Use the full history, not one snapshot.
- **Legal:** public scraping isn't hacking (hiQ); terms of service alone are weak (Bright Data); trade secrets can still be protected (Compulife).
