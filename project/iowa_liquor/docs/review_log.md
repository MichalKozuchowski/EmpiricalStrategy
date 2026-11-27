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
