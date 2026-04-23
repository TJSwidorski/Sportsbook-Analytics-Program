# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run demos/examples:**
```bash
python main.py
```

**Run unit tests:**
```bash
python tests.py
```

**Run Naive Bayes integration test (full season):**
```bash
python test_bayes.py
```

**Train deep neural network:**
```bash
python deep_learn.py
```

**Dependencies** (install via pip — no requirements.txt):
```
requests beautifulsoup4 pandas keras tensorflow scikit-learn
```

## Architecture

This is a sports betting analytics pipeline: scrape odds → transform data → train ML models to predict game outcomes.

**Data flow:**
```
SportsBookReview.com
  → sports.py     (URL generation per sport/date/week)
  → retrieve.py   (HTML scraping → DataFrame)
  → package.py    (odds → probabilities, scores → Win/Loss labels)
  → bayes.py      (Naive Bayes classifier)
  OR deep_learn.py (Keras neural network)
```

**Key modules:**

- **`sports.py`** — `BetTypes` base class generates spread/moneyline/totals URLs for SportsBookReview. Sport subclasses (NFL, NHL, NBA, MLB, MLS, NCAAF, NCAAB, WNBA, CFL) extend it; date-based sports use calendar dates while week-based sports (NFL, NCAAF) use week numbers.

- **`retrieve.py`** — `SportsbookReviewAPI` fetches HTML and dispatches to `MoneyLineAPI` (implemented) which parses odds and scores into a DataFrame. `PointSpreadAPI` and `TotalsAPI` are stubs.

- **`package.py`** — `Package` class converts American odds to implied probabilities, removes vigorish for true probabilities, and labels outcomes as 1 (win) or 0 (loss). With `true_prob=True` returns a single merged DataFrame; with `true_prob=False` returns separate home/away DataFrames for Naive Bayes.

- **`bayes.py`** — `NaiveBayes` class computes P(Win | observed lines) using conditional probability over historical data. Separate models are fit for home and away teams.

- **`deep_learn.py`** — Standalone script that aggregates multi-week NFL data, expands odds lists into feature columns, and trains two `keras.Sequential` models (home and away) with architecture `Dense(512, relu) → Dense(216, relu) → Dense(1, linear)` using Huber loss.

**Supported sports:** NFL (week-based), NHL/NBA/MLB/MLS/NCAAB/WNBA/CFL (date-based), NCAAF (week-based).

**Live dependency:** All data requires a live connection to SportsBookReview.com. All date ranges and model parameters are hardcoded in the scripts, not configurable via CLI or config files.
