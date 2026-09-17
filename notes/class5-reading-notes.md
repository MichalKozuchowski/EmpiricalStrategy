# Class 5 reading — Schwabish, "An Economist's Guide to Visualizing Data"
**Journal of Economic Perspectives, Vol. 28 No. 1, Winter 2014, pp. 209–234.** Full assigned
reading per syllabus (not just intro/data section this time — it's a short applied piece, not a
structural paper). Companion to [class5-slides.md](class5-slides.md).

## Core argument
Economists should invest real effort in graphics, not just narrative text — a good graph taps
into "pre-attentive visual processing" (the brain perceives shape/contrast/color instantly, in
parallel, versus reading text serially). The article demonstrates this with **eight real graphs,
each redesigned**, all using nothing more complicated than Excel — the point being that good
design is a choice, not a tooling limitation.

## Three guiding principles
1. **Show the data.** The data is the point of the graph — but that doesn't mean showing *all*
   of it; many graphs actually show too much and bury the message.
2. **Reduce the clutter.** Heavy gridlines, unnecessary tick marks/labels/icons, textured or
   gradient fills, redundant data markers — all reduce a graph's effectiveness. Simple solid
   shading usually communicates the same thing as a busy texture pattern, more clearly.
3. **Integrate the text and the graph.** Avoid the "slideshow effect" where a separate narration
   explains a graph that can't stand alone. Put legends directly on/near the data (end of a line,
   right below the title) instead of off to the side.

## The eight redesigns (each: what was wrong → the fix)
1. **Line chart** (unemployment/SNAP caseload correlation, 4 small multiples): original had an
   overly dark/thick zero-gridline that visually outcompeted the actual data line, plus
   undefined acronym labels (AO/NC/WE/SS) explained only many pages earlier. Fix: lighten
   gridlines except the meaningful zero-baseline, integrate spelled-out labels into the chart.
2. **Scatterplot ("clutterplot")** (education vs. office-machine trade advantage, ~150 countries,
   every point labeled): unreadable — a wall of overlapping 3-letter codes. Fix: label only the
   handful of countries the accompanying text actually discusses; grey out the rest.
3. **Column chart not starting at zero**: visually exaggerates differences between bars — a bar
   at half the height of another doesn't look half as tall if the axis doesn't start at zero.
   Basic rule: bar/column charts should always start at zero.
4. **3D chart**: the third dimension carries no real data, just visual distortion — a bar
   labeled "6%" can visually appear well under that value because of the fake depth/perspective.
   Fix: flatten to 2D, integrate the legend directly onto the chart.
5. **Unbalanced chart** (bars for one series, differently-encoded markers for another): mixing
   encodings (bar length vs. marker position) makes the two series hard to compare, and one
   series visually dominates purely because bars take up more area than points. Fix (Fig. 5B):
   encode both series the same way (dot plot with connecting lines) so they're directly comparable.
6. **Spaghetti chart** (too many overlapping line series): any single trend gets lost in the
   tangle. Fix: small multiples (one line highlighted per panel, the rest shown faint/grey as
   context) — same idea used in the preschool star-rating lineplots from today's slides.
7. **Pie chart**: contentious in the field — humans are bad at comparing *areas* or *angles*,
   which is exactly what a pie chart asks readers to do; a rotated pie chart can make the same
   data look different depending on where the largest slice starts. Alternatives discussed: a
   labeled bar/column chart, paired columns (for two time periods), a stacked bar, or a **slope
   chart** (points connected by a line from period 1 to period 2, doubling as a trend indicator).
8. *(Covered via the pie-chart alternatives above, forming the eighth transformation in sequence.)*

## Form and Function framework
A 2×2 way to categorize any visualization:
- **Static vs. Interactive** (the "form" axis) — static visualizations show everything at once;
  interactive ones let the user manipulate/explore.
- **Explanatory vs. Exploratory** (the "function" axis) — explanatory visualizations surface a
  specific finding for the reader; exploratory ones let the *user* discover their own findings.
- Most economics work lives in the **static + explanatory** quadrant (a chart reinforcing one
  point in a paper). Interactive/exploratory tools (e.g. OECD's Better Life Index) trade that
  focus for open-ended discovery, following a general design mantra: "overview first, zoom and
  filter, then details on demand."

## Tools and resources (brief)
Color: avoid software's default palettes; ColorBrewer2.0 tests palettes for greyscale/colorblind
safety (~10% of people have some color vision deficiency). Fonts: skip the overused
defaults (Arial/Calibri/Times New Roman); Google Fonts/Font Squirrel are free alternatives.
Beyond Excel/Stata/SAS defaults: R for more graphing power; Tableau/D3/Processing for interactive
work. Mapping: ArcGIS/Stata's `spmap` are the traditional (often expensive or inflexible)
options.

## Conclusion
Bottom line for the class: presentation matters for how quickly and accurately readers absorb
results. Effective visualization shows the data, cuts clutter, and integrates text — and with
today's easy-to-use software, there's little excuse not to invest a bit more time in it.
