# Class 12 slides: Advanced Data Processing Methods (`data_process.pdf`, 20 slides)

**Plan:**
1. Adobe Acrobat Pro to convert text to data
2. BeautifulSoup to extract data from HTML
3. Others: `json`, `re`
4. Scaling techniques: `glob`, `multiprocessing`
5. Automating data processing with Claude

## Structured vs unstructured (slide 3)
- **Structured** = rows and columns, one type per column, e.g. `zip,state,bank_code,region_code,term,balance_tier,apy_pct`.
- What scraping returns instead (Chase example):
  - a **JSONP wrapper**: `jQuery629...({"zipcode":"10001","valid":true,"state":"NY"})`
  - a URL-encoded **cookie**: `Set-Cookie: bankplancode=zipcode%3D10001%26bankNumber%3D802%26planCode%3D001`
  - **nested JSON**: `{"ratesData":{"rates":{"7-Month":["3.50%",...]},"cdTermLabels":[...]}}`
- "Scraped data almost never has the desired structure for data analysis, so we have to convert it."

## Large PDF (slides 4–5)
- TSA throughput (tsa.gov/foia/readingroom): a giant table published as a PDF (996 pages).
- **Non-AI approach, an Adobe Action:**
  - Use guided actions → Actions → New Action → Save action → "..." next to Action Settings → Export to Excel.
  - Then drag and drop many files.
  - For images instead of PDFs, choose OCR.

## Suggested approaches (slide 6)
| Shape | Looks like | Tool |
|---|---|---|
| HTML page | 1.4 MB of tags; each product a `<div data-testid="product-pod">` | BeautifulSoup |
| JSON inside the page | `window.__APOLLO_STATE__={...}` in a `<script>` tag | find with `str.index`, read with `json` |
| JSON tree | 250 KB: Variants → 14SCREEN → Price | `json`, `pandas.json_normalize` |
| Text with a wrapper | `jQuery123_456({"state":"NY"});  Set-Cookie: bankplancode=...` | regex, then json |
| Free text | "Medium 2-Topping Handmade Pan Pizza and 2-Liter of Coca-Cola" | regex for easy fields, a model for the rest |
| PDF | 996 pages of TSA tables | Adobe action, pdfplumber, OCR |

"AI knows all of these techniques well, but it can be helpful to guide, just like saying use polars for large data instead of pandas."

## BeautifulSoup (slide 7)
```python
from bs4 import BeautifulSoup
soup = BeautifulSoup(open("raw/category/page_0000.html").read(), "lxml")   # 1.4 MB; the screen shows 12 product cards
pods = soup.select('[data-testid="product-pod"]')                          # attribute selector -> len(pods) == 24. Not 12.
pods = soup.select('[data-testid="product-pod"][data-product-id]')         # each card is two nested divs with that testid; -> 12
pod = pods[0]
pod.select_one('a[href*="/p/"]')["href"]                                   # '/p/USG-Sheetrock-Brand-1-2-in-x-4-ft-x-12-ft-.../202530306'
pod.select_one('[data-testid="product-header"]').get_text(" ", strip=True)  # 'USG Sheetrock Brand 1/2 in. x 4 ft. x 12 ft. ...'
pod.get_text(" ", strip=True)                                               # the whole card flattened to one string
```

## bs4 + regex (slide 8)
```python
def parse_pod(pod):                                     # one card in, one dict out
    text = pod.get_text(" ", strip=True).replace("​", "")   # '... Model# 14113411712 $ 25 . 47 ( 53 ¢ /sq.ft. ) Buy 34 or more $19.10 ...'
    link = pod.select_one('a[href*="/p/"]')["href"]
    price = re.search(r"\$\s*(\d+)\s*\.\s*(\d{2})", text)      # the page renders '$', '25', '47' as three spans
    bulk  = re.search(r"Buy (\d+) or more \$(\d+\.\d{2})", text)
    stars = re.search(r"\(\s*([\d.]+)\s*/\s*(\d+)\s*\)", text)  # '(4.4 / 6858)': rating and review count
    return {"item_id": re.search(r"/(\d{9})", link).group(1),
            "price": float(f"{price[1]}.{price[2]}") if price else None,
            "bulk_qty": int(bulk[1]) if bulk else None, "rating": float(stars[1]) if stars else None,
            "n_reviews": int(stars[2]) if stars else None}
rows = [parse_pod(p) for p in soup.select('[data-testid="product-pod"]')]
```
Result: item 202530306, $25.47, bulk 34, rating 4.4, 6,858 reviews, "USG Sheetrock 1/2 in. x 4 ft. x 12 ft. UltraLight".
**`​` is a zero-width space** the site puts inside "1/2 in.". It's invisible on screen but breaks matching, so regex/replace fixes it.

## Extracting from HTML, 2025 THD version (slides 9–10)
- Right click → Inspect over the element you want (e.g. `<span class="sui-text-success">26</span> in stock`).
- Tip: use the web developer tools to see which scripts run on a site.

```python
def extract_price_from_html(path: Path):
    """Extract visible and JS price text and numeric value."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    visible_price, js_price = None, None
    node = soup.find(id="superPIP__price")
    if node:
        span = node.find(id="ajaxPrice") or node
        visible_price = span.get_text(" ", strip=True)
    if not visible_price:
        for script in soup.find_all("script"):
            content = script.string or ""
            if "CI_ItemPrice" in content:
                m = re.search(r"CI_ItemPrice\s*=\s*'([^']+)'", content)
                if m:
                    js_price = m.group(1)
                    break
```
Tip: have AI create a **journal of website changes**.

