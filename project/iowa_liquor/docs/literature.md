# Literature notes

## Seim & Waldfogel: "Public Monopoly and Economic Efficiency: Evidence from the Pennsylvania Liquor Control Board's Entry Decisions"
Katja Seim (now at Yale) and Joel Waldfogel.
- **Working paper:** NBER WP 16258 (2010), which we were given.
- **Published:** *American Economic Review* 103(2): 831–862 (2013).
- **The conclusions differ between versions. Cite the published one:**

> "In the absence of the Pennsylvania Liquor Control Board, the state would have roughly 2.5 times the current number of
> stores, higher consumer surplus, and lower payments to liquor store employees. With just over half the number of stores
> that would maximize welfare, the government system is instead best rationalized as profit maximization with profit
> sharing." (AER 2013 abstract)

- **Store counts:**
  - Actual network: 621 stores.
  - Welfare-maximizing: 1,124 at competitive store costs; 566 at the PLCB's own (higher) costs.
  - Profit-maximizing: about 473–492.
  - Free entry: 1,290.
- **The actual network matches** maximizing profit + 0.18 × consumer surplus (competitive costs), or about profit + 1.17 × CS (at PLCB costs).
- **Structural price elasticity −1.2 to −1.5**, about the same as the working paper. Travel cost about $0.61 per km driven.
- The working-paper notes below describe the 2010 framing (the network "looks welfare-maximizing"). The published version revises that conclusion.

**Question.** Pennsylvania's liquor control board (PLCB) is a state monopoly that runs about 620 liquor stores. Does it choose the number and location of stores to maximize **profit** or **welfare** (consumer + producer surplus)?

**Institutions** (relevant to Iowa):
- Pennsylvania is the largest of **18 "control" states**. Pennsylvania is a monopolist at both wholesale and retail. **Iowa controls only wholesale**: since privatization, private licensed stores ("Class E") do the retailing.
- **Prices are set by a markup rule and are identical at every store:** retail = (wholesale × 1.3 + bottle fee) × 1.18 tax, rounded to end in 9.
- **Iowa's rule is simpler:** the state price to stores = 1.5 × the supplier's price. Iowa Code §123.24(2): (a) the manufacturer's price; (b) "a markup of up to fifty percent", which may be higher on selected kinds if the average return stays within 50%; (c) a split-case charge; (d) a bottle surcharge to cover container disposal. We confirm 1.5× for 99.9% of items in the current price list.
- **Iowa HF 830 (2025)**, introduced Mar 7, 2025 and never out of committee, would add a **minimum unit price**: "fifty cents per eighteen milliliters of alcohol in the package". The 50% markup would then apply to the greater of the manufacturer's price and that floor. Source: https://www.legis.iowa.gov/docs/publications/LGI/91/HF830.pdf. **This is our main policy counterfactual.**
- **How Pennsylvania's prices change:** wholesale costs are renegotiated quarterly by product category, in 4-week reporting periods. Temporary sales run in 28-day periods. So prices change in discrete steps, at most twice a month.

**Data.** 2005 daily store × product sales from a Right-to-Know request, plus wholesale costs, 2000 Census tracts and store locations.

