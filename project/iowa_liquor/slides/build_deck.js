// build_deck.js: builds slides/Iowa_Liquor_Final.pptx from the figures in ../output (pptxgenjs).
// Run from project/iowa_liquor:   node slides/build_deck.js        (needs: npm install pptxgenjs)
// Every number on a slide comes from output/*.md (see the comment next to it).
const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.join(__dirname, "..", "output");
const FIG = (f) => path.join(OUT, f);
const DECK = path.join(__dirname, "Iowa_Liquor_Final.pptx");

// ---------- theme: oak brown + amber (whiskey), rust and blue match the matplotlib figures ----------
const THEME = {
  name: "Iowa Liquor",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F1A17", lt1: "FFFFFF", dk2: "3B2A20", lt2: "F3EFEB",
    accent1: "C8811A", accent2: "993F2A", accent3: "2B6CB0", accent4: "6B7F5E", accent5: "8C7B6B", accent6: "BBBBBB",
    hlink: "2B6CB0", folHlink: "993F2A",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                              // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Who pays when Iowa's liquor costs change?";
pres.subject = "MGT 634 final project";
const C = pres.SchemeColor;
const W = 13.333, M = 0.6;                                // slide width, side margin

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "DARK",
  background: { color: HEX.dk2 },
  objects: [],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.lt1 },
  margin: [0.5, 0.6, 0.5, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.35, w: W - 2 * M, h: 1.05, fontFace: THEME.headFontFace,
        fontSize: 30, bold: true, color: C.text2, align: "left", valign: "top", margin: 0 }, text: "" } },
    { text: { text: "Iowa liquor  |  MGT 634 final project", options: { x: M, y: 7.05, w: 6, h: 0.3, fontSize: 10, color: HEX.accent5, margin: 0 } } },
  ],
  slideNumber: { x: W - M - 0.6, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: HEX.accent5, align: "right" },
});

// ---------- helpers ----------
let sectionNow = "";
function section(t) { pres.addSection({ title: t }); sectionNow = t; }
function content(title) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: sectionNow });
  s.addText(title, { placeholder: "title" });
  return s;
}
// small amber circle with a number or symbol (the deck's motif)
function badge(s, x, y, txt, d = 0.46, fill = C.accent1, fs = 14) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: "badge " + txt });
  s.addText(txt, { x, y, w: d, h: d, align: "center", valign: "middle", fontSize: fs, bold: true, color: C.background1, margin: 0, isTextBox: true });
}
// tinted card with a big number and a label
function statCard(s, x, y, w, h, big, label, color = C.accent2, bigSize = 40) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: "card " + big });
  s.addText(big, { x: x + 0.25, y: y + 0.15, w: w - 0.5, h: h * 0.45, fontFace: THEME.headFontFace, fontSize: bigSize, bold: true, color, margin: 0, valign: "bottom", isTextBox: true });
  s.addText(label, { x: x + 0.25, y: y + 0.2 + h * 0.45, w: w - 0.5, h: h * 0.55 - 0.35, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true });
}
function card(s, x, y, w, h, head, body, headColor = C.text2) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: "card " + head });
  s.addText([{ text: head, options: { bold: true, color: headColor, fontSize: 15, breakLine: true } },
             { text: body, options: { fontSize: 14, color: C.text1 } }],
            { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: h - 0.24, valign: "top", margin: 0, paraSpaceAfter: 4, isTextBox: true });
}
function bullets(s, items, x, y, w, h, size = 15) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
            { x, y, w, h, fontSize: size, color: C.text1, valign: "top", paraSpaceAfter: 8, margin: 0, isTextBox: true });
}
function caption(s, txt, x, y, w) {
  s.addText(txt, { x, y, w, h: 0.35, fontSize: 11, italic: true, color: C.accent5, margin: 0, isTextBox: true });
}
const CHART_TXT = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
                    legendFontFace: "+mn-lt", titleFontFace: "+mn-lt", catAxisLabelColor: HEX.dk1, valAxisLabelColor: HEX.accent5,
                    catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, dataLabelFontSize: 12, dataLabelColor: HEX.dk1 };

