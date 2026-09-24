"""Build the HW1 write-up (Word) from the verified results (hw1/results_log.md) and figures."""
import re
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HW1 = r"C:\Users\mnich\OneDrive\Documents\Second Year\EmpiricalStrategy\hw1"
FIG = HW1 + r"\figures\\"
import sys
OUT = sys.argv[1] if len(sys.argv) > 1 else HW1 + r"\report\MGT634_HW1_NHAMCS_writeup.docx"

NAVY = RGBColor(0x1F, 0x3A, 0x5F)
GREY = RGBColor(0x52, 0x51, 0x4E)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for side in ["left_margin", "right_margin"]:
    setattr(sec, side, Inches(0.75))
sec.top_margin, sec.bottom_margin = Inches(0.6), Inches(0.6)

base = doc.styles["Normal"]
base.font.name = "Calibri"
base.font.size = Pt(10)
base.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
base.paragraph_format.space_after = Pt(4)
base.paragraph_format.line_spacing = 1.05
for lvl, size in [(1, 12.5), (2, 11)]:
    h = doc.styles[f"Heading {lvl}"]
    h.font.name, h.font.size, h.font.bold = "Calibri", Pt(size), True
    h.font.color.rgb = NAVY
    h.element.rPr.rFonts.set(qn("w:asciiTheme"), "") if False else None
    h.paragraph_format.space_before = Pt(8 if lvl == 1 else 5)
    h.paragraph_format.space_after = Pt(3)
    h.paragraph_format.keep_with_next = True


def runs(p, text, size=None, color=None):
    """Add text to paragraph p; **bold** segments are rendered bold."""
    for i, part in enumerate(re.split(r"\*\*", text)):
        if part:
            r = p.add_run(part)
            r.bold = i % 2 == 1
            if size:
                r.font.size = Pt(size)
            if color:
                r.font.color.rgb = color
    return p


def para(text, size=None, color=None, align=None, after=None):
    p = runs(doc.add_paragraph(), text, size, color)
    if align:
        p.alignment = align
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def bullet(text):
    p = runs(doc.add_paragraph(style="List Bullet"), text)
    p.paragraph_format.space_after = Pt(2)
    return p


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def table(rows, widths, caption, size=8.5):
    """rows[0] = header. Light grid, shaded header, compact font."""
    cap = para(caption, size=9, color=NAVY, after=2)
    cap.runs[0].bold = True
    cap.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.width = Inches(widths[j])
            c.paragraphs[0].paragraph_format.space_after = Pt(0)
            runs(c.paragraphs[0], str(val), size=size)
            if j > 0 and rows[0][j] != "Reading":
                c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            if i == 0:
                shade(c, "E8EEF5")
                for r in c.paragraphs[0].runs:
                    r.bold = True
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def figure(files, width, caption):
    """One image, or several side by side in a borderless table, plus caption."""
    if len(files) == 1:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        p.add_run().add_picture(FIG + files[0] + ".png", width=Inches(width))
    else:
        t = doc.add_table(rows=1, cols=len(files))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for j, f in enumerate(files):
            c = t.cell(0, j)
            c.width = Inches(width + 0.05)
            cp = c.paragraphs[0]
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cp.paragraph_format.space_after = Pt(0)
            cp.add_run().add_picture(FIG + f + ".png", width=Inches(width))
    cap = para(caption, size=8.5, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, after=6)
    cap.runs[0].bold = True


# ---------------------------------------------------------------- title block
t = para("Exploring U.S. Emergency Department Visits: NHAMCS-ED 2015", size=16, color=NAVY, after=0)
t.runs[0].bold = True
para("MGT 634 Empirical Strategy with AI · Homework 1 · Group: Michal Kozuchowski, Laila Lapins, Nick Giamalis, Raymond Chang, Sean Weller · "
     "September 2026", size=9, color=GREY, after=6)

para("**Bottom line.** U.S. EDs handled an estimated **136.9 million visits** in 2015. Demand is "
     "predictable: it plateaus from 10am to 8pm and is highest on Mondays. Payment is dominated by "
     "public payers (**Medicaid 34.9%, Medicare 19.9%** of visits with a known payer), and "
     "**nearly half of visits (47.6%)** involve a chronic condition. Triage sorts patients sharply by "
     "outcome (a third of the most urgent are admitted vs 2-3% of the least urgent), but median "
     "waits are almost identical (18-20 minutes) for every level except the most urgent.")