**Price endogeneity.** Prices only vary over time (uniform statewide). Their fixes:
1. Use the **list price** (excluding temporary sales, which may be timed to demand).
2. Add **holiday-week dummies** (Thanksgiving, the Christmas–New Year's window, July 4).
3. Use **only the days right before and after a price change** (a regression-discontinuity-in-time idea).
- They find an **elasticity of about −1 (range −0.6 to −1.9)**, in line with the literature: spirits about −1.5 (Leung & Phelps 1993, via Chaloupka et al.).

**Model.**
- Each consumer buys from the nearest store. Utility = Xβ − β_d·distance − β_p·price + logit error (buy vs not buy), with Census tracts as locations, adults 21+ as potential consumers, and one bottle per shopping occasion.
- Estimated by maximum likelihood (a binomial logit on store-day sales).
- **Elasticity −1.18 to −1.28; travel cost about $0.40 per km.**
- **Consumer surplus** = log(1 + e^V)/β_p, the logsum formula from class 18. **Producer surplus** = (p − c)·Q.

**Results.**
- The welfare-maximizing network has **about twice as many stores** as the profit-maximizing one, and the actual network looks like the welfare-maximizing one.
- Free entry would produce too many stores, clustered in high-demand areas: losses of 3–9% of revenue at a fixed store count.

**What we borrow for Iowa:**
- **The question template:** compare the state's actual policy (a 50% markup) with the profit-maximizing and welfare-maximizing benchmarks implied by estimated demand. Their lever is store entry; **ours is the markup** (the statute allows category-specific markups as long as the average stays ≤ 50%).
- **Endogeneity handling for uniform statewide prices:** time-only price variation, holiday controls, and the window right around each price change. We add **tariff shocks** as an excluded cost shifter.
- **Welfare accounting:** logsum consumer surplus plus the state's margin. Iowa's margin per bottle = p − p/1.5 = p/3.

## Course materials we build on (repo `notes/`)
| Topic | File | What we use |
|---|---|---|
| Logit, Berry inversion, elasticities, consumer surplus, IIA | `class18-slides.md` | Share inversion, logsum CS, elasticity formulas |
| Nested logit, BLP instruments, profit counterfactuals | `class19-slides.md` | Nests = spirit types; σ; within-nest share instrument; profit = (p − c)·N·s |
| Zappos lab: market/product definitions, zeros, market size, MLE vs Berry vs paper spec | `class20-zappos-lab-2026-11-17.md` | **Template:** uniform national prices → time-only variation, product fixed effects, steady sellers, rival-characteristic instruments, brand demeaning, no market fixed effects, GMM |
| IV / 2SLS, weak instruments, exclusion | `class15-slides.md` | Tariff as a cost-side instrument; check the first stage, argue exclusion |
| Difference-in-differences, event study, synthetic control | `class14-slides.md` | Tariff pass-through and quantity response; treated vs untreated categories |
| Product variety / across-market demand (Quan & Williams) | `class12-reading-notes-product-variety.md` | Zeros and sparse local shares at county level |
| Merges, big data, DuckDB | `class7-slides.md` | Print shapes before/after every merge; DuckDB for 20M rows |

## External benchmark: Scotland's minimum unit price (verified Nov 27, 2026)
- **Policy:** Scotland set a minimum retail price of 50p per UK unit (10 ml of pure alcohol) from May 2018. It was raised to 65p in Sep 2024.
- **Evaluation:** Public Health Scotland's final evaluation (June 27, 2023) estimates that MUP **cut population alcohol sales by about 3%**. The largest falls were in the products whose prices rose most. It also estimates a **13.4% fall in deaths wholly caused by alcohol**, and finds no consistent effect on the drinks industry as a whole. All of these are modelled estimates.
- **Use in our project:** this is an out-of-sample check on the low end of our HF 830 fan. We simulate −1.8% to −10.7% pure alcohol at elasticity −0.63, and a 3% fall sits near the low end. Note that Scotland's floor is a *retail* floor of about £0.90 per 18 ml. HF 830's floor applies to the *supplier* price before Iowa's 50% markup. The levels are not directly comparable, only the order of magnitude.
- **Sources:**
  - [PHS evidence synthesis](https://publichealthscotland.scot/publications/evaluating-the-impact-of-minimum-unit-pricing-for-alcohol-in-scotland-a-synthesis-of-the-evidence/)
  - [Scottish Government report to Parliament, 2018–2023](https://www.gov.scot/publications/alcohol-minimum-pricing-scotland-act-2012-report-operation-effect-minimum-pricing-provisions-2018-2023/pages/1/)
