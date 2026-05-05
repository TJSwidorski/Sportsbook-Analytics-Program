"""
One-shot CLI: walk every completed season that has cached data per sport, run
the walk-forward backtester, and persist aggregate stats + the per-game log to
the `backtest_history` table.

`/api/history` reads the resulting rows directly — no on-demand recomputation.
Re-run this whenever a new season finishes, you change the model, or the
backtest math (e.g. `max_drawdown` definition) changes.

By default this script **recomputes every completed season** that has any data
in the cache. Pass `--skip-existing` to leave already-aggregated rows alone.

Usage:
    python backtest_history.py                              # all sports, every cached season
    python backtest_history.py --sport nba,nhl
    python backtest_history.py --skip-existing              # only fill missing rows
    python backtest_history.py --model logreg --season 2024 # one specific season
"""

from __future__ import annotations

import argparse
import datetime
import sys
import time

import config
import store
from backtest import Backtester, _date_keys_in_range


_LOOKBACK_YEARS = 8


def _safe_div(num: float, denom: float) -> float | None:
    if not denom:
        return None
    return num / denom


def _existing_history_keys(model: str) -> set[tuple[str, int]]:
    """Return the (sport, season_year) tuples already persisted for `model`."""
    rows = store.load_backtest_history(model=model)
    return {(r['sport'], r['season_year']) for r in rows}


def _completed_seasons_with_data(
    sport: str,
    today: datetime.date,
    lookback_years: int = _LOOKBACK_YEARS,
) -> list[tuple[int, datetime.date, datetime.date]]:
    """
    Return [(season_year, start, end), ...] sorted ascending for every season
    whose end date is strictly before `today` AND that has at least one cached
    key inside its window. Caps the lookback at `lookback_years` seasons.
    """
    out: list[tuple[int, datetime.date, datetime.date]] = []
    seen: set[int] = set()
    for offset in range(0, lookback_years):
        season_year = today.year - offset
        if season_year in seen:
            continue
        seen.add(season_year)
        try:
            start, end = config.season_window(sport, season_year)
        except Exception:  # pragma: no cover — defensive
            continue
        if end >= today:
            continue
        keys = _date_keys_in_range(sport, start.isoformat(), end.isoformat())
        if not keys:
            continue
        out.append((season_year, start, end))
    out.sort(key=lambda x: x[0])
    return out


def aggregate_one(
    sport: str,
    season_year: int,
    start: datetime.date,
    end: datetime.date,
    model: str,
    *,
    force: bool,
    existing: set[tuple[str, int]],
) -> tuple[bool, str]:
    """Compute and persist a single (sport, season). Returns (changed, message)."""
    if not force and (sport, season_year) in existing:
        return False, f'{sport} season {season_year}: already aggregated (skip-existing)'

    print(f'[history] {sport} season {season_year}: backtesting {start} -> {end} ({model})')
    started = time.time()
    result = Backtester(
        sport,
        start.isoformat(),
        end.isoformat(),
        model_type=model,
    ).run()
    elapsed = time.time() - started

    if result.total_games == 0:
        return False, f'{sport} season {season_year}: no cached games in window'

    win_rate = _safe_div(result.correct_picks, result.games_picked)
    roi_flat = _safe_div(result.flat_units, result.games_picked)
    roi_kelly = _safe_div(result.kelly_units, result.games_picked)

    store.save_backtest_history(
        sport, season_year, result.model,
        start_date=result.start, end_date=result.end,
        total_games=result.total_games,
        games_picked=result.games_picked,
        correct_picks=result.correct_picks,
        win_rate=win_rate,
        flat_units=result.flat_units,
        kelly_units=result.kelly_units,
        roi_flat=roi_flat,
        roi_kelly=roi_kelly,
        max_drawdown=result.max_drawdown,
        game_log=result.game_log,
    )
    wr_text = f'{win_rate:.3f}' if win_rate is not None else 'n/a'
    summary = (
        f'{sport} season {season_year}: '
        f'picked={result.games_picked}/{result.total_games}, '
        f'wr={wr_text}, '
        f'flat={result.flat_units:+.2f}u, '
        f'kelly={result.kelly_units:+.4f} bankroll, '
        f'maxdd={result.max_drawdown:.2f}u '
        f'in {elapsed:.1f}s'
    )
    return True, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--sport',
        help='Comma-separated sports to aggregate (default: all in config.SPORTS)',
    )
    parser.add_argument(
        '--model',
        default='logreg',
        help='Model key — must match models.build_model (default: logreg)',
    )
    parser.add_argument(
        '--season',
        type=int,
        help='Limit to a single season year (e.g. --season 2024 → 2024-25 season)',
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Leave rows already in backtest_history alone (default: recompute everything)',
    )
    # Deprecated alias kept for back-compat with old README/runbooks.
    parser.add_argument(
        '--force',
        action='store_true',
        help='(Deprecated — recompute is now the default.) Ignored.',
    )
    args = parser.parse_args(argv)

    if args.sport:
        sports = [s.strip().lower() for s in args.sport.split(',') if s.strip()]
        unknown = [s for s in sports if s not in config.SPORTS]
        if unknown:
            parser.error(f'Unknown sport(s): {", ".join(unknown)}')
    else:
        sports = list(config.SPORTS)

    today = datetime.date.today()
    existing = _existing_history_keys(args.model)
    overall = time.time()
    force = not args.skip_existing
    print(
        f'[history] target sports={sports} model={args.model} '
        f'force={force} season_filter={args.season} today={today}'
    )

    successes = skips = errors = 0
    for sport in sports:
        seasons = _completed_seasons_with_data(sport, today)
        if not seasons:
            print(f'[history] {sport}: no completed cached seasons in lookback window')
            skips += 1
            continue
        if args.season is not None:
            seasons = [s for s in seasons if s[0] == args.season]
            if not seasons:
                print(f'[history] {sport}: season {args.season} not present in cache')
                skips += 1
                continue

        for season_year, start, end in seasons:
            try:
                changed, msg = aggregate_one(
                    sport, season_year, start, end, args.model,
                    force=force, existing=existing,
                )
            except Exception as exc:  # pragma: no cover — defensive
                errors += 1
                print(f'[history] {sport} season {season_year}: FAILED — {type(exc).__name__}: {exc}')
                continue
            if changed:
                successes += 1
                print(f'[history] {msg}')
            else:
                skips += 1
                print(f'[history] {msg}')

    elapsed = time.time() - overall
    print(
        f'[history] done in {elapsed:.1f}s -- '
        f'wrote={successes}, skipped={skips}, errors={errors}'
    )
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
