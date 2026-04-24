# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Start everything (Flask API + Next.js frontend) in one terminal:**
```bash
cd web && npm run dev:all
```

**Start Flask API only:**
```bash
python api.py
```

**Start Next.js frontend only:**
```bash
cd web && npm run dev
```

**Run all unit tests:**
```bash
python -m pytest tests/
```

**Run a single test file:**
```bash
python -m pytest tests/test_package.py
```

**Run a single test by name:**
```bash
python -m pytest tests/test_bayes.py -k "test_probability_bounds"
```

**Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**Install frontend dependencies:**
```bash
cd web && npm install
```

**Seed the SQLite cache (one-shot bulk loader for the last two seasons):**
```bash
python seed_db.py                              # all sports, both seasons
python seed_db.py --sport nba,nhl              # subset
python seed_db.py --seasons previous --force   # re-fetch only previous season
```

## Architecture

Sports betting analytics pipeline: scrape odds → cache → transform → Naive Bayes picks → REST API → Next.js website.

**Data flow:**
```
SportsBookReview.com
  → sports.py     (URL generation per sport/date/week)
  → retrieve.py   (HTML scraping → DataFrame)
  → store.py      (SQLite cache at data/cache.db — games + cached_keys tables)
  → package.py    (odds → probabilities, scores → Win/Loss labels)
  → bayes.py      (Naive Bayes classifier)
  → picks.py      (PickEngine: train + predict_all)
  → runner.py     (daily orchestrator, cache-first then live)
  → backtest.py   (walk-forward Backtester)
  → api.py        (Flask REST API)
  → web/          (Next.js 15 frontend)
```

**Key Python modules:**

- **`config.py`** — `SPORTS` dict with date_type and season windows. `is_in_season(sport, date)` handles cross-year seasons. `date_to_week(sport, date)` converts calendar dates to SBR week numbers using `_WEEK1_STARTS`. Add new season years there each year.

- **`store.py`** — SQLite cache at `data/cache.db`. Public API: `save/load/exists/list_available(sport, key)` plus `max_cached_date(sport)`. The `games` table holds one row per game (odds lists JSON-encoded); `cached_keys` records every fetched `(sport, cache_key)` including empty days so they don't get re-fetched forever. The `key` is a date string for date-based sports or a week number string for week-based sports.

- **`sports.py`** — `BetTypes` base class generates spread/money-line/totals URLs. Nine sport subclasses (NFL, NBA, NHL, MLB, MLS, NCAAF, NCAAB, WNBA, CFL); week-based sports take an int week number, date-based take a `YYYY-MM-DD` string.

- **`retrieve.py`** — `SportsbookReviewAPI(url, bet_type, date_type, date, sport=...)` fetches HTML and dispatches to sport-specific `MoneyLineAPI` subclass. Base `clean_scores()` handles NBA/NFL/NHL/NCAAB (uses % wager markers as game separators). MLB/MLS/WNBA/CFL override with `_sequential_clean_scores()` to skip embedded team/pitcher names. `_PlayerNameMixin` filters goalie/pitcher names from odds data (NHL, MLB).

- **`package.py`** — `Package(df, true_prob=True/False)`. With `true_prob=True` returns merged DataFrame with `Away Odds`, `Home Odds`, `Away W/L`, `Home W/L`. With `true_prob=False` returns separate DataFrames for Naive Bayes training.

- **`bayes.py`** — `NaiveBayes(side, df)` where `side` is `'Home'` or `'Away'`. `probability(lines)` returns P(Win | lines) or None if no history. Prior is applied once (not per feature).

- **`picks.py`** — `PickEngine(sport).train(historical_df)` fits home + away models. `predict_all(games_df)` returns `list[Pick]`. `Pick` has `game_index, pick, confidence, away_prob, home_prob, away_lines, home_lines`.

- **`runner.py`** — `get_daily_picks(sport, date_or_week, training_window_days=60, force_refresh=False)` → `list[Pick]`. `run_all_sports(date)` iterates `config.SPORTS`, skips out-of-season, returns `{sport: [Pick, ...]}`.

- **`backtest.py`** — `Backtester(sport, start, end, training_window_days=60).run()` → `BacktestResult`. Walk-forward only; raises `RuntimeError` on cache miss. Units: correct `-200` → +0.50, correct `+150` → +1.50, wrong → −1.00, No Pick/Tie → 0.00.

- **`prefetch.py`** — `start_background_prefetch(fallback_days_back=60)` launches a daemon thread that gap-fills the cache from `store.max_cached_date(sport)` → today per sport (or the fallback window when the cache is empty), calling `runner._fetch_live` for missing entries. Invoked from `api.py` at startup. Exposes `iter_cache_keys(sport, start, end)` which `seed_db.py` reuses.

- **`seed_db.py`** — One-shot CLI bulk loader. Seeds the last two season windows per sport so the website doesn't need to scrape everything on first run. See Commands above for flags.

- **`api.py`** — Flask server on port 5000. Rewrites proxied from Next.js at `/api/*`. Endpoints: `GET /api/sports`, `GET /api/picks`, `GET /api/picks/all`, `POST /api/backtest`. Spawns `prefetch` thread at startup.

**Frontend (`web/`):**

- Next.js 15 App Router, Tailwind CSS 3, TypeScript, Framer Motion, Three.js.
- `web/next.config.ts` — rewrites `/api/*` → `http://localhost:5000/api/*`.
- `web/components/ui/dotted-surface.tsx` — Three.js animated particle wave background.
- `web/components/ui/morphing-card-stack.tsx` — Swipeable/grid/list pick cards.
- `web/components/ui/border-beam.tsx` — Animated beam border for stat cards.
- `web/components/ui/tracing-beam.tsx` — Scroll-progress indicator for game log.
- `web/components/SportsOrbit.tsx` — 9 sport badges on concentric rotating orbits (hero).
- `web/app/page.tsx` — Picks page (hero + sport tabs + card stack).
- `web/app/backtest/page.tsx` — Backtest terminal (form + stats + game log).

**Supported sports:** NBA, NHL, MLB, MLS, NCAAB, WNBA (date-based) · NFL, NCAAF, CFL (week-based).

**Data dependency:** Live scraping requires a connection to SportsBookReview.com. Backtesting is cache-only — populate the cache first with `python seed_db.py`; the API's prefetch thread keeps it current on subsequent starts.

## Tests

```
tests/
  test_package.py   — implied_prob, true_prob, win_loss, to_values, to_nb_values (18 tests)
  test_bayes.py     — counts, probability bounds, always-win/loss lines, mixed (13 tests)
  test_retrieve.py  — _is_odds, _is_player_name, clean_data, clean_scores, SportsbookReviewAPI (34 tests)
  test_sports.py    — all 9 sports instantiate, URL formats, NCAAF halves regression (38 tests)
```

103 tests total. All network calls are mocked with `unittest.mock.patch`.

**Legacy files (not part of the pipeline):**

- **`main.py`** — Hardcoded demo script (NFL week 9, NHL/NBA 2024-11-15). Use `runner.py` for real orchestration.
- **`deep_learn.py`** — Experimental TensorFlow/Keras neural network (not wired into the pipeline). Requires keras/tensorflow extras not in `requirements.txt`.
- **`tests.py`**, **`test_bayes.py`** (root-level) — Pre-pytest exploration scripts; superseded by `tests/`.
