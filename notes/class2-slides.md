# Class 2 — Slide Deck: "Using Software, Leveraging AI"
**Prof. Kevin Williams, Sep 8, 2026** — supplements [class2-2026-09-08.md](class2-2026-09-08.md)
(that file has the lecture/discussion notes; this one has the exact paths/code from his slides).

## Core message (slide 2)
AI is the primary tool for learning in this course, not just for the homework — using it to
learn a new skill, hone an existing one, and get research/practice feedback matters beyond
MGT 634 itself. But: **understand what the AI is giving you.** Don't blindly trust output.

## Paths (slides 3–4)
- Example: from `/Users/kw468/Downloads`, absolute path to `img.png` is
  `/Users/kw468/Downloads/img.png`; relative path is just `img.png`.
- On the HPC, `~` = home (e.g. `/gpfs/home/kw468` or `/home/kw468`).
- `esai_2026` is **symlinked** into your home directory — materials live at `~/esai_2026/`
  even though the actual data sits in a project folder.
- **You only have read access to the course folder.** Write your own programs in your home
  directory; only reference (read) data from the class folder.

## Installing packages (slide 7)
The canonical snippet to reuse (this is what "copy the install snippet from Session 2 notes"
in the transcript refers to):
```python
import sys
!{sys.executable} -m pip install --user matplotlib
```
Swap `matplotlib` for whatever module you need (e.g. `pandas`). `--user` matters — you don't
have write access outside your home directory on the shared cluster.

## Loading the Chicago Taxi data (slide 8)
```python
import pandas as pd
df = pd.read_csv('~/esai_2026/data/chicago_taxi_trips_2024/Taxi_Trips_2024.csv', nrows=1000)
```
**Watch your quotes.** If you copy this from a slide deck/Word/Notion, the quote marks are often
"smart quotes" (`'…'`) instead of straight quotes (`'…'`) — Python's parser rejects smart quotes
and throws `SyntaxError: invalid character '‘' (U+2018)`. Retype the quotes by hand in the notebook.

## Column names with spaces (slide 11)
`df.Trip Total.max()` is a `SyntaxError` — dot notation breaks on spaces. Use bracket notation:
`df["Trip Total"].max()`.

`df.loc[condition]` selects rows where a condition holds, e.g.:
```python
df["mph"] = df["Trip Miles"] / (df["Trip Seconds"] / 60**2)
df.loc[df["Trip Seconds"] > 0].mph.max()   # excludes the zero-duration trips that produce inf
```

## Market shares recipe (slides 13–17)
1. Load the data
2. Clean it — at minimum, select only 2024 entries
3. Define market share: `MS_f = (trips for firm f) / (total trips in the sample)`
   — also worth computing a dollar-weighted version to see how the two compare

Prof's framing: if you don't know how to do a step (e.g. filtering to 2024, or writing the
groupby), **ask an LLM** — that's expected workflow in this class, not a shortcut around it.
Caveat raised explicitly: some employers won't allow an online AI tool; your org may have an
offline/local alternative (Yale's own example: Clarity). Either way, **we're assuming the LLM's
code is correct — verify it**, e.g. by running it against synthetic data with a known, hand-computed
answer and checking the function recovers it.

## To-dos before class (slide 19)
- [ ] Confirm you can connect to Yale VPN
- [ ] Verify you can log into the HPC
- [ ] Log into OOD, launch a job, open Jupyter, run something trivial (e.g. print `"HELLO"`),
      then disconnect the session cleanly
