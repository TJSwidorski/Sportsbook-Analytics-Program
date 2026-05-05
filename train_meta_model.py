"""
Offline trainer for the `logreg_v2` meta-gate.

Walk-forward backtests the base model (default: logreg) over every completed,
cached season per sport, builds a (features, realized-units) corpus from the
resulting `BacktestResult.game_log`, fits a shallow gradient-boosted-tree
regressor, and pickles the result to `data/meta_models/<name>.pkl`. The Flask
API picks the new pickle up on the next process restart.

Usage:
    python train_meta_model.py
    python train_meta_model.py --base-model logreg --holdout-season 2024
    python train_meta_model.py --walk-forward --force
    python train_meta_model.py --no-rebalance --force

Modes:
    Default (single-gate, holdout = most recent completed season per sport):
        Writes `data/meta_models/<name>.pkl`. Honest ONLY when you backtest
        on the held-out season — every other season the gate has seen, so
        backtest_history numbers are inflated.

    `--walk-forward` (recommended for honest backtest_history / rolling):
        Builds the full corpus once and fits one gate per holdout season Y,
        each excluding Y. Saves them as `<name>.<Y>.pkl`. Also fits a
        "live" gate on every completed season as `<name>.pkl` for daily
        picks and the current-season rolling window (leak-free by
        construction — the trainer never includes incomplete seasons).
        The Backtester loads the right per-season gate automatically.

    `--holdout-season YYYY`:
        Single-gate with a fixed holdout for every sport.

    `--no-holdout`:
        Single-gate trained on every completed season — diagnostics only.

Diagnostic output includes per-sport row counts and feature importances.
Single-gate modes also print grouped 5-fold CV residuals; walk-forward
mode prints per-holdout residuals (each season scored against the gate
that didn't see it).
"""

from __future__ import annotations

import argparse
import datetime
import os
import pickle as _pkl
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any

import numpy as np
import sklearn
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold

import config
import meta_models
from backtest import Backtester, GameResult
from backtest_history import _completed_seasons_with_data
from betmath import decimal_odds, is_valid_line
from meta_models import (
    FEATURE_NAMES,
    SPORT_COLUMNS,
    MetaGate,
    _pickle_path,
    feature_vector,
    save_meta_gate,
)


# ---------------------------------------------------------------------------
# Per-(base_model, sport, season_year) corpus cache
# ---------------------------------------------------------------------------

_CORPUS_CACHE_DIR = os.path.join(
    os.path.dirname(__file__), 'data', 'meta_models', 'corpus_cache',
)


def _corpus_cache_path(base_model: str, sport: str, season_year: int) -> str:
    return os.path.join(_CORPUS_CACHE_DIR, f'{base_model}_{sport}_{season_year}.pkl')


# ---------------------------------------------------------------------------
# Module-level worker (must be at top-level for Windows multiprocessing spawn)
# ---------------------------------------------------------------------------

def _backtest_season(
    sport: str,
    season_year: int,
    start_iso: str,
    end_iso: str,
    base_model: str,
    use_cache: bool,
    force_recompute: bool,
) -> tuple[str, int, list[tuple[np.ndarray, float]], int, int]:
    """
    Backtest one (sport, season) pair and return corpus rows.

    Returns (sport, season_year, rows, total_games, kept) where:
      - rows is [(feature_vector, realized_units), ...]
      - total_games == -1 signals a cache hit (elapsed not meaningful)
    """
    cache_path = _corpus_cache_path(base_model, sport, season_year)
    if use_cache and not force_recompute and os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                rows = _pkl.load(f)
            return sport, season_year, rows, -1, len(rows)
        except Exception:
            pass  # corrupt cache — fall through and recompute

    try:
        result = Backtester(sport, start_iso, end_iso, model_type=base_model).run()
    except Exception as exc:
        print(f'[train_meta] {sport} season {season_year}: FAILED — {exc}')
        return sport, season_year, [], 0, 0

    rows: list[tuple[np.ndarray, float]] = []
    for g in result.game_log:
        if _eligible(g):
            rows.append((feature_vector(_row_to_candidate(g, sport, season_year)), float(g.units)))

    if use_cache:
        os.makedirs(_CORPUS_CACHE_DIR, exist_ok=True)
        with open(cache_path, 'wb') as f:
            _pkl.dump(rows, f, protocol=_pkl.HIGHEST_PROTOCOL)

    return sport, season_year, rows, result.total_games, len(rows)


