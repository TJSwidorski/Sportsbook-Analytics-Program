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

**Lint / build the frontend:**
```bash
cd web && npm run lint
cd web && npm run build
```

**Seed the SQLite cache (one-shot bulk loader):**
```bash
python seed_db.py                              # all sports, last 7 seasons (default)
python seed_db.py --lookback 7                 # explicit lookback (increase for more history)
python seed_db.py --sport nba,nhl              # subset
python seed_db.py --seasons previous --force   # re-fetch only previous season
```

**Aggregate per-sport backtest history (manual CLI, populates `/api/history`):**
```bash
python backtest_history.py                     # all sports, last completed season
python backtest_history.py --sport nba,nhl     # subset
python backtest_history.py --force             # recompute existing rows
```

**Recompute the rolling 7/30/90-day backtests (drives the History tab):**
```bash
python rolling_backtest.py                     # all in-season sports, 30-day window
python rolling_backtest.py --window 7 --force  # 7-day window, recompute even if cached
python rolling_backtest.py --sport nba,nhl     # subset
```
The Flask prefetch thread runs this automatically at startup; the CLI is for
manual refreshes.

**Train the `logreg_v2` meta-gate (offline; pickled to `data/meta_models/`):**
```bash
python train_meta_model.py --walk-forward --force                    # RECOMMENDED
python train_meta_model.py --walk-forward --target kelly --force     # kelly units target (default)
python train_meta_model.py --walk-forward --target flat --force      # flat units target (original)
python train_meta_model.py                                           # single gate, default holdout
python train_meta_model.py --holdout-season 2024 --force             # single gate, fixed holdout
python train_meta_model.py --no-holdout --force                      # diagnostics only
```
`--target kelly` (default) trains the gate to predict kelly-weighted realized units.
`--target flat` trains it to predict flat ±1 unit outcomes (the original behavior).
Each target uses a separate corpus cache (`logreg_nba_2023_kelly.pkl` vs `_flat.pkl`) so
switching targets does not require `--force`. Walk-forward fits one per-season gate plus a
live gate; the Backtester loads the right one automatically.

**Select and save per-sport, per-season thresholds (bias-free):**
```bash
python optimize_threshold.py --walk-forward --objective sharpe --save          # RECOMMENDED
python optimize_threshold.py --walk-forward --objective sharpe --target kelly  # explicit target
python optimize_threshold.py --test-holdout 1 --objective sharpe               # holdout validation only
python optimize_threshold.py                                                    # show grid, no save
```
`--walk-forward` is the bias-free option: for each season Y the threshold is selected using
only corpus rows from seasons strictly before Y. Saves a nested JSON to
`data/meta_models/thresholds.json`; `config.py` and `PickEngine` resolve the per-season
threshold automatically during backtests and the live threshold for daily picks.

## Deployment

The site is split into two independently hosted pieces:

- **Frontend** — Next.js, hosted on Netlify at `axiompicks.com`
- **Backend** — Flask + SQLite, hosted on a DigitalOcean Droplet (or any Linux VPS) at `api.axiompicks.com`

### Environment variables

**Backend (set in `/etc/environment` or a `.env` file sourced by systemd):**
```
ALLOWED_ORIGINS=https://axiompicks.com,https://www.axiompicks.com
PORT=5000
API_HOST=0.0.0.0
```

**Frontend (set in the Netlify UI under Site → Environment variables):**
```
API_BASE_URL=https://api.axiompicks.com
```

For local dev, no env files are needed — defaults point everything to `localhost`.
See `.env.example` (backend) and `web/.env.example` (frontend) for reference.

### Production server setup (DigitalOcean Droplet)

```bash
# One-time: populate the cache, run backtest history, train the meta-gate
python seed_db.py --lookback 7
python backtest_history.py
python train_meta_model.py --walk-forward --force

# Keep Flask running via systemd (see README.md for full unit file)
sudo systemctl start axiom-api
sudo systemctl enable axiom-api
```

The Flask prefetch thread handles real-time data updates automatically on startup —
no GitHub Actions or external cron is needed for picks freshness.

### Weekly cron (model retraining)

