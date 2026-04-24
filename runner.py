"""
Daily picks runner.

get_daily_picks() fetches (or loads from cache) odds for one sport/date, trains
a PickEngine on the preceding training_window_days of cached data, and returns
a list of Picks.

run_all_sports() iterates every sport in config.SPORTS, skips sports that are
out of season, and collects picks for a given calendar date string.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import pandas as pd

import config
import sports as sp
import store
from picks import Pick, PickEngine
from retrieve import SportsbookReviewAPI

# Maps sport key → (sports.py class, date_type)
_SPORT_CLASS = {
    'nba':   (sp.NBA,   'date'),
    'nfl':   (sp.NFL,   'week'),
    'nhl':   (sp.NHL,   'date'),
    'mlb':   (sp.MLB,   'date'),
    'mls':   (sp.MLS,   'date'),
    'ncaaf': (sp.NCAAF, 'week'),
    'ncaab': (sp.NCAAB, 'date'),
    'wnba':  (sp.WNBA,  'date'),
    'cfl':   (sp.CFL,   'week'),
}


def _fetch_live(sport: str, date_or_week) -> pd.DataFrame:
    """Fetch live data from SBR and return raw retrieve.py DataFrame."""
    cls, date_type = _SPORT_CLASS[sport]
    sport_obj = cls(date_or_week)
    url = sport_obj.money_line
    api = SportsbookReviewAPI(url, 'Money Line', date_type, date_or_week, sport=sport)
    return api.return_data()


def _cache_key(sport: str, date_or_week) -> str:
    return str(date_or_week)


def _training_dates(sport: str, anchor: datetime.date, window: int) -> list[str]:
    """Return date strings for the window days before anchor (exclusive)."""
    cfg = config.SPORTS[sport]
    date_type = cfg['date_type']
    keys = []
    for offset in range(1, window + 1):
        d = anchor - datetime.timedelta(days=offset)
        if not config.is_in_season(sport, d):
            continue
        if date_type == 'week':
            week = config.date_to_week(sport, d)
            if week is not None:
                key = str(week)
                if key not in keys:
                    keys.append(key)
        else:
            keys.append(d.strftime('%Y-%m-%d'))
    return keys


def get_daily_picks(
    sport: str,
    date_or_week,
    training_window_days: int = 60,
    force_refresh: bool = False,
) -> list[Pick]:
    """
    Return Naive Bayes picks for one sport on one date/week.

    Steps:
      1. Load today's odds from cache; fetch live and cache if absent or forced.
      2. Load training data from cache for the prior training_window_days.
      3. Train PickEngine on the combined training DataFrame.
      4. Return picks for today's games.
    """
    key = _cache_key(sport, date_or_week)

    if force_refresh or not store.exists(sport, key):
        df_today = _fetch_live(sport, date_or_week)
        store.save(sport, key, df_today)
    else:
        df_today = store.load(sport, key)

    if isinstance(date_or_week, str) and '-' in date_or_week:
        anchor = datetime.date.fromisoformat(date_or_week)
    else:
        # week-based: use today as anchor for training window lookup
        anchor = datetime.date.today()

    training_keys = _training_dates(sport, anchor, training_window_days)
    training_frames = []
    for tk in training_keys:
        df = store.load(sport, tk)
        if df is not None:
            training_frames.append(df)

    engine = PickEngine(sport)
    if training_frames:
        historical = pd.concat(training_frames, ignore_index=True)
        engine.train(historical)

    return engine.predict_all(df_today)


def run_all_sports(date: str) -> dict[str, list[Pick]]:
    """
    Return picks for every in-season sport on the given calendar date string.
    Week-based sports convert the date to a week number via config.date_to_week().
    Sports out of season are skipped (empty list in the result).
    """
    d = datetime.date.fromisoformat(date)
    results: dict[str, list[Pick]] = {}

    for sport, cfg in config.SPORTS.items():
        if not config.is_in_season(sport, d):
            results[sport] = []
            continue

        if cfg['date_type'] == 'week':
            date_or_week = config.date_to_week(sport, d)
            if date_or_week is None:
                results[sport] = []
                continue
        else:
            date_or_week = date

        try:
            results[sport] = get_daily_picks(sport, date_or_week)
        except Exception as exc:
            print(f'[runner] {sport} failed: {exc}')
            results[sport] = []

    return results
