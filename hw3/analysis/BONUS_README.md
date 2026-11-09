# HW3 BONUS: Porter (1983) Table 3, columns 3–4 (maximum likelihood, yielding PN)

**AI use:** this bonus is the **only** part of HW3 where AI is allowed, and it was done with AI (Claude).
Questions 1–5 are **not** in this folder; they must be done without AI.

## Files
| File | What it is |
|---|---|
| `bonus_table3_ml.py` | Full annotated code: data → model → Kiefer E-M → ML standard errors → table + figure |
| `bonus_output.txt` | Console output of the run (iterations, robustness, final table) |
| `bonus_table3_ml.csv` | Our Table 3 cols 3–4 next to Porter's numbers |
| `bonus_PN_series.csv` | Week-by-week probability of collusion (w_t) and the PN classification |
| `bonus_figure_PN_vs_PO.png` | Grain rate with observed (PO) vs estimated (PN) price wars, like Porter's Figure 1 |

## How to run
- **Locally (uv):**
  ```
  uv run --with pandas --with numpy --with scipy --with numdifftools --with matplotlib --with xlrd python bonus_table3_ml.py
  ```
- **Cluster:**
  1. Paste the whole `.py` file into one Jupyter cell.
  2. Uncomment the two `pip` / `sys.path` lines in section 0.
  3. Run it. The script searches your home folder and `/gpfs/project/esai_2026` for the JEC file (csv/xls/xlsx/dta).
- **Runtime:** about 30 seconds.
- **Data:** the run below used the public Stock & Watson `JEC.xls`. It's the same 328 weeks, and its means match Porter's Table 2 (GR 0.2465, TQG 25,384).

## Method (Porter pp. 305–306)
- **Demand:** `log Q = a0 + a1 log P + a2 LAKES + seasons + U1`
- **Supply:** `log P = b0 + b1 log Q + b2'DM + b3 I + seasons + U2`
  - `I` = collusion indicator (unobserved).
  - `U ~ N(0, Σ)`, with the Jacobian `|1 − a1·b1|` in the likelihood.
- **Variable mapping:**
  - `LAKES = 1 − ice`.
  - `PO = cartel`.
  - `DM1–DM4` are built from the running week number using Porter's Table 1 dates (52 weeks per year).
  - 12 seasonal dummies (`seas1–seas12`) enter both equations.
- **Kiefer E-M**, starting from `w0 = PO` as Porter did:
  - **E-step:** compute `w_t = Pr(I_t = 1 | data)` by Bayes' rule.
  - **M-step:** maximize the weighted likelihood (Σ concentrated out), then set `λ = mean(w)`.
  - Iterate to convergence, then polish by maximizing the full likelihood (eq. 5) directly.
- **Standard errors:** from the numerical Hessian of eq. (5).
- **Classification:** `PN = 1` if `w_t > .5` (Lee & Porter rule).

## Results
| Variable | Demand (ours) | Demand (Porter) | Supply (ours) | Supply (Porter) |
|---|---|---|---|---|
| C | 9.030 (.156) | 9.090 (.149) | −1.858 (1.001) | −2.416 (.710) |
| LAKES | −.426 (.118) | −.430 (.120) | | |
| GR (log price) | −.842 (.098) | −.800 (.091) | | |
| DM1 | | | −.170 (.035) | −.165 (.024) |
| DM2 | | | −.196 (.041) | −.209 (.036) |
| DM3 | | | −.313 (.042) | −.284 (.027) |
| DM4 | | | −.220 (.074) | −.298 (.073) |
| PN (β3) | | | .515 (.045) | .545 (.032) |
| TQG (log quantity) | | | .035 (.098) | .090 (.068) |
| R² | .299 | .307 | .833 | .863 |
| s | .401 | .399 | .121 | .109 |

- **λ = 0.758:** the model classifies 250 of 328 weeks as collusive (`PO` has 203). PN and PO agree in 79% of weeks.
- **Implied conduct parameter** θ = a1(e^(−β3) − 1) = **0.339** (Porter: 0.336). This is roughly **Cournot**: between competitive pricing (0) and full joint monopoly (1).
- **Close but not exact.** The likelihood is **very flat in the supply slope** (TQG):
  - Fixing TQG at Porter's .090 lowers the log-likelihood by only 0.14 (LR = 0.28, p = 0.59).
  - At that value the supply constant becomes −2.420 (Porter: −2.416) and PN becomes .538 (Porter: .545).
  - So Porter's estimates are statistically indistinguishable from ours. The gap comes from optimizer and stopping-rule details: Porter stopped when the correlation of successive w's exceeded .999. With that rule our E-M stops after 7 iterations, at a log-likelihood 0.4 below the maximum.
- **Robustness to starting values:**
  - Starting from `PO` or from "high-price weeks" converges to the same maximum (log-likelihood −79.76, identical PN).
  - Flat or random starting weights get stuck at a no-switching point (β3 ≈ 0, log-likelihood −143.7, far worse). The E-M needs an informative start, as Porter's did.
- **Interpretation:**
  - Demand is inelastic (−0.84).
  - Price is about 0.5 log points (~67%) higher in collusive weeks.
  - The model's price wars line up with the Railway Review reports (1881, 1884, 1885), but tend to start a little later and end at the same time. This is consistent with Porter's remark that PO sometimes reports a war before PN.