# ---------------------------------------------------------------- 1. data
doc.add_heading("1. Data, sample design and cleaning (Q1-Q2)", level=1)
para("**What the data are.** The NCHS public-use file has **21,061 rows and 1,031 columns**. "
     "**Each row is one sampled ED visit** (one Patient Record Form), not a patient: the same person "
     "could appear twice. Hospital code + patient code uniquely identify every row (0 duplicates), "
     "and the visits come from **248 EDs** (median 94 sampled visits each). Summing the survey weight "
     "PATWT gives **136,943,181 estimated U.S. ED visits** in 2015, exactly the documented total and "
     "well over 100 million. Weights are very unequal (117 to 42,002, median 5,232; the top 10% of "
     "rows carry 28.7% of weighted visits), and the sample over-represents the Northeast (20.4% of "
     "rows vs 17.3% of visits) while under-representing the South (33.3% vs 37.8%). We therefore "
     "weight every total, share and rate by PATWT.")
para("**Missing data are hidden as codes.** The standard pandas missing-value check (isna) reports NaN in 600 columns, but these are "
     "mostly empty drug-category text slots. Real missing answers are stored as negative numbers: "
     "**-9 = blank, -8 = unknown, -7 = not applicable** (codebook p.37 onward). Counting those codes, "
     "118 variables are more than 5% missing and 56 are more than 20% missing. For our variables: "
     "unimputed ethnicity 24.2% (so we use the imputed ETHIM, 0% missing), pain scale 29.5%, triage "
     "level 22.2%, wait time 15.2% blank (+3.4% not seen by a provider), payer 8.7%, length of visit "
     "7.0%. INTENT15 (75% blank) and HDSTAT (91% \"not applicable\") are structurally missing: they are "
     "only asked for injury visits and admitted patients. We confirmed this reading of the codes by "
     "reproducing NCHS's published nonresponse rates (Table 1).")
para("**Missingness is not random.** Wait time is missing for 7-12% of triaged visits but 38-45% of "
     "visits with no triage recorded, and for 9.8% of Midwest vs 19.7% of Northeast visits. This is a "
     "missing-at-random pattern tied to observable ED processes. Wait-time statistics therefore describe "
     "EDs that record wait times, and may understate waits in less-structured settings.")
para("**Cleaning rules.** (1) Convert every -9/-8/-7 to missing before computing anything. "
     "(2) Recode yes/no items to 0/1. (3) Convert ARRTIME from military time to an arrival hour "
     "(1.3% blank). (4) Handle long tails rather than delete them: length of visit reaches 5,732 "
     "minutes (95 hours) and waits 1,305 minutes, so we report medians and winsorize means at the "
     "99.5th percentile (98 and 86 visits capped). (5) Test the weighted mean, median and correlation "
     "functions on data with known answers, and re-check every published NCHS figure we could find. "
     "A final clean run passes all 20 of 20 verification checks.")
table([["Check", "Our result", "NCHS codebook"],
       ["Records", "21,061", "21,061 (p.115)"],
       ["Weighted U.S. ED visits", "136,943,181", "136,943,181 (p.28)"],
       ["Female share (weighted)", "55.44%", "55.436% (p.115)"],
       ["Hispanic share (weighted)", "16.49%", "16.493% (p.115)"],
       ["Medicaid as primary payer (weighted)", "31.15%", "31.152% (p.116)"],
       ["Visits with no medications (weighted)", "20.94%", "20.943% (p.117)"],
       ["Weighted drug mentions", "340,550,921", "340,550,921 (p.118)"],
       ["BUN/creatinine test ordered", "6.67%", "6.7% (p.4)"],
       ["Length of visit / wait time missing", "7.0% / 15.2%", "7.0% / 15.7% (p.15)"]],
      [2.7, 1.4, 1.6], "Table 1. Our estimates reproduce every published NCHS figure we checked")

