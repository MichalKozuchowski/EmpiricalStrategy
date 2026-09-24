# HW1: Exploring Hospital ED Data (NHAMCS-ED 2015), due Sep 29

- `report.md` (or .docx/.pdf) - 3-4 page write-up: methods, approach, results, conclusions
  (plus up to 5 slides)
- `analysis/hw1_nhamcs_analysis.py` - the analysis code, one commented section per question.
  Sections are added as each one is verified on the cluster. To run it: paste it into a
  JupyterLab notebook cell in your home folder and press Shift+Enter. It reads
  `~/esai_2026/data/NHAMCS/nhamcsed2015.csv` and saves charts to `~/hw1_output/figures/`.
- `figures/` - the 18 charts (PNG, 200 dpi) produced by the notebook, for the write-up and slides.
- `results_log.md` - verified outputs and methodology notes for the write-up and slides.
- `docs/` - the assignment (`MGT_634_HW1.pdf`), the NCHS codebook (`nhamcsed2015.pdf`) and the
  variable/label listing (`desc.txt`).

**Data trap:** missing answers are stored as negative codes (-9 Blank, -8 Unknown,
-7 Not applicable), not as blanks. Remove them before computing any statistic. Use PATWT
weights for all totals and rates.
