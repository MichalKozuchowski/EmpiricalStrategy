# Iowa's liquor monopoly: who pays for tariffs, and is the 50% markup the right price?

MGT 634 (Empirical Strategy with AI), final project, Fall 2026.
- **Deadlines:** all materials due **before class Thu Dec 10**; 15-minute presentations Dec 10 / Dec 15.
- The brief is summarized in `docs/project_plan.md`; the original is `MGT_634_Final_Project.pdf` on Canvas.

## The question (business / policy decision)
- Iowa is the **sole wholesaler of spirits**. It buys from suppliers (Diageo, Sazerac, Pernod…) and resells to about 2,100 private stores at **1.5 × supplier cost**, the same price everywhere.
- **Two decisions** depend on how Iowa's liquor demand responds to price:
  1. **Tariff incidence:** when the US put a 25% tariff on single-malt Scotch (Oct 2019 – Mar 2021) and 10–15% tariffs on UK/EU spirits (2025), how much reached Iowa prices, how much did buyers cut back, and where did they switch to? Iowa's percentage markup **multiplies** a tariff: the state earns 50% on top of it.
  2. **The markup itself:** is the 50% markup revenue-maximizing, welfare-maximizing, or neither? Would category-specific markups do better (the statute allows this if the average stays ≤ 50%)?
- This follows Seim & Waldfogel's question about Pennsylvania's liquor monopoly, profit vs welfare (`docs/literature.md`). Our lever is price rather than store locations.

## Methods (from the second half of the course)
| Method | What for | Course reference |
|---|---|---|
| **Difference-in-differences / event study** | Tariff pass-through to Iowa prices and the quantity response (treated categories vs untreated ones) | class 14 |
| **Instrumental variables** | Tariff shocks as cost shifters for price; rival-product characteristics for the within-nest share | class 15, class 20 lab |
| **Nested logit demand** (Berry inversion) | Price elasticities and substitution (nests = spirit types: whiskey, vodka, rum, tequila, …) | classes 18–19, class 20 lab |
| **Counterfactuals / optimization** | Revenue- and welfare-maximizing markups (uniform and by category); tariff incidence for consumers vs the state vs suppliers | classes 18–19, Seim & Waldfogel |

## How to run
Everything uses `uv`. Run from `project/iowa_liquor/`. Data go **outside the repo** (about 4.5 GB raw); set `IOWA_DATA_DIR` or use the default `~/mgt634_data/iowa_liquor`.

1. **Download:** 2018–2025 sales plus the current product list (about 1 minute).
   ```
   uv run --with requests python code/01_download.py
   ```
2. **Build the panels:** item × month and county × item × month, using DuckDB.
   ```
   uv run --with duckdb --with pandas --with pyarrow python code/02_build_panel.py
   ```
3. **Descriptives:** market size, price-change frequency and timing, categories → `output/descriptives.md`.
   ```
   uv run --with duckdb --with pandas --with matplotlib --with tabulate python code/03_descriptives.py
   ```
4. **2019 Scotch tariff event study:** price pass-through and quantity → `output/tariff2019_results.md` and the figure.
   ```
   uv run --with duckdb --with pandas --with numpy --with statsmodels --with pyhdfe --with matplotlib --with tabulate python code/04_tariff_2019_scotch.py
   ```
5. **First-pass logit / nested logit demand** (not final) → `output/demand_first_pass.md`.
   ```
   uv run --with duckdb --with pandas --with numpy --with pyhdfe --with linearmodels --with tabulate python code/05_demand_first_pass.py
   ```

Coming next (see `docs/project_plan.md`): the 2025 tariffs, demand with instruments, and markup counterfactuals.

## Status (Nov 27)
- ✅ Data downloaded and cleaned. Duplicate rows found and removed; see `docs/data_notes.md`.
- ✅ Descriptives.
- ✅ 2019 tariff event study: **~3–5% Iowa price increase** for single malts (~15–20% pass-through), sticky after removal, no detectable quantity drop.
- ⏳ First-pass demand.
- ⬜ 2025 tariffs.
- ⬜ IV demand.
- ⬜ Markup counterfactuals.
- ⬜ Slides.

## Folder
```
project/iowa_liquor/
  README.md            this file
  code/                numbered scripts, run in order
  docs/
    project_plan.md    brief -> requirements -> plan, timeline, who does what, open questions
    data_notes.md      verified facts about the data (and the surprises)
    literature.md      Seim & Waldfogel + the course notes we build on
  output/              tables and figures (small; committed)
  slides/              presentation (to come)
```