# ---------------------------------------------------------------- 2. descriptives
doc.add_heading("2. Who comes to the ED, and how long they stay (Q3)", level=1)
table([["Statistic", "Unweighted", "Weighted"],
       ["Age: mean / median (years; 93 = top-code \"93+\")", "37.6 / 34", "37.0 / 34"],
       ["Female / Hispanic (imputed ETHIM)", "55.1% / 15.9%", "55.4% / 16.5%"],
       ["Wait to see a provider: median (n = 17,153)", "19 min", "18 min"],
       ["Wait: mean, winsorized 99.5%", "39.5 min", "38.7 min"],
       ["Length of visit: mean raw / winsorized (n = 19,581)", "221.9 / 216.5 min", "213.7 / 209.8 min"],
       ["Length of visit: median", "154 min", "154 min"]],
      [3.6, 1.45, 1.45], "Table 2. Descriptive statistics, unweighted vs weighted")
para("**Patient flow.** The typical patient is a young adult (median age 34), and 55% of visits are by "
     "women. Half of patients see a provider within **18 minutes**, but the mean wait (39 minutes) is "
     "twice the median. Length of visit is similarly skewed (median **2.6 hours**, mean 3.5 hours): "
     "a minority of very long waits and stays (for example, patients boarding while they wait for an "
     "inpatient bed) consumes a disproportionate share of bed-hours. By Little's law (average patients "
     "in the ED = arrival rate x time spent there), 375,000 visits/day x 3.56 hours means about "
     "**55,700 patients are in U.S. EDs at any moment**, roughly 12 per ED across the country's "
     "4,820 EDs (codebook p.120). ED capacity is driven as much by throughput time as by arrivals.")
para("**Effect of weighting.** Weighting moves the headline numbers only slightly: mean age falls "
     "0.5 years, mean length of visit falls 8 minutes, and children rise from 18.6% to 19.8% of visits. "
     "That's because the weights shift toward the under-sampled South and toward children, who have "
     "shorter visits. Medians do not move. So the sample is broadly representative, but unweighted "
     "counts are meaningless for volume (21,061 vs 136.9 million), and small tilts compound in "
     "subgroup analysis. We therefore weight everything.")

# ---------------------------------------------------------------- 3. timing
doc.add_heading("3. When demand arrives (Q4)", level=1)
figure(["q4_arrivals_by_hour", "q4_visits_by_weekday"], 3.4,
       "Figure 1. Weighted ED arrivals by hour of day (left) and average visits per day by weekday (right)")
para("**Busiest days and times.** Because 2015 had 53 Thursdays, we compare weekdays as average visits "
     "per day. **Monday is busiest (432,000 visits/day)** and Sunday quietest (346,000), a 25% gap. "
     "Volume declines from Monday through Thursday. Arrivals bottom out between 3am and 6am (1.3-1.4% "
     "of daily arrivals per hour), climb steeply from 7am, and **plateau from 10am to 8pm**, peaking at "
     "**6pm (6.3%)**. The peak hour receives 4.7 times as many arrivals as the quietest, 69% of "
     "patients arrive between 10am and 10pm, and the single busiest slot is Monday 9-10am (about "
     "28,500 visits nationally).")
para("**Staffing implications.** Staff to a long daytime plateau rather than a single peak. Stagger shift "
     "starts through the 7-10am ramp, and keep full coverage until roughly midnight: a patient arriving "
     "at the 6pm peak stays a median 2.6 hours, so occupancy peaks later than arrivals do. Roster more "
     "heavily on Mondays and Tuesdays, consistent with pent-up weekend demand while doctors' offices "
     "are closed. Overnight volume runs at about a quarter of peak, which suits lean staffing and on-call "
     "coverage.")

# ---------------------------------------------------------------- 4. payer
doc.add_heading("4. Payer mix and financial exposure (Q5)", level=1)
para("PAYTYPER assigns each visit one primary expected payer using an NCHS hierarchy. Across all visits "
     "(weighted), **Medicaid/CHIP pays for 31.2%, private insurance 27.6%, Medicare 17.7% and self-pay "
     "9.0%**; for 10.8% the payer is blank or unknown. Among the 89.2% of visits with a known payer: "
     "**Medicaid 34.9%, private 30.9%, Medicare 19.9%, self-pay 10.1%**. Public payers together cover "
     "54.8%, and self-pay plus charity care cover 11.0%. Payer mix is driven by age (Figure 2): "
     "Medicaid pays for 65% of child visits, Medicare for 78-87% of visits by patients 65 and over, and "
     "self-pay peaks at 17.5% among 25-44-year-olds.")
