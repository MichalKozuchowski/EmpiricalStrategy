"""Build the HW1 slide deck (5 slides) from the verified results in hw1/results_log.md."""
import sys
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

HW1 = r"C:\Users\mnich\OneDrive\Documents\Second Year\EmpiricalStrategy\hw1"
OUT = sys.argv[1] if len(sys.argv) > 1 else HW1 + r"\report\MGT634_HW1_NHAMCS_slides.pptx"

NAVY = RGBColor(0x16, 0x32, 0x4F)     # dominant: title/closing backgrounds, headings
BLUE = RGBColor(0x2A, 0x78, 0xD6)     # data
CORAL = RGBColor(0xEB, 0x68, 0x34)    # accent: the one number that matters
TINT = RGBColor(0xEC, 0xF1, 0xF7)     # card background
INK = RGBColor(0x1A, 0x1A, 0x1A)
SOFT = RGBColor(0x5A, 0x5F, 0x66)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ICE = RGBColor(0xCA, 0xDC, 0xFC)
PAYER_COLOURS = [BLUE, CORAL, RGBColor(0x1B, 0xAF, 0x7A), RGBColor(0xED, 0xA1, 0x00),
                 RGBColor(0xE8, 0x7B, 0xA4)]

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def bg(slide, colour):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = colour


