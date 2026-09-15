# Class 4 reading — Bodéré, "Dynamic Spatial Competition in Early Education"
**Assigned per syllabus: introduction + data section only** (the full paper runs to a structural
dynamic-game model and counterfactual policy simulations — out of scope for this reading, and not
summarized here). This is the source of the preschool dataset used in [class4-slides.md](class4-slides.md).

## What the paper is about
Pierre Bodéré (Yale SOM), working paper dated Aug 5, 2026. Studies the Pennsylvania preschool
(early childhood education, "ECE") market: prices, quality, and provider entry/exit/investment
decisions, and how two kinds of state policy affect access — income-based subsidies for parents,
and quality-tiered reimbursements for providers. Builds and estimates a dynamic equilibrium model,
then simulates what happens if PA broadened subsidy eligibility or made quality reimbursements
more generous.

## Motivation (Introduction)
- Early childhood education has well-documented long-run benefits, especially for disadvantaged
  kids, but U.S. provision is mostly private (>80% of center-based programs), unlike K-12.
- That creates a real tension: high costs for providers, high prices and inconsistent quality for
  parents, and low enrollment as a result — the U.S. ranks 41st/43rd among OECD countries for
  3-/4-year-old preschool enrollment.
- States respond with income-based subsidies (help parents pay) and quality-tiered reimbursements
  (pay providers more for serving low-income kids at high quality) — but there's been little
  empirical evidence on how these actually play out: how fast supply responds, and who wins/loses.

## Four descriptive facts the paper documents (this is the "data section" payoff)
1. **Access is unequally distributed geographically** — neighborhoods with more college-educated
   women have more nearby centers, especially high-quality (STAR 4) ones.
2. **Provider dynamics reinforce that inequality** — centers in poor neighborhoods exit the market
   at a much higher rate, and upgrade to the top quality tier far less often, than centers in rich
   neighborhoods (e.g. of STAR-1 centers as of 2010: ~60% exited by 2018 in the poorest tracts vs.
   <30% in the richest).
3. **Quality upgrades raise both enrollment and prices** — and price increases after an upgrade are
   larger in higher-income/more-educated neighborhoods, i.e. providers price to local willingness
   to pay.
4. **Providers respond to financial incentives** — an extra $100/day in subsidy revenue at a center
   is associated with roughly a 3 percentage-point higher chance of upgrading to the top quality
   tier.

## Data sources
- **Main dataset**: Pennsylvania's Keystone STARS quality-rating system, provider-level, 2010–2018
  (obtained via a Freedom of Information Act request). Includes prices by age group, enrollment by
  age/subsidy status, STAR ratings (1–4 scale), capacity, ownership/for-profit status, and the
  policy schedule itself (subsidy income thresholds, copayment schedules, add-on reimbursement
  rates) for each year.
- **One real limitation flagged explicitly**: STAR 1 (lowest-rated) providers aren't required to
  report enrollment, since they're not eligible for the supply-side incentives — same missing-data
  pattern the slide deck highlighted today (missingness tied to *why* it's missing, not random).
- **American Community Survey (ACS)**: block-group-level demographics (population by age, gender,
  income, education) for the demand side, imputed from tract level where block-group data is
  unavailable.
- **National Survey of Early Care and Education (NSECE)**: nationally representative survey used to
  supplement the PA data with individual-level detail (distance traveled, costs) that the
  provider-level data doesn't capture directly.

## Descriptive stats worth remembering (2018 sample, from Table 1)
- 3,929 centers total; the market skews low-quality — 2,025 are STAR 1, vs. only 756 at STAR 4.
- Price rises with quality: $35.00/day (STAR 1) → $40.25/day (STAR 4), 2015 dollars.
- Capacity rises with quality too: 71 kids (STAR 1) → 123 kids (STAR 4) licensed capacity.
- Accreditation is rare and concentrated at the top: 3% of STAR 1 centers are accredited vs. 35%
  of STAR 4 centers.

## Why this matters for today's class exercise
The preschool dataset in class today (`data_preschools.csv`, `data_blockgroup_2010_2018.csv`) is
this paper's actual data. The missing-data and outlier examples in the slide deck (enrollment
missing for STAR 1, prices missing in early years, price/enrollment winsorizing) are the real
data-cleaning steps behind this research, not toy examples.
