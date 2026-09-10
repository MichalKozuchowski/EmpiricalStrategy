# Class 3 — Slide Deck: "Data Basics"
**Prof. Kevin Williams, Sep 10, 2026** — slide deck only; discussion/transcript notes to be
added separately once the recording comes in.

## Three views on data work (slide 2)
1. **Never touch raw data** — trust a codebook + AI queries to get the "correct" sample.
   Downside: prompting AI well is itself a skill requiring real investment and oversight.
2. **Explore manually first** to find strengths/weaknesses, then guide the AI with that.
   Downside: AI may actually spot those issues faster/better than a human would.
3. **Only do the processing yourself**, so you know exactly what's in the final product.
   Downside: humans make mistakes too — and "all errors are my own" arguably still covers
   AI use anyway.

This class tries all three across the semester.

## Getting on the HPC (slide 3, review)
1. Connect to Yale Secure WiFi (or VPN)
2. Open a **private/incognito browsing window** (Safari or Chrome)
3. Go to Open OnDemand (OOD) and log in

## Initial data pipelines (slide 4)
- Create a folder in your home directory to organize each day's code.
- For bigger projects, consider subfolders: `src` (source code), `aux` (misc tables/resources),
  `_out` (output), `_err` (errors) — ask the AI for best-practice folder layouts.
- Today's skill: data cleaning and data processing. Start a new Jupyter notebook, load the
  2024 taxi data.

## Reminder: loading the data (slide 5)
```python
import sys
!{sys.executable} -m pip install --user matplotlib

import pandas as pd
df = pd.read_csv('~/esai_2026/data/chicago_taxi_trips_2024/Taxi_Trips_2024.csv', nrows=1000)
```
**Same quote gotcha as last class** — copying straight from the slide gives curly quotes,
which throw a `SyntaxError`. Retype straight `'` or `"` quotes.

## Data cleaning: on the fly, or saved to disk? (slide 6)
- Last class: trips with avg MPH of 0 or `inf` — comes from 0-distance and/or 0-duration trips.
- Whether to drop them depends on the application; there's no universal answer.
- Rule of thumb from the professor: **the bigger the project (millions of rows) or the more
  complex the cleaning, the more worth it to pre-clean the data once and save it**, rather than
  re-clean on the fly every time.

## Today's exercise: ORD arrivals vs. departures (slides 7–10)
**Setup**: build two dataframes from the 2024 taxi data —
1. Rides that **end** at O'Hare (ORD)
2. Rides that **start** at ORD

Identify ORD via Census Tract: **tract 9800**, GEOID **17031980000**.

**Prompt given in class**: *"It is not an unreasonable hypothesis that taxi trips to airports
differ from taxi trips from airports. Relevant factors include day of the week, origin/destination
location, time of day, etc. Is this true? Can we measure it?"*

**Task**: determine whether rides *to* ORD differ from rides *from* ORD, and how.

Cleaning considerations raised explicitly:
- Rides that don't go anywhere (0 distance/duration) — same issue as last class
- Rides that take longer than some threshold X — what's a reasonable cutoff?
- Missing Census Tract data: Chicago DOT's own note says tract is blanked for some trips for
  privacy, and is often blank for locations outside Chicago — decide whether/how that matters
  for this analysis

**Pipeline framing**: Load → Clean → Split → Analyze → Summarize (for the 2024 file). For the
much bigger 2013–2023 data (hundreds of millions of rows across many files), the order likely
needs to shift to Load → Clean → Analyze → Aggregate → Summarize instead — size and resource
constraints change what pipeline makes sense, not just the question being asked.

**Your actual task** (per the slide): define a set of cleaning criteria, implement it *before*
splitting into the two dataframes, then analyze the partitioned samples and document what
differs.

## Tips (slide 10)
- Add sanity checks throughout: print the row count right after loading, and again after every
  drop/filter, so you can see exactly what each step removed.

**Debrief questions to be ready to answer:**
- What did you drop, and why?
- What did you find — do ORD-bound and ORD-origin trips actually differ?
- How would you present this information?