def _row_to_candidate(g: GameResult, sport: str, season_year: int) -> dict[str, Any]:
    """Build the feature-vector input from a settled GameResult."""
    # Closing Line Value: how much did the line improve vs the opener?
    # away_lines[0] / home_lines[0] is the SBR 'Open' column.
    open_line = (g.away_lines[0] if g.pick == 'Away' else g.home_lines[0]) if (
        g.away_lines if g.pick == 'Away' else g.home_lines
    ) else None
    if (open_line and is_valid_line(open_line) and g.bet_line and is_valid_line(g.bet_line)):
        try:
            opening_line_edge = decimal_odds(g.bet_line) - decimal_odds(open_line)
        except (ValueError, ZeroDivisionError):
            opening_line_edge = 0.0
    else:
        opening_line_edge = 0.0

    # Season fraction: how far into the season is this game?
    season_fraction = 0.5  # safe fallback
    try:
        start, end = config.season_window(sport, season_year)
        game_date = datetime.date.fromisoformat(g.date_or_week)
        total_days = (end - start).days
        if total_days > 0:
            season_fraction = max(0.0, min(1.0, (game_date - start).days / total_days))
    except Exception:
        pass

    return {
        'sport': sport,
        'ev': g.ev or 0.0,
        'confidence': g.confidence,
        'bet_line': g.bet_line,
        'away_lines': g.away_lines,
        'home_lines': g.home_lines,
        'home_prob': g.home_prob,
        'opening_line_edge': opening_line_edge,
        'season_fraction': season_fraction,
    }


def _eligible(g: GameResult) -> bool:
    """Keep only rows that represent an actual placed bet that resolved."""
    return g.pick != 'No Pick' and g.actual != 'Tie' and g.bet_line is not None


