# Quick check that Playwright works: open a page in headless Chromium, read its title and text, save a screenshot.
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()                 # headless by default; launch(headless=False) to watch it
    page = browser.new_page()
    page.goto("https://example.com")
    print("Title:", page.title())
    print("First paragraph:", page.locator("p").first.inner_text()[:80])
    page.screenshot(path="example.png")
    browser.close()
print("Playwright OK - screenshot saved to example.png")