para("**Financial performance.** More than half of ED revenue comes from public payers, which typically "
     "reimburse below private rates, and about 1 in 9 visits is uninsured or charity care. Federal law "
     "(EMTALA) requires EDs to screen and stabilize everyone regardless of ability to pay, so hospitals "
     "cannot turn this demand away. Privately insured visits (under a third) cross-subsidize the rest. "
     "The 10.8% of visits with an unknown payer point to a documentation and revenue-cycle gap. Young "
     "adults are the main bad-debt exposure, and an aging population will shift mix further toward "
     "Medicare.")
figure(["q5_payer_mix_by_age"], 4.6, "Figure 2. Primary expected payer by age group (weighted, known payer)")

# ---------------------------------------------------------------- 5. clinical
doc.add_heading("5. Clinical profile: chronic disease, injuries, diagnostics, medications (Q6-Q9)", level=1)
figure(["q6_chronic_condition_prevalence", "q8_blood_tests"], 3.4,
       "Figure 3. Most common chronic conditions (left) and blood tests ordered at blood-test visits (right), weighted")
para("**Chronic conditions (Q6).** Excluding the 1.6% of visits where the section was blank, **47.6% of "
     "visits involve at least one chronic condition** (48.5% unweighted) and 14.9% involve three or "
     "more. TOTCHRON matches the 22 individual checkboxes on 100% of visits. **Hypertension is most "
     "prevalent (24.0%)**, followed by asthma (10.0%) and depression (9.5%). Diabetes type 2 alone is "
     "4.7% and obesity 3.6%, but diabetes is split across three checkboxes: combined, **any diabetes "
     "covers 11.1%**, making it the second most common condition. Chronic burden rises from 13% of "
     "under-15 visits to 90% of visits by patients 75+. EDs are therefore a front line for chronic "
     "disease: many visits are flare-ups of conditions that primary care could manage. That argues "
     "for ED-based care coordination, follow-up referrals and medication reconciliation.")
para("**Injuries (Q7).** **33.1% of visits** (weighted) relate to an injury (29.5%), an overdose or "
     "poisoning (1.4%) or an adverse effect of medical care (2.2%). Intent is never recorded for "
     "adverse effects (the question is only asked for injuries and overdoses), and it's blank for 21% "
     "of injuries. **Among visits with known intent, 7.3% are intentional and 92.7% unintentional.** "
     "Intentional shares are highest for overdoses (13.2%) and patients aged 15-24 (12.1%).")
para("**Diagnostics (Q8).** **47.0% of visits include imaging** (X-ray 33.7%, CT 16.5%, ultrasound 4.4%, "
     "MRI 0.7%), rising from 29% for children to 70% for patients 75+, and from 44% of non-injury "
     "visits to 54% of injury visits. 42.4% of visits include a blood test. At those visits, "
     "**CBC is by far the most common (85.4%)**, followed by the comprehensive (55.3%) and basic "
     "(25.2%) metabolic panels, with 3.2 different tests per visit on average. Standalone glucose, "
     "BUN/creatinine and electrolytes are low because the panels already include them.")
para("**Medications (Q9).** The weighted **mean is 2.49 medications per visit and the median is 2**. "
     "**20.9% of visits involve none, 41.9% involve 1-2 and 37.2% involve 3 or more**, exactly matching "
     "NCHS (Table 1). On average 1.62 are given in the ED and 1.08 prescribed at discharge. Treatment "
     "intensity tracks complexity: 2.0 medications with no chronic condition vs 3.8 with three or more, "
     "peaking at 3.1 for ages 45-64. More than a third of visits are pharmacologically complex, which "
     "raises medication-safety and pharmacy-staffing needs.")

# ---------------------------------------------------------------- 6. correlations
doc.add_heading("6. Correlations and outcomes (Q10)", level=1)
para("We built about 20 cleaned variables (codes set to missing, wait and length of visit winsorized) "
     "and computed **weighted** Pearson correlations using rows where both variables are present. "
     "Triage level runs from 1 = immediate to 5 = nonurgent, so a negative r means \"more for "
     "urgent patients\".")