```
0 3 * * 1  cd /opt/axiom && python train_meta_model.py --walk-forward >> /var/log/axiom-retrain.log 2>&1
```

## Architecture

Sports betting analytics pipeline: scrape odds → cache → transform → Naive Bayes picks → REST API → Next.js website.

**Data flow:**
```
SportsBookReview.com
  → sports.py            (URL generation per sport/date/week)
  → retrieve.py          (HTML scraping → DataFrame)
  → store.py             (SQLite cache at data/cache.db —
                          games · cached_keys · backtest_history ·
                          rolling_backtest_cache · picks_log)
  → package.py           (odds → probabilities, scores → Win/Loss labels)
  → bayes.py / models.py (Naive Bayes / logistic regression classifiers)
  → betmath.py           (settle_pick: pick + actual + line → flat/kelly units)
  → picks.py             (PickEngine: train + predict_all)
  → runner.py            (daily orchestrator, cache-first then live)
  → prefetch.py          (background gap-fill, logs picks, settles results)
  → backtest.py          (walk-forward Backtester)
  → backtest_history.py  (CLI aggregator → backtest_history table)
  → api.py               (Flask REST API)
  → web/                 (Next.js 15 frontend — Axiom Terminal)
```

**Key Python modules:**

- **`config.py`** — `SPORTS` dict with date_type and season windows. `is_in_season(sport, date)` handles cross-year seasons. `date_to_week(sport, date)` converts calendar dates to SBR week numbers using `_WEEK1_STARTS`. `last_completed_season(sport, today=None)` returns `(season_year, start, end)` for the most recent season that has fully ended — used by `backtest_history.py`.

- **`store.py`** — SQLite cache at `data/cache.db` with four tables:
    - `games` — one row per game, odds lists JSON-encoded.
    - `cached_keys` — every fetched `(sport, cache_key)` (including empty days) so we don't re-fetch.
    - `backtest_history` — one row per `(sport, season_year, model)` written by `backtest_history.py`; powers `/api/history`.
    - `picks_log` — one row per Pick generated by the daily prefetch; settled with `result`, `flat_units`, `kelly_units` once the game's scores arrive. Powers `/api/history/recent-picks` and `/api/history/performance`.
  
  Public API: `save/load/exists/list_available(sport, key)`, `max_cached_date(sport)`, plus `save_backtest_history`, `load_backtest_history`, `log_picks`, `unsettled_picks`, `settle_pick_record`, `recent_settled_picks`, `daily_performance`.

- **`betmath.py`** — `settle_pick(pick, actual, bet_line, unit_size)` converts a settled outcome into `(flat_units, kelly_units, result)`. Single source of truth shared by `backtest.py` and `prefetch.settle_completed_picks`.

- **`sports.py`** — `BetTypes` base class generates spread/money-line/totals URLs. Nine sport subclasses (NFL, NBA, NHL, MLB, MLS, NCAAF, NCAAB, WNBA, CFL); week-based sports take an int week number, date-based take a `YYYY-MM-DD` string. CFL is date-based: SBR's `?week=` URL only returns placeholders for archived weeks, so `?date=` is used instead.

- **`retrieve.py`** — `SportsbookReviewAPI(url, bet_type, date_type, date, sport=...)` fetches HTML and dispatches to sport-specific `MoneyLineAPI` subclass. Base `clean_scores()` handles NBA/NFL/NHL/NCAAB (uses % wager markers as game separators). MLB/MLS/WNBA/CFL override with `_sequential_clean_scores()` to skip embedded team/pitcher names. `_PlayerNameMixin` filters goalie/pitcher names from odds data (NHL, MLB).

- **`package.py`** — `Package(df, true_prob=True/False)`. With `true_prob=True` returns merged DataFrame with `Away Odds`, `Home Odds`, `Away W/L`, `Home W/L`. With `true_prob=False` returns separate DataFrames for Naive Bayes training.

- **`bayes.py`** — `NaiveBayes(side, df)` where `side` is `'Home'` or `'Away'`. `probability(lines)` returns P(Win | lines) or None if no history. Prior is applied once (not per feature).

