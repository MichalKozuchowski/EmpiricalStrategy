# Class 12 reading notes: "Aiming for the Goal: Contribution Dynamics of Crowdfunding"

Deb, Öry & Williams, *American Economic Review* 114(12), Dec 2024, pp. 3847-3876. (Kevin Williams, a co-author, teaches MGT 634.)

---

## 1. One-paragraph summary

**Question:** On Kickstarter, a campaign gets its money only if it reaches its goal by a deadline. Most backers ("investors"/"buyers") pledge to get a reward, such as the product. A few people ("donors") give money and take no reward, because they just want the project to happen. Why do donors give when they do, and how much does that timing help campaigns succeed? **Data:** every Kickstarter campaign launched March 2017 - September 2018 (42,462 campaigns), recorded every 12 hours, with reward pledges kept separate from donations. **Method:** (a) a game-theory model in which the donor's gifts act as a *signal* that tells buyers "this project will make it"; (b) descriptive facts that check the model's predictions; (c) the model is *calibrated* (its unknown numbers are set so it reproduces the data) and then used for *counterfactuals* ("what if" simulations). **Findings:** donations are 14% of all money raised. They stop after a campaign hits its goal (they fall 72% within 3 days, while buyer pledges fall only 37%). They spike right before the deadline: 78% of campaigns that succeed at the deadline would have failed without last-minute donations. In the calibrated model, letting the donor give bit by bit over time gives a success rate of about 16%. With no signaling it is about 3% (an average gap of 13 percentage points). Letting the donor give only once, at the start or at the end, does even worse than no signaling.

## 2. Key vocabulary

- **Crowdfunding, all-or-nothing:** many people each chip in a little online. Under "all-or-nothing", nobody is charged unless the total reaches the goal by the deadline. If it falls short, everyone gets their money back.
- **Investor / buyer:** someone who pledges the reward price *p* to get a reward worth *v* to them. They care about the project only because of their own reward (a *private benefit*).
- **Donor:** someone who gives money and takes no reward. He cares only that the project succeeds (a *public-minded* motive). In the model, his *valuation* *w* is the most he would ever give. Buyers cannot see it.
- **Outside option (v0):** what a buyer gets by not pledging, for example spending the money elsewhere. Pledging to a campaign that fails wastes this option. That is the buyer's *opportunity cost*.
- **Coordination problem:** each buyer is happy to pledge only if enough others also pledge. Each one is unsure what the others will do, so too few pledge.
- **Free riding:** letting others pay for something you benefit from. The model is built so free riding is not the issue. The issue is coordination.
- **Signal / costly signal:** an action that shows hidden information because it costs something. Here the donor's money is the signal: a real gift makes it believable that he has more budget behind it.
- **Equilibrium (Perfect Bayesian Equilibrium):** a situation where everyone's strategy is their best response to the others' strategies. "Bayesian" means buyers update their beliefs about the donor's budget logically (using Bayes' rule) from what they observe.
- **Pooling-threshold (PT) equilibrium:** every donor with enough budget gives *just* enough to keep total donations above a cutoff (the "threshold"). From outside, rich and poor donors look identical ("pool") until a poorer donor runs out of money.
- **Success-maximizing / success-minimizing equilibrium:** the model has many possible equilibria. These two are the best case and the worst case for the chance of reaching the goal. The worst case is the same as if everyone knew the donor's budget, so no signaling happens.
- **Calibration:** choosing the model's unknown numbers (here, buyer utility *v*) so the model's predictions match the data (here, the share of campaigns that succeed).
- **Counterfactual:** a simulation of a world that did not happen. Example: "What if donors could give only on day one?"
- **Selection (Heckman) correction:** a fix for the fact that some things are observed only for a non-random subset of the data. Here a donor's full budget is seen only when a campaign *fails*, because he gave everything he had.
- **Fixed effect:** a separate intercept (baseline level) for each group, here each campaign category. It soaks up everything constant within that group.
- **Standard error (SE):** how uncertain an estimate is. A rough rule: an estimate more than about 2 SEs away from zero is "statistically significant".

## 3. Data

