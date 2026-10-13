# Class 12 Reading Notes: Quan & Williams (2018)

**"Product Variety, Across-Market Demand Heterogeneity, and the Value of Online Retail"**, *RAND Journal of Economics* 49(4), pp. 877-913. Thomas W. Quan (Univ. of Georgia) and Kevin R. Williams (Yale, our professor).

---

## 1. One-paragraph summary

**Question:** How much do consumers gain from the huge selection of products available online? An earlier, well-known study (Brynjolfsson, Hu & Smith 2003, about Amazon books) found the gain from more variety was 7 to 10 times bigger than the gain from lower online prices. Quan & Williams argue that this overstates the gain, because local stores already stock what local people want: Floridians don't need 5,000 extra kinds of winter boots. **Data:** more than 13.5 million shoe sales (over $1 billion) from a large online retailer in 2012-2013, with the buyer's zip code, price, reviews, and daily inventory. They add a snapshot of which shoes are in stock at Macy's and Payless stores. **Method:** a demand model (nested logit, explained below) that lets each product's popularity differ randomly from place to place. A new trick deals with the fact that most products sell zero units in most places. **Findings:** tastes differ a lot across places. Once that is accounted for, the gain from online variety is **$37.1 million (5.8%)** instead of $65.1 million (10.6%), which is **about 45% lower**. Ignoring local tastes overstates the gain by about 75%. A 5% online price cut would deliver slightly more than half of the total gain, so variety and price matter about equally.

---

## 2. Key vocabulary (plain English)

- **Product variety:** how many different products a consumer can choose from. Here, a "product" is a shoe model in a specific color (a SKU, or stock-keeping unit).
- **Long tail:** a sales pattern where a few hits sell a lot and a very large number of niche products each sell a little. Together, the niche products add up. "Long tail" is Anderson's (2004) name for the idea that online stores make money (and create value) from this tail.
- **Demand heterogeneity across markets:** people in different places want different things. Boots sell in cold states and sandals in warm ones; one brand is far more popular in the Northeast.
- **Market:** the place and time where a choice is made. The main analysis uses one of 213 areas (165 CSAs, which are metro-area clusters, plus the rest of each of 48 states) in a given month.
- **Market share:** the fraction of potential buyers in a market who bought a given product.
- **Discrete choice / logit:** a model in which each person picks exactly one option (one shoe, or "buy nothing") that gives them the highest satisfaction, called "utility." The logit version adds a random personal-taste term with a particular statistical shape. That gives simple formulas for the probability that each option is chosen.
- **Outside good:** the option "buy none of these shoes."
- **Nested logit:** a logit model where products are grouped into "nests," which here are categories like sneakers or boots. People are more likely to switch between products in the same nest. The **nesting parameter λ** (between 0 and 1) measures how strong that within-category substitution is. At 0 the model becomes plain logit.
- **Random coefficients / random effects:** letting a parameter vary randomly across people or places instead of being one fixed number. Here every product gets a random local "taste shock" (η) in each market. Its spread is σ (sigma). A big σ means the product is loved in some places and ignored in others.
- **Fixed effects:** a separate intercept (a dummy variable) for each group, such as each brand, color, category, or month. It absorbs anything constant within that group.
- **Endogeneity:** an explanatory variable is tangled up with the unobserved error term, so its coefficient is biased. Price is endogenous because firms charge more for shoes with high unobserved quality, which is also what makes people buy them. That makes price look less harmful to demand than it really is.
- **Instrumental variables (IV):** variables that move price (or another endogenous variable) but are unrelated to unobserved quality. They let you isolate the true effect of price.
- **Price elasticity:** the % change in quantity sold when price rises 1%. An elasticity of -3 means a 1% price increase cuts sales by 3%.
- **Consumer surplus / welfare:** the value consumers get above what they pay, measured in dollars. "Welfare gain" here means the increase in consumer surplus.
- **Counterfactual:** a simulated "what if" world. Here it is a world without online retail, where people can only buy what local stores would stock.
- **Value of online retail:** the extra consumer surplus (and retail revenue) from the full online selection plus any lower prices, compared with the counterfactual offline world.
- **GMM / micro moments:** GMM (generalized method of moments) picks parameters so that model predictions match chosen features of the data. A "micro moment" is one such feature. Here it is the fraction of local markets where a product had zero sales.

---

## 3. Data