## Data may already be JSON (slide 11)
```python
import json
html = open("raw/category/page_0000.html").read()
start = html.index("window.__APOLLO_STATE__=") + len("window.__APOLLO_STATE__=")
state, end = json.JSONDecoder().raw_decode(html, start)      # read exactly one JSON value; ignore the JavaScript after it
products = [v for v in state.values() if isinstance(v, dict) and v.get("__typename") == "BaseProduct"]
rows = [{"item_id": p["itemId"], "brand": p["identifiers"]["brandName"],
         "model": p["identifiers"]["modelNumber"], "label": p["identifiers"]["productLabel"]} for p in products]
# 12 products, 106 KB of JSON, each with pricing({"storeId":"121"}) and reviews blocks
```
- Many sites send the data inside the page and render it in the browser, so `json` can replace bs4.
- Tip: ask AI to check this first, to skip HTML processing entirely.

## JSON with pandas, the small case (slide 12)
```python
import pandas as pd, json
from io import StringIO
json_data = """[{"id": 1, "name": "Alice Johnson", "age": 28, "city": "New York", "salary": 92000, "department": "Engineering"},
                {"id": 2, "name": "Bob Smith", "age": 34, "city": "San Francisco", "salary": 75000, "department": "Marketing"}]"""
df = pd.read_json(StringIO(json_data))     # slide passes the string directly; newer pandas wants StringIO
```
- The debt (Treasury API) data are JSON, and so is Google clickstream data.
- Flat JSON → `read_json`. Nested → `json_normalize` or a loop.

## Regex for some of the results (slide 13)
| What the file says | Pattern | You get |
|---|---|---|
| `jQuery6292...877({"zipcode":"10001","state":"NY"})` | `re.search(r"\((.*)\)", s, re.S).group(1)` | JSON text, then `json.loads` |
| `Set-Cookie: bankplancode=zipcode%3D10001%26bankNumber%3D802%26planCode%3D001; Expires=...` | `re.search(r"bankplancode=([^;]+)", s)` then `parse_qs(unquote(...))` | `{'bankNumber': ['802'], 'planCode': ['001']}` |
| `$ 25 . 47 ( 53 ¢ /sq.ft. )` | `r"\$\s*(\d+)\s*\.\s*(\d{2})"` | 25.47 |
| `Buy 34 or more $19.10` | `r"Buy (\d+) or more \$(\d+\.\d{2})"` | (34, 19.10) |
| `(4.4 / 6858)` | `r"\(\s*([\d.]+)\s*/\s*(\d+)\s*\)"` | (4.4, 6858) |
| `Model# 14113411712` | `r"Model#\s*(\w+)"` | 14113411712 |

- In pandas, `df["text"].str.extract(pattern)` gives one column per group for a whole column at once.
- Tip: this can be slow, so minimize use.

## Scaling: glob (slide 14)
- `glob.glob("*")` lists all files in the current folder, e.g. `glob.glob("*.menu.json.gz")` → `['1078.menu.json.gz', ...]`.
- Tip: with **many** files, ask AI for a function that **lazily** walks the directory (like dask: don't do all the work at once).

## multiprocessing (slide 15)
- Run many tasks at once on multiple CPU cores. Most useful for many **independent files**.
- Divide the work across a pool of workers. AI can write and tune this code.
```python
from multiprocessing.dummy import Pool
import time
import os

def do_work(x):
    time.sleep(1)
    print(x)

jobs = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

with Pool(4) as pool:
    pool.map(do_work, jobs)
```
- `multiprocessing.dummy` = threads (good for waiting/I/O).
- `multiprocessing.Pool` = processes (CPU-heavy parsing). On Windows it needs `if __name__ == "__main__":`.

## Activities (slides 16–20)
1. **Chase CD rates.**
   - Do it "manually": chat with an LLM in Clarity and pass example files.
   - (1) Write a function that extracts all the rates for one bank region; (2) `glob` over all files into a df.
   - How much rate variation? (83,000 requests; random zips at first, until a pattern appeared.)
2. **Domino's.**
   - (1) A function for all product prices at one location; (2) glob; (3) multiprocessing into a master data set.
   - How much variation? Patterns by product?
3. **2013 Home Depot.**
   - Use any of Claude's capabilities: (1) a price function; (2) files are saved as SKU-Store-Date incl. HH:MM; (3) glob; (4) map with geopandas.
   - 2,004 files in the THD folder on the cluster; a good fit for multiprocessing. (Compare the paper's Menards cement-block map.)
4. **(HARD) 2026 Home Depot.**
   - Mostly JSON, many more files, plus **test results that shouldn't be included** (like the "experiment results" from a previous session).
   - Have AI work through the archive. Revisit price discrimination by THD, 2013 vs 2026, with a graphic of how zone pricing changed.
5. **(HARD) Kickstarter** (Deb, Öry & Williams 2024).
   - Each folder holds a project's funding page at 12-hour frequency.
   - Process **all** of it into a complete, filled-in data set with **an observation for every project every 12 hours**.