def build_corpus(
    base_model: str,
    sports: list[str],
    today: datetime.date,
    holdout_season: int | None = None,
    use_default_holdout: bool = False,
    skip_holdout: bool = True,
    workers: int = 1,
    use_cache: bool = True,
    force: bool = False,
) -> tuple[
    np.ndarray, np.ndarray, list[str], list[int], dict[str, int], dict[str, int | None],
]:
    """
    Walk-forward backtest each (sport, completed_season) pair for `base_model`
    and accumulate (features, realized-units) rows. Returns:
        (X, y, group_sport, group_season, train_rows_per_sport, holdout_seasons)

    When `skip_holdout=True` (the single-gate flow), the per-sport holdout
    season is dropped at corpus-build time. When `skip_holdout=False`
    (walk-forward flow), every completed season is included and the caller
    filters per-holdout when fitting each gate.

    `workers > 1` runs each (sport, season) pair in a separate process.
    `use_cache=True` (default) stores each backtest result to disk so
    re-runs skip already-computed seasons. `force=True` bypasses the cache.
    """
    # --- Phase 1: collect tasks, respecting holdout logic ---
    tasks: list[tuple[str, int, str, str]] = []   # (sport, season_year, start_iso, end_iso)
    holdout_per_sport: dict[str, int | None] = {}

    for sport in sports:
        seasons = _completed_seasons_with_data(sport, today)
        if not seasons:
            print(f'[train_meta] {sport}: no completed cached seasons — skipping')
            holdout_per_sport[sport] = None
            continue

        if holdout_season is not None:
            held_out = holdout_season
        elif use_default_holdout:
            held_out = max(s[0] for s in seasons)
        else:
            held_out = None
        holdout_per_sport[sport] = held_out

        for season_year, start, end in seasons:
            if skip_holdout and held_out is not None and season_year == held_out:
                print(f'[train_meta] {sport} season {season_year}: holdout — skipped')
                continue
            tasks.append((sport, season_year, start.isoformat(), end.isoformat()))

    if not tasks:
        return (
            np.empty((0, len(FEATURE_NAMES))),
            np.empty(0),
            [], [],
            {},
            holdout_per_sport,
        )

    # --- Phase 2: run backtests (sequential or parallel) ---
    X_rows: list[np.ndarray] = []
    y_rows: list[float] = []
    group_sport: list[str] = []
    group_season: list[int] = []
    rows_per_sport: Counter[str] = Counter()

    def _absorb(sp: str, sy: int, rows: list, total_games: int, kept: int) -> None:
        if total_games == -1:
            print(f'[train_meta] {sp} season {sy}: cache hit — {kept} rows')
        else:
            print(f'[train_meta] {sp} season {sy}: kept {kept} / {total_games}')
        for fvec, units in rows:
            X_rows.append(fvec)
            y_rows.append(units)
            group_sport.append(sp)
            group_season.append(sy)
        rows_per_sport[sp] += kept

    n_workers = min(max(1, workers), len(tasks))
    if n_workers > 1:
        print(f'[train_meta] dispatching {len(tasks)} tasks across {n_workers} workers …')
        futures: dict = {}
        with ProcessPoolExecutor(max_workers=n_workers) as pool:
            for sport, season_year, start_iso, end_iso in tasks:
                f = pool.submit(
                    _backtest_season,
                    sport, season_year, start_iso, end_iso,
                    base_model, use_cache, force,
                )
                futures[f] = (sport, season_year)
            for future in as_completed(futures):
                sport, season_year = futures[future]
                try:
                    sp, sy, rows, total_games, kept = future.result()
                    _absorb(sp, sy, rows, total_games, kept)
                except Exception as exc:
                    print(f'[train_meta] {sport} season {season_year}: worker error — {exc}')
    else:
        for sport, season_year, start_iso, end_iso in tasks:
            print(
                f'[train_meta] {sport} season {season_year}: '
                f'backtesting {start_iso} -> {end_iso} ({base_model})'
            )
            t0 = time.time()
            sp, sy, rows, total_games, kept = _backtest_season(
                sport, season_year, start_iso, end_iso,
                base_model, use_cache, force,
            )
            elapsed = time.time() - t0
            if total_games == -1:
                print(f'[train_meta]   cache hit — {kept} rows ({elapsed:.1f}s)')
            else:
                print(f'[train_meta]   kept {kept} / {total_games} in {elapsed:.1f}s')
            for fvec, units in rows:
                X_rows.append(fvec)
                y_rows.append(units)
                group_sport.append(sp)
                group_season.append(sy)
            rows_per_sport[sp] += kept

    if not X_rows:
        return (
            np.empty((0, len(FEATURE_NAMES))),
            np.empty(0),
            [], [],
            dict(rows_per_sport),
            holdout_per_sport,
        )

    X = np.vstack(X_rows)
    y = np.asarray(y_rows, dtype=np.float64)
    return X, y, group_sport, group_season, dict(rows_per_sport), holdout_per_sport


def _fit_estimator(
    X: np.ndarray,
    y: np.ndarray,
    sample_weight: np.ndarray | None,
    args,
) -> GradientBoostingRegressor:
    estimator = GradientBoostingRegressor(
        max_depth=args.max_depth,
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate,
        subsample=0.8,
        min_samples_leaf=20,
        random_state=0,
    )
    estimator.fit(X, y, sample_weight=sample_weight)
    return estimator


def _build_gate(
    estimator: GradientBoostingRegressor,
    args,
    rows_per_sport: dict[str, int],
    holdout_seasons: dict[str, int | None],
) -> MetaGate:
    return MetaGate(
        estimator=estimator,
        feature_names=FEATURE_NAMES,
        sport_columns=SPORT_COLUMNS,
        base_model=args.base_model,
        name=args.name,
        trained_at=meta_models.now_iso(),
        sklearn_version=sklearn.__version__,
        train_rows_per_sport=rows_per_sport,
        holdout_seasons=holdout_seasons,
    )