table([["Pair", "Weighted r", "Reading"],
       ["Age - Medicare", "0.61", "Mechanical: Medicare eligibility starts at 65"],
       ["Age - # chronic conditions", "0.55", "Chronic burden accumulates with age"],
       ["# blood tests - admitted", "0.37", "Workup intensity signals severity"],
       ["Triage level - # blood tests", "-0.35", "Urgent patients get more tests"],
       ["# chronic conditions - admitted", "0.33", "Complex patients are admitted more"],
       ["Length of visit - # blood tests", "0.31", "Diagnostics lengthen stays"],
       ["Wait - length of visit", "0.28", "Front-end delays carry through"],
       ["Arrived by ambulance - admitted", "0.24", "Ambulance arrivals are sicker"],
       ["Sex, ethnicity, pain - any outcome", "about 0", "No meaningful association"]],
      [2.5, 0.9, 3.1], "Table 3. Selected weighted correlations")
figure(["q10_triage_admission_and_wait"], 6.3,
       "Figure 4. Admission rate (left) and median wait (right) by triage level, weighted")
para("**Outcomes.** Deaths are too rare for correlations to capture: only 28 sampled visits died in the "
     "ED (0.10% weighted), 7 were dead on arrival (0.04%), and 40 of 1,752 admitted patients died in "
     "hospital (2.6%). Their correlations are near zero even where the relationship is strong, so we "
     "compare rates across groups instead. By triage level, the admission rate falls from **33% "
     "(immediate) to 2-3% (semi- and nonurgent)**, **6.4% of immediate patients die in the ED**, and "
     "41% of them arrive by ambulance. By age, admission rises from 2.5% (under 15) to 29.1% (75+). "
     "The operational surprise: **median waits are 14 minutes for immediate patients but 18-20 minutes "
     "for every other level**, so triage fast-tracks only the sickest, and emergent patients wait as "
     "long as nonurgent ones. These are associations, not causal effects: age simultaneously drives "
     "chronic burden, payer and treatment intensity.")

# ---------------------------------------------------------------- 7. takeaways
doc.add_heading("7. Implications for hospital management, and limitations", level=1)
bullet("**Capacity:** staff to a 10am-8pm plateau with a Monday premium. Throughput time (a median "
       "2.6-hour stay with a long tail) is as important a capacity lever as arrival volume.")
bullet("**Triage and flow:** emergent (level 2) patients wait as long as nonurgent ones. A fast track "
       "for levels 4-5 could free provider time for level 2-3 patients.")
bullet("**Finance:** 55% public payers and 11% uninsured or charity. Accurate payer capture (10.8% "
       "unknown) and Medicaid contracting matter for margins.")
bullet("**Chronic care:** nearly half of visits involve chronic disease. Care coordination and follow-up "
       "could shift avoidable visits to cheaper settings.")
bullet("**Limitations:** these are weighted point estimates without survey-design standard errors "
       "(CSTRATM/CPSUM; NCHS advises testing at the 1% level). Wait-time missingness is not random. "
       "Chronic conditions such as obesity are likely under-recorded, and the 2015 form changes limit "
       "comparisons with earlier years.")

para("**AI use.** As the course requires, we used AI throughout. The analysis code was written with "
     "Claude (Anthropic) through Claude Code, directed by the group question by question. We ran every "
     "step ourselves on the Yale HPC cluster, reviewed each output before moving on, and verified results "
     "against published NCHS figures (20 of 20 checks pass). This write-up and the slides were drafted "
     "with AI assistance from those verified outputs, then reviewed and edited by the group.",
     size=9, color=GREY)

# Save in modern Word format (avoid "Compatibility Mode")
compat = doc.settings.element.find(qn("w:compat"))
if compat is None:
    compat = OxmlElement("w:compat")
    doc.settings.element.append(compat)
cs = OxmlElement("w:compatSetting")
for k, v in [("name", "compatibilityMode"), ("uri", "http://schemas.microsoft.com/office/word"), ("val", "15")]:
    cs.set(qn("w:" + k), v)
compat.append(cs)
doc.save(OUT)
print("saved", OUT)
