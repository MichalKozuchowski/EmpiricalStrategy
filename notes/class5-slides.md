# Class 5 — Slide Deck: "Visualizing Data"
**Pierre Bodéré (guest instructor), Sep 17, 2026** — application: same Pennsylvania preschool
market data as Class 4. Companion reading: [class5-reading-notes.md](class5-reading-notes.md)
(Schwabish, "An Economist's Guide to Visualizing Data").

## Plan for today
- Overview of good principles for visual display of quantitative information (Tufte, 1983):
  multiple roles for graphics (exploration, uncertainty, synthesis, communication); graphics
  shine where data is complex and tables would be restrictive/inefficient; what separates a good
  graph from a poor one from a misleading one
- Inventory of graph types using `matplotlib` and `seaborn`: 1D (histograms, density, boxplot),
  2D (scatter, binscatter, line, bar charts), multidimensional (heatmap, map)
- Revisit and expand the preschool market analysis using more powerful tools

## First principles
- A good graph should **reveal** rather than hide the underlying data
- A great graph tells a story: from simple argument to complex narrative
- Quantitative information (units, scale) should be clearly labeled and visible
- Proportionality between graph real estate and the statistical quantity represented
- Graphic design (color, shape, layout) should serve the argument: **data/ink ratio**

**"A graph is only as good as the underlying model of the world"** — illustrated with the classic
spurious correlation between solar radiation and NY/London stock prices (1929): a technically
well-made chart can still be meaningless if the underlying claim is nonsense.

**Inconsistent graphic design** — example shown: a partisan approval-rating chart with a
non-standard axis. Lesson: unless there's a specific reason not to, stick to conventions
(y-axis increasing, left to right). More examples of what goes wrong: r/dataisugly.

## Setup (same preschool data as Class 4)
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd

projectPath = "/gpfs/project/esai_2026/"
dataPath = os.path.join(projectPath, "data","preschools","combinedData")
print(dataPath)

df_preschools = pd.read_csv(os.path.join(dataPath,"data_preschools.csv"))
df_blockgroup = pd.read_csv(os.path.join(dataPath,"data_blockgroup_2010_2018.csv"))
```

## 1D distributions: histogram → winsorized histogram → density
- A raw histogram of enrollment (2015) is **compressed by outliers** — nearly all mass sits in
  one bin near zero, the tail stretches out to ~1,500 with almost nothing visible. Fix: show the
  **winsorized** (0.5%) data instead — reveals the actual shape (right-skewed, peak around 15-30).
- **Histogram by category** (preschool price by star rating, overlaid): difference in category
  prevalence can compress information — since there are far more STAR 1 centers than any other
  rating, their bars dwarf the others even where the underlying distributions differ meaningfully.
  Fix: show a **density (ridge) plot** instead — normalizes each rating's distribution to its own
  area, so shapes are comparable regardless of group size. With mean/median lines per rating,
  this cleanly shows STAR 4 prices shifted right of STAR 1-3.
- **Box plot**: focuses on select statistics of the distribution (quartiles, whiskers, outlier
  points, mean marker) rather than the full shape — useful for a compact side-by-side comparison
  across the four ratings when you don't need the full density shape.

## 2D relationships: scatter → statistical overlay → binscatter
- **Scatter plot** (median household income vs. ratio of college/non-college graduates, by
  blockgroup): a necessary first step to check a relationship, but statistical relationships can
  be hard to detect visually in a dense raw scatter.
- **Adding a statistical relationship**: overlay a linear fit, and report the coefficient and
  standard error **in interpretable units** directly on the chart (e.g. "Coefficient (SE): 1.58
  (0.02)" for log household income vs. college ratio) — don't make the reader hunt in a table.
- **Binscatter**: bins the x-axis and plots conditional means, flexibly representing conditional
  expectations — nonlinear patterns can emerge that a raw scatter with an imposed straight line
  would hide. Cleaner visually, but the data transformation (binning) erases outliers and bunching
  that the raw scatter showed.

## Time series: lineplot, three iterations
1. **Naive lineplot** (preschool counts by star rating, 2010-2018, one shared y-axis): combining
   time series can be delicate when class frequencies differ wildly — STAR 1's huge count
   (~1,700-1,900) flattens STAR 2/3/4's much smaller lines near the bottom, hiding their trends.
2. **Faceted, free y-scale** (small multiples, one panel per rating, each with its own y-axis):
   fixes the visibility problem, but faceting with a free y-scale is an option that **may obscure
   different relative magnitudes** — STAR 4's dramatic growth looks similarly sized to STAR 1's
   near-flat line because each panel's axis auto-scales independently.
3. **Indexed to 2010 = 100, common y-axis**: successfully conveys the real story — low quality is
   still the most common rating, but high-quality supply is growing fast (STAR 4 index rises from
   100 to ~616 by 2018, while STAR 1 stays close to flat).

## Bar chart
Preschool access (seats per child under 5) in the 10 most populous PA counties, 2010 vs. 2018,
horizontal bars, grouped by year. Flexible form: can flip coordinates, rank labels or not, add
uncertainty bands, dodge bars side-by-side or superimpose them.

## Multidimensional graphs
Referenced the canonical example: **Minard's 1869 figurative map of Napoleon's 1812 Russian
campaign** — flow width encodes army size, position encodes geography, color encodes
direction/season, all in one static image (a frequent Tufte touchstone for "good graphics done
before computers").

**Heatmap**: correlation matrix of blockgroup variables (median household income, median home
value, median rent, college/non-college ratio) — heatmaps visualize correlation effectively, and
at scale (many more variables than a scatter-matrix could show legibly).

## Mapping the preschool market (geopandas)
```python
import os
import numpy as np
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

# Settings.
map_year = 2018
market_name = "mkt_pitt_east"
market_id = f"{market_name}-{map_year}"
map_label = f"Pittsburgh East, {map_year}"
map_crs = "EPSG:3649"  # Projected coordinates measured in metres.
hex_miles = 0.75
```
- **Loading shapefiles**: block-group polygons filtered to the chosen year/market, merged with the
  data (e.g. college ratio), reprojected to `map_crs`. Market boundary loaded separately and used
  to `gpd.clip()` the block groups to just that market's area.
- **Constructing preschool points**: preschools have no shapefile of their own — build one from
  `longitude`/`latitude` via `gpd.points_from_xy()`, starting in standard lat/long CRS
  (`EPSG:4326`) then reprojected to match the map.
- **Define the graphic theme once, up front** (colors, symbols, axis limits) — avoids repeating
  the same styling code across multiple map variants, and guarantees every map in the sequence
  uses identical color scales/extents for honest comparison.
- **Build-up sequence** (three maps, same underlying market):
  1. Choropleth of college-graduate ratio across Pittsburgh East block groups
  2. Same choropleth + preschools plotted as points, colored/shaped by STAR rating
  3. Same map with a **hexagon grid** replacing the raw block-group polygons as the background —
     cleans up visual noise from oddly-shaped/tiny block groups while preserving the color pattern
