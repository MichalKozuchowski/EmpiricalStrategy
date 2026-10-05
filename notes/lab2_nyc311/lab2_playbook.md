# Lab Day 2 playbook: NYC 311 review (Tue Oct 6, 80 minutes)

Scenario: McKinsey team reviewing the NY State Comptroller's (OSC) **NYC311 Monitoring Tool**
(report 3-2026, May 2025) after Mayor Mamdani's pledge that **from Oct 1, 2026 inspectors
investigate every heat complaint**. Data: ~3,000 JSON files (64 GB+ if loaded at once).
Toolkit: [lab2_toolkit.ipynb](lab2_toolkit.ipynb) (same code as `lab2_toolkit.py`), tested on a
152-file fake dataset under Python 3.9 / pandas 2.3.3. Fresh run: 12 s for 1.5M rows; a cached
re-run: 6 s.

## Before class (5 min)
1. OnDemand: **2 people reserve 4 cores / 32 GB** (production), the others 1 core / 4 GB.
2. Upload `lab2_toolkit.ipynb` to your cluster home folder.
3. Prototypers: set `STRIDE = 30` in the setup cell (every 30th file, spread over all years).

## Minute-by-minute
| Time | Production seats | Prototype seats |
|---|---|---|
| 0-10 | Run setup + recon (prints folder, files, GB, years, fields) | Same with STRIDE = 30; read the handout, split the questions |
| 10-20 | Run convert + clean (minutes) | Draft answers on the sample with `show("SELECT ...")` |
| 20-60 | Full-data answers; run A, B, C | Charts, the dashboard critique, recommendations |
| 60-75 | Re-check every number on full data | Write-up |
| 75-80 | Submit | |

One shared doc for answers. If the professor hands out lettered questions, map each to a cell
or snippet below; anything new is one `show()` call against the `sr` / `heat` views.

## Where each kind of question lives
| Question type | Use |
|---|---|
| What's in the data / how big / which years | Recon cell |
| Data problems (bad dates, ZIPs, boroughs, duplicates) | Section 3 check table |
| Do we match the OSC report? | Block A (Appendix B, 2019/2023/2024) |
| Heat volume, label change, seasons | B1, chart D1 |
| Were heat complaints actually investigated? | B2 outcome mix, chart D2 |
| Repeat complaints / buildings | B3 |
| Inspector staffing for "every complaint" | B4 (change `INSPECTIONS_PER_DAY`) |
| Has anything changed since Oct 1, 2026? | B5 |
| Response / closing times | Block C |
| New file handed out (population, ZIP crosswalk...) | `df = profile(path)`, then `to_duck(df, "name")` or `merge_report()` |

## Ready-made queries (paste into `show("...")`)
- Top 10 complaint types in 2024 and their growth vs 2023:
  `SELECT complaint_type, sum((year=2023)::INT) n23, sum((year=2024)::INT) n24, n24/n23-1 growth FROM sr GROUP BY 1 ORDER BY n24 DESC LIMIT 10`
- Busiest borough for heat per season: `SELECT heat_season, boro, count(*) n FROM heat GROUP BY ALL ORDER BY 1, n DESC`
- Channel mix (phone / online / app) by year: `SELECT year, open_data_channel_type, count(*) n FROM sr GROUP BY ALL ORDER BY 1, n DESC`
- Hour of day (only real times): `SELECT hour(created) h, count(*) n FROM sr WHERE NOT date_only GROUP BY 1 ORDER BY 1`
- Community boards with most heat complaints in 2024-25: `SELECT community_board, count(*) n FROM heat WHERE heat_season='2024-25' GROUP BY 1 ORDER BY n DESC LIMIT 10`
- Buildings with the most heat complaints: `SELECT bbl, any_value(incident_address) addr, count(*) n FROM heat WHERE heat_season='2024-25' GROUP BY 1 ORDER BY n DESC LIMIT 10`
- Share closed within 7 days, by agency: `SELECT agency, avg((days_to_close<=7)::INT) share FROM sr WHERE closed_ok GROUP BY 1 ORDER BY 2`
- Per-capita (if a population table is given): `to_duck(pop, "pop")`, then join on borough / ZIP / community board.

## Data traps (all handled in the toolkit, worth saying out loud)
- Heat label changed: **"HEATING"** in older years, **"HEAT/HOT WATER"** later. Count both.
- **Borough "Unspecified"** on 62% of sample rows: recovered from the building id (bbl) and the ZIP.
- **Closed dates of 1900-01-01** and closings before opening: excluded from time-to-close.
- **62% of timestamps are midnight** (date only): response times in days, hour-of-day only on real times.
- **9-digit / missing / non-NYC ZIPs.** OSC dropped 321k requests without a valid ZIP from its neighborhood view.
- **Duplicate request ids** across files: the latest copy is kept.
- **Unreadable files** are skipped and listed.
- Records leave out empty fields, so columns are not the same in every record.

## What the sample already shows (batch 0001, 2010, 4,103 heat complaints)
Only **~9% of heat complaints led to an inspection** (6.8% no violation + 2.3% violation).
The rest:
- 63% corrected by phone with an occupant
- 15% no access
- 12% "restored" per a tenant

If that holds in recent seasons, "inspect every complaint" means **roughly 10× the current
inspection volume**. That's the headline to test with B2 and size with B4.

## Dashboard critique (OSC tool) to tie to class
1. **Pie charts** (Figure 2): Class 5 said never; use sorted bars or a slope chart 2019 → 2024.
2. **Counts complaints, not problems**: one building's outage can produce dozens of calls (B3). Show unique buildings and building-days.
3. **Wrong denominator for heat**: per 1,000 residents, not per rental unit / regulated building.
4. **Missing ZIPs dropped** (321k) from the neighborhood view: biased if missingness is not random (Class 4: MAR/MNAR).
5. **ZIP → PUMA** is an approximation of neighborhoods; community board / bbl are in the data.
6. **Volume only, no outcomes**: no time to close, no inspection rate, no repeat rate, which is exactly what the pledge needs.
7. **No snapshot date**: the city revises the dataset, so the tool's numbers can't be reproduced (our block A shows the gap).
8. **Dropped retired complaint types**: fine for "current demand", but label changes (HEATING) need a mapping, not a drop.

## Recommendations (draft)
- A **heat pledge scorecard**, updated weekly:
  - share of heat complaints inspected in person
  - median time to inspection
  - no-access rate
  - repeat complaints within 7 days
  - by community board and per rental unit
- **Count unique building-days**, not raw calls, to plan inspector capacity, and staff for cold-snap peaks (B4).
- **Publish the data snapshot date** and a label crosswalk, so the tool is reproducible.
