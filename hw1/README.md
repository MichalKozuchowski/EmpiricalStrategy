# HW1: Exploring Hospital ED Data (NHAMCS-ED 2015), due Sep 29

- `report/` - the 4-page Word write-up and 5-slide PowerPoint deck (plus PDF copies), and the
  Python scripts that build them from the verified numbers (`build_writeup.py`, `build_slides.py`)

- `analysis/hw1_nhamcs_analysis.ipynb` - the submission notebook, one commented cell per
  question, with outputs from a clean Run All (ends with a verification cell: 20/20 checks
  pass). To re-run it: upload it to JupyterLab in your home folder, then Kernel > Restart Kernel
  and Run All Cells. It reads `~/esai_2026/data/NHAMCS/nhamcsed2015.csv` and saves charts to
  `~/hw1_output/figures/`.
- `analysis/hw1_nhamcs_analysis.py` - the same code as a plain script.
- `figures/` - the 18 charts (PNG, 200 dpi) produced by the notebook, for the write-up and slides.
- `results_log.md` - verified outputs and methodology notes for the write-up and slides.
- `docs/` - the assignment (`MGT_634_HW1.pdf`), the NCHS codebook (`nhamcsed2015.pdf`) and the
  variable/label listing (`desc.txt`).

**Data trap:** missing answers are stored as negative codes (-9 Blank, -8 Unknown,
-7 Not applicable), not as blanks. Remove them before computing any statistic. Use PATWT
weights for all totals and rates.
