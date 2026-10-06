"""Build the Lab 2 write-up (Word) from the full-data results (cluster run, 28,240,000 requests).

Charts: put the cluster's lab2_output/figures/*.png in notes/lab2_nyc311/figures/ and re-run; until then
each chart is a placeholder line. Run:  uv run --with python-docx python build_writeup.py
"""
import re
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
OUT = HERE / "MGT634_Lab2_NYC311_writeup.docx"
GREEN, GREY = RGBColor(0x63, 0x6E, 0x4F), RGBColor(0x59, 0x59, 0x59)

doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Inches(0.8)
sec.top_margin = sec.bottom_margin = Inches(0.7)
st = doc.styles["Normal"]
st.font.name, st.font.size = "Calibri", Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.paragraph_format.space_after = Pt(3)
for name, size in [("Heading 1", 13), ("Heading 2", 11)]:
    h = doc.styles[name]
    h.font.name, h.font.size, h.font.bold, h.font.color.rgb = "Calibri", Pt(size), True, GREEN
    h.paragraph_format.space_before, h.paragraph_format.space_after = Pt(9), Pt(3)


def runs(p, text, size=None, color=None, italic=False):
    for i, part in enumerate(re.split(r"\*\*", text)):
        if part:
            r = p.add_run(part)
            r.bold, r.italic = i % 2 == 1, italic
            if size:
                r.font.size = Pt(size)
            if color:
                r.font.color.rgb = color
    return p


def para(text, **kw):
    return runs(doc.add_paragraph(), text, **kw)


def bullet(text):
    p = runs(doc.add_paragraph(style="List Bullet"), text)
    p.paragraph_format.space_after = Pt(2)


def figure(name, caption, width=6.6):
    f = FIG / f"{name}.png"
    if f.exists():
        doc.add_paragraph().add_run().add_picture(str(f), width=Inches(width))
    else:
        para(f"[Chart: lab2_output/figures/{name}.png]", color=GREY, italic=True)
    para(caption, size=8.5, color=GREY, italic=True)


