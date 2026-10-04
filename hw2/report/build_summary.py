"""Build the HW2 write-up (Word): a 1-page executive summary, then charts and methods notes.

All numbers come from hw2/results_log.md (verified outputs of analysis/hw2_zappos_analysis.py);
charts are the PNGs that notebook saves in hw2/figures. Nothing is re-computed here.
Run with:  uv run --with python-docx python build_summary.py
"""
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HW2 = Path(__file__).resolve().parents[1]
FIG = HW2 / "figures"
OUT = HW2 / "report" / "MGT634_HW2_Zappos_summary.docx"

GREEN = RGBColor(0x63, 0x6E, 0x4F)     # Upshot dark green, matches the charts
GREY = RGBColor(0x59, 0x59, 0x59)
TEAM = "Michal Kozuchowski, Laila Lapins, Nick Giamalis, Raymond Chang, Sean Weller"

# ---------------------------------------------------------------- document setup
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(0.7)
sec.top_margin = sec.bottom_margin = Inches(0.55)

base = doc.styles["Normal"]
base.font.name = "Calibri"
base.font.size = Pt(9.5)
base.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
base.paragraph_format.space_after = Pt(3)
base.paragraph_format.line_spacing = 1.0
for name, size in [("Heading 1", 11.5), ("Heading 2", 10.5)]:
    h = doc.styles[name]
    h.font.name, h.font.size, h.font.bold = "Calibri", Pt(size), True
    h.font.color.rgb = GREEN
    h.paragraph_format.space_before = Pt(7)
    h.paragraph_format.space_after = Pt(2)
    h.paragraph_format.keep_with_next = True


def runs(p, text, size=None, color=None, italic=False):
    """Add text to paragraph p; **bold** segments are rendered bold."""
    for i, part in enumerate(re.split(r"\*\*", text)):
        if part:
            r = p.add_run(part)
            r.bold = i % 2 == 1
            r.italic = italic
            if size:
                r.font.size = Pt(size)
            if color:
                r.font.color.rgb = color
    return p


def para(text, size=None, color=None, after=None, italic=False, align=None):
    p = runs(doc.add_paragraph(), text, size, color, italic)
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    if align:
        p.alignment = align
    return p


def bullet(text, size=None):
    p = runs(doc.add_paragraph(style="List Bullet"), text, size)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Inches(0.2)
    return p


def shade_paragraph(p, hex_fill):
    """Light background box behind a paragraph (used for the bottom line)."""
    ppr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    ppr.append(shd)


def figure_pair(left, right, cap_left, cap_right, width=3.45):
    """Two charts side by side, each with a one-line takeaway underneath."""
    t = doc.add_table(rows=2, cols=2)
    for j, (f, cap) in enumerate([(left, cap_left), (right, cap_right)]):
        if f is None:
            continue
        c = t.cell(0, j)
        c.width = Inches(width + 0.05)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.add_run().add_picture(str(FIG / f), width=Inches(width))
        cp = t.cell(1, j).paragraphs[0]
        runs(cp, cap, size=8, color=GREY)
        cp.paragraph_format.space_after = Pt(6)


def figure_wide(f, cap, width=6.6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(FIG / f), width=Inches(width))
    runs(doc.add_paragraph(), cap, size=8, color=GREY).paragraph_format.space_after = Pt(6)


# ================================================================ PAGE 1: executive summary
p = para("**Zappos, July 2012 – August 2013: where to grow, how to price, and what reviews really do**",
         size=14, color=GREEN, after=1)
para(f"MGT 634 Homework 2 · {TEAM}", size=8.5, color=GREY, after=1)
para("Based on 13.5 million pairs sold ($1.17 billion), 61,433 products, 615 brands and the reviews of 21,242 "
     "products. Charts and methods follow on the next pages.", size=8.5, color=GREY, after=5)

bl = para("**Bottom line.** Zappos's business is women's shoes and winter boots, mostly sold at full price. "
          "Discounts pile up on the products customers like least, and star ratings mostly reflect how good a "
          "product already is rather than driving extra sales on their own. Growth will come from a better "
          "women's assortment (comfort), sharper seasonal planning and event-based promotions, not from "
          "constant markdowns or chasing higher star ratings.", after=5)
shade_paragraph(bl, "EEF1E8")

doc.add_heading("1. Which customers and products to prioritize", level=1)
bullet("**Women's shoes are the core business but the weakest experience.** They are 55% of pairs and 63% of "
       "revenue at the highest average price ($98), yet they have the lowest ratings (4.38 vs 4.51 stars for "
       "men's), driven by comfort. Dress heels score just 4.0 out of 5 on comfort. A comfort-led women's "
       "assortment (better-fitting dress shoes, clearer fit information) is the biggest growth lever.")
bullet("**Boots punch above their weight.** Boots are 16% of pairs but 26% of revenue ($138 average). Their "
       "sales run at 2.5 times their yearly average in November–December and collapse by spring; sandals "
       "mirror this in May–June, while sneakers (the largest category, 35% of pairs) sell steadily all year. "
       "Inventory, marketing and markdown calendars should follow these seasons, with boot stock secured by "
       "October.")
