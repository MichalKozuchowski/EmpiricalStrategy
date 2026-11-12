# Reading notes: "The Value of Personalized Recommendations: Evidence from Netflix"

Zielnicki, Aridor, Bibaut, Tran, Chou & Kallus (June 2026, arXiv). Posted with the Session 18 logit-demand materials.
- Most authors work at Netflix; Aridor is at Kellogg.
- The re-posted slides, guide and data (Nov 12) are **identical** to the Nov 10 versions summarized in `class18-slides.md`.

## The question
How much of what people watch on Netflix comes from the **recommendation system (RecSys)**, and how much from what they'd have wanted anyway?
- This is hard because recommendations are **targeted**: Netflix recommends a show *because* it predicts you'll like it.
- So "recommended and watched" mixes the recommendation effect with your existing taste (selection).

## The model: the multinomial logit from class, at scale
- **Choice:** each user, each day, picks **one** title out of ~7,000, or **the outside option** (watch nothing that day).
- **Utility:** u_ijt = A_it · B_j + Σ_r β_jr · 1{j recommended in slot r} + ε_ijt, with ε ~ Type I extreme value (logit).
  - **B_j:** a title's "characteristics", **learned from viewing choices**, not genre or cast tags (which predict movie demand poorly).
  - **A_it:** the user's taste weights. These **come from their watch history**, summarized by a transformer-style attention model, so there's no separate parameter per user.
  - **β_jr:** a **recommendation "bonus"** to utility for appearing in the billboard, the top-25 or the top-100 tiles.
- **Choice probability:** exactly the class formula, P(j) = e^{V_j} / (1 + Σ_k e^{V_k}).
  - **"Engagement"** = 1 − P(outside option), i.e. the chance a user watches anything that day.
- **Estimation:** maximum likelihood by stochastic gradient descent in PyTorch on GPUs.
  - ~2 million US users over 35 days (Feb 18–Mar 25, 2025).
- **The link to class:** the same logit/softmax engine as the streaming example and LLM next-token prediction.
  - Here there's **no price variation** (subscribers watch for free), so recommendations play the role price usually plays.

## Identification (the endogeneity problem in this setting)
- **Exposure is endogenous:** it's targeted at people likely to watch anyway, the same idea as price responding to ξ.
- **Their fix:** condition on everything the RecSys itself sees (user, title and state features). The leftover variation in what gets shown comes from the RecSys's **random exploration**, and is treated as **conditionally exogenous**.
- **Validation with a real randomized experiment:**
  - 8 arms of ~1M users each, for 5 weeks. Each arm **boosts** one category of titles in recommendations and **dilutes** the others.
  - That gives **model-free diversion ratios**: when a title is shown less, where do its viewers go? (Wald estimator, as in Conlon & Mortimer.)
  - **The model's predicted diversion vs the experiment:** correlation **0.86**, R² **0.73**, out of sample.
  - In-sample title shares fit with R² = 0.99.

## Findings
| Replace today's RecSys with… | Engagement | HHI (concentration) |
|---|---|---|
| Random recommendations | **−16%** | −2.5% |
| Popularity-based (same top titles for everyone) | **−12%** | **+42.5%** |
| Matrix factorization (Netflix's ~2015 method) | **−4%** | **+37.5%** |

- **Today's RecSys gives both more engagement and more diversity.** The older methods concentrate viewing on fewer titles.
- **Breaking down why recommended titles get watched more:**

  | Selection (would have watched anyway) | Targeting (shown to the *right* people) | Exposure (shown to anyone) |
  |---|---|---|
  | **51.3%** | **41.9%** | **6.8%** |

  - Mechanical exposure alone still roughly **triples** a title's viewing probability for the average user.
  - **Targeting matters 7× more than exposure.** Under matrix factorization, the two are about equal.
- **Who benefits most from targeting:** **mid-popularity titles** with a sizeable but specific audience. Not blockbusters, and not very niche titles.
- **Value of a title:** the model can simulate removing a title to get its **incremental engagement**, i.e. demand net of the recommendation boost. That's useful for catalog and licensing decisions.
  - An extension uses pre-release embeddings so it can also handle **new** titles.

## Limitations the authors flag
- The recommendation bonus is the **same for every user**: an approximation of consideration-set effects, not a fully personalized response.
- It's a **reduced-form** effect of recommendations, so they **don't make consumer-welfare claims**. Engagement is a proxy for retention and firm value.
- One title per user per day, chosen at random if they watched several.
- **Conflict of interest:** written by Netflix employees with a financial stake.

## Connections to class 18
- **Logit with an outside option:** "watch nothing today" plays the role of "no paid service". It must stay in the denominator.
- **Unobserved appeal and endogeneity:** targeted exposure is like price responding to ξ. Here the fix is exogenous variation (exploration plus an experiment) instead of a cost instrument.
- **Substitution patterns:** diversion ratios are the empirical version of the "where do lost accounts go?" slides.
  - Plain logit's IIA would be too restrictive here. The learned embeddings A·B let similar titles substitute more closely, which addresses the red bus / blue bus problem.
- **Softmax and transformers:** the same machinery as the LLM slide (Vaswani et al. 2017).