- **Source:** point-of-sale (POS) records from a large online retailer, collected with the retailer's permission. The paper does not name the retailer.
- **Time period:** 2012-2013. Over $1 billion of shoe sales.
- **Unit of observation:** a transaction. It records a timestamp, the 5-digit shipping zip code, the price paid, and the shoe model and style. A transaction ID shows multi-pair orders. There is no other customer information.
- **Size:** over 13.5 million shoe transactions, about two-thirds of them women's shoes. Over 580,000 reviews, with ratings (1-5) for comfort, look, and overall appeal; these are heavily skewed toward favorable ratings. Daily inventory for every shoe: the average daily assortment is over 50,000 products, and over 100,000 varieties were offered at some point. Shoe photos are image-processed to create color variables.
- **Merges:** sales are merged with reviews (ratings change over time, so they reflect what the buyer saw on the day of purchase) and inventory (which shows the full choice set, including shoes that never sold). Market size (N) is the male or female population from the American Community Survey, with zip codes mapped to CSAs. Each person is assumed to make one shoe decision per month.
- **Brick-and-mortar data:** a snapshot from August-September 2014 of in-store availability, checked size by size through "check in store" queries. It covers **649 Macy's stores** (13,914 styles, 42.1% online-only, average store assortment 871.7) and **3,141 Payless stores** (1,430 styles, 19.2% online-only, average 513.0). It **cannot be merged** with the online data because the dates and product IDs differ.
- **Sample restrictions:** adult shoes only. Men's and women's demand are estimated separately, with average choice sets of about 13,250 and 27,500 products. Data are at the monthly level. The number of product-market observations is 1.8 to 3.9 million. Brand fixed effects are used only for brands averaging at least 50 sales a month, with small brands grouped together: 213 brand effects for men, 331 for women. Few orders include multiple pairs, and of those, fewer than a quarter contain the same shoe twice, so resellers are not a concern.

---

## 4. Main empirical facts

- **Stores localize their stock.** Most Macy's shoes are carried in only a few stores, while Payless's distribution has two peaks: many shoes are in only a few stores, others are in all of them. The share of products two stores have in common (overlap) **falls with distance between them**. Macy's carries more sandals (up to 10% of the local assortment) in warm places and more boots (up to 4%) in cold places. The average Macy's stocks fewer than half of the 160 brands.
- **Local top sellers ≠ national top sellers (Table 2).** At the CSA+state-month level, a market's own top 500 products earn **67.05%** of its revenue, but those same 500 products earn only **7.19%** of national revenue. At the 5-digit zip level the numbers are 99.96% vs 4.69%. Tests of "local shares = national shares" are rejected in 40-94% of markets, depending on how a market is defined.
- **Boots vs sandals:** boots take a larger share of revenue in colder states and sandals in warmer ones (Figure 3). People in Florida and Hawaii buy *more* sandals online, so they are not just shopping online for things local stores lack.
- **A popular brand** has under 2.5% of sales in Florida but over 6% in parts of NY, NJ, and MA (Figure 4).
- **The zeros problem (Table 3):** at the zip-code-month level, **99.96%** of products have zero sales. Even at the state-month level it is **85.25%**, and at the CSA+state-month level it is 95.54%. Grouping products into brands still leaves 59.27% zeros (Table 4).
- **Long tail comes from adding markets together (Figure 6):** in the median market, fewer than 2,000 products make up all local sales (a short tail). The national curve has a long tail.

---

## 5. The model in plain words

Each consumer in a market chooses one shoe or no shoe. A shoe's appeal depends on its ratings, brand, color, category, and price, plus unobserved quality. The key addition is that **unobserved quality = a national average part (ξ) + a local deviation (η)**. The local part is drawn from a normal (bell-curve) distribution with spread σ, which differs by category. Boots and sandals get separate summer and winter values.

**Why zeros matter.** Standard methods (Berry 1994) compute demand from the log of each product's local market share, and the log of zero is undefined. The common fixes both fail:
- **Dropping zeros** acts as if nobody in that place wants the product. Prices then look less important to consumers than they really are, and tastes look more different across places than they really are.
- **Adding a small number to every zero** treats every unsold product the same, as if the unsold boot in Alaska were the same as the unsold sandal in Alaska.

The authors instead add up demand to the national level, where shares are positive. That lets them recover each product's average appeal. They then choose σ so that the model reproduces the **share of markets with zero sales** for each product. A product with many total sales but many zero-sale markets must be a "local favorite," which implies a high σ.

