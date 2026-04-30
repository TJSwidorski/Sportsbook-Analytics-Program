"""
Rolling N-day backtest aggregator.

Runs `Backtester` over the most recent `window_days` for each sport that is
currently in season, then upserts the aggregate row into the
`rolling_backtest_cache` table. The Flask /api/history/rolling endpoint reads
this cache directly so page loads stay fast.

Refresh policy: results are cached per (sport, end_date, window_days, model).
`compute_all_rolling()` skips sports that already have a row computed today
unless `force=True`.

Triggered automatically by `prefetch.start_background_prefetch()` once per
calendar day. Can be run manually:

    python rolling_backtest.py
    python rolling_backtest.py --window 7
    python rolling_backtest.py --force --sport nba,nhl
"""

from __future__ import annotations

import argparse
import datetime
import sys
import time
from collections import defaultdict
from typing import Optional

import config
import store
from backtest import Backtester


def _daily_units_from_log(game_log) -> list[dict]:
    """
    Bucket a backtest game_log into a per-day series with cumulative units.
    Each entry: {day, units, kelly_units, cum_units, cum_kelly_units}.

    Date-based sports use `date_or_week` directly; week-based sports collapse
    to the cache_key as a stand-in (so the chart still has a continuous
    series even if the x-axis is weeks rather than dates).
    """
    by_day_flat = defaultdict(float)
    by_day_kelly = defaultdict(float)
    for g in game_log:
        key = getattr(g, 'date_or_week', None) if not isinstance(g, dict) else g.get('date_or_week')
        if not key:
            continue
        flat = float(getattr(g, 'units', 0.0) if not isinstance(g, dict) else g.get('units', 0.0))
        kelly = float(getattr(g, 'kelly_units', 0.0) if not isinstance(g, dict) else g.get('kelly_units', 0.0))
        by_day_flat[key] += flat
        by_day_kelly[key] += kelly

    series = []
    cum_flat = 0.0
    cum_kelly = 0.0
    for day in sorted(by_day_flat.keys()):
        cum_flat += by_day_flat[day]
        cum_kelly += by_day_kelly[day]
        series.append({
            'day': day,
            'units': round(by_day_flat[day], 4),
            'kelly_units': round(by_day_kelly[day], 6),
            'cum_units': round(cum_flat, 4),
            'cum_kelly_units': round(cum_kelly, 6),
        })
    return series


def compute_rolling(
    sport: str,
    end_date: datetime.date,
    window_days: int = 30,
    model: str = 'logreg',
) -> Optional[dict]:
    """
    Run `Backtester(sport, end_date - window_days, end_date)` and persist the
    result. Returns the saved row as a dict, or None if the sport is not in
    season at `end_date` or the cache is empty for the window.
    """
    if not config.is_in_season(sport, end_date):
        return None

    start_date = end_date - datetime.timedelta(days=window_days - 1)
    try:
        result = Backtester(
            sport,
            start_date.isoformat(),
            end_date.isoformat(),
            model_type=model,
        ).run()
    except RuntimeError:
        # Cache miss in the window — skip this sport for now; the prefetch
        # thread will fill it in and we'll catch it on the next run.
        return None

    if result.total_games == 0:
        return None

    win_rate = (
        result.correct_picks / result.games_picked
        if result.games_picked else None
    )
    daily_units = _daily_units_from_log(result.game_log)

    store.save_rolling_backtest(
        sport,
        end_date=end_date.isoformat(),
        window_days=int(window_days),
        start_date=start_date.isoformat(),
        model=model,
        total_games=result.total_games,
        games_picked=result.games_picked,
        correct_picks=result.correct_picks,
        win_rate=win_rate,
        flat_units=result.flat_units,
        kelly_units=result.kelly_units,
        max_drawdown=result.max_drawdown,
        daily_units=daily_units,
        game_log=result.game_log,
    )
    return {
        'sport': sport,
        'end_date': end_date.isoformat(),
        'window_days': int(window_days),
        'start_date': start_date.isoformat(),
        'total_games': result.total_games,
        'games_picked': result.games_picked,
        'correct_picks': result.correct_picks,
        'win_rate': win_rate,
        'flat_units': result.flat_units,
        'kelly_units': result.kelly_units,
        'max_drawdown': result.max_drawdown,
        'daily_units': daily_units,
    }


def compute_all_rolling(
    end_date: Optional[datetime.date] = None,
    window_days: int = 30,
    model: str = 'logreg',
    *,
    force: bool = False,
    sports: Optional[list[str]] = None,
) -> dict[str, str]:
    """
    Compute rolling backtests for every in-season sport. Skips sports whose
    cache row was already computed today unless `force=True`. Returns a map
    of {sport: status} for logging.
    """
    end_date = end_date or datetime.date.today()
    sport_keys = sports or list(config.SPORTS.keys())
    statuses: dict[str, str] = {}

    for sport in sport_keys:
        if not config.is_in_season(sport, end_date):
            statuses[sport] = 'out-of-season'
            continue
        if not force and store.rolling_computed_today(sport, window_days, model):
            statuses[sport] = 'cached'
            continue
        try:
            row = compute_rolling(sport, end_date, window_days, model)
        except Exception as exc:  # pragma: no cover — defensive
            statuses[sport] = f'error: {type(exc).__name__}: {exc}'
            continue
        statuses[sport] = 'computed' if row else 'no-data'

    return statuses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sport', help='Comma-separated sports (default: all)')
    parser.add_argument('--window', type=int, default=30, help='Window in days (default: 30)')
    parser.add_argument('--end-date', help='YYYY-MM-DD (default: today)')
    parser.add_argument('--model', default='logreg')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args(argv)

    sports = (
        [s.strip().lower() for s in args.sport.split(',') if s.strip()]
        if args.sport else None
    )
    if sports:
        unknown = [s for s in sports if s not in config.SPORTS]
        if unknown:
            parser.error(f'Unknown sport(s): {", ".join(unknown)}')

    end_date = (
        datetime.date.fromisoformat(args.end_date)
        if args.end_date else datetime.date.today()
    )

    started = time.time()
    statuses = compute_all_rolling(
        end_date=end_date,
        window_days=args.window,
        model=args.model,
        force=args.force,
        sports=sports,
    )
    elapsed = time.time() - started

    for sport, status in statuses.items():
        print(f'[rolling] {sport}: {status}')
    print(f'[rolling] window={args.window}d end={end_date} elapsed={elapsed:.1f}s')
    return 0


if __name__ == '__main__':
    sys.exit(main())