bullet("**Keep the wide catalog.** UGG leads revenue and Nike leads pairs, and the top 10 brands bring in a third "
       "of revenue, but it takes 99 of 615 brands to reach 80%. Customers spread their spending across a long "
       "tail of brands, which is exactly the variety advantage of selling online (Quan & Williams).")

doc.add_heading("2. Pricing and promotions", level=1)
bullet("**Markdowns clear weak products rather than grow demand.** 31% of pairs sell at a discount, averaging "
       "21% off. Discounts are most common where ratings are lowest: 41% of heels and 35% of flats sell "
       "discounted, vs 24% of kids' shoes. Days with more discounting are not busier (correlation −0.29).")
bullet("**Concentrated events work.** Cyber Monday 2012 was the single biggest day (57,700 pairs, 43% "
       "discounted, $5.5 million). Fewer, bigger promotional events beat constant markdowns.")
bullet("**One national price list is fine.** The average price paid ranges only from $80 (Florida) to $92 "
       "(Washington DC), and 30–32% of sales are discounted in every US region.")
bullet("**Time promotions by the hour.** The hour of the day explains 86% of the hour-to-hour swings in orders; "
       "the day of the week and the month explain about 2% each. Mondays are the busiest day and Saturdays "
       "the quietest, so emails, flash sales and customer-service staffing should follow the daily clock.")

doc.add_heading("3. How customer reviews relate to sales", level=1)
bullet("**Ratings are high and stable**: 4.3 stars overall, with looks (4.7) scoring well above comfort (4.3). "
       "Ratings did not rise or fall over the year.")
bullet("**Good ratings mark good products more than they create sales.** Across products, each extra star goes "
       "with about 26% more monthly sales. But when we compare the same product over time, a change in its "
       "rating has no measurable effect on its sales (−4%, not statistically different from zero). So invest "
       "in better products, especially comfort, rather than in pushing star ratings. To measure the true "
       "effect of ratings, Zappos could compare products just above and below the half-star rounding shown "
       "on the site, or randomly vary which reviews shoppers see first.")
para("Caveats: these are patterns in sales data, not experiments. New review activity fades after January 2013, "
     "9 days have recording gaps, and 4.8% of sales lack color-level product details.",
     size=8, color=GREY, italic=True, after=0)

# ================================================================ appendix: charts by question
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
doc.add_heading("Appendix A. Charts by assignment question", level=1)
para("Every chart is produced by the notebook (analysis/hw2_zappos_analysis.ipynb); captions give the takeaway.",
     size=8.5, color=GREY)

doc.add_heading("Q1–Q2. Brands and product characteristics", level=2)
figure_pair("q1_top10_brands_skus.png", "q2_feature_completeness.png",
            "Q1. 615 parent brands (842 brand names in POS, which lists sub-lines such as \"Nike Kids\"). Merging "
            "brand_list onto POS by sku matches 100% of 13.5M sales rows.",
            "Q2. Only gender, list price, color, occasion, closures, weight and materials are over 90% complete. "
            "We use gender, occasion and material.")
figure_pair("q2_price_distribution.png", "q2_discounts_by_gender.png",
            "Q2. Price paid: mean $86.26, median $70.99, SD $56.00, range $8.49–$3,150. List price (msrp): mean "
            "$93.77, median $79.95, SD $62.81, range $10–$3,150.",
            "Q2. Women's shoes are discounted most often (33%) and most deeply (23% off when discounted); kids' "
            "least (24%, 16% off). Highest-msrp brands: Roberto Cavalli, Giuseppe Zanotti, Alexander McQueen, "
            "Sergio Rossi, Bottega Veneta (all women's designer shoes, $786–$966).")

doc.add_heading("Q3–Q4. Customer reviews", level=2)
figure_pair("q3_products_with_reviews.png", "q3_reviews_vs_rating.png",
            "Q3. Products with reviews grow from 12,963 to 21,242, then level off; new reviews fade after "
            "January 2013 (a coverage limit of the data).",
            "Q3. Average over product-months: overall 4.30, comfort 4.29, look 4.67 (highest). More reviews go "
            "with slightly higher (+0.06 stars per doubling) and far more stable ratings.")
figure_pair("q3_rating_trend.png", "q4_ratings_by_features.png",
            "Q3. Ratings are flat: new reviews average 4.3–4.4 stars every month (trend −0.002 stars/month, not "
            "significant). The running average dips only because newly reviewed products join.",
            "Q4. 95.9% of review records match our 3 features. Women's (4.22), dress (4.14) and synthetic (4.18) "
            "shoes rate lowest overall, mostly because of comfort; looks score 4.6–4.8 everywhere.")

doc.add_heading("Q5. Transaction patterns", level=2)
figure_pair("q5_top15_states.png", "q5_avg_price_by_state_map.png",
            "Q5. 13,546,258 transactions (pairs) from Jul 13, 2012 to Aug 15, 2013. California (14%) and New York "
            "(11%) lead; 0.7% of sales go to territories or military addresses.",
            "Q5. Average price paid per pair by state: national $86; DC, Vermont, Montana, Oregon and Colorado "
            "pay the most ($91–$92), Florida and Hawaii the least ($80–$82).")