- **Source:** Kickstarter's public campaign pages. The authors built a *panel* (the same units tracked over time) by recording **every campaign launched March 2017 - September 2018, every 12 hours, from launch to deadline**. The paper calls this scraping/tracking, and the 12-hour frequency is described as "a novel aspect".
- **Key feature:** the data separate **pledges for rewards** from **donations** (money given with no reward). Construction details are in online Appendix D, which is *not* in this PDF. Footnote 7: if one person both buys a reward *and* adds extra money, the authors cannot see that without data on individual backers.
- **Size:** 42,462 campaigns: 24,624 unsuccessful and 17,838 successful. The arrival-model estimation uses 845,643 campaign-period observations, and the donor-valuation estimation uses 13,863 campaigns.
- **Restrictions:** Table 2 and Figure 4 use only 30-day campaigns. The calibration also uses only 30-day campaigns, and only the **first quartile (smallest 25%) of goal amounts** within each category, because solving the model is computationally hard when G/p is large.
- **Robustness:** the authors run 12 sets of robustness checks (online appendix). One example treats cheap "rewards" such as a thank-you card or meeting the creator as donations.
- **Cleaning I could *not* find in the main text:** the 30 pages here do not discuss cancelled or withdrawn pledges, or irregular scrape timing (missed or late snapshots). Those details, if covered, would be in online Appendix D. Do not quote numbers on them from this paper.

## 4. Main empirical facts (Table 1, Table 2, Figures 3-4, Section IV.C)

- **Table 1 (all / unsuccessful / successful means):** campaign length 33.1 / 34.7 / 30.7 days (median 30). Goal $16,366.5 / $21,982.5 / $8,613.9 (median $5,113.6). Donor revenue per 12 hours $19.1 / $3.3 / $43.7. Buyer revenue per 12 hours $119.5 / $14.0 / $283.8. Average share of each campaign's revenue from donations 29.2% / 33.1% / 24.6% (median 15.8%).
- **42%** of campaigns succeed. Bigger goals go with longer deadlines (correlation 0.14). Donations are **14% of total revenue** in aggregate.
- **Figure 3:** final revenue/goal bunches at **0** and at **1**: campaigns either get almost nothing or just barely make it. Success times are **bimodal**: many campaigns succeed near the start or near the deadline.
- **After success:** donations drop **72%** within 3 days, while buyer pledges drop only **37%**. This matches the model: donors care only about success, while buyers still want rewards.
- **Table 2 (medians, successful 30-day campaigns) for early (goal reached within 3 days) / middle / late (last 3 days) finishers:** goal $2,000 / $3,510 / $5,254. Average price $90.6 / $118.7 / $171.5. Revenue/goal 3.1 / 1.2 / 1.0. **Donations as a share of revenue 4.8% / 14.7% / 34.3%**. Number of campaigns 1,437 / 3,470 / 2,616.
- **Figure 4:** all campaigns get a burst of purchases at launch. Donations spike only for late finishers, right at the deadline.
- **Tests of the model's predictions (Proposition 5):** (i) **78%** of deadline-successes would have failed without last-minute donations. (ii) The median share of revenue from buyers in the period of success is **91%**. (iii) Donations are negatively associated with how far the campaign has progressed toward its goal (Table D2, online only). (iv) Failed campaigns with more donations fail later: correlation **0.15, t = 10.1**. (v) Only **29%** of campaigns have an average donation of at least the average reward price. That is evidence *against* the no-signaling (success-minimizing) equilibrium.

## 5. The model in plain words

Buyers show up at random times. Each one decides once, on the spot: pledge *p* for a reward, or take the outside option. A buyer pledges only if she thinks the campaign is likely enough to succeed. Precisely: the chance of success times her gain (v - p) must be at least v0. One long-lived donor has a secret budget *w* and can add money at any moment.

Why do donations matter? Buyers look at how much has been donated so far and infer that the donor probably has *at least* that much budget and will keep backing the project. So an early donation makes the next buyer optimistic enough to pledge. After a buyer pledges, the project is closer to its goal, so the donor can **hold back**. The threshold he must keep donations above goes down after a pledge. When no one pledges for a while, it goes up. So the donor gives in steps: a "seed money" push at launch, then pauses, then top-ups when things stall, and often a big final push before the deadline. Giving too little kills the campaign for good, because buyers conclude the donor is out of money. Giving too much wastes funds. Revealing *w* openly would produce the *lowest* success probability.

