# Project plan

## 1. What the brief asks for (Prof. Williams, MGT 634 Final Project)
| Requirement | How we meet it |
|---|---|
| A question that matters for a **business/policy decision**, with an answer we don't already know | Iowa's pricing of its liquor monopoly: tariff incidence plus whether the 50% markup is the right price (revenue vs welfare) |
| **Real data** with real data work | Every Iowa store order 2018–2025 (about 20M rows) plus the state price list; built with DuckDB |
| Core analysis uses **second-half methods**, ideally two or more | DiD/event study (tariffs) + IV (tariff cost shifter, rival characteristics) + nested logit demand + optimization (markups) |
| Credible analysis; explain what didn't work | Endogeneity discussion (price changes timed to demand?), placebo tests, robustness to market size and nests |
| **Deliverables** (due before class **Thu Dec 10**) | (1) slides; (2) a folder with code + data + a short README (if the data are too large, code to download them, which is `01_download.py`) |
| **Presentation**: 15 minutes + Q&A, Dec 10 or 15; **every member presents** and answers questions on any part | Split the slides by section (see §4) |

## 2. Analysis pipeline
1. **Build** (`02_build_panel.py`, done): item × month and county × item × month panels; category list.
2. **Descriptives** (`03_descriptives.py`):
   - market size and seasonality;
   - how often prices change, and when;
   - category shares;
   - a top-sellers table;
   - price-change timing (quarterly like Pennsylvania? January?).
3. **Tariff event studies** (`04_tariffs.py`):
   - **2019 Scotch tariff:** single malt vs blended Scotch and other whiskies. Monthly event study of log price (pass-through) and log bottles (quantity), Oct 2019 on and Mar 2021 off.
   - **2025 UK/EU tariffs:** imported EU/UK categories vs domestic and tariff-exempt (tequila, bourbon).
   - **Pass-through:** % change in Iowa price ÷ tariff rate. With the 1.5× markup, full pass-through of the cost means the state's price rises by the full tariff % and the state collects extra margin on it.
4. **Nested logit demand** (`05_demand.py`), following the class 20 Zappos spec:
   - j = item (product × bottle size); m = Iowa × month (and county × month as an extension).
   - Market size M = adults 21+ × an assumed bottles-per-month figure (choose and justify; test robustness).
   - Nests = spirit type (whiskey / vodka / rum / tequila / gin / brandy / liqueur / other).
   - Endogenous: price and log(within-nest share).
   - Instruments: tariff exposure × post-period; rival characteristics in the nest (proof, age, size counts and averages from the price list); the number of products in the nest.
   - Fixed effects: product, or brand groups by demeaning (as in the paper spec), plus calendar-month and holiday controls; **no** nest × market fixed effects.
   - Compare with OLS. Check the first-stage F and partial R², whether σ is in [0, 1), and the sign of α.
5. **Counterfactuals** (`06_counterfactuals.py`):
   - State revenue R(m) = Σ (p_j − c_j)·q_j with p_j = (1 + m)·c_j.
   - Find m* maximizing revenue and m** maximizing CS (logsum) + revenue; compare with m = 0.5.
   - Category-specific markups subject to the average ≤ 50%.
   - **Tariff incidence:** split each tariff dollar between consumers (CS loss), the state (margin gain or loss) and suppliers (lost sales).

## 3. Timeline (today = Fri Nov 27)
| Date | Milestone |
|---|---|
| Nov 27–29 | Data downloaded and built ✅; descriptives; tariff dates confirmed; nest and tariff-exposure mapping |
| Nov 30 – Dec 2 | Event studies (both tariffs); first demand estimates |
| Dec 3–5 | Instruments, robustness, counterfactual markups; draft figures |
| Dec 6–8 | Slides; README for the submission folder; practice run |
| Dec 9 | Final check that everything runs from scratch |
| **Dec 10** | **Submit before class**; be ready to present |

## 4. Open questions for the team (need decisions)
- **Team:** who is in the group, and who takes which section (data/descriptives, tariffs, demand, counterfactuals, slides)?
- **The professor's reply** to the Nov 17 paragraph: any constraints or suggestions?
- **Scope:** both tariff events, or focus on one? (The 2025 tariffs are more topical; 2019 has a clean on/off.)
- **Market:** Iowa × month (simple) vs county × month (adds geography; needs county adult population from the Census).
- **Consumer welfare:** these are store orders, so the "consumer" in the model is the store's customers. State the assumption that store markups don't change.
