"""
Background cache prefetcher.

On API startup this walks forward from the latest cached date (or a fallback
window when the cache is empty) to today, fetching any entries that are
missing from the SQLite cache. Runs in a daemon thread so Flask startup is
non-blocking. Progress and per-sport failures are logged to stdout so the
terminal doubles as a retrieval-bug surface.

The shared `iter_cache_keys(sport, start, end)` helper is also used by
seed_db.py for the one-shot bulk loader.
"""

from __future__ import annotations

import datetime
import threading
import time
from typing import Iterator

import config
import store
from runner import _fetch_live


def iter_cache_keys(
    sport: str,
    start: datetime.date,
    end: datetime.date,
) -> Iterator[tuple[object, str]]:
    """
    Yield unique (date_or_week, cache_key) pairs for the in-season days in
    [start, end] (inclusive). Week-based sports dedupe so each week number
    appears at most once.

    `date_or_week` is what gets passed to runner._fetch_live — an int for
    week-based sports, a 'YYYY-MM-DD' string for date-based.
    `cache_key` is the str form used by the store module.
    """
    if end < start:
        return
    cfg = config.SPORTS[sport]
    seen: set[str] = set()

    day = start
    while day <= end:
        if not config.is_in_season(sport, day):
            day += datetime.timedelta(days=1)
            continue

        if cfg['date_type'] == 'week':
            week = config.date_to_week(sport, day)
            if week is not None:
                key = str(week)
                if key not in seen:
                    seen.add(key)
                    yield week, key
        else:
            key = day.strftime('%Y-%m-%d')
            if key not in seen:
                seen.add(key)
                yield key, key

        day += datetime.timedelta(days=1)


def refresh_today_and_tomorrow(delay_seconds: float = 0.5) -> None:
    """
    Force-refresh today's and tomorrow's slate for every in-season sport.

    The gap-fill loop in prefetch_recent only fetches keys that aren't yet in
    the cache. That means once today's row is written (even if the slate was
    incomplete at fetch time, e.g. SBR hadn't listed all games yet), it stays
    stuck until tomorrow rolls around. This pass runs separately and overwrites
    today's and tomorrow's keys regardless of cache presence so the front-end
    always sees the live SBR slate.
    """
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    for sport in config.SPORTS:
        for date_or_week, key in iter_cache_keys(sport, today, tomorrow):
            try:
                df = _fetch_live(sport, date_or_week)
                store.save(sport, key, df)
                print(f'[prefetch:refresh] {sport}/{key}: refreshed {len(df)} rows')
            except Exception as exc:
                print(f'[prefetch:refresh] {sport}/{key}: FAILED — {type(exc).__name__}: {exc}')
            if delay_seconds:
                time.sleep(delay_seconds)


def prefetch_recent(
    fallback_days_back: int = 60,
    delay_seconds: float = 0.5,
) -> None:
    """
    Walk each sport from MAX(cached_date)+1 (or today - fallback_days_back
    when nothing is cached) up to today, fetching missing entries.

    Also force-refreshes today's and tomorrow's slate up front so a stale row
    from earlier in the day doesn't undercount the live game list.
    """
    print(f'[prefetch] starting — fallback_window={fallback_days_back} days')
    overall_start = time.time()
    refresh_today_and_tomorrow(delay_seconds=delay_seconds)
    today = datetime.date.today()

    for sport in config.SPORTS:
        fetched = skipped = errors = 0
        sport_start = time.time()

        max_cached = store.max_cached_date(sport)
        if max_cached is None:
            window_start = today - datetime.timedelta(days=fallback_days_back)
            print(f'[prefetch] {sport}: no cache — fetching last {fallback_days_back} days')
        else:
            window_start = max_cached + datetime.timedelta(days=1)
            print(f'[prefetch] {sport}: gap-fill from {window_start} to {today}')

        for date_or_week, key in iter_cache_keys(sport, window_start, today):
            if store.exists(sport, key):
                skipped += 1
                continue

            try:
                df = _fetch_live(sport, date_or_week)
                store.save(sport, key, df)
                fetched += 1
                print(f'[prefetch] {sport}/{key}: cached {len(df)} rows')
            except Exception as exc:
                errors += 1
                print(f'[prefetch] {sport}/{key}: FAILED — {type(exc).__name__}: {exc}')

            if delay_seconds:
                time.sleep(delay_seconds)

        elapsed = time.time() - sport_start
        print(
            f'[prefetch] {sport} done in {elapsed:.1f}s '
            f'(fetched={fetched}, already_cached={skipped}, errors={errors})'
        )

    print(f'[prefetch] all sports done in {time.time() - overall_start:.1f}s')

    _refresh_rolling_backtests()


def _refresh_rolling_backtests() -> None:
    """
    Recompute the rolling 7/30/90-day backtests for every in-season sport.
    Cheap when rows for today already exist (skipped via `rolling_computed_today`).
    Imported lazily so prefetch can run even if rolling_backtest fails to import.
    """
    try:
        from rolling_backtest import compute_all_rolling
    except Exception as exc:  # pragma: no cover — defensive
        print(f'[prefetch] rolling backtest import failed: {exc}')
        return

    for window in (7, 30, 90):
        started = time.time()
        try:
            statuses = compute_all_rolling(window_days=window)
        except Exception as exc:  # pragma: no cover — defensive
            print(f'[prefetch] rolling-{window}d FAILED — {type(exc).__name__}: {exc}')
            continue
        computed = sum(1 for v in statuses.values() if v == 'computed')
        cached = sum(1 for v in statuses.values() if v == 'cached')
        skipped = len(statuses) - computed - cached
        print(
            f'[prefetch] rolling-{window}d: computed={computed} cached={cached} '
            f'skipped={skipped} in {time.time() - started:.1f}s'
        )


def start_background_prefetch(fallback_days_back: int = 60) -> threading.Thread:
    """Launch prefetch_recent on a daemon thread and return the handle."""
    thread = threading.Thread(
        target=prefetch_recent,
        kwargs={'fallback_days_back': fallback_days_back},
        name='cache-prefetch',
        daemon=True,
    )
    thread.start()
    return thread
