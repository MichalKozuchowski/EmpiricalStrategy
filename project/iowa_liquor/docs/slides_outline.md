# Slides outline (15 minutes; every team member presents)

**The deck is built:** `slides/Iowa_Liquor_Final.pptx` has 13 slides plus 2 backup slides, with speaker notes. It was rebuilt from `slides/build_deck.js`. The table below is the original plan. The deck follows it, with a data slide, a 2019 pass-through slide and a 2025 slide added.

**Headline:** *In Iowa, suppliers decide who pays. They passed on half of the 2019 tariff, absorbed the 2025 ones, and would pocket most of a minimum-price windfall. Tax alcohol content, not price.*

About 80 seconds per slide. The presenter split is a placeholder; assign it once team roles are set.

| # | Slide title (the takeaway) | Content | Source | Presenter |
|---|---|---|---|---|
| 1 | **Iowa sells every bottle of spirits, at 1.5 × the supplier's price** | Iowa is the sole wholesaler: about 2,200 stores, one statewide price. Data: every order 2018–2026 (25–31M bottles/yr, $139M state margin). The decision: what should Iowa's pricing rule be? | `data_notes.md` | TBD |
| 2 | **Two questions a legislator would ask** | (1) When costs rise (tariffs), who pays: suppliers, the state or drinkers? (2) Bill HF 830 (2025) proposes a minimum price per unit of alcohol. What would it do to drinking and revenue, and who gets the money? | README | TBD |
| 3 | **Identification: prices only move over time** | Uniform prices (0.03% of item-days differ across stores) and rare changes (3% of items a month, in quarterly waves). So we use tariff shocks and list-price changes, as Seim & Waldfogel did in Pennsylvania. Methods: DiD/event study, IV, logit and nested logit, simulation | `fig_price_change_timing.png` | TBD |
| 4 | **2019: a 25% tariff → +5% in Iowa, and it never came back down** | Event-study figure: single malt and EU/UK liqueurs jump one quarter after Oct 2019; flat pre-trends; Irish whiskey placebo flat; no reversal after the 2021 suspension. Census customs values: 45% pass-through (CI 30–61%), liqueurs 49%. Per bottle: $3.43 duty → +$2.32 in Iowa | `fig_tariff2019_event_study.png`, `04` | TBD |
| 5 | **2025: 10–15% tariffs → nothing** | Event study: UK/EU vs US/USMCA, ±1.6% across five regimes. Robust to group trends (≤ +2.5%) and re-numbered products. Why? Contested, temporary-looking tariffs; national pricing by big importers; weak market. **Same state, same markup rule, opposite pass-through: suppliers decide** | `fig_tariff2025_event_study.png`, `06` | TBD |
| 6 | **Iowa buyers barely react to price** | Logit elasticity −0.63; own list-price increases −0.2 to −0.4; stores stock up +3% the month before increases (an anticipation check). Seim & Waldfogel: −1.2 to −1.5 in Pennsylvania | `fig_price_change_events.png`, `05`, `07` | TBD |
| 7 | **What didn't work: the nested logit** | The class-20 spec (rival-vendor instruments, liter shares, zero-fill) gives a price coefficient > 0, partial R² < 1%. Honest negative result → σ becomes a sensitivity parameter in the simulations. (Shows the AI-reviewer loop: two independent critiques, `review_log.md`) | `08`, `review_log.md` | TBD |
| 8 | **HF 830 would hit cheap handles, not drinks in general** | Binds on 14% of items but 48% of liters. Black Velvet 1.75 L $17 → $29; cheap vodkas +130–160%. Cheapest quartile −12% liters; pricier tiers +9–11% (people trade up) | `counterfactuals.md` incidence tables | TBD |
| 9 | **Who gets the money? Suppliers, unless the law stops them** | Bar chart, A1 vs A2. The state gains +$44–60M if suppliers keep prices, but only +$13–26M if they price up to the floor (suppliers +$27–53M). Border leakage −$3–15M | `09` | TBD |
| 10 | **Better: price the alcohol, not the bottle** | A revenue-neutral markup per liter of pure alcohol: −1% to −7% pure alcohol, $0 revenue cost, no supplier windfall clause needed. Scotland's MUP (−3% sales) as a reality check | `09`, `literature.md` | TBD |
| 11 | **Recommendation and limits** | (1) If Iowa wants less drinking, use an alcohol-content markup, or write HF 830 so the gap between the floor and the supplier's price is collected as a state levy, so a supplier gains nothing by raising its price up to the floor. (2) Don't count on tariffs reaching shelves: it depends on supplier strategy. Limits: store orders ≠ consumption; elasticity extrapolated to big price jumps; customs values not yet measured | all | TBD |

## Figures
- **Done** (`code/10_slide_figures.py`):
  - slide 9: `output/fig_hf830_who_gets_money.png` (state vs supplier gain, A1/A2/B);
  - slide 10: `output/fig_policy_alcohol.png` (pure alcohol change by policy and elasticity, with the Scotland benchmark).
- **To do:** slide 8, price change by quartile and nest (from the incidence tables in `counterfactuals.md`); slide 1, a simple numbers graphic (optional).
