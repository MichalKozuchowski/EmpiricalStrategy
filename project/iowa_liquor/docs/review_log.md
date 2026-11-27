# Review log: independent critique and our responses

We used a separate AI reviewer agent ("skeptical IO economist") to critique the analysis, then fixed what it caught. That is part of the project's AI workflow, and it's worth showing in the talk.

## Review 1 (Nov 27): main points and what we did
| # | Critique | Response |
|---|---|---|
| 1 | A uniform-markup optimum isn't identified: month FE absorb aggregate variation, and the outside share is just the assumed market size M | **Agreed.** We dropped "the revenue-maximizing markup" as a headline. Counterfactuals (09) use a calibrated nested logit and report results over a grid of M (1.5×, 2×, 3× observed liters) and σ (0, 0.5, 0.8) |
| 2 | Posted prices mix list prices and temporary cuts; stores stock up before announced increases | **Confirmed in our data** (07): about +2.6% in the month before an increase. The event study keeps only changes that hold ≥ 2 months: implied elasticity −0.31 (increases) / −0.59 (decreases), consistent with the logit −0.63. We state that store orders are a proxy for consumer demand |
| 3 | 2019 pass-through used the wrong denominator: the tariff is on customs value, not the Iowa price | **Fixed.** We report pass-through for customs shares of 30–100% of the supplier price: about 36–72% at plausible shares. Exact customs unit values need the Census trade API (free key; to do) |
| 4 | 2025 null may be an artifact: new 700 ml SKUs, survivors only, category-based treatment, pre-trends | **Fixed.** Origin coded by brand (`nests.origin_of`, about 92% of imported dollars hand-checked). Base = 12 months right before Apr 2025. $-weighted and unweighted. **700 ml = 0.5% of treated dollars**, so not the explanation. **The null survives** |
| 5 | 2019 control group contamination; collector bottles; unweighted | **Fixed.** $1–150 items only, $-weighted. **Added a second treated group the 2019 tariff covered** (DE/IE/IT/ES/UK liqueurs): +6–7%, which replicates the Scotch result. Caveats listed in the script header |
| 6 | Nested logit: σ ≈ 1 is mechanical; count instruments invalid; homoskedastic F; follow the class-20 spec | **Done** (08): brand-group demeaning, liter shares, zero months filled, rival-vendor characteristic instruments, no month FE, cluster-robust F at nest-month. **Result: still invalid** (price coefficient > 0, λ = 0.94, partial R² ≤ 0.8%). Reported as a negative result; the counterfactuals use σ as a sensitivity parameter |
| 7 | Code details | Cluster-robust F added (`econ.cluster_F`); Nov 2025 excluded from the price-change timing figure; blank categories and vendors handled |
| 8 | Docs: Seim & Waldfogel AER conclusion; Iowa §123.24 wording; stale status | **Fixed.** AER 2013 abstract quoted ("profit maximization with profit sharing"); §123.24(2)(a)–(d) quoted including the bottle surcharge; status updated |
| 9 | Headline should be actionable: HF 830 minimum unit price, alcohol-based markup | **Adopted:** 09 simulates HF 830 and a revenue-neutral alcohol-content markup |

## Review 2 (Nov 27): main points and what we did
| # | Critique | Response |
|---|---|---|
| 1 | HF 830 bases the 50% markup on max(supplier price, floor). A profit-maximizing supplier will raise its price to the floor and keep the difference | **Adopted** (09): two cases. **A1** (suppliers keep prices): state +$44–60M/yr. **A2** (suppliers price up to the floor): state only +$13–26M; suppliers **+$27–53M**. Upper bounds with no quantity response: $68M vs $23M |
| 2 | Drinking effects rest on an elasticity estimated from small price changes, applied to +60–160% jumps | **Adopted:** fans over elasticity −0.4 / −0.63 / −1.0 × σ × M. Checked against Scotland's MUP (PHS 2023: about −3% sales), which sits near the low end of our fan (`literature.md`) |
| 3 | Cross-border leakage could undo a floor in border counties | **Adopted:** the floor-bound border volume carries $30M of margin; 10/25/50% leakage costs $3.0/7.6/15.1M/yr |
| 4a | 2025: EU price gap drifted down before the tariff, so a level DiD can hide pass-through | **Done** (06 §4): group-specific linear trends. EU 15%: +1.2% (SE 1.0); EU 10% from Mar 2026: +2.5% (SE 1.2). Treated as an upper bound; still far below full pass-through (about +6%) |
| 4b | 2025: suppliers might raise prices by re-listing under a new item number (Hennessy VS 48106 → 48241) | **Checked** (06 §5): 10 tariffed re-listings after Apr 2025 averaged +1.1% vs +5.3% for 57 control re-listings. No hidden pass-through |
| 4c | 2025: alternative explanations (national pricing by US subsidiaries, weak market, stronger euro) | **Added** to the interpretation (`data_notes.md`). Framed as a contrast between two episodes, not a causal claim about why |
| 4d | 2019: extend to 2023; add a placebo | **Done** (04): window to Dec 2023. Republic of Ireland whiskey (EU, not covered): +1.3% $-weighted / −0.4% unweighted. Effect persists through 2021; single malt drifts up again from late 2022 (separate trend, not attributed) |
| 5 | 07: trim outliers, cluster by item; decreases follow falling sales | **Done:** \|dlog p\| ≤ 0.5, SE by item. Increases are the clean estimate (−0.2 to −0.4); decreases have a pre-trend (+3.4%), so cuts partly respond to demand |
| 6 | Small errors: 8,300 vs 9,059 price changes; stale docstrings in 05 and 07 | **Fixed** |
| 7 | Talk storyline and headline | **Adopted:** `docs/slides_outline.md` |
| — | Not yet done | Customs unit values (Census API key needed) to pin down 2019 pass-through. A second control state's price list for 2025 (e.g. a Pennsylvania or Virginia ABC list) |