Who prefers what: the donor likes the success-maximizing equilibrium best. Buyers prefer something in between, because in the success-maximizing equilibrium they sometimes pledge to campaigns whose donor is nearly out of money. Policy analogy: a government supporting a new industry, or a large firm attracting suppliers, does better with incremental support than with one big push at the start.

## 6. Key estimation tables (appendix)

These are maximum-likelihood models with a selection correction. Standard errors come from 1,000 bootstrap samples (re-estimating on resampled data). Category coefficients are measured relative to an omitted category, presumably Art, which has no row. **None of these is a causal effect.** Each describes how the fitted donor budgets or arrival rates differ across observable campaign features.

**Table A1: donor valuation, log(w) (13,863 obs., 37 parameters).** Because the outcome is in logs, a coefficient *b* means roughly a 100·b% difference (exactly e^b - 1).
- **log(G) 0.324 (0.004):** a campaign with a 1% bigger goal has a donor budget about 0.32% bigger (this is an *elasticity*, a %-for-% relationship). Highly significant. Bigger projects attract bigger donors. Association, not causation.
- **Love 1.432 (0.050):** campaigns marked "loved" by Kickstarter have much higher donor budgets, e^1.432 ≈ 4.2 times as large. Significant. This could reflect quality that the platform picks out, so it is not a causal effect of the badge.
- **Theater 0.997 (0.072), Dance 0.841 (0.083), Design 0.704 (0.028), Comics 0.603 (0.037):** these categories have larger donor budgets than the omitted category. All significant.
- **Fashion 0.029 (0.025), Crafts 0.047 (0.031), Journalism -0.036 (0.057):** small and within about 1.5 SEs of zero. **Not significant**: no detectable difference from the base category.
- **μ (correlation) 0.708 (0.005):** the unobserved factors that drive "being in the observed sample" and "donor budget" are strongly positively correlated. That is why the selection correction matters. Ignoring it would bias the budget estimates, and correcting shifts the fitted distribution to the right (Figure 5A).
- **Selection equation: log(B) -0.993 (0.016), log(G) 0.952 (0.016).** The budget is observed only for *failed* campaigns. More pledges → less likely to fail. A bigger goal → more likely to fail. log(B), total pledges, is the "excluded variable": it is assumed to affect selection but not the donor's budget. That assumption is a key identifying assumption.

**Table A2: buyer arrivals (Poisson model with selection; 845,643 obs., 41 parameters).** Coefficients are on the log of the expected number of arrivals per period.
- **log(G) 0.730 (0.001):** a 1% bigger goal goes with about 0.73% more buyer arrivals. Significant. This is a correlation, since bigger projects draw more traffic.
- **Love 0.295 (0.001):** "loved" campaigns get about 34% more arrivals (e^0.295 - 1). Significant, not causal.
- **Time-linear -0.190, time-quadratic 0.007 (SEs 0.000):** arrivals fall over the campaign and then rise again near the end. This is the U-shape seen in Figure 4.
- **Selection: log(D) 9.474 (0.014):** more cumulative donations relative to the goal strongly raise the chance that arrivals are observed. Donations are the excluded variable here, assumed to shift success but not arrivals directly.
- **ρ -0.016 (0.001):** almost no correlation between the unobservables, so selection matters little here.

**Table A3: buyer utility calibration.** The model matches each category's success rate. For example, Art data 0.215 vs model 0.217, and Fashion 0.138 vs 0.138. But it misses some categories: Theater 0.422 vs 0.088, Food 0.185 vs 0.023. The authors say they understate the variance of donations for Theater.

## 7. Counterfactual results (Table 3, Figure 7)

Probability of success (%) under four regimes: success-maximizing (the model as estimated) / success-minimizing (no signaling) / donate only at the beginning / donate only at the end.

| Category | Max | Min | Start only | End only |
|---|---|---|---|---|
| Art | 21.8 | 0.4 | 0.3 | 0.0 |
| Comics | 32.0 | 1.1 | 1.0 | 31.2 |
| Crafts | 14.4 | 13.3 | 12.5 | 8.9 |
| Film/video | 28.7 | 6.8 | 6.4 | 0.0 |
| Music | 29.5 | 0.9 | 0.8 | 0.0 |
| Publishing | 19.9 | 0.5 | 0.5 | 0.0 |
| Technology | 8.3 | 0.0 | 0.0 | 0.0 |
| Theater | 8.8 | 4.2 | 2.9 | 3.2 |

