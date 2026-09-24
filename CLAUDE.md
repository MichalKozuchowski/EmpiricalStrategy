# CLAUDE.md

Context for any Claude Code session working in this repo — read this first. This file exists so
that context survives an account switch (e.g. moving to a Yale-sponsored Claude account): repo
content travels with GitHub regardless of which Claude account opens it, unlike Claude's local
per-machine memory.

## Who this is for

Michal Kozuchowski (mnichow@gmail.com), a Yale School of Management student taking
**MGT 634: Empirical Strategy with AI** (Prof. Kevin Williams, Fall 2026, T/Th 10:05am; guest
instructor Pierre Bodéré for several sessions). He is **new to coding/Python** — the course
explicitly requires no prior coding experience and leans on AI tools for the programming side.

Coursework runs on Yale's HPC cluster via Open OnDemand/JupyterLab (course folder `esai_2026`,
symlinked as `~/esai_2026`, actual project path `/gpfs/project/esai_2026/` or
`/home/<netid>/esai_2026/` depending on context). **Claude cannot access the cluster directly**
(no credentials, no SSH, no VPN) — Michal runs all code himself in Jupyter and reports back
screenshots of output/errors for live debugging. This means: give him copy-paste-ready code, not
"try running X" — he can't be told to explore interactively, only to run exact blocks and report
back.

## Repo structure and conventions

- `hw0/` .. `hw4/` — assignments (group work)
- `project/` — final project
- `notes/` — class notes, one `classN-YYYY-MM-DD.md` per session transcript, plus
  `classN-slides.md` when a separate slide-deck PDF was ingested, and `classN-reading-notes.md`
  / `classN-*-cheat-sheet.md` for companion readings/references. **Check these first** before
  writing merge/analysis code from scratch — see "match the professor's code" below.
- `setup/installpackages.ipynb` — starter package-install notebook for cluster sessions
- `.gitignore` excludes raw data broadly, with explicit per-assignment exceptions (e.g.
  `hw0/data/*.csv`, `hw0/data/*.pdf`) for small source files worth keeping in git

**`git` is not installed on the Yale HPC cluster's Python/Jupyter environment** — Michal cannot
`git clone` this repo there. Cluster work is copy-pasted from chat into Jupyter, not synced via
git. Class notes get pushed to this repo from the local machine (OneDrive-synced clone at
`C:\Users\mnich\OneDrive\Documents\Second Year\EmpiricalStrategy`), separately from the live
cluster session.

## Working style rules (all learned live, hold firm going forward)

- **Comment code with `#` explaining what each part does.** This is a teaching sandbox, not just
  a means to an end — comments should be present on all code given to him.
- **No unexplained jargon or UI shortcuts.** He didn't initially know what a terminal was, or
  that Jupyter cells run Python (not shell) unless prefixed with `!`. Spell out UI steps (which
  menu, which icon, "code cell" vs. "Terminal tab") rather than assuming familiarity.
- **Give ONE consolidated copy-paste block** once a script grows past 2-3 cells, not scattered
  snippets — he loses track of what's been run vs. not, and can't easily find old cell outputs
  in a long notebook.
- **Avoid deprecated code patterns** (e.g. pandas `.groupby().apply()` FutureWarnings,
  `sns.boxplot(palette=...)` without `hue=`) — the professor explicitly flagged this in class and
  asked that AI tools not introduce them.
- **Prefer efficient code at scale**: `usecols` on `read_csv`, vectorized ops over `.apply()`,
  single `.agg()` passes over repeated `.groupby()` calls — efficiency is an explicit course
  requirement, not just nice-to-have.
- **For large-data work, actively weigh Dask/DuckDB/Polars against plain pandas** based on actual
  data size — don't default to Dask blindly, but don't ignore it either. Rule of thumb from Class
  7: pandas is fine under ~10M rows or whatever comfortably fits in RAM; beyond that it degrades
  sharply (or crashes outright) while Dask/DuckDB/Polars stay far more scalable. DuckDB in
  particular is extremely fast for SQL-style aggregation/joins at real scale (a 300GB join that
  pandas couldn't finish took DuckDB 13 seconds in the professor's own benchmark).
- **Every merge (`pd.merge`, `.join`, Dask/Polars/DuckDB equivalents) must print row/column shape
  before and after, and flag it if size changes by a large factor.** Direct instruction from
  Prof. Williams, Class 7: "every time you do a merge, tell me the dimension before and after,
  and flag if something increases by a factor of x or shrinks by y." This catches silent
  many-to-many blowups and duplicate-key merge bugs (a classic failure mode covered explicitly in
  Class 7 — see `notes/class7-slides.md`, "merge gone wrong"). Apply this by default, not just
  when asked.
- **Always check the ingested `notes/classN-*.md` files first and use the professor's exact code**
  for in-class exercises, rather than writing a logically-equivalent variant from scratch — live
  exercises get compared directly against the professor's screen and classmates' numbers, and an
  improvised (even if correct) version causes confusing "we have different numbers" mismatches.
  Only improvise beyond the notes when he's asking for something they genuinely don't cover.
- **Diagnose from actual error screenshots, not guesses** — verify the fix against the exact
  error/traceback shown (e.g. a `SyntaxError` from smart quotes pasted out of a PDF, a package
  installed but still `ModuleNotFoundError` because the cluster's Jupyter kernel excludes
  `~/.local/lib/python3.9/site-packages` from `sys.path` by default — fix with
  `sys.path.insert(0, os.path.expanduser("~/.local/lib/python3.9/site-packages"))`, or a package
  needing `--user` installs since the cluster disallows system-wide installs:
  `!{sys.executable} -m pip install --user <package>`).
- **During live in-class walkthroughs, auto-advance to the next slide's code as soon as he
  confirms output/success — don't wait for him to say "next."** Treat a screenshot of correct
  output as an implicit go-ahead, unless he explicitly says to hold on a slide or a step needs a
  decision from him first.

## Cluster environment quick reference

- Python 3.9, JupyterLab via Open OnDemand
- Package installs: `import sys; !{sys.executable} -m pip install --user <pkg>` (system-wide
  installs are blocked)
- If a package installs successfully but still throws `ModuleNotFoundError`: the kernel isn't
  looking in the `--user` install folder by default — add it to `sys.path` manually (see above).
  This has hit polars, pyarrow, dask, duckdb, geopandas, seaborn, scipy at various points — it's
  a recurring, expected first failure, not a sign of a deeper problem.
- Typical data paths: `/gpfs/project/esai_2026/data/...` or `/home/<netid>/esai_2026/data/...`
  (varies by which system component is speaking — always verify with `os.listdir()` rather than
  guessing a path from a slide, since guessed paths from slides have repeatedly turned out
  slightly wrong in practice).