- **`picks.py`** — `PickEngine(sport, model_type='logreg', meta_threshold=0.0, season_year=None).train(historical_df)` fits home + away models. `predict_all(games_df)` returns `list[Pick]`. After selecting the higher-EV side, the engine consults `model.predict_pick_value(candidate)`: if the model returns a float (e.g. `logreg_v2`), the bet fires iff `predicted_units > meta_threshold` (REPLACES the legacy `EV >= 0` rule); if it returns `None`, the legacy rule applies. Every `Pick` carries `predicted_units` (None when no gate ran), `ev`, `bet_line`, and `unit_size` so callers see what the gate decided regardless of pass/fail. `season_year` is forwarded to `model.set_evaluation_context(...)` so `LogregV2Model` loads the leak-free per-season meta-gate when one exists.

- **`models.py`** — Registry of swappable win-probability models behind `build_model(name)`: `nb`, `nb_bucketed`, `logreg`, and the `logreg_v2` meta-gated composite. `_ModelBase.predict_pick_value(candidate)` defaults to `None` (legacy gate); `LogregV2Model` overrides it with a fitted `MetaGate` that predicts realized flat-units. `LogregV2Model.train()` only fits the underlying logistic regression — the meta-gate is a frozen offline-trained artifact.

- **`meta_models.py`** — Components for the `logreg_v2` meta-gate: `feature_vector(candidate)` (15-feature row: ev, confidence, line_magnitude, book_disagreement, book_count, model_market_gap, plus 9 sport one-hots), `consensus_home_prob_stats(away, home)` (single source of truth for de-vigging math, also reused by `LogisticRegressionModel`), `MetaGate` dataclass wrapping a `GradientBoostingRegressor` plus provenance metadata, and `save_meta_gate(gate, season_year=None)` / `load_meta_gate(name, season_year=None)` (lru-cached). Pickles live at `data/meta_models/<name>.pkl` (the "live" gate, used for daily picks and current-season rolling) and `data/meta_models/<name>.<Y>.pkl` (per-season gates, written by `--walk-forward`, used for honest backtesting of completed season Y). `load_meta_gate(name, season_year=Y)` prefers the season-keyed pickle and silently falls back to the live pickle when no season-specific file exists (the documented behavior for the in-progress season). Missing pickles raise a clear "run train_meta_model.py" error only on first `predict_pick_value` call (registry instantiation never loads the pickle).