(Other categories are in Table 3.) On average the gap between maximum and minimum is **13 percentage points**, or about **16% vs 3%** per the introduction. Restricting *when* the donor can give does even worse than no signaling. **Figure 7 (Publishing):** with one up-front donation the donor gives *more* at the start (up to about $170, versus about $70 in the success-maximizing equilibrium), but success is still lower. Incremental support beats one big push.

## 8. Limitations and threats

- **Selection:** the donor's budget is seen only for failed campaigns, and arrivals only for successful ones. The fix (Heckman / Terza) depends on assumed bivariate normal errors and on exclusion restrictions (pledges do not affect donor budgets; donations do not affect arrivals directly). If those assumptions are wrong, the estimates are biased.
- **Equilibrium assumption:** the calibration *assumes* every campaign plays the success-maximizing equilibrium. The counterfactual gaps inherit that assumption.
- **Model fit:** poor fit for some categories (Theater, Food). The calibration covers only 30-day, small-goal campaigns, so results may not generalize.
- **Measurement:** donations are inferred at the campaign level. The authors cannot see a person who both buys and donates (footnote 7), and robustness checks reclassify cheap rewards. A 12-hour snapshot blurs the exact order of pledges and donations within a window. Any missed or late scrape (my inference, not discussed in the main text) would add timing error.
- **Endogeneity / confounding:** Kickstarter promotes campaigns near their deadline (footnote 13), which may itself drive last-minute money. "Loved" status and goal size are chosen by people or the platform and are linked to unobserved quality.
- **Single representative donor:** the model ignores free riding among several donors and social learning about quality. The extensions show these can weaken signaling.

## 9. Quiz angle

- **Scraping as data collection:** the core data are snapshots of public web pages, taken on a fixed 12-hour schedule. The new variable (donation vs pledge) comes from how the pages were parsed.
- **Panel at fixed intervals:** campaign × 12-hour period. Gaps or late snapshots would need handling, for example carrying the last known cumulative value forward. That is valid because cumulative totals only change when contributions arrive, though it shifts *when* the change is recorded.
- **Measurement error:** the 12-hour sampling interval blurs timing, and so does misclassifying rewards as donations. Error in an explanatory variable usually pulls estimates toward zero (attenuation bias).
- **Endogeneity / omitted-variable bias (OVB):** project quality, unobserved by the researcher, raises both donations and buyer arrivals. So "donations → success" in raw data is not causal. The authors use a structural model rather than a regression to make claims about mechanisms.
- **Fixed effects:** category fixed effects in Tables A1 and A2 compare campaigns within the same category.
- **Interpreting coefficients:** logs give percentages or elasticities. Check the sign, the size, and whether the estimate is more than 2 SEs from zero. Category dummies are relative to the omitted category.
- **Correlation vs causation:** the corr = 0.15 between donations and failure time, and the 72% drop in donations after success, are descriptive patterns consistent with the model, not experiments.
- **Workflow critique:** online appendices hold the sample construction details. Replication data and code are on Yale Dataverse. Note the restriction to 30-day, small-goal campaigns for computational reasons.

**Practice T/F/U**

1. *"Because successful campaigns receive more donations per 12 hours ($43.7 vs $3.3), donations cause campaign success."* **False/Uncertain.** That is a correlation. Quality and popularity drive both, and success itself attracts deadline top-ups (reverse causality). The paper's causal claims come from the model's counterfactuals, not this comparison.
2. *"Requiring donors to give their entire contribution at launch would raise success rates, since early money boosts buyer confidence."* **False (per the paper).** In Table 3, success with donations only at the start is at or below the no-signaling level in every category, for example Art 0.3% vs 21.8% when the donor gives over time. Figure 7 shows larger initial gifts but lower success.
3. *"Estimating donor budgets only from failed campaigns, where the donor gave everything, without a correction would understate typical donor budgets."* **True (most likely).** Failed campaigns are not a random sample: their donors were the ones who ran out. The estimated correlation μ = 0.708 shows selection matters, and correcting moves the fitted distribution to the right (Figure 5A).
