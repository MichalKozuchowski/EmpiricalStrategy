"""Rebuild the quiz study guide: quiz_study_guide.md -> quiz_study_guide.html -> MGT634_Quiz_Study_Guide.pdf.

Run from EmpiricalStrategy/notes:  uv run --with markdown-it-py --with playwright build_quiz_guide.py
(needs Playwright's Chromium once: uv run --with playwright playwright install chromium)
"""
from pathlib import Path

from markdown_it import MarkdownIt
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
STYLE = """<html><head><meta charset='utf-8'><style>
body{font-family:Calibri,Arial,sans-serif;font-size:10.5pt;line-height:1.35;color:#1a1a1a;margin:0}
h1{font-size:20pt;color:#4b5a3a;border-bottom:2px solid #636e4f;padding-bottom:4px}
h2{font-size:14.5pt;color:#636e4f;margin-top:18px;border-bottom:1px solid #d9d9d9;padding-bottom:2px}
h3{font-size:12pt;color:#993f2a;margin-top:12px}
table{border-collapse:collapse;margin:6px 0 10px 0;font-size:9.5pt}
th{background:#eef1e8;text-align:left}
th,td{border:1px solid #bfbfbf;padding:3px 6px;vertical-align:top}
code{font-family:Consolas,monospace;font-size:9pt;background:#f3f3f3}
blockquote{border-left:3px solid #d1725c;margin:6px 0;padding:2px 10px;color:#555;background:#fbf4f1}
li{margin-bottom:2px}
</style></head><body>"""

md = (HERE / "quiz_study_guide.md").read_text(encoding="utf-8")
body = MarkdownIt("commonmark").enable("table").render(md)   # CommonMark: 2-space nested lists work
html_path = HERE / "quiz_study_guide.html"
html_path.write_text(STYLE + body + "</body></html>", encoding="utf-8")

pdf_path = HERE / "MGT634_Quiz_Study_Guide.pdf"
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(html_path.as_uri(), wait_until="load")
    page.pdf(path=str(pdf_path), format="Letter", print_background=True,
             margin={"top": "0.6in", "bottom": "0.6in", "left": "0.6in", "right": "0.6in"})
    browser.close()
print("built", html_path.name, "and", pdf_path.name)