// =====================================================================================================
section("Question");
// 1. title
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: sectionNow });
  badge(s, M, 1.2, "1.5×", 1.1, C.accent1, 26);
  s.addText("Who pays when Iowa's liquor costs change?", { x: M, y: 2.55, w: 11.5, h: 1.3, fontFace: THEME.headFontFace, fontSize: 44, bold: true, color: C.background1, margin: 0, isTextBox: true });
  s.addText("Tariff pass-through, demand and a minimum price in a state liquor monopoly",
            { x: M, y: 3.85, w: 11.5, h: 0.6, fontSize: 22, color: C.accent1, margin: 0, isTextBox: true });
  s.addText("MGT 634 Empirical Strategy with AI  |  Final project  |  December 2026",
            { x: M, y: 6.3, w: 11.5, h: 0.4, fontSize: 14, color: C.background2, margin: 0, isTextBox: true });
  s.addNotes("Opening (about 30 seconds). Iowa is one of 17 control states: the state itself is the only wholesaler of spirits. " +
             "We ask who pays when costs change, using tariffs as natural experiments, and what that means for a minimum-price bill.");
}
// 2. setting + questions
{
  const s = content("Iowa buys every bottle and resells it to stores at 1.5× cost");
  const boxes = [["Suppliers", "Diageo, Sazerac, Pernod, Bacardi...\nset their price c"],
                 ["Iowa ABD (the state)", "sole wholesaler\nprice = 1.5 × c, same statewide"],
                 ["~2,200 stores", "groceries, liquor and convenience stores; set their own shelf markup"],
                 ["Drinkers", "~22M liters a year"]];
  const bw = 2.75, gap = 0.37, y = 1.65;
  boxes.forEach(([h, b], i) => {
    const x = M + i * (bw + gap);
    const fill = i === 1 ? C.accent1 : C.background2, tc = i === 1 ? C.background1 : C.text1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: bw, h: 1.55, rectRadius: 0.08, fill: { color: fill }, line: { color: fill }, objectName: "flow " + h });
    s.addText([{ text: h, options: { bold: true, fontSize: 16, breakLine: true } }, { text: b, options: { fontSize: 13 } }],
              { x: x + 0.15, y: y + 0.1, w: bw - 0.3, h: 1.35, color: tc, valign: "middle", margin: 0, isTextBox: true });
    if (i < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + bw + 0.05, y: y + 0.6, w: gap - 0.1, h: 0.35, fill: { color: C.accent5 }, line: { color: C.accent5 }, objectName: "arrow " + i });
  });
  s.addText("Two decisions for Iowa's legislature and its Alcoholic Beverages Division", { x: M, y: 3.6, w: 12, h: 0.45, fontSize: 18, bold: true, color: C.text2, margin: 0, isTextBox: true });
  badge(s, M, 4.25, "1");
  s.addText([{ text: "When costs rise, who pays: suppliers, the state or drinkers? ", options: { bold: true } },
             { text: "Two tariff shocks hit imported spirits: 25% in 2019 and 10–15% in 2025–26. Because the markup is a percentage, Iowa multiplies any cost increase that reaches it." }],
            { x: M + 0.65, y: 4.18, w: 11.4, h: 1.0, fontSize: 15, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  badge(s, M, 5.25, "2");
  s.addText([{ text: "Should Iowa set a minimum price per unit of alcohol? ", options: { bold: true } },
             { text: "Bill HF 830 (2025) would price every bottle at 1.5 × max(supplier price, $0.50 per 18 ml of alcohol). What happens to drinking, revenue, and who gets the money?" }],
            { x: M + 0.65, y: 5.18, w: 11.4, h: 1.0, fontSize: 15, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  s.addNotes("Iowa Code 123.24: state price = supplier cost plus 50%, uniform across the state. " +
             "The state does not set shelf prices; stores add their own markup. Our data are the state's sales to stores, which is exactly the level the state controls.");
}
// 3. answer up front
{
  const s = content("The answer up front: suppliers decide who pays");
  const cw = 3.85, g = 0.38, y = 1.6, h = 2.6;
  statCard(s, M, y, cw, h, "45%", "of the 2019 tariff reached Iowa's supplier price, which Iowa then marked up by 50%");
  statCard(s, M + cw + g, y, cw, h, "≈ 0%", "of the 2025–26 tariffs reached Iowa prices. Suppliers absorbed them", C.accent3);
  statCard(s, M + 2 * (cw + g), y, cw, h, "$27–53M", "a year to suppliers under HF 830, if they raise their price up to the floor (as the formula allows)", C.accent2, 40);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: 4.6, w: W - 2 * M, h: 1.75, rectRadius: 0.08, fill: { color: C.text2 }, line: { color: C.text2 }, objectName: "recommendation" });
  s.addText([{ text: "Recommendation  ", options: { bold: true, color: C.accent1, fontSize: 18 } },
             { text: "If Iowa wants less heavy drinking, charge the markup per liter of alcohol instead of per dollar. " +
                     "At the same state revenue, pure alcohol falls 1–7%, and there is no floor for suppliers to price up to.", options: { color: C.background1, fontSize: 17 } }],
            { x: M + 0.3, y: 4.75, w: W - 2 * M - 0.6, h: 1.45, valign: "middle", margin: 0, isTextBox: true });
  s.addNotes("Three numbers to remember. Sources: output/customs_passthrough.md (45%), output/tariff2025_results.md (about 0), " +
             "output/counterfactuals.md (A2 supplier gain $27-53M at elasticity -0.63). Recommendation from 09 policy B.");
}
// 4. data + identification
section("Data and methods");
{
  const s = content("Data: every bottle Iowa sold to stores, 2018–2026");
  const cw = 2.85, g = 0.3, y = 1.6, h = 1.55;
  // descriptives.md: bottles 2018-2026 sum = 261.6M; items.parquet 12,374; state margin 2025 = $141.7M; order lines ~2.5M/yr
  statCard(s, M, y, cw, h, "262M", "bottles in 22M order lines", C.accent2, 30);
  statCard(s, M + (cw + g), y, cw, h, "12,374", "products (item × bottle size)", C.accent2, 30);
  statCard(s, M, y + h + g, cw, h, "$142M", "state margin in 2025", C.accent2, 30);
  statCard(s, M + (cw + g), y + h + g, cw, h, "+2 sources", "price list; Census customs", C.accent2, 30);
  const x2 = M + 2 * (cw + g) + 0.25;
  s.addText("Data work that changed the answers", { x: x2, y: 1.6, w: W - x2 - M, h: 0.4, fontSize: 17, bold: true, color: C.text2, margin: 0, isTextBox: true });
  bullets(s, ["The portal repeats order lines: about 0.5M duplicates a year in 2020–22 and 518k in 2025. Removing them shrinks the \"COVID spike\" from +34% to +11%",
              "Prices are uniform statewide (0.03% of item-days differ), so there is no geographic price variation",
              "Prices change rarely (about 3% of items a month), so we identify effects from changes over time and tariff shocks",
              "Each brand coded to its country of origin, so tariff exposure is by product, not by category"],
          x2, 2.1, W - x2 - M, 3.2, 14);
  const ms = [["DiD / event studies", "2 tariffs, own price changes"], ["IV / 2SLS", "nested logit instruments"],
              ["Logit demand", "Berry inversion, elasticities"], ["Policy simulation", "HF 830, alcohol markup"]];
  const mw = (W - 2 * M - 3 * 0.25) / 4;
  ms.forEach(([h1, b1], i) => {
    const x = M + i * (mw + 0.25);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 5.3, w: mw, h: 1.15, rectRadius: 0.08, fill: { color: C.text2 }, line: { color: C.text2 }, objectName: "method " + h1 });
    s.addText([{ text: h1, options: { bold: true, color: C.accent1, fontSize: 15, breakLine: true } }, { text: b1, options: { color: C.background1, fontSize: 13 } }],
              { x: x + 0.2, y: 5.35, w: mw - 0.4, h: 1.05, valign: "middle", margin: 0, isTextBox: true });
  });
  s.addNotes("Source: Iowa Liquor Sales (Iowa Dept. of Revenue, open data), one file per year, about 550 MB each; built with DuckDB. " +
             "Duplicates: exact copies of order lines (before Jul 2025 invoice_id is unique per line, so an exact copy can't be a real order). " +
             "Methods are all from the second half of the course: event studies (class 14), IV (class 15), logit/nested logit (classes 18-20).");
}
// 5. 2019 event study
section("Tariffs");
{
  const s = content("2019: a 25% tariff raised Iowa prices 5%, and they stayed up");
  s.addImage({ path: FIG("fig_tariff2019_event_study.png"), x: M, y: 1.45, w: 12.1, h: 12.1 / 2.907, altText: "Event study of 2019 tariffs on Iowa prices and bottles" });
  const y = 5.75, cw = (W - 2 * M - 2 * 0.3) / 3;
  [["+5.2% single malt, +6.3% liqueurs", "vs untariffed whiskies and US liqueurs; item + month fixed effects, $-weighted"],
   ["Placebo: Irish whiskey ≈ 0", "EU product the tariff did not cover: no jump"],
   ["No reversal", "prices stayed up after the March 2021 suspension; bottles: no detectable change"]].forEach(([h1, b1], i) =>
    card(s, M + i * (cw + 0.3), y, cw, 1.1, h1, b1));
  s.addNotes("Design: item x month DiD and quarterly event study, SE clustered by item, $-weighted by pre-period sales, regular-price items ($1-150). " +
             "Treated: 97 single malts vs 582 untariffed whiskies; 61 covered liqueurs (DE/IE/IT/ES/UK brands) vs 235 US liqueurs. " +
             "The jump comes one quarter after Oct 2019, matching Iowa's quarterly price reviews. Source: output/tariff2019_results.md.");
}
// 6. pass-through
{
  const s = content("Half the 2019 tariff reached Iowa, then Iowa added 50%");
  // customs_passthrough.md: duty $3.43, supplier cost +$1.55, Iowa price +$2.32, state margin +$0.77 per 750 ml 86-proof bottle
  s.addChart(pres.charts.BAR, [{ name: "$ per bottle", labels: ["Tariff paid at the border", "Rise in Iowa's supplier price", "Rise in Iowa's price (× 1.5)", "of which: extra state margin"],
                                 values: [3.43, 1.55, 2.32, 0.77] }],
    Object.assign({ x: M, y: 1.5, w: 6.6, h: 4.9, barDir: "bar", catAxisOrientation: "maxMin", showValue: true, dataLabelPosition: "outEnd",
      dataLabelFormatCode: "$0.00", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
      chartColors: [HEX.dk1, HEX.accent2, HEX.accent1, HEX.accent5], showLegend: false, barGapWidthPct: 45,
      showTitle: true, title: "Single-malt Scotch, $ per 750 ml bottle (86 proof)", titleFontSize: 13, titleColor: HEX.dk2 }, CHART_TXT));
  const x2 = 7.6;
  s.addText("How we measured it", { x: x2, y: 1.55, w: W - x2 - M, h: 0.4, fontSize: 17, bold: true, color: C.text2, margin: 0, isTextBox: true });
  bullets(s, ["The tariff is charged on the customs value, not on Iowa's price, so we need that value",
              "Only single malt paid the duty. Census import records split by duty status therefore give its customs value: $21.72 per proof liter, about half of Iowa's supplier cost",
              "Pass-through = rise in supplier cost ÷ duty paid"],
          x2, 2.05, W - x2 - M, 2.6, 14);
  statCard(s, x2, 4.75, 2.45, 1.65, "45%", "single malt\n95% CI 30–61%", C.accent2, 32);
  statCard(s, x2 + 2.65, 4.75, 2.45, 1.65, "49%", "liqueurs\n95% CI 12–86%", C.accent3, 32);
  s.addNotes("Census International Trade API, HS 2208.30.3030 (Scotch and Irish whisky, up to 4 L) from the UK. Rate provision 69 = dutiable under Chapter 99: " +
             "duty / value = 24.5%, so these lines are the single malts. Liqueurs: HS 2208.70.0030 from DE, IE, IT, ES, UK. " +
             "The other half was absorbed by exporters and importers. Because Iowa's markup is a percentage, the state earned $0.77 a bottle more from the tariff. " +
             "Caveat: US-wide customs values; Iowa's single-malt mix may differ. Source: output/customs_passthrough.md.");
}
// 7. 2025
{
  const s = content("2025–26: 10–15% tariffs, and no change in Iowa prices");
  s.addImage({ path: FIG("fig_tariff2025_event_study.png"), x: M, y: 1.45, w: 12.1, h: 12.1 / 2.935, altText: "Event study of 2025-26 tariffs" });
  const y = 5.7, cw = (W - 2 * M - 2 * 0.3) / 3;
  card(s, M, y, cw, 1.2, "Robust", "−1.6% to +0.9% in all 5 regimes; even with trends ≤ +2.5%, vs ≈ +6% if fully passed on");
  card(s, M + cw + 0.3, y, cw, 1.2, "No hidden increases", "re-listed products (new item number) rose +1.1%, vs +5.3% for untariffed ones");
  card(s, M + 2 * (cw + 0.3), y, cw, 1.2, "Why not like 2019?", "smaller, contested, temporary-looking tariffs; big importers price nationally; weak market", C.accent2);
  s.addNotes("Treatment by brand origin (UK whisky, UK gin etc., EU) vs US and USMCA-exempt spirits; base = 12 months before Apr 2025; 2,611 items. " +
             "Regimes: EU 10% Apr 2025, 15% Aug 2025, 10% (Section 122) Feb 2026, 10% (Section 301) Jul 2026; UK whisky 0% from Jul 2026. " +
             "The 'why' is an interpretation that contrasts two episodes, not a causal estimate. Sources: output/tariff2025_results.md, docs/data_notes.md.");
}
// 8. demand
section("Demand");
{
  const s = content("Iowa buyers barely react to price: demand is inelastic");
  const cw = 4.1, h = 1.5;
  statCard(s, M, 1.55, cw, h, "−0.63", "own-price elasticity (logit, item + month fixed effects)", C.accent2, 32);
  statCard(s, M, 1.55 + h + 0.25, cw, h, "−0.2 to −0.4", "around the item's own list-price increases (2,116 events)", C.accent2, 28);
  statCard(s, M, 1.55 + 2 * (h + 0.25), cw, h, "+3%", "stores stock up the month before an announced increase", C.accent1, 32);
  const iw = W - 2 * M - cw - 0.35;
  s.addImage({ path: FIG("fig_price_change_events.png"), x: M + cw + 0.35, y: 1.55, w: iw, h: iw / 2.159, altText: "Event study around own price changes" });
  caption(s, "Benchmark: Pennsylvania's state monopoly, −1.2 to −1.5 (Seim & Waldfogel, AER 2013)", M + cw + 0.35, 1.6 + iw / 2.159 + 0.1, iw);
  s.addNotes("Event study: changes of at least 3% that hold at least 2 months, each compared with up to 20 same-nest items whose price did not change; " +
             "item and event-by-month fixed effects; SE clustered by item. Increases are the cleaner estimate: price cuts follow falling sales (pre-trend). " +
             "Sources: output/demand_first_pass.md, output/price_change_events.md.");
}
// 9. what didn't work
{
  const s = content("What didn't work: the nested logit could not be identified");
  const hdr = (t) => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk2 } } });
  const rows = [
    [hdr("Specification"), hdr("Price effect"), hdr("Nesting parameter"), hdr("Verdict")],
    ["Nested logit, OLS", "≈ 0", "σ = 0.99", "mechanical: σ → 1 without instruments"],
    ["2SLS, nest-count instruments", "wrong size", "σ = 1.6", "invalid (σ must be < 1)"],
    ["2SLS, class-20 spec (rival-vendor characteristics, brand-group demeaning)", "positive (+0.006)", "λ = 0.94", "invalid; instruments weak (partial R² < 1%)"],
  ];
  s.addTable(rows, { x: M, y: 1.6, w: 7.6, colW: [2.6, 1.3, 1.4, 2.3], fontSize: 14, color: HEX.dk1, border: { type: "solid", pt: 0.5, color: HEX.accent6 },
                     fill: { color: HEX.lt1 }, valign: "middle", rowH: [0.55, 0.8, 0.8, 1.15] });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: 5.55, w: W - 2 * M, h: 0.95, rectRadius: 0.08, fill: { color: C.text2 }, line: { color: C.text2 }, objectName: "consequence" });
  s.addText([{ text: "Consequence  ", options: { bold: true, color: C.accent1 } }, { text: "Every policy number in this talk is a range over substitution (σ) and market size, not a single point estimate", options: { color: C.background1 } }],
            { x: M + 0.3, y: 5.6, w: W - 2 * M - 0.6, h: 0.85, fontSize: 16, valign: "middle", margin: 0, isTextBox: true });
  const x2 = M + 7.6 + 0.4;
  s.addText("What we learned", { x: x2, y: 1.6, w: W - x2 - M, h: 0.4, fontSize: 17, bold: true, color: C.text2, margin: 0, isTextBox: true });
  bullets(s, ["Rival products' characteristics barely move within a spirit type from month to month, so they can't shift prices",
              "Prices themselves move rarely: little variation to separate price from substitution",
              "So we use the logit elasticity and treat substitution within spirit type (σ = 0, 0.5, 0.8) as a sensitivity range in every simulation"],
          x2, 2.1, W - x2 - M, 3.6, 14);
  s.addNotes("The brief asks us to explain what did not work. We followed the professor's class-20 Zappos specification. " +
             "Cluster-robust first-stage F is large (163 and 73) but partial R-squared is under 1% and the price coefficient has the wrong sign. " +
             "Sources: output/nested_logit.md, output/demand_first_pass.md, docs/review_log.md.");
}
// 10. HF 830 incidence
section("Policy");
{
  const s = content("A minimum price (HF 830) would hit cheap big bottles hardest");
  // counterfactuals.md incidence table (elasticity -0.63, sigma 0.5, M 2x)
  s.addChart(pres.charts.BAR, [
      { name: "price change %", labels: ["Cheapest quarter", "2nd", "3rd", "Priciest quarter"], values: [64.4, 0, 0, 0] },
      { name: "liters change %", labels: ["Cheapest quarter", "2nd", "3rd", "Priciest quarter"], values: [-11.8, 11.1, 9.4, 8.7] }],
    Object.assign({ x: M, y: 1.5, w: 7.2, h: 4.9, barDir: "col", barGrouping: "clustered", showValue: true, dataLabelPosition: "outEnd",
      dataLabelFormatCode: "+0;-0;0", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
      chartColors: [HEX.accent2, HEX.accent3], showLegend: true, legendPos: "t", legendFontSize: 12, barGapWidthPct: 60,
      showTitle: true, title: "Products grouped by price per liter of alcohol, central case", titleFontSize: 13, titleColor: HEX.dk2 }, CHART_TXT));
  const x2 = M + 7.2 + 0.4;
  statCard(s, x2, 1.55, W - x2 - M, 1.45, "48% of liters", "are below the floor (but only 14% of products)", C.accent2, 28);
  s.addText("Examples, 1.75 L bottles (Iowa price)", { x: x2, y: 3.25, w: W - x2 - M, h: 0.4, fontSize: 15, bold: true, color: C.text2, margin: 0, isTextBox: true });
  bullets(s, ["Hawkeye Vodka: $11.24 → $29.17 (+160%)", "Black Velvet whisky: $17.24 → $29.17 (+69%)", "Tito's Vodka: $28.50 → $29.17 (+2%)"],
          x2, 3.7, W - x2 - M, 1.4, 14);
  caption(s, "Drinkers trade up: pricier products sell more. Pure alcohol falls about 2–11% overall. Price jumps this large are far outside our data, so treat the size as a range", x2, 5.3, W - x2 - M);
  s.addNotes("Floor: $0.50 per 18 ml of pure alcohol on the supplier price, so a 1.75 L 80-proof bottle has a floor supplier price of $19.44 and an Iowa price of $29.17. " +
             "Central case: elasticity -0.63, sigma 0.5, market size 2x liters. Pure-alcohol range -1.8% to -10.7% across sigma and market size. Source: output/counterfactuals.md.");
}
// 11. who gets the money
{
  const s = content("HF 830's money goes to suppliers, unless the law stops them");
  const iw = 8.0;
  s.addImage({ path: FIG("fig_hf830_who_gets_money.png"), x: M, y: 1.5, w: iw, h: iw / (9 / 5.2), altText: "State vs supplier gains under HF 830 and the alcohol markup" });
  const x2 = M + iw + 0.35;
  s.addText("Why suppliers win", { x: x2, y: 1.55, w: W - x2 - M, h: 0.4, fontSize: 17, bold: true, color: C.text2, margin: 0, isTextBox: true });
  bullets(s, ["The bill sets the state price at 1.5 × max(supplier price, floor)",
              "A supplier below the floor can raise its own price up to the floor: the shelf price doesn't change, and it keeps the difference",
              "Then the state gains only $13–26M a year instead of $44–60M, and suppliers get $27–53M",
              "Buyers living near the border can shop across the state line: that costs $3–15M a year if 10–50% of affected volume leaves"],
          x2, 2.05, W - x2 - M, 4.4, 14);
  s.addNotes("Ranges over sigma in {0, .5, .8} and market size {1.5, 2, 3}x liters at elasticity -0.63; dot = central case. " +
             "Upper bounds with no quantity response: state +$68M (suppliers keep prices) or +$23M (suppliers price up). Source: output/counterfactuals.md, code/10_slide_figures.py.");
}
// 12. alcohol markup
{
  const s = content("A better tool: put the markup on the alcohol, not on the price");
  const iw = 8.0;
  s.addImage({ path: FIG("fig_policy_alcohol.png"), x: M, y: 1.5, w: iw, h: iw / (9 / 5.0), altText: "Change in pure alcohol by policy" });
  const x2 = M + iw + 0.35;
  statCard(s, x2, 1.55, W - x2 - M, 1.5, "≈ $18", "per liter of pure alcohol replaces the 50% markup and raises the same revenue", C.accent1, 34);
  bullets(s, ["Pure alcohol −1% to −7% at zero revenue cost to the state",
              "No floor, so nothing for suppliers to price up to",
              "Hits the strongest, cheapest alcohol hardest, the same products as HF 830",
              "Scotland's minimum price cut alcohol sales about 3% (Public Health Scotland, 2023), in line with our ranges"],
          x2, 3.3, W - x2 - M, 3.2, 14);
  s.addNotes("Policy B in 09: state price = supplier cost + t × liters of pure alcohol, with t solved so the state margin is unchanged ($17.8-19.8 across assumptions; $18.13 in the central case). " +
             "Central case: pure alcohol -2.9%. Stores spend about $21M more because buyers shift toward pricier, lower-strength products; that money goes to suppliers through volume, not a windfall.");
}
// 13. recommendations + limits (dark)
section("Conclusion");
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: sectionNow });
  s.addText("What Iowa should do", { x: M, y: 0.5, w: 12, h: 0.9, fontFace: THEME.headFontFace, fontSize: 36, bold: true, color: C.background1, margin: 0, isTextBox: true });
  const recs = [["Price alcohol content", "Replace part of the 50% markup with about $18 per liter of pure alcohol: less drinking at the same revenue"],
                ["Fix HF 830 if it moves", "Collect the gap between the floor and the supplier's price as a state levy, so suppliers gain nothing by pricing up to the floor"],
                ["Don't budget on tariffs passing through", "About half reached Iowa in 2019 and none in 2025. It depends on supplier strategy, not on Iowa's markup rule"]];
  recs.forEach(([h1, b1], i) => {
    const y = 1.65 + i * 1.25;
    badge(s, M, y + 0.05, String(i + 1));
    s.addText([{ text: h1, options: { bold: true, color: C.accent1, fontSize: 18, breakLine: true } }, { text: b1, options: { color: C.background1, fontSize: 15 } }],
              { x: M + 0.7, y, w: 7.3, h: 1.1, valign: "top", margin: 0, isTextBox: true });
  });
  const x2 = 8.9;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x2, y: 1.6, w: W - x2 - M, h: 3.9, rectRadius: 0.08, fill: { color: C.background1 }, line: { color: C.background1 }, objectName: "limits" });
  s.addText("Limits", { x: x2 + 0.25, y: 1.75, w: W - x2 - M - 0.5, h: 0.4, fontSize: 17, bold: true, color: C.text2, margin: 0, isTextBox: true });
  bullets(s, ["Store orders, not what people drink; shelf markups assumed unchanged",
              "Elasticity comes from small price changes and is stretched to large jumps, so we show ranges",
              "Customs values are US-wide averages",
              "Substitution within spirit type isn't identified (σ is a range)"],
          x2 + 0.25, 2.25, W - x2 - M - 0.5, 3.1, 14);
  s.addNotes("Close (about 1 minute). Then questions. Backup slides follow: simulation assumptions and how we used AI and checked ourselves.");
}
// ---------- appendix ----------
section("Appendix");
{
  const s = content("Appendix: assumptions behind the simulations");
  const hdr = (t) => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk2 } } });
  const rows = [[hdr("Choice"), hdr("Value"), hdr("Why / robustness")],
    ["Demand", "Nested logit in log price, calibrated to the data", "Own elasticity −0.63 (05); fans at −0.4 and −1.0"],
    ["Substitution within spirit type σ", "0, 0.5, 0.8", "Not identified (08), so we report the range"],
    ["Market size M", "1.5×, 2×, 3× observed liters", "Outside option = not buying spirits in Iowa"],
    ["Baseline", "Nov 2025 – Oct 2026: 4,988 items, 21.6M liters, $139M margin", "Latest 12 months"],
    ["HF 830 floor", "$0.50 per 18 ml of pure alcohol on the supplier price", "Bill text; A1 = suppliers keep their prices, A2 = suppliers price up to the floor"],
    ["Alcohol markup", "c + t × liters of alcohol; t solves for the same state margin", "t ≈ $18 per liter of pure alcohol"],
    ["Border leakage", "10 / 25 / 50% of floor-bound volume in border counties", "$30M of post-floor margin at stake"]];
  s.addTable(rows, { x: M, y: 1.55, w: W - 2 * M, colW: [2.9, 4.5, 4.73], fontSize: 13, color: HEX.dk1, border: { type: "solid", pt: 0.5, color: HEX.accent6 },
                     fill: { color: HEX.lt1 }, valign: "middle" });
  s.addNotes("Source: code/09_counterfactuals.py and output/counterfactuals.md.");
}
{
  const s = content("Appendix: how we used AI, and how we checked it");
  card(s, M, 1.6, 5.9, 1.45, "AI did the heavy lifting",
       "Downloading 9 years of data, the DuckDB pipeline, fast fixed-effects 2SLS in numpy, checking tariff dates and the bill text against primary sources");
  card(s, M, 3.3, 5.9, 1.45, "Independent AI reviewers, twice",
       "A separate \"skeptical IO economist\" agent critiqued code and results; every point and our response is in docs/review_log.md");
  card(s, M, 5.0, 5.9, 1.45, "What the review caught",
       "Our first nested logit gave σ ≈ 1. The reviewer showed this was mechanical (no valid instruments), so we report it as a failure, not a result", C.accent2);
  const x2 = M + 5.9 + 0.4;
  s.addText("What the reviews changed", { x: x2, y: 1.6, w: W - x2 - M, h: 0.4, fontSize: 17, bold: true, color: C.text2, margin: 0, isTextBox: true });
  bullets(s, ["Dropped \"the revenue-maximizing markup\": it isn't identified",
              "Pass-through measured against the customs value (the tariff's base), not Iowa's price",
              "Treatment coded by brand origin, plus a placebo, group trends and a re-listing check",
              "HF 830: added the case where suppliers price up to the floor, which became a headline",
              "Simulations reported as ranges over assumptions, checked against Scotland"],
          x2, 2.1, W - x2 - M, 4.3, 14);
  s.addNotes("The course is Empirical Strategy with AI: this slide shows the workflow. Full log in docs/review_log.md.");
}

(async () => {
  await pres.writeFile({ fileName: DECK });
  const { applyTheme } = require(process.env.PPTX_SKILL_SCRIPTS ? path.join(process.env.PPTX_SKILL_SCRIPTS, "apply_theme.js") : "./apply_theme.js");
  await applyTheme(DECK, THEME);
  console.log("Saved " + DECK);
})();
