# Class 11 reading — Adams & Williams (2019), "Zone Pricing in Retail Oligopoly"

*American Economic Journal: Microeconomics* 11(1): 124–156. Brian Adams (BLS) and Kevin R. Williams (our professor). File: `11_1 Zone Pricing in Retail Oligopoly.pdf`.

## One-paragraph summary
Big retail chains (Home Depot, Lowe's, Menards) don't set one national price, and they don't price store by store either. They group stores into **pricing zones** that share one price. A monopolist could only gain by pricing more finely. With competitors, that isn't guaranteed: finer pricing can intensify competition. The authors **scrape the retailers' websites** to get prices and daily inventory, estimate a demand model for drywall, and simulate what happens under uniform, zone, and market-level pricing. Their findings:
- **Home Depot would gain from finer pricing; Lowe's would prefer coarser pricing.**
- Zone pricing **softens competition in urban (competitive) markets** but **shields rural (monopoly) consumers** from high prices.
- Overall, zone pricing gives **higher consumer surplus** than finer price discrimination would.

## Key vocabulary
- **Third-degree price discrimination:** charging different prices to different groups (here, by location).
- **Zone pricing:** one price shared by all stores in a zone. **Uniform pricing:** one national price. **Market pricing:** one price per local market (CBSA/county).
- **Monopoly market:** only one chain's store present. **Duopoly:** both Home Depot and Lowe's present.
- **Strategic complementarity:** when my rival cuts price, my best response is to cut too. Prices move together.
- **Residual demand elasticity:** how sensitive *my* sales are to *my* price, given the rivals. It is more elastic where there is competition.
- **Nested logit:** a demand model where products in the same "nest" (here mold-resistant vs regular drywall) are closer substitutes. λ ∈ [0,1]; λ → 1 means near-perfect substitutes within a nest.
- **Menu costs:** the cost of setting and maintaining many prices (managerial effort, IT).
- **Agency problem:** store managers maximizing their own store's profit hurt the chain, because they steal sales from sister stores.

## Data (the "advanced data collection" link to today's class)
1. **Cross-section of national prices:** a web scraper set the website's location to each store to reveal the local price (footnote 8). The result is **801,498 prices** (2013–14) across about 4,000 stores for 10 categories: drywall, insulation, LED bulbs, mosaic glass tile, plywood, roof underlayment, sanders, screwdrivers, stone pavers, window film. Products were randomly sampled within each category.
2. **Daily panel for drywall in the Intermountain West** (Idaho, Montana, New Mexico, Utah, western Colorado, eastern Washington): **75 Home Depot and 53 Lowe's stores**, Feb 12 – Jul 29, 2013, **72,092 obs**, 31 distinct products.
   - **Sales = the daily drop in inventory on hand** (the websites show quantity-on-hand).
   - An inventory increase of more than 15 sheets is classed as a **delivery**. On those days, sales are imputed as the average for that product, store, and day of week.
   - Duplicate SKUs (same product listed under different brands with identical prices and inventory) were removed. Brand labels were unreliable.
3. **Costs:**
   - wholesale price from confidential **BLS** microdata (the only non-public input)
   - plus **transport cost** = driving distance from factory to flatbed distribution center to store × flatbed $/mile ÷ sheets per truck
   - Factory locations come from *Global Gypsum Magazine*; DCs were found on the retailers' sites and Google Maps street view.

Why drywall and this region: known plant locations, so costs can be estimated; infrequent deliveries, so less measurement error from using inventory changes as sales; varied competition; bulky goods, so buyers don't travel far; rarely promoted or used as a loss leader; zones are big but countable; and Menards is absent, so there are only two sellers.

## Descriptive facts
- **Table 1:** the number of unique prices per product varies a lot by category and chain.
  - Drywall: HD mean 46 and median 50 prices; Lowe's 37 / 32; Menards 22 / 24.
  - Screwdrivers and window film are near-uniform.
  - Plywood: HD 4 vs Lowe's 24.
  - Big, bulky items get finer pricing.
- Average coefficient of variation (CV) of price across stores is 0.039, or **0.114 excluding uniformly priced products**.
- **Maps (Figs 1–4)** show geographically contiguous zones. One HD drywall zone spans 500 miles: Salt Lake City, Boise, and small towns in Idaho, Nevada, and Wyoming. Prices range from $6.98 to $19.85 for Lowe's drywall nationally. Menards cement block varies 2× nationally.
- Zones come from HD's internal hierarchy: store → market → buying office → region. A category manager pools "markets" into zones. Nationally HD has **165 drywall zones** and Lowe's **129**.
- **Table 2 (the killer example):** HD stores in Logan UT, Rock Springs WY, and Elko NV charge **identical prices** ($11.47 mold-resistant, $10.98 regular), even though:
  - the nearest Lowe's is 1 vs 107 vs 168 miles away;
  - the nearest distribution center is 58 vs 177 vs 251 miles away;
  - median income ranges from $64k to $84k.
- **Table 3:** sales per product per day are 11.6 sheets (Lowe's) and 14.7 (HD). Price is about $11.8. Total revenue for the 128 stores is $19.4M/yr.

## Model
- **Demand: nested logit (Berry 1994 inversion).**
  - `log(s_js) − log(s_0) = x_js β − α_ℓ p_js + λ log(s_js|c) + ξ_js`
  - Controls: market FE, month FE, length dummies, a mold-resistance indicator, a chain dummy, and price × local income.
  - Market = CBSA (or county) over 2 weeks. Market size is proportional to 2010 county population.
- **Endogeneity → IV.**
  - Price is correlated with the unobserved quality ξ, and the within-nest share is mechanically correlated with ξ.
  - Instruments: marginal costs; the sum and count of products and characteristics at allied and rival stores; and a **Hausman instrument**, the average price of the same product in markets **more than 300 miles away, outside the focal zone**.
- **Supply:** each chain picks prices to maximize total category profit, Σ over zones Σ over stores (p_jz − c_js) q_js. Prices are constrained to be equal within a zone, and firms compete in Bertrand–Nash fashion.

## Results
- **Table 4 (demand):**

  | | Logit | Nested logit |
  |---|---|---|
  | Price | −0.301 (0.117) | −0.110 (0.048) |
  | λ | — | 0.878 (0.055): drywall is highly substitutable |
  | Mean own-price elasticity | −2.5 | **−5.6** |

  - Income × price is tiny and insignificant.
  - Chain dummy is positive.
  - Mold resistance is negative (heavier, less fire-resistant).
  - **Industry elasticity ≈ −0.7.**
- **Observed vs optimal (Fig 6):** observed prices are on average **9.2% below** model-optimal (median 7.4%). Markups range from −0.9% to 38% at observed prices.
- **Counterfactuals (Table 6, variable profit $M/yr, Lowe's / HD):**

  | Lowe's \ HD | Uniform | Zone | Market |
  |---|---|---|---|
  | Uniform | 2.215 / 4.522 | 2.097 / 4.672 | 1.844 / 5.170 |
  | Zone | 2.222 / 4.500 | **2.108 / 4.664** (status quo) | 1.860 / 5.167 |
  | Market | 2.325 / 4.344 | 2.220 / 4.519 | 1.995 / 5.055 |

  - Moving from (zone, zone) to (market, market): **Lowe's −5.7%, HD +8.4%**.
  - Why the asymmetry: HD has many more monopoly stores (21 monopoly markets vs Lowe's 4).
  - Market pricing is a **dominant strategy** for both chains, a prisoner's-dilemma-like regime game. Yet neither uses it.
  - **Menu costs (Table 8)** rationalize the zones. Lowe's picks zones over market pricing only if the extra cost of market pricing over zone pricing (μᴹ−μᶻ) is above $0.112M; for HD the threshold is above $0.503M.
  - If λ < 0.75, finer pricing would lower industry profit.
- **Prices:**
  - Under market pricing, HD prices in its monopoly markets are **+50%**, and Lowe's prices in its monopoly markets are **+81%**.
  - Duopoly prices fall about 3.7%.
- **Consumer surplus (Table 7):** moving from zone to market pricing gives
  - **monopoly (rural) markets −$1.56M/yr**
  - **duopoly (urban) markets +$0.63M/yr**
  - **net −$0.93M/yr**
  - The per-person effect in monopoly markets is **10× larger**.
  - So zone pricing protects rural consumers at the cost of slightly higher urban prices.
- **Ignoring competition (Table 9):** if you hold the rival's prices fixed (as the older Dominick's literature had to), the gain from moving to market pricing is overstated **5.15× for Lowe's and 1.26× for HD**. The menu costs implied by that older approach are overstated 1.26–5.15×.
- **Store-manager pricing (Fig 8):** decentralizing to store-level profit maximization cuts duopoly-market profits by **39.6% (Lowe's) and 27.1% (HD)**, or −14.7% for the industry. That is the agency problem, and it is probably why the chains centralize pricing.

## Limitations (authors' own)
- No individual purchase data, and no consumer travel costs.
- Drywall is barely differentiated, so the findings may not carry over to other categories. Online competition is ignored.
- Zones and the product set are taken as **exogenous**. The data can't say *why* zones differ (costs, demand, negotiation, managerial ability).
- Costs leave out labor, warehousing, and floor space, so they are a lower bound. The Appendix recovers costs from first-order conditions (MPEC) instead.
  - Transport coefficient: $0.0024 per sheet-mile.
  - Marginal cost IQR: $3.66–$9.93.
  - These costs come out about $1 lower than the wholesale-based ones.

## How this maps to course concepts (quiz angle)
- **Data collection:**
  - scraping store-level prices by spoofing location
  - inventory differencing as a sales proxy, which brings **measurement error** (deliveries and returns), handled with a >15-sheet delivery rule plus imputation; results are robust to it (footnote 19: elasticity −5.6 vs −5.3)
  - duplicate-SKU cleaning
  - merging in outside cost data (BLS, plant locations, Google Maps distances)
- **Endogeneity:** price is correlated with unobserved quality (ξ), so OLS on price is biased toward zero. **IV fixes it** with cost shifters and Hausman instruments. The exclusion argument: prices in faraway markets share cost shocks but not local demand shocks, and the >300-mile, outside-the-zone rule guards against zones being endogenous.
- **Fixed effects:** market and month indicators absorb local and seasonal demand.
- **Robust SEs** are reported in Table 4. Read it as: coefficient (SE), t ≈ coefficient/SE. E.g. nested-logit price: −0.110/0.0483 ≈ −2.3, significant at 5%.
- **Selection of sample:** one region and one category chosen for tractability, so external validity is limited (the authors say so).
- **Counterfactual logic:** structural model plus equilibrium re-solve. Holding rivals fixed ignores strategic complementarity and overstates gains, which is the same flavor of mistake as ignoring general-equilibrium or competitive responses.
