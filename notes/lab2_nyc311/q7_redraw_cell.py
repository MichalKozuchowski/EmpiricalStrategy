# Q7 (final version): real map of NYC's 59 community districts (official NYC Planning boundaries,
# file nyc_community_districts.geojson next to this notebook). Left map = request volume, right map =
# share of requests about housing conditions; three insights underneath. Uses tables computed above.
import json
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection

BORO_CODE = {"MANHATTAN": 1, "BRONX": 2, "BROOKLYN": 3, "QUEENS": 4, "STATEN ISLAND": 5}
cdm = sql("""SELECT cd, count(*) AS n, avg((category = 'Building owner / landlord')::INT) AS share_housing
             FROM sr WHERE cd IS NOT NULL GROUP BY 1""")
cdm["BoroCD"] = [BORO_CODE.get(c[3:].strip(), 0) * 100 + int(c[:2]) for c in cdm["cd"]]
years = max(1, (span["last"] - span["first"]).days / 365.25)
cdm["per_year"] = cdm["n"] / years
GEO = HERE / "nyc_community_districts.geojson"
if not GEO.exists():                                        # official boundaries (NYC Dept. of City Planning)
    import urllib.request
    urllib.request.urlretrieve("https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/NYC_Community_Districts/"
                               "FeatureServer/0/query?where=1=1&outFields=BoroCD&outSR=4326&f=geojson&geometryPrecision=5", GEO)
gj = json.load(open(GEO))
shapes = []                                                 # (BoroCD, list of rings) for every district
for f in gj["features"]:
    geom = f["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    shapes.append((int(f["properties"]["BoroCD"]), [p[0] for p in polys]))
data = cdm.set_index("BoroCD")
residential = lambda code: code % 100 <= 18                 # 26-28, 55-56, 64, 80-84, 95 = parks / airports


def draw(ax, column, cmap, title, fmt):
    patches, values = [], []
    for code, rings in shapes:
        for ring in rings:
            patches.append(MplPolygon(np.array(ring), closed=True))
            values.append(data[column].get(code, np.nan) if residential(code) else np.nan)
    values = np.array(values, dtype=float)
    pc = PatchCollection(patches, cmap=cmap, edgecolor="white", linewidth=0.5)
    pc.set_array(np.ma.masked_invalid(values))
    pc.cmap.set_bad("#e6e6e6")                               # parks / airports in grey
    ax.add_collection(pc)
    ax.autoscale_view()
    ax.set_aspect(1.3)
    ax.axis("off")
    ax.set_title(title, fontsize=11.5)
    cb = fig.colorbar(pc, ax=ax, orientation="horizontal", fraction=0.04, pad=0.01, aspect=35)
    cb.ax.xaxis.set_major_formatter(FuncFormatter(fmt))
    cb.outline.set_visible(False)
    # label the top 3 districts on this measure
    top = data[[residential(c) for c in data.index]].nlargest(3, column)
    for code, row in top.iterrows():
        rings = next(r for c, r in shapes if c == code)
        pts_ = np.vstack(rings)
        ax.annotate(row["cd"].title(), pts_.mean(axis=0), fontsize=8, fontweight="bold", ha="center",
                    color="white" if column == "per_year" else INK,
                    path_effects=[matplotlib.patheffects.withStroke(linewidth=2, foreground=INK if column == "per_year" else "white")])


import matplotlib.patheffects
fig = plt.figure(figsize=(13.5, 7.6))
gs = fig.add_gridspec(2, 2, height_ratios=[4.2, 1], hspace=0.08, wspace=0.05)
ax_a, ax_b, ax_t = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
draw(ax_a, "per_year", matplotlib.colors.LinearSegmentedColormap.from_list("v", ["#f3f0e2", SAGE, DARK_GREEN, INK]),
     "311 requests per year, by community district", lambda v, _: f"{v / 1000:,.0f}k" if v >= 1000 else f"{v:,.0f}")
draw(ax_b, "share_housing", matplotlib.colors.LinearSegmentedColormap.from_list("h", ["#f7efe3", SALMON, DARK_RED]),
     "Share of requests about housing conditions", lambda v, _: f"{v:.0%}")
ax_t.axis("off")
ax_t.text(0.0, 0.95, "Three insights for the Mayor", fontsize=12, fontweight="bold", va="top", color=INK)
ax_t.text(0.0, 0.62, "\n".join(ins), fontsize=10.5, va="top", color=INK, linespacing=1.6,
          bbox=dict(boxstyle="round,pad=0.6", facecolor="#f3f0e2", edgecolor="none"))
fig.suptitle("311 demand is uneven: the Bronx files the most per resident, and housing drives it",
             x=0.02, ha="left", fontweight="bold", fontsize=14)
save(fig, "q7_geography", note="boundaries: NYC Dept. of City Planning community districts; grey = parks/airports; population: 2020 Census")

import shutil                                               # rebuild the submission zip with the new chart
shutil.make_archive(str(HERE / "MGT634_Lab2_NYC311_team"), "zip", OUT)
print("Updated:", FIG / "q7_geography.png", "and", HERE / "MGT634_Lab2_NYC311_team.zip")