def text(slide, x, y, w, h, content, size=16, colour=INK, bold=False, font="Calibri",
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False):
    """Text box; `content` may be a list of (text, size, colour, bold) tuples, one per paragraph."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ["margin_left", "margin_right", "margin_top", "margin_bottom"]:
        setattr(tf, side, 0)
    items = content if isinstance(content, list) else [(content, size, colour, bold)]
    for i, (t, s, c, b) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(6)
        r = p.add_run()
        r.text = t
        r.font.size, r.font.color.rgb, r.font.bold, r.font.name = Pt(s), c, b, font
        r.font.italic = italic
    return tb


def card(slide, x, y, w, h, fill=TINT):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.adjustments[0] = 0.08
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def stat(slide, x, y, w, number, label, num_colour=NAVY, fill=TINT, label_colour=SOFT, h=1.55):
    card(slide, x, y, w, h, fill)
    text(slide, x + 0.25, y + 0.18, w - 0.5, 0.75, number, 34, num_colour, True, "Cambria")
    text(slide, x + 0.25, y + 0.92, w - 0.5, h - 1.0, label, 12.5, label_colour)


def title(slide, t, sub=None, colour=NAVY):
    text(slide, 0.6, 0.4, 12.1, 0.8, t, 30, colour, True, "Cambria")
    if sub:
        text(slide, 0.6, 1.12, 12.1, 0.45, sub, 15, SOFT)


def style_chart(chart, legend=False, font_size=11):
    chart.font.size, chart.font.name = Pt(font_size), "Calibri"
    chart.font.color.rgb = SOFT
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
    va = chart.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = RGBColor(0xE3, 0xE3, 0xE0)
    va.format.line.fill.background()
    chart.category_axis.format.line.color.rgb = RGBColor(0xBB, 0xBB, 0xBB)
    chart.category_axis.has_major_gridlines = False


def label_font(dl, size, colour, bold=True):
    """Custom data-label text ignores dl.font - style the run itself."""
    r = dl.text_frame.paragraphs[0].runs[0]
    r.font.size, r.font.bold, r.font.name = Pt(size), bold, "Calibri"
    r.font.color.rgb = colour


def notes(slide, t):
    slide.notes_slide.notes_text_frame.text = t


# ============================================================ 1. title + approach
s = prs.slides.add_slide(BLANK)
bg(s, NAVY)
text(s, 0.6, 0.55, 12, 0.4, "MGT 634 · HOMEWORK 1 · NHAMCS EMERGENCY DEPARTMENT DATA, 2015", 13, ICE, True)
text(s, 0.6, 0.95, 12, 1.4, "137 million ED visits: what a national sample tells hospital managers",
     36, WHITE, True, "Cambria")
text(s, 0.6, 2.2, 12, 0.4, "Group: Michal Kozuchowski, [add teammate names]", 14, ICE)
dark_card = RGBColor(0x22, 0x46, 0x6C)
for i, (n, l) in enumerate([("21,061", "sampled visits (rows) from 248 EDs, 1,031 variables"),
                            ("136.9M", "U.S. ED visits once weighted by PATWT, exactly the NCHS total"),
                            ("-9 / -8 / -7", "blank / unknown / N/A codes, hidden missing data we removed"),
                            ("20 / 20", "checks against published NCHS figures pass")]):
    stat(s, 0.6 + i * 3.1, 3.05, 2.85, n, l, num_colour=WHITE, fill=dark_card, label_colour=ICE, h=1.75)
text(s, 0.6, 5.2, 12.1, 1.8, [
    ("Approach", 15, WHITE, True),
    ("Load → recode missing-value codes → weight every estimate → cap extreme waits and stays at the "
     "99.5th percentile → check each result against the codebook. One commented notebook, one cell "
     "per question, re-run cleanly end to end.", 14, ICE, False)])
notes(s, "Each row is one sampled ED visit, not a patient. The main data-quality trap: NCHS stores "
         "missing answers as negative codes, so df.isna() misses them. We verified our reading by "
         "reproducing NCHS's published nonresponse rates (LOV 7.0%, PAYTYPER 8.7%, IMMEDR 22.2%). "
         "Missingness is not random: wait time is missing 38-45% of the time when there was no "
         "triage, vs ~10% otherwise.")

# ============================================================ 2. demand timing
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "Demand is predictable: 10am-8pm plateau, Monday peak",
      "Weighted share of daily ED arrivals by hour of arrival, 2015")
cd = CategoryChartData()
cd.categories = [str(h) for h in range(24)]
hours = [2.20, 1.83, 1.62, 1.42, 1.36, 1.34, 1.76, 2.64, 3.59, 5.06, 6.05, 5.75, 6.08, 5.66,
         5.80, 5.61, 5.65, 5.77, 6.34, 5.90, 5.46, 5.00, 4.64, 3.46]
cd.add_series("% of daily arrivals", hours)
ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.5), Inches(1.7), Inches(8.3),
                        Inches(5.2), cd).chart
style_chart(ch)
plot = ch.plots[0]
plot.gap_width = 40
ser = plot.series[0]
ser.format.fill.solid()
ser.format.fill.fore_color.rgb = BLUE
pt = ser.points[18]                       # 6pm peak highlighted
pt.format.fill.solid()
pt.format.fill.fore_color.rgb = CORAL
pt.data_label.has_text_frame = True
pt.data_label.text_frame.text = "6pm peak: 6.3%"
label_font(pt.data_label, 12, CORAL)
pt.data_label.position = XL_LABEL_POSITION.OUTSIDE_END
pt.data_label.font.size, pt.data_label.font.bold = Pt(11), True
pt.data_label.font.color.rgb = CORAL
pt.data_label.font.name = "Calibri"
ch.value_axis.maximum_scale = 7.5
ch.value_axis.minimum_scale = 0
ch.has_title = False
ch.value_axis.tick_labels.number_format = '0"%"'
ch.value_axis.tick_labels.number_format_is_linked = False
ch.category_axis.has_title = True
ch.category_axis.axis_title.text_frame.text = "Arrival hour (0 = midnight)"
ch.category_axis.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
stat(s, 9.2, 1.75, 3.6, "4.7x", "arrivals in the 6pm peak hour vs the 5am trough")
stat(s, 9.2, 3.5, 3.6, "+25%", "Monday (432k visits/day) vs Sunday (346k), average per day")
card(s, 9.2, 5.25, 3.6, 1.65)
text(s, 9.45, 5.4, 3.1, 1.4, [("Staffing", 13, NAVY, True),
                              ("Stagger shifts through the 7-10am ramp, keep full coverage to ~midnight "
                               "(median stay 2.6 h), and roster heavier on Mondays.", 12, INK, False)])
notes(s, "Weekdays are compared as average visits per day because 2015 had 53 Thursdays. 69% of "
         "arrivals come between 10am and 10pm; the single busiest slot is Monday 9-10am (~28,500 "
         "visits nationally). By Little's law, ~55,700 patients are in U.S. EDs at any moment, "
         "about 12 per ED.")

# ============================================================ 3. payer mix
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "Public payers fund most ED visits, and age decides who pays",
      "Primary expected payer by age group, weighted % of visits with a known payer")
cd = CategoryChartData()
cd.categories = ["Under 15", "15-24", "25-44", "45-64", "65-74", "75+"]
mix = {"Medicaid/CHIP": [65.2, 40.8, 34.9, 26.0, 6.0, 3.3],
       "Private": [27.2, 37.7, 34.7, 41.4, 10.8, 7.9],
       "Medicare": [1.1, 2.5, 6.8, 18.0, 78.3, 86.9],
       "Self-pay": [4.7, 14.2, 17.5, 9.5, 2.3, 0.4],
       "Other": [1.9, 4.7, 6.1, 5.2, 2.6, 1.5]}
for k, v in mix.items():
    cd.add_series(k, v)
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_STACKED_100, Inches(0.5), Inches(1.7), Inches(8.3),
                        Inches(5.3), cd)
ch = gf.chart
style_chart(ch, legend=True)
ch.plots[0].gap_width = 45
ch.plots[0].overlap = 100
ch.category_axis.reverse_order = True     # youngest at the top
ch.value_axis.tick_labels.number_format = '0%'
ch.value_axis.tick_labels.number_format_is_linked = False
for ser, colour in zip(ch.plots[0].series, PAYER_COLOURS):
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = colour
    ser.format.line.color.rgb = WHITE
for idx, name in [(0, "Medicaid/CHIP"), (2, "Medicare")]:   # label only the two public payers
    ser = ch.plots[0].series[idx]
    for j, v in enumerate(mix[name]):
        if v >= 5:                                              # skip thin slivers
            dl = ser.points[j].data_label
            dl.has_text_frame = True
            dl.text_frame.text = f"{v:.0f}%"
            label_font(dl, 11, WHITE)
            dl.position = XL_LABEL_POSITION.CENTER
            dl.font.size, dl.font.bold, dl.font.name = Pt(10), True, "Calibri"
            dl.font.color.rgb = WHITE
stat(s, 9.2, 1.75, 3.6, "54.8%", "of known-payer visits paid by Medicaid (34.9%) or Medicare (19.9%)")
stat(s, 9.2, 3.5, 3.6, "11.0%", "self-pay or charity care; EDs must treat regardless (EMTALA)",
     num_colour=CORAL)
card(s, 9.2, 5.25, 3.6, 1.65)
text(s, 9.45, 5.4, 3.1, 1.4, [("Margin pressure", 13, NAVY, True),
                              ("Private insurance (30.9%) cross-subsidizes. 10.8% of visits have no "
                               "recorded payer, a revenue-cycle gap.", 12, INK, False)])
notes(s, "PAYTYPER uses an NCHS hierarchy to pick one primary payer per visit; our shares match the "
         "codebook exactly (Medicaid 31.15% of all visits). Self-pay peaks at 17.5% among "
         "25-44-year-olds, the main bad-debt exposure.")

# ============================================================ 4. clinical profile
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "EDs treat complex patients: chronic disease and injuries")
for i, (n, l, c) in enumerate([("47.6%", "visits with 1+ chronic condition (90% at 75+)", NAVY),
                               ("33.1%", "injury, overdose or adverse-effect visits (7.3% intentional)", NAVY),
                               ("47.0%", "visits with imaging; 42.4% with a blood test (CBC in 85%)", NAVY),
                               ("37.2%", "visits with 3+ medications (mean 2.49, median 2)", CORAL)]):
    stat(s, 0.6 + i * 3.1, 1.35, 2.85, n, l, num_colour=c, h=1.6)
cd = CategoryChartData()
cond = [("Hypertension", 23.97), ("Any diabetes", 11.06), ("Asthma", 9.98), ("Depression", 9.45),
        ("Hyperlipidemia", 8.17), ("Substance abuse", 6.65), ("Coronary artery disease", 6.08),
        ("COPD", 5.37)]
cd.categories = [c for c, _ in cond]
cd.add_series("% of visits", [v for _, v in cond])
ch = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(3.25), Inches(8.3),
                        Inches(3.85), cd).chart
style_chart(ch)
ch.has_title = True
ch.chart_title.text_frame.text = "Most common chronic conditions (% of ED visits, weighted)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(13)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.color.rgb = NAVY
ch.category_axis.reverse_order = True
ch.plots[0].gap_width = 45
ser = ch.plots[0].series[0]
ser.format.fill.solid()
ser.format.fill.fore_color.rgb = BLUE
ser.data_labels.show_value = True
ser.data_labels.number_format = '0.0"%"'
ser.data_labels.number_format_is_linked = False
ser.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
ser.data_labels.font.size = Pt(10)
ch.value_axis.visible = False
ch.value_axis.has_major_gridlines = False
card(s, 9.2, 3.4, 3.6, 3.6)
text(s, 9.45, 3.6, 3.1, 3.3, [
    ("What it means", 13, NAVY, True),
    ("EDs act as a front line for chronic disease: care coordination and follow-up referrals could "
     "move avoidable visits to cheaper settings.", 12, INK, False),
    ("Diabetes is split across three checkboxes; combined it is the #2 condition, not #9.",
     12, INK, False),
    ("Intensity follows complexity: imaging rises from 29% of child visits to 70% at 75+, and "
     "medications from 2.0 per visit (no chronic condition) to 3.8 (three or more).", 12, INK, False)])
notes(s, "Chronic burden rises from 13% of under-15 visits to 90% at 75+. Imaging rises from 29% "
         "(children) to 70% (75+). Medications rise from 2.0 per visit with no chronic condition to "
         "3.8 with three or more. Totals match NCHS: 340.6M weighted drug mentions.")

# ============================================================ 5. triage + takeaways
s = prs.slides.add_slide(BLANK)
bg(s, NAVY)
text(s, 0.6, 0.4, 12.1, 0.8, "Triage sorts outcomes sharply, but not waiting times", 30, WHITE, True,
     "Cambria")
text(s, 0.6, 1.12, 12.1, 0.45, "Weighted, by triage level (1 = immediate ... 5 = nonurgent)", 15, ICE)
levels = ["1 Immediate", "2 Emergent", "3 Urgent", "4 Semi-urgent", "5 Nonurgent"]
for k, (vals, ttl, fmt, colour) in enumerate([
        ([33.34, 25.03, 11.40, 2.28, 2.53], "Admitted to hospital (%)", '0"%"', ICE),
        ([14, 18, 20, 19, 18], "Median wait to see a provider (min)", "0", CORAL)]):
    cd = CategoryChartData()
    cd.categories = levels
    cd.add_series(ttl, vals)
    x = 0.5 + k * 4.2
    card(s, x, 1.75, 4.0, 3.55, RGBColor(0x22, 0x46, 0x6C))
    ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x + 0.1), Inches(1.85),
                            Inches(3.8), Inches(3.35), cd).chart
    style_chart(ch, font_size=9)
    ch.font.color.rgb = ICE
    ch.has_title = True
    ch.chart_title.text_frame.text = ttl
    ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(12)
    ch.chart_title.text_frame.paragraphs[0].runs[0].font.color.rgb = WHITE
    ch.value_axis.visible = False
    ch.value_axis.has_major_gridlines = False
    ch.plots[0].gap_width = 50
    ser = ch.plots[0].series[0]
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = colour
    ser.data_labels.show_value = True
    ser.data_labels.number_format = fmt
    ser.data_labels.number_format_is_linked = False
    ser.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    ser.data_labels.font.size, ser.data_labels.font.bold = Pt(11), True
    ser.data_labels.font.color.rgb = WHITE
text(s, 9.0, 1.75, 3.8, 3.6, [
    ("Correlations (weighted r)", 14, WHITE, True),
    ("# blood tests - admitted  0.37", 12.5, ICE, False),
    ("# chronic conditions - admitted  0.33", 12.5, ICE, False),
    ("Length of visit - # blood tests  0.31", 12.5, ICE, False),
    ("Age - Medicare  0.61 (eligibility at 65)", 12.5, ICE, False),
    ("Deaths are rare (28 in ED, 7 DOA in sample), so we compare rates: 6.4% of immediate "
     "patients die in the ED.", 12.5, ICE, False)])
text(s, 0.6, 5.6, 12.1, 1.6, [
    ("Takeaways for hospital managers", 15, WHITE, True),
    ("Staff to the plateau and Mondays  ·  Fast-track levels 4-5 so emergent patients stop waiting "
     "as long as nonurgent ones  ·  Protect margins through Medicaid contracting and payer capture  "
     "·  Invest in chronic-care coordination", 13.5, ICE, False)])
notes(s, "Admission falls from 33% for immediate patients to 2-3% for semi- and nonurgent, but "
         "median waits are 14 minutes for immediate and 18-20 for every other level. Correlations "
         "are associations, not causal effects; age drives chronic burden, payer and treatment "
         "intensity together. Limitations: point estimates without survey-design standard errors.")

prs.save(OUT)
print("saved", OUT)
