# Empirical Strategy with AI — MGT 634

Yale SOM · Prof. Kevin Williams · Fall 2026 · T/Th 10:05am, Evans 2230

## Team
| Name | GitHub |
|---|---|
| Michal Kozuchowski | [@MichalKozuchowski](https://github.com/MichalKozuchowski) |
| _teammate 2_ | _pending invite_ |
| _teammate 3_ | |
| _teammate 4_ | |

## Repo layout
```
hw1/ .. hw4/   Each written assignment: report + code/analysis (see syllabus — 3–4 pg report, clean replicable code)
project/       Final group project & presentation (topic TBD after fall break)
notes/         Personal/shared notes, readings summaries
data/          Local-only datasets (gitignored — see below). Never commit raw data files here.
```

## Deadlines
| Date | Item |
|---|---|
| Sep 29 | HW1 due |
| Oct 13 | HW2 due |
| Oct 15 | Quiz (closed-book, no AI, no coding) |
| after fall break | Project topic sign-up |
| Nov 10 | HW3 due |
| Dec 3 | HW4 due |
| Dec 10 / Dec 15 | Final project presentations |

## Grading
Attendance 15% · Written Assignments 40% · Quiz 20% · Project & Participation 25%

## Data sets used in the course
Zappos.com, Chicago Taxi Trips, TSA Security Checkpoint Totals, NYC 311 Complaints, Yelp Reviews,
LendingClub, Airline Route/Ticketing Statistics, Home Depot Drywall, Joint Executive Committee (historical),
NHAMCS Emergency Room data. Large files should live on Yale HPC / Open OnDemand, not in this repo.

## Workflow
1. Pull latest before starting work: `git pull`
2. Create a branch per assignment/feature: `git checkout -b hw1-yourname`
3. Commit early and often — commit history doubles as the contribution record the syllabus' group-work
   policy asks each member to keep (a name should only appear on a submission with substantive contributions).
4. Open a PR into `main` when ready for teammates to review, or merge directly for small/uncontested changes.

## Setup
- Python 3.10+ (local install optional — Yale HPC via Open OnDemand + Jupyter is the primary environment)
- Git + GitHub CLI (`gh`) for version control
- VS Code (or your preferred editor)
- At least one AI chatbot subscription (Clarity is free and required for class; Codex/Claude Code available too)