def _sample_weights(group_sport: list[str], rebalance: bool) -> np.ndarray | None:
    """`1 / count(sport)` weights, normalized to mean=1. None when disabled."""
    if not rebalance or not group_sport:
        return None
    counts = Counter(group_sport)
    raw = np.array([1.0 / counts[s] for s in group_sport], dtype=np.float64)
    return raw * (len(raw) / raw.sum())


def _grouped_cv_residuals(
    X: np.ndarray,
    y: np.ndarray,
    groups: list[tuple[str, int]],
    sample_weight: np.ndarray | None,
    sport_labels: list[str],
    n_splits: int = 5,
) -> dict[str, dict[str, float]]:
    """5-fold grouped CV, returning per-sport mean residual + std."""
    if len(set(groups)) < n_splits:
        n_splits = max(2, len(set(groups)))
    if n_splits < 2 or len(y) < 50:
        return {}

    encoded_groups = np.array([hash(g) for g in groups])
    gkf = GroupKFold(n_splits=n_splits)
    per_sport_resid: defaultdict[str, list[float]] = defaultdict(list)

    for tr, te in gkf.split(X, y, groups=encoded_groups):
        est = GradientBoostingRegressor(
            max_depth=3, n_estimators=200, learning_rate=0.05,
            subsample=0.8, min_samples_leaf=20, random_state=0,
        )
        sw = sample_weight[tr] if sample_weight is not None else None
        est.fit(X[tr], y[tr], sample_weight=sw)
        preds = est.predict(X[te])
        for i, idx in enumerate(te):
            per_sport_resid[sport_labels[idx]].append(float(y[idx] - preds[i]))

    return {
        sport: {
            'mean': float(np.mean(rs)),
            'std': float(np.std(rs)),
            'n': len(rs),
        }
        for sport, rs in per_sport_resid.items()
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--base-model', default='logreg',
        help='Base model to backtest for the training corpus (default: logreg).',
    )
    parser.add_argument(
        '--name', default='logreg_v2',
        help='Output pickle name (default: logreg_v2).',
    )
    parser.add_argument(
        '--sport',
        help='Comma-separated sport keys (default: every key in config.SPORTS).',
    )
    parser.add_argument(
        '--holdout-season', type=int,
        help='Season year to exclude per sport. Default: most recent completed.',
    )
    parser.add_argument(
        '--no-holdout', action='store_true',
        help='Train on every season (no leakage protection — diagnostics only).',
    )
    parser.add_argument(
        '--no-rebalance', action='store_true',
        help='Disable per-sport sample-weight rebalancing.',
    )
    parser.add_argument(
        '--n-estimators', type=int, default=200,
        help='Number of boosted trees (default: 200).',
    )
    parser.add_argument(
        '--max-depth', type=int, default=3,
        help='Tree depth (default: 3).',
    )
    parser.add_argument(
        '--learning-rate', type=float, default=0.05,
        help='GBR learning rate (default: 0.05).',
    )
    parser.add_argument(
        '--walk-forward', action='store_true',
        help=(
            'Train one gate per holdout season (saved as <name>.<Y>.pkl) plus '
            'a "live" gate trained on every completed season (saved as '
            '<name>.pkl). Backtester loads the right per-season gate '
            'automatically — recommended for honest backtest_history.'
        ),
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Overwrite existing pickles and bypass corpus cache without prompting.',
    )
    parser.add_argument(
        '--workers', type=int, default=1,
        help=(
            'Worker processes for corpus building (default: 1). '
            'Each (sport, season) pair runs in its own process. '
            'Recommended: 4–8 on a modern machine.'
        ),
    )
    parser.add_argument(
        '--no-cache-corpus', action='store_true',
        help=(
            'Disable the on-disk corpus cache. By default each '
            '(sport, season) backtest result is saved to '
            'data/meta_models/corpus_cache/ so re-runs are instant.'
        ),
    )
    args = parser.parse_args(argv)

    if args.sport:
        sports = [s.strip().lower() for s in args.sport.split(',') if s.strip()]
        unknown = [s for s in sports if s not in config.SPORTS]
        if unknown:
            parser.error(f'Unknown sport(s): {", ".join(unknown)}')
    else:
        sports = list(config.SPORTS)

    if args.walk_forward and (args.holdout_season is not None or args.no_holdout):
        parser.error(
            '--walk-forward is mutually exclusive with --holdout-season / --no-holdout. '
            'Walk-forward mode trains one gate per holdout automatically.'
        )

    use_default_holdout = (args.holdout_season is None and not args.no_holdout)
    today = datetime.date.today()

    if not args.force:
        existing = [
            p for p in (
                _pickle_path(args.name),
                # In walk-forward mode the season-keyed pickles also count.
                # We can't know the season set until after the corpus is
                # built, so just guard the "live" pickle here; per-season
                # pickles are guarded individually before each save below.
            ) if os.path.exists(p)
        ]
        if existing:
            parser.error(
                f'Refusing to overwrite existing pickle(s): {existing}. '
                f'Pass --force to overwrite.'
            )

    print(
        f'[train_meta] base_model={args.base_model} sports={sports} '
        f'mode={"walk-forward" if args.walk_forward else "single-gate"} '
        f'holdout_season={args.holdout_season} '
        f'no_holdout={args.no_holdout} rebalance={not args.no_rebalance}'
    )

    use_cache = not args.no_cache_corpus
    if args.walk_forward:
        return _run_walk_forward(args, sports, today, use_cache)
    return _run_single_gate(args, sports, today, use_default_holdout, use_cache)


