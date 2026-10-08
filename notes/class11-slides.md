# Class 11 — Advanced Data Collection (Thu Oct 8, 2026)

Slides: `data_collect.pdf` (Kevin Williams, 17 slides). Companion reading: Adams & Williams (2019), "Zone Pricing in Retail Oligopoly". See `class11-reading-notes.md`.
Local setup for this class: `notes/data_collection/` (uv project with Playwright and a `test_playwright.py` smoke test). agent-browser is installed globally via npm.

## Plan for today
1. Using `requests` to gather data from the internet
2. Pulling data from APIs
3. Asking Claude to write capture-and-processing programs
4. Playwright CLI, agent-browser, etc.

## 1–2. Gathering EIA data without a web browser

Motivating page: the EIA "Gasoline and Diesel Fuel Update" (eia.gov/petroleum/gasdiesel/). It has a weekly table of US regular gasoline prices by PADD region (e.g. US $3.123 on 07/28/25) and a "full history XLS" link.

- Once you know where the XLS lives (`https://www.eia.gov/petroleum/gasdiesel/xls/pswrgvwall.xls`), you can write a program to fetch it, and automate it to collect the weekly updates.
- "This is simple to do with Python and **Cron** (look this up on your own)." Cron is the Unix scheduler that runs a script on a timetable; on Windows the equivalent is Task Scheduler.

Professor's code (verbatim):

```python
import requests
import pandas as pd
from io import BytesIO

# URL of the Excel file with weekly gasoline prices
url = "https://www.eia.gov/petroleum/gasdiesel/xls/pswrgvwall.xls"

# Make a GET request to fetch the raw Excel file
response = requests.get(url)

# Check successful retrieval
if response.status_code == 200:
    # Load Excel content directly into a pandas DataFrame
    excel_file = BytesIO(response.content)

    # Data starts at row 3 (0-based index), the first two rows are headers
    df = pd.read_excel(excel_file, sheet_name="Data 1", skiprows=2)
```

Key ideas:
- `requests.get(url)` is how a program "visits" a URL. Status **200** means OK. Other codes: 403 = forbidden (often bot blocking), 404 = not found, 429 = too many requests (rate limit).
- `BytesIO` wraps the downloaded bytes so pandas can read them as if they were a file. Nothing is saved to disk.
- Reading `.xls` (old Excel) needs the `xlrd` package installed.

### Alternatives to Python + requests for this task
- **Version 1:** tell the LLM you want to monitor daily diesel prices. Have it find the source, write a program to gather and store the data, and explain how to update the table daily.
- **Version 2:** point the LLM directly at the data source URL above.

## 3. Pulling data from APIs

An API (Application Programming Interface) is a structured way to request data from a server. Instead of a web page, you get machine-readable data, usually JSON.

APIs often use a readable syntax in the URL:

```
https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?filter=record_date:gte:2024-01-01,record_date:lte:2024-01-10
```

Pasting this into a browser shows JSON: a `data` list of records with fields `record_date`, `debt_held_public_amt`, `intragov_hold_amt`, `tot_pub_debt_out_amt`, `src_line_nbr`, `record_fiscal_year`, `record_fiscal_quarter`, `record_calendar_year/quarter/month/day`. All values are strings.

### Using an API instead
`requests` can gather these data for us. The function below passes parameters to the request, which narrows down what is returned. Professor's code (verbatim):

```python
import requests
import pandas as pd

def get_us_debt(start_date: str, end_date: str):
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
    params = {
        'filter': f"record_date:gte:{start_date},record_date:lte:{end_date}",
        'page[size]': 100
    }
    response = requests.get(url, params=params,verify=False)
    if response.status_code == 200:
        data = response.json().get('data', [])
        if not data:
            print("No data returned for given date range.")
            return pd.DataFrame()
        df = pd.DataFrame(data)[['record_date', 'tot_pub_debt_out_amt']]
        df.columns = ['Date', 'Total Public Debt Outstanding (USD)']
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date')
    else:
        raise Exception(f"API Error: {response.status_code}")

# Example usage:
df = get_us_debt("2024-01-01", "2024-01-10")
print(df)
```

Things to notice:
- `params=` builds the `?filter=...&page[size]=100` part of the URL for you. `gte`/`lte` mean ≥ and ≤.
- `page[size]` relates to **pagination**: APIs return results in pages. Long date ranges need a loop over `page[number]`, or a bigger page size.
- `verify=False` turns off SSL certificate checking. This is a workaround for campus/cluster certificate problems and prints a warning. Don't use it in production.
- The amounts come back as **strings**. Convert them with `pd.to_numeric(...)` before doing any math.

