# Axiom Picks

AI-powered sports betting analytics. Scrapes daily moneyline odds from SportsBookReview, trains a Naive Bayes classifier on historical data, and serves picks + backtesting results through a Next.js web interface.

## Supported Sports

| Sport | Schedule | Leagues |
|-------|----------|---------|
| NBA, NHL, MLB, MLS, NCAAB, WNBA | Date-based | Professional + College |
| NFL, NCAAF, CFL | Week-based | Professional + College |

## Setup

```bash
# Python backend
pip install -r requirements.txt

# Next.js frontend
cd web && npm install
```

## Running

**Start the Flask API** (from project root):
```bash
python api.py
# → http://localhost:5000
```

**Start the web app** (in a second terminal):
```bash
cd web && npm run dev
# → http://localhost:3000
```

**Run tests:**
```bash
python -m pytest tests/
```

## Architecture

```
SportsBookReview.com
  → sports.py      URL generation per sport / date / week
  → retrieve.py    HTML scraping → raw DataFrame
  → package.py     Odds → probabilities, scores → Win/Loss labels
  → bayes.py       Naive Bayes classifier
  → picks.py       PickEngine: train + predict per game
  → runner.py      Daily orchestrator (cache-first, then live fetch)
  → backtest.py    Walk-forward backtester (cache-only, no data leakage)
  → api.py         Flask REST API
  → web/           Next.js frontend (Axiom Picks)
```

**Key modules:**

- **`config.py`** — Sport metadata, season windows, `date_to_week()` converter, `is_in_season()` guard.
- **`store.py`** — Local parquet cache at `data/{sport}/{date_or_week}.parquet`. Avoids re-scraping.
- **`sports.py`** — URL generation for each sport/bet type/period on SportsBookReview.
- **`retrieve.py`** — `SportsbookReviewAPI` fetches HTML; sport-specific `MoneyLineAPI` subclasses parse odds and scores. MLB/MLS/WNBA/CFL use `_sequential_clean_scores()` to handle embedded team/pitcher names.
- **`package.py`** — Converts American odds to true probabilities (vig removed), assigns Win/Loss labels.
- **`bayes.py`** — `NaiveBayes`: P(Win | observed lines) via conditional probability over historical data.
- **`picks.py`** — `PickEngine` wraps two `NaiveBayes` models (home + away). `Pick` dataclass holds result per game.
- **`runner.py`** — `get_daily_picks()` loads from cache or fetches live. `run_all_sports()` iterates all in-season sports.
- **`backtest.py`** — `Backtester.run()` walk-forward loop: train on [D−window, D−1], test on D. Returns `BacktestResult` with per-game units log.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/sports` | All sports + in-season status |
| `GET` | `/api/picks?sport=nba&date=YYYY-MM-DD` | Picks for one sport/date |
| `GET` | `/api/picks/all?date=YYYY-MM-DD` | Picks for all in-season sports |
| `POST` | `/api/backtest` | Run walk-forward backtest |

**Backtest request body:**
```json
{ "sport": "nba", "start": "2024-01-01", "end": "2024-12-31", "training_window_days": 60 }
```

## Units Calculation

Backtesting uses moneyline odds-adjusted units:

| Outcome | Units |
|---------|-------|
| Correct pick on −200 line | +0.50 |
| Correct pick on +150 line | +1.50 |
| Wrong pick | −1.00 |
| No Pick or Tie | 0.00 |

## Web App

The frontend (`web/`) is a Next.js 15 app with:

- **`/`** — Today's picks by sport. Sport tabs → swipeable game pick cards (MorphingCardStack) with confidence bars and odds lines. Three.js animated particle wave background.
- **`/backtest`** — Backtest terminal. Configure sport/dates/window → stats dashboard with cumulative units chart and scrollable game log.

**Frontend stack:** Next.js 15, Tailwind CSS 3, TypeScript, Framer Motion, Three.js.
