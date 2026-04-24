"""
One-shot cache seeder.

Populates the SQLite cache (data/cache.db) with the two most recent seasons
for each sport (or a subset via flags). Run this once so the Naive Bayes
training window and the backtester have history to chew on without making
the website wait on a full scrape at startup.

Usage:
    python seed_db.py
    python seed_db.py --sport nba,nhl
    python seed_db.py --seasons previous --delay 1.0
    python seed_db.py --sport wnba --force
"""

from __future__ import annotations

import argparse
import datetime
import sys
import time

import config
import store
from prefetch import iter_cache_keys
from runner import _fetch_live


def _season_window(sport: str, season_year: int) -> tuple[datetime.date, datetime.date]:
    """
    Return (start, end) calendar dates for a sport's season starting in
    `season_year`. Handles seasons that cross a calendar year.
    """
    mm_dd_start, mm_dd_end = config.SPORTS[sport]['season']
    m_s, d_s = (int(x) for x in mm_dd_start.split('-'))
    m_e, d_e = (int(x) for x in mm_dd_end.split('-'))
    start = datetime.date(season_year, m_s, d_s)
    end_year = season_year + 1 if m_e < m_s else season_year
    end = datetime.date(end_year, m_e, d_e)
    return start, end


def most_recent_seasons(
    sport: str,
    today: datetime.date,
    count: int = 2,
) -> list[tuple[datetime.date, datetime.date, int]]:
    """
    Return up to `count` season windows (newest first) whose start is on or
    before `today`. Each entry is (start, end, season_year).
    """
    windows: list[tuple[datetime.date, datetime.date, int]] = []
    for offset in range(0, 6):
        season_year = today.year - offset
        start, end = _season_window(sport, season_year)
        if start <= today:
            windows.append((start, end, season_year))
        if len(windows) >= count:
            break
    return windows


def _pick_seasons(
    sport: str,
    today: datetime.date,
    which: str,
) -> list[tuple[datetime.date, datetime.date, int]]:
    windows = most_recent_seasons(sport, today, count=2)
    if which == 'current':
        return windows[:1]
    if which == 'previous':
        return windows[1:2]
    return windows


def seed_sport(
    sport: str,
    seasons: str,
    delay: float,
    force: bool,
    today: datetime.date,
) -> tuple[int, int, int]:
    """Seed one sport; returns (fetched, skipped, errors)."""
    windows = _pick_seasons(sport, today, seasons)
    if not windows:
        print(f'[seed] {sport}: no matching seasons — skipping')
        return 0, 0, 0

    fetched = skipped = errors = 0
    for start, end, season_year in windows:
        clamp_end = min(end, today)
        print(
            f'[seed] {sport} season {season_year}: '
            f'{start} → {clamp_end} '
            f'(season end {end})'
        )
        for date_or_week, key in iter_cache_keys(sport, start, clamp_end):
            if not force and store.exists(sport, key):
                skipped += 1
                continue
            try:
                df = _fetch_live(sport, date_or_week)
                store.save(sport, key, df)
                fetched += 1
                print(f'[seed] {sport}/{key}: cached {len(df)} rows')
            except Exception as exc:
                errors += 1
                print(f'[seed] {sport}/{key}: FAILED — {type(exc).__name__}: {exc}')
            if delay:
                time.sleep(delay)

    return fetched, skipped, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--sport',
        help='Comma-separated list of sports to seed (default: all in config.SPORTS)',
    )
    parser.add_argument(
        '--seasons',
        choices=('both', 'current', 'previous'),
        default='both',
        help='Which season(s) to seed relative to today',
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Seconds to sleep between scrapes',
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-fetch keys that are already cached',
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
    overall_start = time.time()
    print(
        f'[seed] target sports={sports} seasons={args.seasons} '
        f'delay={args.delay}s force={args.force}'
    )

    totals = {'fetched': 0, 'skipped': 0, 'errors': 0}
    for sport in sports:
        sport_start = time.time()
        fetched, skipped, errors = seed_sport(
            sport, args.seasons, args.delay, args.force, today,
        )
        totals['fetched'] += fetched
        totals['skipped'] += skipped
        totals['errors'] += errors
        elapsed = time.time() - sport_start
        print(
            f'[seed] {sport} done in {elapsed:.1f}s '
            f'(fetched={fetched}, already_cached={skipped}, errors={errors})'
        )

    print(
        f'[seed] all done in {time.time() - overall_start:.1f}s — '
        f'fetched={totals["fetched"]}, already_cached={totals["skipped"]}, '
        f'errors={totals["errors"]}'
    )
    return 0 if totals['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