### Some API tips
- Useful both for frequent data gathering and for occasional large pulls.
- You often need an **API key**, both inside a firm and for public data.
- Watch out for **rate limits, throttling**, etc.
- Popular APIs: US Treasury, Census, Ticketmaster, etc.

## Legality of data gathering ("I'm not a lawyer, not legal advice")
- **hiQ Labs v. LinkedIn (9th Cir.):** scraping public data does not violate the Computer Fraud and Abuse Act (CFAA).
- **X Corp. v. Bright Data (N.D. Cal. 2024):** some claims were dismissed. The court was skeptical that terms of service (ToS) alone can ban scraping of public content.
- **Compulife Software v. Newman (11th Cir. 2024):** publicly available data can still be off-limits if it is effectively a **trade secret**.
- Firms often give their data to an aggregator, which sells it back to competitors (e.g. **Nielsen**).

## Gathering own/competitor data
- Firms scrape their competitors. They also **scrape themselves** to check their own actions, e.g. that the price in the system matches the price consumers see.
- Scraping prices is hard because scrapers are easy to spot.
- Ideas: browser extensions, Python combined with browser engines, or mimicking a browser entirely within Python.
- Every website is different, so there are start-up costs. One idea: hire someone on Upwork, Freelancer, etc.

### Example: Adams & Williams (2019)
Slide shows a Home Depot product page (Glacier Bay McKenna faucet, $69, store "East Haven", zip 06512, pickup "26 in stock", delivery "1,176 available"). The page reveals a **store-specific price and inventory**. That is exactly the data behind the zone-pricing paper: they set the location to each store, read the local price, and difference the daily inventory to get sales.

### Some tips (monitoring)
- Firms update their websites all the time, so your code may work one day and not the next. Monitor it.
- His setup: scripts download, then process the collected data. Afterwards Python **emails him stats** (pages collected, errors, etc.).
- Example email: "Kickstarter scraping: successfully scraped existing projects — Download complete: there are 24932 projects in the master. Of those, 80 are determined to be active."

### Capturing websites manually, automated processing
Procedure:
1. Use your browser's **Web Developer Tools** (F12 → Network tab) to understand store numbering, product SKUs, etc.
2. See how the website calls its **internal API** to retrieve price and inventory data.
3. Write a scraper that pulls the relevant information.
   - Using the API is much better than loading large web pages routinely,
   - but it is also easier to detect, so you have to strike a balance.

## 4. Scraping is much easier with additional tech
- Download and install **Playwright** (Microsoft) and **agent-browser** (Vercel Labs).
- These tools drive a browser from your code.
- **Playwright** is a library that launches Chrome and handles the network, cookies, etc.
- **agent-browser** is newer and fast (have the LLM read its manual), and works well with CLI programs.
- Others: Claude in Chrome, Browser Use, Stagehand.

Local commands (verified Oct 8):

```bash
# agent-browser (installed: npm install -g agent-browser ; agent-browser install)
agent-browser open https://example.com   # launch browser + go to page
agent-browser snapshot                   # accessibility tree with [ref=e1] handles
agent-browser click @e1                  # act on an element by ref
agent-browser get title
agent-browser close
```

```bash
# Playwright (Python, in notes/data_collection)
uv run test_playwright.py
```

## You try: use AI to write a capture-and-process program
- Look at prompt A (or B). One calls for Playwright, the other for agent-browser. You are not restricted to those two.
- Think of a website whose information changes regularly (e.g. an account balance).
- Work with AI to turn the prompt into code. Then have it process and store the results, appending to a DataFrame that it creates.
- Ideas: hotel or flight prices, apartment/house listings, car inventory, job listings, current OpenTable availability, current Powerball jackpot.

## Advanced techniques: 3 labs (or your own)
| Level | Site | Question | Challenge |
|---|---|---|---|
| HARD | Home Depot | Price variation across stores | Getting around **Akamai** bot detection |
| MEDIUM | Chase | CD rates across locations | Figuring out the exact requests from server behavior |
| EASY | Domino's | Franchisee price variation | Simpler: curl, JSON, etc. |

## Quiz relevance (Oct 15)
- Probably a Section 3 workflow critique. Good critique points:
  - no monitoring or alerting
  - no rate limiting
  - loading full pages instead of the API
  - a scraper that silently breaks when the site changes
  - `verify=False`
  - amounts stored as strings
  - no pagination, so only the first page is returned
  - no raw-data archive, so results can't be reproduced
  - ignoring ToS/trade-secret risk
- Collection choices shape the data: inventory differencing as a proxy for sales is **measurement error** (deliveries, returns). See the reading notes.