def _run_single_gate(
    args,
    sports: list[str],
    today: datetime.date,
    use_default_holdout: bool,
    use_cache: bool = True,
) -> int:
    """Default and `--holdout-season` / `--no-holdout` flows: fit one gate."""
    X, y, group_sport, group_season, rows_per_sport, holdout_seasons = build_corpus(
        base_model=args.base_model,
        sports=sports,
        today=today,
        holdout_season=args.holdout_season,
        use_default_holdout=use_default_holdout,
        skip_holdout=True,
        workers=args.workers,
        use_cache=use_cache,
        force=args.force,
    )

    if len(y) == 0:
        print('[train_meta] no training rows — aborting. Populate the cache first.')
        return 2

    print(f'[train_meta] training corpus: n={len(y)}, features={X.shape[1]}')
    for sport, count in sorted(rows_per_sport.items(), key=lambda kv: -kv[1]):
        print(f'[train_meta]   {sport:>6}: {count} rows')

    sample_weight = _sample_weights(group_sport, rebalance=not args.no_rebalance)

    # Grouped CV for honest per-sport residuals.
    cv_groups = list(zip(group_sport, group_season))
    print('[train_meta] running grouped CV …')
    cv_residuals = _grouped_cv_residuals(
        X, y, cv_groups, sample_weight, group_sport, n_splits=5,
    )
    if cv_residuals:
        for sport, stats in sorted(cv_residuals.items()):
            print(
                f'[train_meta]   CV residual {sport}: '
                f'mean={stats["mean"]:+.4f} std={stats["std"]:.4f} n={stats["n"]}'
            )
    else:
        print('[train_meta]   (skipped — too few groups or rows)')

    estimator = _fit_estimator(X, y, sample_weight, args)
    _print_feature_importances(estimator)

    gate = _build_gate(
        estimator, args, rows_per_sport,
        {s: holdout_seasons.get(s) for s in sports},
    )
    pkl_path = save_meta_gate(gate)
    print(f'[train_meta] wrote {pkl_path}')
    return 0