**Why ignoring local tastes overstates the value of variety.** If tastes are the same everywhere, a local store's limited shelf misses much of what each person wants, so the full online catalog looks very valuable. If tastes differ by place and stores stock what local people like, consumers already had most of what they wanted, and the online catalog adds less. Logit models also tend to overvalue adding products, because each new product brings a new random personal-taste draw. The local random effects help limit that.

---

## 6. Key estimation tables

**Instruments.** Price and the within-category share (the nesting term) are both endogenous. The paper uses the usual "BLP-style" instruments: the number of available styles (color combinations) for a shoe model, and the **sum and average of characteristics of the same brand's other shoes in the same category**. These change a shoe's competitive position, and so its price, but are assumed unrelated to its own unobserved quality. Estimation is two-step GMM. All models include category, brand, and color fixed effects. Standard errors are robust.

**Reading the price coefficient.** Price is in dollars, so the coefficient is the change in mean utility per $1. Dividing another coefficient by the price coefficient turns it into dollars. For example, 0.210/0.016 ≈ $13 matches the paper's "$13" figure for men's summer boots.

**Table 5 (men), preferred column (4) Local RE:**
- Price **-0.016 (0.001)\*\*\***: higher price, lower demand. Significant, correct sign. Mean price elasticity **-3.333** (SD 2.508), so a 1% price increase cuts sales by about 3.3%.
- Overall rating **0.162 (0.008)\*\*\***: a one-point-higher overall rating raises appeal by about as much as a ~$10 price cut (0.162/0.016).
- Look **0.019 (0.010)\***: small and only weakly significant (10% level). Comfort **0.006 (0.008)**: not significant.
- No review **0.712 (0.049)\*\*\***: positive. The authors read this as extra promotion of new products, not a love of unreviewed shoes. It is a correlation, not a causal effect.
- λ **0.465 (0.005)\*\*\***: substantial substitution within a category.
- Compare: **Local NL Unadjusted (1)** price -0.007, elasticity only -0.876 (inelastic, which is implausible), caused by dropping the zeros. **Local NL Adjusted (2)** price **+0.001**, the wrong sign, meaning higher prices would raise demand. **National NL (3)** price -0.006, λ 0.814, elasticity -3.635.

**Table 6 (women), column (4) Local RE:** price **-0.012 (0.0004)\*\*\***, comfort 0.050\*\*\*, look 0.019\*\*\*, overall 0.148\*\*\*, no review 0.782\*\*\*, λ **0.281 (0.010)**, so women substitute less within a category than men. Mean elasticity **-2.129**. Unadjusted column (1): elasticity -0.592, λ -0.034 (outside 0-1). Adjusted column (2): price +0.003 (wrong sign). National NL: elasticity -3.055, λ 0.370.

**Table 7 (σ, across-market taste spread):** almost all are significant. Men: sneakers 0.544, boots-winter 0.511, sandals-summer 0.500, loafers 0.489, boots-summer 0.210. Men's clogs and men's winter sandals are not significant (SEs of 15.8 and 95.0). Women: 0.625 (clogs) to 0.878 (heels). In dollars, a one-SD local taste shock equals a price change of **$0-34 for men and $52-73 for women**, depending on category. Without local heterogeneity (σ=0), the model **under-predicts zeros**. An error of 0.5 percentage points corresponds to wrongly predicting sales in 65,934 men's and 85,622 women's product-market pairs that actually had none.

---

## 7. Counterfactual / welfare results

- **Setup:** "pre-Internet" choice set. Each market gets the products with the highest local appeal, with assortment size set from Macy's/Payless counts × the number of shoe stores in Census County Business Patterns, predicted from local population.
- **Table 8:** the **Local RE, tailored assortment** gain is **$37.1M (5.8%)** in consumer surplus: men $11.4M (6.9%), women $25.7M (5.4%). With a **national (one-size-fits-all) assortment** it is $65.1M (10.6%). Ignoring tailoring overstates the gain by **75.4% in dollars and 83.5% in percent**. National NL gives $174.0M (21.7%), about twice the Local RE national-assortment figure, which shows the logit overvaluation of new products. Local NL with unadjusted shares finds a gain of **0** (wrong). Revenue gain is $59.6M (7.4%) tailored vs $103.2M (13.6%) national. Tailoring raises local revenue by **5.8%**.
- **Table 9 (adding price cuts):** with a 1% price cut the total gain is $45.1M and prices account for 17.7% of it. At 5%: **$77.2M (12.8%), 51.9% from prices**. At 10%: $117.4M, 68.4% from prices. At 20%: $198.8M, 81.3% from prices. With a 10% cut, the variety-to-price gain ratio is **0.49:1**, compared with 7:1 to 10:1 for books in earlier work.
- **Robustness (Tables 10-11):** the percentage overstatement holds at 86-122% across assortment sizes of 3,000-24,000. A national store stocking 3,000 products could raise revenue by about **28%** by tailoring its assortment. With no local heterogeneity at all, the gains would be about 60% higher. With twice the estimated heterogeneity, they would be about 35% of the baseline.

