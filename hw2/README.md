# HW2: Zappos product, review and sales data (2012-2013), due Oct 13

Deliverables (per the assignment PDF): a 1-page executive summary for a non-technical audience
(charts after it) and the commented notebook.

- `report/MGT634_HW2_Zappos_summary.docx` / `.pdf` - page 1 is the executive summary; then
  Appendix A (all 18 charts by question, each with its takeaway) and Appendix B (data, cleaning,
  methods, AI disclosure). Built by `report/build_summary.py` from the verified numbers.
- `analysis/hw2_zappos_analysis.ipynb` - the submission notebook, one section per question, ending
  with a check that re-verifies the raw-file fingerprints and 13 key numbers.
  `analysis/hw2_zappos_analysis.py` is the same code as a plain script (the notebook is generated
  from it with jupytext).
- `figures/` - the 18 charts (PNG, 200 dpi).
- `results_log.md` - every verified number and data decision, by question.

**To run on the cluster:** upload the notebook to your home folder, then Kernel > Restart Kernel
and Run All Cells. It reads `~/esai_2026/data/zappos/` (never changes it), installs duckdb/pyarrow/
statsmodels with `pip --user` if missing, and saves charts to `~/hw2_output/figures/`. The first run
converts the 2.6 GB `POS.dta` into `~/hw2_cache/pos.parquet` (about 2 minutes).

**To run locally:** put the five files plus `pos.parquet` in `data/zappos/` (git-ignored), then
`uv run python analysis/hw2_zappos_analysis.py` from `hw2/` (uv project: `pyproject.toml`).

**Data traps:**
- `stock_chars` is one row per product x color, so merge on sku + styleid, never on sku alone.
- `reviews.rev_cnt` and the ratings are running totals, not monthly values.
- POS `brand` holds sub-lines ("Nike Kids"); `brand_list` holds parent brands.
- 9 days have missing hours of sales records.
- 0.7% of sales go to territories or military addresses.