def _run_walk_forward(
    args,
    sports: list[str],
    today: datetime.date,
    use_cache: bool = True,
) -> int:
    """Build the corpus once, fit one gate per holdout season + the live gate."""
    X, y, group_sport, group_season, rows_per_sport, _ = build_corpus(
        base_model=args.base_model,
        sports=sports,
        today=today,
        holdout_season=None,
        use_default_holdout=False,
        skip_holdout=False,
        workers=args.workers,
        use_cache=use_cache,
        force=args.force,
    )

    if len(y) == 0:
        print('[train_meta] no training rows — aborting. Populate the cache first.')
        return 2

    print(f'[train_meta] training corpus: n={len(y)}, features={X.shape[1]}')
    for sport, count in sorted(rows_per_sport.items(), key=lambda kv: -kv[1]):
        print(f'[train_meta]   {sport:>6}: {count} rows')

    holdout_years = sorted(set(group_season))
    print(f'[train_meta] walk-forward: training {len(holdout_years) + 1} gates')

    season_arr = np.asarray(group_season)

    # Pre-flight: refuse to clobber any season-keyed pickle without --force.
    if not args.force:
        clashes = []
        for y_holdout in holdout_years:
            p = _pickle_path(args.name, season_year=y_holdout)
            if os.path.exists(p):
                clashes.append(p)
        if clashes:
            print(
                f'[train_meta] refusing to overwrite existing per-season '
                f'pickles: {clashes}. Pass --force to overwrite.'
            )
            return 1

    per_holdout_residuals: dict[int, dict[str, float]] = {}

    for y_holdout in holdout_years:
        train_mask = season_arr != y_holdout
        eval_mask  = season_arr == y_holdout
        n_train = int(train_mask.sum())
        n_eval = int(eval_mask.sum())
        if n_train == 0:
            print(f'[train_meta] skipping holdout {y_holdout}: empty training set')
            continue

        X_tr = X[train_mask]
        y_tr = y[train_mask]
        gs_tr = [group_sport[i] for i in range(len(group_sport)) if train_mask[i]]
        sw_tr = _sample_weights(gs_tr, rebalance=not args.no_rebalance)

        rows_per_sport_tr: Counter[str] = Counter()
        for s in gs_tr:
            rows_per_sport_tr[s] += 1

        estimator = _fit_estimator(X_tr, y_tr, sw_tr, args)

        # Score on the held-out season as the honest signal.
        if n_eval > 0:
            preds = estimator.predict(X[eval_mask])
            resid = y[eval_mask] - preds
            per_holdout_residuals[y_holdout] = {
                'n': float(n_eval),
                'mean_resid': float(np.mean(resid)),
                'std_resid': float(np.std(resid)),
                'mean_pred': float(np.mean(preds)),
                'mean_actual_units': float(np.mean(y[eval_mask])),
            }

        gate = _build_gate(
            estimator, args, dict(rows_per_sport_tr),
            {s: y_holdout for s in sports},
        )
        pkl_path = save_meta_gate(gate, season_year=y_holdout)
        print(
            f'[train_meta] holdout {y_holdout}: n_train={n_train} n_eval={n_eval} '
            f'-> {pkl_path}'
        )

    # Live gate: trained on EVERYTHING in the corpus. Used for daily picks
    # and the current-season rolling window — both naturally leak-free since
    # the trainer never includes incomplete seasons.
    sample_weight = _sample_weights(group_sport, rebalance=not args.no_rebalance)
    live_estimator = _fit_estimator(X, y, sample_weight, args)
    _print_feature_importances(live_estimator)

    live_gate = _build_gate(
        live_estimator, args, rows_per_sport,
        {s: None for s in sports},
    )
    live_path = save_meta_gate(live_gate)
    print(f'[train_meta] live gate (no holdout): n_train={len(y)} -> {live_path}')

    if per_holdout_residuals:
        print('[train_meta] per-holdout residuals (honest, out-of-sample):')
        for yr, stats in sorted(per_holdout_residuals.items()):
            print(
                f'[train_meta]   holdout {yr}: n={int(stats["n"])} '
                f'mean_pred={stats["mean_pred"]:+.4f} '
                f'mean_actual={stats["mean_actual_units"]:+.4f} '
                f'mean_resid={stats["mean_resid"]:+.4f} '
                f'std_resid={stats["std_resid"]:.4f}'
            )
    return 0


def _print_feature_importances(estimator: GradientBoostingRegressor) -> None:
    importance_pairs = sorted(
        zip(FEATURE_NAMES, estimator.feature_importances_),
        key=lambda kv: -kv[1],
    )
    print('[train_meta] feature importances:')
    for name, imp in importance_pairs:
        print(f'[train_meta]   {name:>22}: {imp:.4f}')


if __name__ == '__main__':
    sys.exit(main())
