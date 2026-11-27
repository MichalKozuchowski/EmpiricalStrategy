"""
01_download.py: download the Iowa Liquor Sales data (one file per year) + the current product price list.

Source: Iowa Department of Revenue, Alcoholic Beverages Division, CC BY 4.0
        (catalog: https://catalog.data.gov/dataset/iowa-liquor-sales-<year>).
Each "rows.csv" endpoint actually returns a ZIP containing several part CSVs; we unzip them.

Run:  uv run --with requests python code/01_download.py            (from project/iowa_liquor)
Data are written OUTSIDE the repo (too large for git): set IOWA_DATA_DIR or default ~/mgt634_data/iowa_liquor
"""
import os
import sys
import zipfile
import requests

DATA_DIR = os.environ.get("IOWA_DATA_DIR", os.path.expanduser("~/mgt634_data/iowa_liquor"))
RAW = os.path.join(DATA_DIR, "raw")
API = "https://idh-be.iowa.gov/api/v1/datasets/{id}/rows.csv"

# Dataset id for each year (looked up on catalog.data.gov, Nov 2026)
YEAR_IDS = {2012: 1249, 2013: 1250, 2014: 1251, 2015: 1252, 2016: 1253, 2017: 1254, 2018: 1255,
            2019: 1256, 2020: 1257, 2021: 1258, 2022: 1259, 2023: 1260, 2024: 1261, 2025: 1262, 2026: 1263}
PRODUCTS_ID = 1029            # "Iowa Liquor Products": current price list with proof, age, size, cost, retail
YEARS = range(2018, 2027)     # project window: 2018-2026 (pre-period for the Oct 2019 Scotch tariff -> 2025-26 tariffs)


def fetch(dataset_id, out_dir, label):
    """Download one dataset; unzip if the server sends a ZIP (it usually does)."""
    os.makedirs(out_dir, exist_ok=True)
    if any(f.endswith(".csv") for f in os.listdir(out_dir)):
        print(f"{label}: already downloaded -> {out_dir}")
        return
    tmp = out_dir + ".download"
    with requests.get(API.format(id=dataset_id), headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    if zipfile.is_zipfile(tmp):
        with zipfile.ZipFile(tmp) as z:
            z.extractall(out_dir)
        os.remove(tmp)
    else:
        os.replace(tmp, os.path.join(out_dir, f"{label}.csv"))
    size = sum(os.path.getsize(os.path.join(out_dir, f)) for f in os.listdir(out_dir)) / 1e6
    print(f"{label}: {len(os.listdir(out_dir))} file(s), {size:,.0f} MB -> {out_dir}")


if __name__ == "__main__":
    years = [int(a) for a in sys.argv[1:]] or list(YEARS)
    for y in years:
        fetch(YEAR_IDS[y], os.path.join(RAW, str(y)), f"sales_{y}")
    fetch(PRODUCTS_ID, os.path.join(RAW, "products"), "products")