---

## 8. Limitations and threats

- **No before/after variation:** they never see e-commerce arrive. The results come from comparing with a simulated no-online world (authors' own point).
- **One retailer:** competition and pricing of local stores are not modeled. Selection risk: online buyers may differ from store shoppers, for example people who shop online because their niche product isn't sold locally. The authors argue the online patterns (boots in cold states, brands common in stores) make this less worrying, but it cannot be formally tested.
- **No shoe sizes in the sales data:** this understates gains for people with unusual sizes.
- **No consumer search costs.** If online search is costlier than offline, the estimates are an upper bound. If the reverse is true, the gains are understated.
- **Assumptions:** stores know local tastes perfectly, and the brick-and-mortar assortment sizes come from a different year (2014) and only two chains. The normal-distribution assumption for local deviations and the category-level σ are further assumptions. The early inventory data were imputed, not tracked daily.
- **External validity:** the results apply to shoes. Other categories may have different levels of local heterogeneity.

---

## 9. Quiz angle

- **Big transaction data:** 13.5M POS rows, more than 50,000 products a day. The number of products can grow faster than the number of purchases, so observed shares are noisy and mostly zero.
- **Merging:** sales + reviews (time-varying) + inventory (choice set) + Census population (market size) + image-based color variables. Store data could not be merged because of different IDs and dates, which is a lesson about matching keys.
- **Long tail and outliers:** sales are highly concentrated locally. The national long tail is partly created by adding up many markets. Removing single-sale products shortens local tails but not the national one (Figure 11).
- **Choice of level:** how finely you define a market or product changes the results (Tables 2-4). Coarse aggregation hides heterogeneity, and fine aggregation produces zeros.
- **Fixed effects:** brand, color, category, and time dummies absorb average differences, so price is identified from variation within those groups.
- **Endogeneity/IV:** price is correlated with unobserved quality, and the authors instrument with other products' characteristics. Dropping zeros causes selection bias. A wrong-signed price coefficient is a warning sign.
- **Units:** coefficient / |price coefficient| = dollars. Elasticities are unit-free.
- **Correlation vs causation:** the positive "no review" coefficient probably reflects promotion of new products, not a causal effect of having no reviews.
- **External validity:** shoes, one retailer, 2012-13.

**Practice T/F/U**
1. *"Because online sales show a long tail, consumers must gain hugely from online variety."* **False/Uncertain.** The national long tail is mostly an artifact of adding up markets with different tastes. Local tails are short, and accounting for this cuts the estimated gain by about 45%.
2. *"Dropping product-market observations with zero sales is harmless because those products had no demand."* **False.** Zero sales may just reflect small samples. Dropping them causes selection bias (elasticity -0.88 vs -3.3 for men) and makes the gain from variety look like zero.
3. *"If the price coefficient is -0.016 and the overall-rating coefficient is 0.162, a one-point rating increase is worth about $10 to the average consumer."* **True,** given that price is in dollars and the model is correct (0.162/0.016 ≈ 10). This depends on the instruments having removed the price bias.

**Link to Homework 2 (Zappos data)**
- HW2 uses the same kind of data: POS sales, stock (inventory) characteristics, categories, brands, and reviews. The paper shows why the inventory file matters: it defines the choice set, including items that never sold.
- Expect heavy skew and many zero or near-zero sellers by brand and category. Look at the full distribution, check concentration of sales among top products, and be careful about how you aggregate (by product vs brand, by week vs month).
- Review variables (comfort, look, overall, no-review) and category, brand, and color fixed effects are natural regressors. Price coefficients from plain regressions are likely biased toward zero, for the endogeneity reasons above.
