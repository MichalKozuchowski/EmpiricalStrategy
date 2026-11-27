# Iowa's liquor monopoly: who pays for tariffs, and what would a minimum unit price do?

MGT 634 (Empirical Strategy with AI), final project, Fall 2026.
- **Deadlines:** all materials due **before class Thu Dec 10**; 15-minute presentations Dec 10 / Dec 15.
- The brief is summarized in `docs/project_plan.md`.

## The question
Iowa is the **sole wholesaler of spirits**. It buys from suppliers and resells to about 2,200 private stores at **1.5 × the supplier's price**, the same price everywhere (Iowa Code §123.24). Two decisions depend on how prices and demand respond:
1. **Tariffs: who pays?** The US taxed imported spirits twice in our data: the 2019 "Airbus" tariffs (25%) and the 2025–26 UK/EU tariffs (10–15%). Iowa's percentage markup would *multiply* any cost increase that reaches it.
2. **Iowa's own pricing.** Bill **HF 830 (2025)** would put a **minimum unit price** ($0.50 per 18 ml of alcohol) under the 50% markup. What would that do to drinking, state revenue and consumers, compared with simply charging the markup per liter of alcohol?

This follows Seim & Waldfogel's (AER 2013) question for Pennsylvania's liquor monopoly, profit vs welfare (`docs/literature.md`), applied to pricing rather than store locations.

## Headline
> **In Iowa, suppliers decide who pays.** They passed on half of the 2019 tariff, absorbed the 2025 ones, and would pocket most of a minimum-price windfall. **Tax alcohol content, not price.**

## Headline findings so far (details in `output/`, `docs/data_notes.md`)
| Result | Evidence |
|---|---|
| **2019 tariffs: about half reached Iowa, and stayed.** Single-malt Scotch **+5.2%** and covered EU/UK liqueurs **+6.3%** vs untariffed products; flat pre-trends; **no reversal** after the 2021 suspension; **placebo** (Irish whiskey, not covered) about 0. Using US customs values (Census, dutiable lines): **pass-through 45% (95% CI 30–61%) for single malt, 49% for liqueurs**. Per 750 ml bottle: $3.43 duty → Iowa supplier cost +$1.55 → **Iowa price +$2.32**, of which $0.77 is extra state margin | `04`, `11`, `fig_tariff2019_event_study.png`, `customs_passthrough.md` |
| **2025–26 tariffs were not passed on** through Oct 2026: UK/EU prices moved −1.6% to +0.9% vs US/Mexico/Canada spirits across all five tariff regimes. With group-specific trends, at most +1–2.5% (full pass-through: about +6%). There was no hidden pass-through through re-numbered products | `06`, `fig_tariff2025_event_study.png` |
| **Iowa demand is inelastic:** own-price elasticity about **−0.6** (within-item logit) and **−0.2 to −0.4** around list-price increases. **Stores stock up** about +3% the month before an increase | `05`, `07`, `fig_price_change_events.png` |
| **HF 830 minimum unit price** binds on **48% of liters** (cheap handles +60–160%). Pure alcohol falls **−2% to −11%**: the cheapest quartile −12%, pricier tiers *gain*. Scotland's MUP cut sales about 3%, near our low end | `09`, `counterfactuals.md` |
| **Who gets the HF 830 money depends on suppliers.** If they keep their prices, the state gains **+$44–60M/yr** (on $139M). If they raise prices to the floor, as the bill's formula lets them, the state gains only **+$13–26M** and suppliers **+$27–53M**. Border leakage costs $3–15M | `09` |
| **A revenue-neutral alcohol-content markup** cuts pure alcohol **1–7% at zero revenue cost** to the state | `09` |
| Nested logit: neither our nest-count instruments nor the professor's class-20 spec (rival-vendor characteristics) gives valid estimates (price coefficient > 0). **Reported as a negative result**; σ is a sensitivity parameter | `05`, `08`, `docs/review_log.md` |

## Methods (second half of the course)
| Method | Where | Course reference |
|---|---|---|
| DiD / event studies: two tariff episodes, own price changes; customs-value pass-through | `04`, `06`, `07`, `11` | class 14 |
| IV / 2SLS: nested logit with BLP-style rival instruments; weak/invalid instrument diagnostics | `05`, `08` | class 15, class 20 lab |
| Logit / nested logit demand (Berry inversion), elasticities | `05`, `08`, `09` | classes 18–19 |
| Counterfactual simulation: HF 830, alcohol-based markup, markup grid | `09` | classes 18–19, Seim & Waldfogel |

## How to run (laptop or cluster)
- Everything uses `uv`; run from `project/iowa_liquor/`.
- Data go **outside the repo**: set `IOWA_DATA_DIR`, or use the default `~/mgt634_data/iowa_liquor`.
- **Space:** about 5 GB raw + 1 GB built.
- **Speed:** DuckDB streams all heavy steps (4 GB memory cap, spills to disk), and the estimation code is plain numpy (`code/econ.py`). Every step runs in seconds to a few minutes on a laptop or one cluster core.

```
uv run --with requests python code/01_download.py                     # 2018-2026 sales + price list (~2 min)
uv run --with duckdb --with pandas --with pyarrow python code/02_build_panel.py   # dedupe + panels (~5 min)
uv run --with duckdb --with pandas --with matplotlib --with tabulate python code/03_descriptives.py
uv run --with duckdb --with pandas --with numpy --with matplotlib --with tabulate python code/04_tariff_2019_scotch.py
uv run --with duckdb --with pandas --with numpy --with tabulate python code/05_demand_first_pass.py
uv run --with duckdb --with pandas --with numpy --with matplotlib --with tabulate python code/06_tariff_2025.py
uv run --with duckdb --with pandas --with numpy --with matplotlib --with tabulate python code/07_price_change_events.py
uv run --with duckdb --with pandas --with numpy --with tabulate python code/08_nested_logit.py
uv run --with duckdb --with pandas --with numpy --with scipy --with tabulate python code/09_counterfactuals.py
uv run --with pandas --with matplotlib python code/10_slide_figures.py                 # slide charts from 09 output
uv run --with duckdb --with pandas --with numpy --with matplotlib --with requests --with tabulate python code/11_customs_passthrough.py   # needs a free Census API key
```
**On the Yale cluster (no `uv`):**
1. Install once: `python -m pip install --user duckdb pyarrow pandas numpy scipy matplotlib tabulate requests`.
2. Run everything in order with `python code/run_all.py`. To run only some steps, list them, e.g. `python code/run_all.py 06 09`.

## Folder
```
code/     01-11 numbered steps; econ.py (fast exact FE + 2SLS); nests.py (spirit-type nests, country of origin)
docs/     project_plan.md, data_notes.md (verified facts + results), literature.md, review_log.md (two AI reviews), slides_outline.md
output/   results (.md) and figures (.png)
slides/   Iowa_Liquor_Final.pptx (the deck, 13 slides + 2 backup) and build_deck.js (rebuilds it from output/; needs node + pptxgenjs)
```