def table(rows, header):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(header):
        t.rows[0].cells[i].text = h
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = str(v)
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                for r in p.runs:
                    r.font.size = Pt(8.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ============================================================ title + executive summary (Q11)
runs(doc.add_paragraph(), "**NYC 311 Service Analytics: data assessment for the Mayor's Office**", size=16, color=GREEN)
para("MGT 634 Lab Day 2 · Michal Kozuchowski, Laila Lapins, Nick Giamalis, Raymond Chang, Sean Weller", size=9, color=GREY)
para("Data: 2,824 JSON files, 28,240,000 service requests, Jan 1 2010 – Nov 20 2021. Code: MGT634_Lab2_NYC311_v3.ipynb "
     "(one Run All reproduces every number, chart and the dashboard).", size=9, color=GREY)

doc.add_heading("Q11. Executive summary (5 minutes with the Mayor)", level=1)
para("**Three critical findings**")
bullet("**The 311 data is not yet reliable enough to set budgets.** 3.65M requests (13%) carry no time of day; 267,339 "
       "were closed before they were opened; agencies close thousands of requests in a single second (17,088 by DSNY "
       "at once); key fields hide missing values behind 'Unspecified'; hacking strings sit in the complaint-type field; "
       "and the last weeks of data (Oct–Nov 2021) are incomplete.")
bullet("**Housing is where service is slowest and most concentrated.** Landlord-responsibility complaints (heat, "
       "plumbing, paint, construction) take a median 6–9 days to close versus hours for most other complaints, and they "
       "make up 44% of all Bronx requests. Every 10°F drop in temperature adds about 283 heat complaints a day.")
bullet("**Some districts wait longer for the same problems.** Comparing like with like, Queens 13, Bronx 12 and Queens 5 "
       "are about 20% slower than the citywide norm for the same complaint types; HPD, DOB, DPR and DOHMH remain slow "
       "even after adjusting for how hard their complaints are.")
para("**Two immediate actions**")
bullet("**Weather-triggered staffing:** use the 5-day forecast to surge HPD heat inspectors before cold snaps (and DEP / "
       "Parks crews before storms), since cold and rain predict which complaints will arrive.")
bullet("**Fix data at intake:** require borough, ZIP and a real timestamp; reject code-like text; keep administrative bulk "
       "closures out of the response-time KPI.")
para("**One long-term recommendation**")
bullet("Publish a **difficulty-adjusted response-time scorecard** by community district and agency (built on our Q8 "
       "dashboard and one standard complaint-type list), and move resources to districts below the citywide standard.")

# ============================================================ Part 1
doc.add_heading("Part 1: Data quality assessment", level=1)
doc.add_heading("Q1. Missing values", level=2)
para("We measured missingness three ways, because a blank is not the only way data goes missing:")
bullet("**Truly empty (NULL).** Mostly specialised fields: bridge/highway, taxi and vehicle fields are 99–100% empty, "
       "landmark 87.5%. Core location fields are mostly present: latitude/longitude 8.7% missing, ZIP 5.1%, address 16.9%.")
bullet("**Disguised missing** (looks filled, carries no information): park_facility_name 'Unspecified' 99.3%; "
       "facility_type 'N/A' 74%; open_data_channel_type 'UNKNOWN' 21%; community_board '0 Unspecified' 10.2%; borough "
       "'Unspecified' 4.4%; plus impossible values (dates before 2003, coordinates of 0).")
bullet("**Not applicable:** many fields only matter for some of the 478 complaint-type spellings (vehicle_type is used by "
       "2 types, taxi borough by 3). Judged only where they apply, address fields are 11–13% missing and coordinates 5% "
       "(vehicle_type stays 88% missing even where it applies: a real gap).")
bullet("**Other issues:** 267,339 closed before created; 3,654,438 created at exactly midnight; 38 test records "
       "('Closed - Testing'); no duplicate request ids.")
figure("q1_missing_values", "Figure 1. Missing share by field: empty (green), disguised (red); dot = missing where the field applies.")

doc.add_heading("Q2. Consistency over time", level=2)
bullet("**Daily volume (a):** 4,342 days, none completely empty, but 90 days fall below half of the local 4-week median. "
       "The **end of the file is incomplete**: late Oct–Nov 2021 has days with 5–400 requests against ~5,500–7,900 normally. "
       "Spikes are real events: Tropical Storm Isaias (Aug 4–5, 2020: 24,415 requests, 2.3× normal) and the first cold snap "
       "each January (e.g. the Jan 7, 2014 polar vortex).")
bullet("**Timestamp precision changed:** 30–34% of requests in 2010–2014 have a date but no time (stamped midnight), "
       "14% in 2015, under 2% from 2016. Hour-level analysis before 2016 is unreliable. Volume grew from 2.0M (2010) to 2.9M "
       "requests a year (2020).")
bullet("**Closings (b):** 5.78M closed at exactly midnight; 1.04M closed in the same second they were opened (automatic "
       "closures); 267k closed before opening; 5,921 have 1900 placeholder dates; 9 lie in the future; 335k took over a year. "
       "**Batch closures** are administrative clean-ups, not service: 18,033 DOB requests on Sep 10, 2019 and 17,088 DSNY "
       "requests in one second on Jun 20, 2023 (two years after the data ends). Real closing times peak at midday.")
figure("q2_openings_closings", "Figure 2 (c). Openings and closings over time, by day of week and by week of year.")

doc.add_heading("Q3. Complaint-type consistency", level=2)
bullet("**(a) Examples:** 478 spellings reduce to 459 types after standardising. Same category, different names: HEATING vs "
       "HEAT/HOT WATER (2.4M requests), 'Traffic/Illegal Parking' vs 'Illegal Parking', upper vs lower case (PLUMBING / "
       "Plumbing, ELEVATOR / Elevator), 'Derelict Vehicle(s)', 'Dirty Condition(s)', 'Animal Abuse' vs 'Animal - Abuse', "
       "'Hazardous Material(s)'. Unusual entries: 166 types with under 10 requests, many of them **cyber-attack probes typed "
       "into the online form** (SQL injection such as \"';DECLARE @Q…\" and 'WAITFOR DELAY', path attacks such as "
       "'%2fetc%2fpasswd'), all under agency DVS. 36 types (8.5% of requests) are service or information requests, not "
       "complaints.")
bullet("**(b) Strategy:** keep the raw field untouched and add (1) `standard_type` from an automatic normalizer (case, "
       "spacing, punctuation) plus a short alias table for known renames, and (2) `category` from keyword rules (building "
       "owner, city infrastructure, neighbors, nature/weather, information request). The mapping is exported as "
       "complaint_type_map.csv. New data runs through the same rules automatically; any new name is flagged by a "
       "similarity check for a one-line decision, code-like text is quarantined, and the detailed `descriptor` is kept.")

doc.add_heading("Q4. Response times (time to closure)", level=2)
table([["27,413,243", "23.6", "1.43", "148.4", "0.1", "7.0", "25.2", "466"]],
      ["Closed requests", "Mean (days)", "Median", "SD", "Q1", "Q3", "P90", "P99"])
bullet("**(a)** 3.8M requests (13.9%) exceed the outlier fence (Q3 + 1.5×IQR = 17.4 days); the longest took 15.7 years. "
       "The mean is 16× the median, so medians are the right KPI.")
bullet("**(b) Areas:** we compare each district with the citywide median for the same complaint types (1.0 = typical). "
       "Slowest: Queens 13 (1.22), Bronx 12 (1.20), Queens 5 (1.20), Queens 1 (1.14). Queens is the slowest borough once "
       "the complaint mix is accounted for (1.06); Manhattan the fastest (0.94).")
bullet("**(c) Agencies:** a regression of log hours to close on agency, controlling for complaint category, borough, month, "
       "weekday and channel (about 380,000 randomly sampled requests), barely changes the ranking (R² 0.48 → 0.50), so slow agencies are "
       "not just handling harder problems. Fastest after adjustment: NYPD, DHS, DEP (excluding 311 itself); slowest: EDC, DOE, DPR, DOB, TLC, DOHMH, HPD. "
       "DOT drops from 6th to 9th once adjusted (from 44% faster than average to 13% slower) (its speed comes from easy complaints); DOF and DSNY improve. Caveat: "
       "NYPD's speed partly reflects quick 'no action needed' closures.")

# ============================================================ Part 2
doc.add_heading("Part 2: Visualization and insights", level=1)
doc.add_heading("Q5. Top 10 complaint types", level=2)
figure("q5_top10_complaints", "Figure 3. Residential noise (9.0%) and heat/hot water (8.6%) lead; the top 10 are 47% of all requests.")
doc.add_heading("Q6. Complaints and the weather", level=2)
para("We merged daily NYC weather (Open-Meteo historical archive: temperature, precipitation, snowfall) on date: 4,342 days "
     "before and after, 100% matched. **Weather changes what people complain about more than how much:** total daily "
     "volume barely moves (weather explains 0.4%), but the content shifts strongly:")
bullet("Heat/hot water: correlation −0.76 with the daily low; **+283 complaints/day per 10°F colder**.")
bullet("Sewer & water: +110 per inch of rain; trees: +105 per inch (storm damage, e.g. Isaias); noise rises in warm weather "
       "and falls ~300/day per inch of rain.")
figure("q6_weather", "Figure 4. Average complaints per day by overnight low temperature (heat, Oct-May) and by rainfall (sewer, trees); (x) = multiple of the mildest / driest days.")
doc.add_heading("Q7. Geographic disparities", level=2)
figure("q7_geography", "Figure 5. Map of the 59 community districts: requests per year (left) and share about housing conditions (right), with three insights.")
bullet("The Bronx files **1.3×** as many requests per resident as Queens (305 vs 234 per 1,000 a year).")
bullet("**10 of 71** community districts generate **25%** of requests.")
bullet("**44%** of Bronx requests concern housing conditions, versus 19% in Queens and 13% in Staten Island.")
doc.add_heading("Q8. Web dashboard", level=2)
para("lab2_output/q8_dashboard.html is an interactive, zoomable map (Plotly) of 61,837 ~100 m cells. Colour = main source of "
     "complaints, size = volume; hovering shows the top complaint, community district, median days to close and share "
     "unresolved. Staff can zoom from borough to block level in a browser, with no software needed.")

# ============================================================ Part 3
doc.add_heading("Part 3: Combined analysis and strategy", level=1)
doc.add_heading("Q9. Equity in service delivery", level=2)
figure("q9_equity", "Figure 6. Community districts: share of requests unresolved vs time to close relative to the same complaint types citywide; colour = main source, size = volume.")
bullet("**Unresolved:** Staten Island districts 3, 1 and 2 hold the most unresolved requests (up to 5.4%), mainly street "
       "conditions; Queens 12 and 7 and Bronx 10 follow.")
bullet("**Concentration by type and origin:** Bronx problems come from landlords (2.3M housing requests); Queens and Staten "
       "Island from city infrastructure; Manhattan and Brooklyn from neighbors (noise, parking).")
bullet("**Inequity:** landlord-responsibility complaints take a median 6–9 days (8.8 on Staten Island, 8.0 in Queens) "
       "versus 0.1 days for neighbor complaints, so housing-heavy districts wait longer; and Queens 13 / Bronx 12 are ~20% "
       "slower even for identical complaint types, which points to capacity, not difficulty.")
doc.add_heading("Q10. Features for a volume model", level=2)
table([["Last week's volume", "0.53"], ["Day of week", "0.20"], ["Month", "0.02"], ["Weather (temperature, rain, snow)", "0.004"],
       ["All together", "0.57"]], ["Feature (daily total volume)", "R² alone"])
bullet("Most valuable: recent volume (persistence) and day of week; weather and season matter for the **mix** of "
       "complaints (heat, sewer, trees), which is what staffing needs; add holidays and borough/category for local forecasts.")
bullet("Link to response times (daily): weekday (correlation −0.23) and cold (−0.20) are related; busier days close faster "
       "(−0.22 days per extra 1,000 requests), because they are dominated by quickly closed noise complaints (R² 0.31).")

doc.add_heading("Method notes and AI disclosure", level=2)
para("All 2,824 JSON files were read with DuckDB and converted once to Parquet (4 minutes on 4 cores / 32 GB); the raw "
     "files were never modified. Every merge reports rows before/after and its match rate. A first attempt to remove "
     "duplicate ids ran out of memory; a cheap check showed there were none (28,240,000 = 2,824 × 10,000), so that step is "
     "skipped unless duplicates exist. We used Claude (Anthropic) via Claude Code, as the course requires, to write and debug "
     "the code and draft this write-up; all numbers come from the notebook output.", size=9)

doc.save(OUT)
print("Saved", OUT, "| charts found:", sorted(p.name for p in FIG.glob("*.png")) if FIG.exists() else "none yet")