- **`train_meta_model.py`** — One-shot CLI offline trainer for the meta-gate. Walk-forward backtests the chosen base model (default: `logreg`) over every completed cached season per sport and builds `(features, realized-units)` rows from `BacktestResult.game_log`. Two modes:
    - **Single-gate** (default, or `--holdout-season YYYY` / `--no-holdout`) — fits one gate and saves to `<name>.pkl`. Honest only on the held-out season.
    - **Walk-forward** (`--walk-forward`, recommended) — builds the corpus once, then fits one gate per holdout season Y excluding Y from training (saved as `<name>.<Y>.pkl`), plus a "live" gate on every completed season (saved as `<name>.pkl`). The Backtester loads the leak-free per-season gate automatically when evaluating any completed season, so `backtest_history.py` and `rolling_backtest.py` are out-of-sample everywhere.
  
  Both modes rebalance per-sport sample weights by default, print feature importances, and refuse to overwrite existing pickles without `--force`. Single-gate mode prints grouped 5-fold CV residuals; walk-forward mode prints per-holdout residuals (each season scored against the gate that didn't see it).

- **`runner.py`** — `get_daily_picks(sport, date_or_week, training_window_days=60, force_refresh=False, model_type='logreg', meta_threshold=0.0)` → `list[Pick]`. `run_all_sports(date)` iterates `config.SPORTS`, skips out-of-season, returns `{sport: [Pick, ...]}`. `model_type` and `meta_threshold` are plumbed through `get_upcoming_picks` / `run_all_sports_upcoming` as well.

- **`backtest.py`** — `Backtester(sport, start, end, model_type='logreg', meta_threshold=0.0).run()` → `BacktestResult`. Walk-forward only; raises `RuntimeError` on cache miss. For each test_key the Backtester derives the season the key falls into (via `_season_year_for_key`) and threads it through `PickEngine` so season-aware models load the leak-free per-season meta-gate. Units: correct `-200` → +0.50, correct `+150` → +1.50, wrong → −1.00, No Pick/Tie → 0.00. Each `GameResult` row carries `confidence`, `home_prob`, and `predicted_units` so `train_meta_model.py` can rebuild the meta-gate's feature vectors directly from a backtest's `game_log`.

- **`prefetch.py`** — `start_background_prefetch(fallback_days_back=60)` launches a daemon thread that gap-fills the cache from `store.max_cached_date(sport)` → today per sport (or the fallback window when the cache is empty), calling `runner._fetch_live` for missing entries. After each fetch it calls `store.log_picks(...)` for fresh picks and runs `settle_completed_picks()` to fill in `picks_log` results from completed games. Invoked from `api.py` at startup. Exposes `iter_cache_keys(sport, start, end)` which `seed_db.py` reuses.

- **`seed_db.py`** — One-shot CLI bulk loader. Seeds the last five season windows per sport so the website doesn't need to scrape everything on first run. See Commands above for flags.

- **`backtest_history.py`** — One-shot CLI aggregator. For each sport (or the `--sport` filter), runs `Backtester` over the most recent completed season window from `config.last_completed_season` and upserts the aggregate row into `store.backtest_history`. Use `--force` to recompute; otherwise existing rows are skipped. The Flask `/api/history` endpoint reads this table only — never recomputes on request. Each row carries `max_drawdown` (largest peak-to-trough loss in cumulative flat units) alongside flat/Kelly totals.

- **`rolling_backtest.py`** — Rolling N-day Backtester driver. `compute_rolling(sport, end_date, window_days)` runs `Backtester` over the last `window_days` for any in-season sport and upserts the result into `store.rolling_backtest_cache` keyed by `(sport, end_date, window_days, model)`. `compute_all_rolling()` iterates all sports and skips rows already computed today (use `--force` to recompute). Wired into `prefetch.start_background_prefetch()` so the cache is refreshed daily for 7/30/90-day windows. The Flask `/api/history/rolling` endpoint reads this cache; first-time hits compute synchronously.

- **`api.py`** — Flask server on port 5000 (waitress). Rewrites proxied from Next.js at `/api/*`. The picks endpoints accept `model=logreg_v2` and `meta_threshold=<float>` (default 0.0); `_pick_to_dict` emits `predicted_units` on every Pick. Endpoints:
    - `GET /api/sports`
    - `GET /api/picks?sport=&date=&model=&meta_threshold=`
    - `GET /api/picks/all?date=&model=&meta_threshold=`
    - `GET /api/picks/upcoming?date=&model=&meta_threshold=` (today + tomorrow per sport)
    - `POST /api/backtest` `{ sport, start, end, model?, meta_threshold? }` (returns `max_drawdown` and per-game `predicted_units` alongside units/accuracy)
    - `GET /api/history?model=` — read-only aggregate from `backtest_history` (includes `max_drawdown`)
    - `GET /api/history/recent-picks?limit=` — settled picks ledger
    - `GET /api/history/performance?days=` — daily/cumulative units from `picks_log` (legacy)
    - `GET /api/history/rolling?days=&model=` — rolling N-day backtest per in-season sport, served from `rolling_backtest_cache`. Drives the History tab and the Home/ticker last-30-day KPIs.
  
  Spawns the `prefetch` thread at startup.

**Frontend (`web/`):** Next.js 15 App Router · Tailwind CSS 3 · TypeScript. Single-page Axiom Terminal: header + ticker + 5 tabs (Home/Today/History/Backtest/About), no client-side routing.

- `web/next.config.ts` — rewrites `/api/*` → `http://localhost:5000/api/*`. Do not touch.
- `web/app/layout.tsx` — loads IBM Plex Sans + JetBrains Mono via `next/font/google`.
- `web/app/globals.css` — Axiom CSS vars (`--bg`, `--surface`, `--accent`, `--blue`, `--danger`, …) for light + `.dark` themes.
- `web/app/page.tsx` — renders `<TerminalShell />`.

Components (`web/components/terminal/`):
- `TerminalShell.tsx` — header (logo, tab switcher, dark toggle), ticker strip with live KPIs, mounts `MeshBg` and the active tab.
- `MeshBg.tsx` — animated canvas mesh background (port of `Axiom/mesh.jsx`, `precise` variant).
- `TerminalHome.tsx` — hero copy + 3-cell metrics strip + methodology card + sparkline + 4 teaser cards.
- `TerminalToday.tsx` — full board of upcoming picks with sport filter + sticky 420px detail panel.
- `TerminalHistory.tsx` — KPI strip + range tabs (7d/30d/90d) backed by the rolling-backtest cache. Shows max-drawdown alongside units won + a per-sport breakdown that also reflects the selected window.
- `TerminalBacktest.tsx` — sport/date form, KPI strip with results (incl. max drawdown), hand-drawn equity curve, season grid.
- `TerminalAbout.tsx` — plain-English explainer ("For Bettors") plus technical breakdown ("For Quants") of the pipeline, model, walk-forward training, edge math, and bet sizing.
- `GameCard.tsx` · `DetailPanel.tsx` · `KpiStrip.tsx` · `UnitsChart.tsx` · `SparklineChart.tsx` · `RecentPicksTable.tsx` · `SeasonGrid.tsx` · `SportFilter.tsx` — reusable building blocks.

Hooks (`web/lib/`):
- `use-upcoming-picks.ts` — `/api/picks/upcoming` (existing).
- `use-history.ts` — `/api/history`.
- `use-recent-picks.ts` — `/api/history/recent-picks`.
- `use-performance.ts` — `/api/history/performance`.
- `use-backtest.ts` — `POST /api/backtest`.
- `palette.ts` — `getPalette(dark)` returns the Axiom oklch palette object passed to every Terminal component.
- `formatters.ts` · `pick-adapter.ts` — display helpers (RawPick → GameCardData, etc.).

Note: the pipeline is moneyline-only. Spreads/totals are not modeled; the UI displays Moneyline + the actual `bet_line` consistently. The `Axiom/` folder stays on disk as design source but is not imported by the build.

**Supported sports:** NBA, NHL, MLB, MLS, NCAAB, WNBA, CFL (date-based) · NFL, NCAAF (week-based).

**Data dependency:** Live scraping requires a connection to SportsBookReview.com. Backtesting is cache-only — populate the cache first with `python seed_db.py`; the API's prefetch thread keeps it current on subsequent starts.

## Tests

```
tests/
  test_package.py           — implied_prob, true_prob, win_loss, to_values, to_nb_values
  test_bayes.py             — counts, probability bounds, always-win/loss lines, mixed
  test_models.py            — logistic-regression model wrapper
  test_picks.py             — PickEngine train + predict_all
  test_retrieve.py          — _is_odds, _is_player_name, clean_data, clean_scores, SportsbookReviewAPI
  test_sports.py            — all 9 sports instantiate, URL formats, NCAAF halves regression
  test_runner.py            — get_daily_picks orchestration, cache-first behavior, run_all_sports
  test_backtest.py          — Backtester walk-forward loop, cache-miss errors, units accounting
  test_betmath.py           — settle_pick math (correct/wrong/push/no-pick × kelly variants)
  test_store.py             — backtest_history upsert, picks_log insert/settle/query
  test_backtest_history.py  — CLI smoke test with mocked Backtester
  test_meta_models.py       — consensus_home_prob_stats, feature_vector, MetaGate
                              pickle roundtrip, LogregV2Model + PickEngine gate behavior
```

200+ tests total. All network calls are mocked with `unittest.mock.patch`. On Windows the `python` shim may be absent — use `py -m pytest tests/` if so.

**Legacy files (not part of the pipeline):**

- **`main.py`** — Hardcoded demo script (NFL week 9, NHL/NBA 2024-11-15). Use `runner.py` for real orchestration.
- **`deep_learn.py`** — Experimental TensorFlow/Keras neural network (not wired into the pipeline). Requires keras/tensorflow extras not in `requirements.txt`.
- **`tests.py`**, **`test_bayes.py`** (root-level) — Pre-pytest exploration scripts; superseded by `tests/`.
