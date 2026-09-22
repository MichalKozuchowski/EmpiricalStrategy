# Class 6 — Lab Day 1: TSA Checkpoint Data Challenge
**Session 6, MGT 634** — timed team lab (prelim findings due 11:20am same day).
Companion: [class6-reading-notes.md](class6-reading-notes.md) (NYT air-travel-recovery article,
same TSA checkpoint dataset, same instructor Kevin Williams).

## Scenario
Airbnb "US air team" — tracking air travel (via TSA security checkpoint counts) as a proxy for
trip-driven Airbnb demand. Explicitly **demand-side only**; a separate team covers supply
(real estate). Checkpoint data = hourly passenger counts per security checkpoint, nationwide.
Key structural quirk: connecting passengers are counted only at their **origin** checkpoint (a
Hartford→Denver→Kona traveler appears only in the Hartford count) — so counts are an origin-level
demand signal, not a true airport-traffic signal.

## Data & environment
- Data: `~/esai_2026/data/TSA` (parquet files)
- Helper functions: `~/esai_2026/class/Session6/` (includes `haversine_example.py` for
  distance-based questions)
- OOD setup: reserve **2 hours**
  - 2 team members: **4 Cores / 32G** — run "production code" on full data for final answers
  - Remaining team members: **1 Core / 4G** — prototype/test with a subsampled frame:
    ```python
    import polars as pl
    df = pl.scan_parquet(<<FILENAME>>).limit(100000).collect().to_pandas()
    ```

## The 15 questions (lettered A–O)
| # | Ask |
|---|-----|
| A | Checkpoint with the highest passenger count ever |
| B | Date with the most passengers flying from Miami, FL (MIA) |
| C | Busiest airport in the country in 2024 |
| D | Busiest hour of day overall (aggregate) |
| E | Airport with greatest % growth, 2024 vs. 2021 |
| F | Airport with greatest growth in levels, full-year 2023 vs. full-year 2024 |
| G | Busiest airport between 10–11pm in 2025 |
| H | Among airports whose busiest weekday is Friday, which has highest 2022 volume |
| I | Airport with most consistent travel across weekdays (lowest avg. variance) |
| J | Busiest airport on New Year's Day, 12:01am–1am, 2015 |
| K | State(s) in 2024 where July is busier than March |
| L | Airport with >100k passengers/year in 2018 with the greatest % drop by 2024 |
| M* | Two closest airports within California (Haversine distance) |
| N* | Among airports with >1M passengers/year, the two closest to each other |
| O*** | Given traffic level, growth, variability, and nearby-city demand potential — which airport should Airbnb target, and why (short write-up) |

\* M and N require merging in a separate airport-location file from the same data folder.
\*\* Use the Haversine distance formula — see `haversine_example.py`.
\*\*\* O is a synthesis question requiring outputs from the others, with a short written rationale.

**Scoring**: highest-scoring team wins (prize: Elena's).

## Team strategy notes (as worked out with Claude, live)
- Team of 4 — pair each 4-Core "production runner" with a 1-Core "prototyper," split the letter
  set into two parallel streams so both big-compute seats run simultaneously.
- Do a 5-minute shared schema recon first (column names, date/time format, airport code field,
  whether state is already present) before splitting — avoids 4 people re-discovering the same
  thing independently.
- K may also need the location/merge file if state isn't already a column — flagged as unverified
  going in, confirm during recon.
- Centralize answers in one shared sheet/doc as they land, not 4 separate copies.
- O last, after both streams report in — it needs the full picture (traffic, growth, variance,
  proximity) to write the rationale.