figure_pair("q5_discount_share_by_region.png", "q5_ratings_by_price_tier.png",
            "Q5. The share of discounted sales is 29.7% (Northeast) to 32.0% (West): almost no regional "
            "difference.",
            "Q5. By list price, $50–$100 shoes rate lowest (4.24); under-$50 (4.32) and $200+ (4.34) rate "
            "highest. Ratings do not simply rise with price.")

doc.add_heading("Q6–Q7. Brands and timing", level=2)
figure_pair("q6_top10_brands_units.png", "q7_daily_sales_revenue.png",
            "Q6. Nike sells the most pairs (984k) but UGG earns the most revenue ($75.9M) at twice Nike's average "
            "price.",
            "Q7. A median day sells 33,500 pairs. Cyber Monday (Nov 26, 2012) is the peak; Mondays are the busiest "
            "weekday. Red dots mark the 9 days with missing hours of records.")
figure_wide("q6_revenue_by_brand.png",
            "Q6. Total revenue $1,168M. UGG ($75.9M), Nike ($65.3M) and Frye ($44.4M) lead; the top 10 brands "
            "earn 33% of revenue and 99 brands earn 80%.")
figure_pair("q7_smoothed_sales_revenue.png", "q7_category_seasonality.png",
            "Q7. 7- and 28-day moving averages remove the weekly cycle: sales build to a December peak; daily "
            "revenue then runs 19% lower in Feb–Jul 2013 than in Jul–Nov 2012.",
            "Q7. Category codes inferred from best sellers and features (e.g., 1 = boots: UGG Classic Short, "
            "8 = sandals, 10 = sneakers). Boots and sandals have opposite seasons; sneakers are steady.")
figure_pair("q7_time_of_day_vs_week_vs_month.png", None,
            "Q7. Time of day explains 86% of hourly variation in pairs sold; day of week 2% and month 2%. On "
            "daily totals, month (28%) and weekday (23%) matter similarly.", "")

# ================================================================ appendix: data and methods
doc.add_heading("Appendix B. Data, cleaning and methods", level=1)
for t in [
    "**Files and levels.** POS.dta: 13,546,258 rows, one per pair sold. brand_list.dta and categories.csv: one "
    "row per product (sku). stock_chars.dta: 117,493 rows, one per product × color (style_id). reviews.csv: "
    "297,388 rows, one per product × month (21,242 products × 14 months).",
    "**Never change the raw data.** The 2.6 GB POS file is read in 1-million-row pieces and saved once as a "
    "compressed Parquet copy (309 MB); all large queries run in DuckDB SQL on that copy (Class 7). Raw files are "
    "fingerprinted (SHA-256) at the start and re-checked at the end.",
    "**Checks on all 13.5M sales.** No zero prices, no price above list price, discount always equals list "
    "price minus price paid, and the sale flag always agrees. No exact duplicate rows. date_* is the purchase "
    "time (local US time; the 2 am hour is missing on the daylight-saving day). 9 days with missing hours of "
    "records are flagged and excluded from smoothing and time-of-day models.",
    "**Merges (rows before → after, match rate).** POS × brand_list on sku: 13,546,258 → 13,546,258, 100%. "
    "POS × stock_chars on sku + color: rows unchanged, 95.2% matched (97.8% with the product-level fallback). "
    "reviews × product features on sku: 297,388 → 297,388, 95.9% matched. Every merge asserts a unique key and "
    "uses many-to-one validation, so no row can be duplicated.",
    "**Definitions.** Transaction = one pair sold. Revenue = sum of prices paid. Discounted = price below list "
    "price. Price tiers use each product's list price, so a temporary sale does not move it between tiers. "
    "Regions are US Census regions; territories and military addresses are excluded from state and region "
    "results. Reviews are running totals, so each month's new reviews are recovered from the change in totals.",
    "**Ratings → sales regressions** (product × month panel, 232,895 observations, standard errors clustered by "
    "product). Outcome: log(1 + pairs sold this month); key variable: last month's rating. Naive: +0.261 "
    "(SE 0.010). With controls and month fixed effects: +0.056 (0.008). With product and month fixed effects "
    "(within estimator, Class 8): −0.043 (0.024). The drop shows omitted-variable bias: product quality, "
    "brand and style raise both ratings and sales.",
    "**Time-of-day vs weekday vs month.** Hourly pair counts (388 complete days × 24 hours) regressed on hour, "
    "weekday and month dummies; R² 0.856, 0.017 and 0.021 respectively (0.895 together).",
]:
    bullet(t, size=8.5)

doc.add_heading("AI disclosure", level=2)
para("We used Claude (Anthropic) through Claude Code, as the course requires, to plan the analysis, write and debug "
     "the Python code, and draft this summary. Every number was checked against the notebook output, and the "
     "notebook re-verifies 13 key values and the raw-file fingerprints on each run.", size=8.5)

doc.save(OUT)
print("Saved", OUT)
