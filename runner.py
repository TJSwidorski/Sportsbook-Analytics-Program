"""
Daily picks runner.

get_daily_picks() fetches (or loads from cache) odds for one sport/date, trains
a PickEngine on the preceding training_window_days of cached data, and returns
a list of Picks.

run_all_sports() iterates every sport in config.SPORTS, skips sports that are
out of season, and collects picks for a given calendar date string.

get_upcoming_picks() / run_all_sports_upcoming() power the front page: today's
picks with already-completed games filtered out, plus tomorrow's full slate.
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
from backtest import _season_window_for

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
    'cfl':   (sp.CFL,   'date'),
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


def _training_keys_for_date(sport: str, test_key: str) -> list[str]:
    """
    Return cached keys for training: the full previous season plus the current
    season-to-date (strictly before test_key). This eliminates the cold-start
    problem at the start of each season while matching the Backtester's logic.

    Week-based sports (NFL, NCAAF) store week numbers as keys — previous season
    weeks are overwritten in the cache — so they fall back to all earlier weeks.
    """
    available = store.list_available(sport)
    cfg = config.SPORTS[sport]

    if cfg['date_type'] == 'date':
        test_d = datetime.date.fromisoformat(test_key)
        season_start, _ = _season_window_for(sport, test_d)
        prev_season_start, _ = _season_window_for(sport, season_start - datetime.timedelta(days=1))
        prev_start_iso = prev_season_start.strftime('%Y-%m-%d')
        return [k for k in available if prev_start_iso <= k < test_key]

    test_week = int(test_key)
    return [k for k in available if k.isdigit() and int(k) < test_week]


def get_daily_picks(
    sport: str,
    date_or_week,
    training_window_days: int = 60,  # unused; kept for API compatibility
    force_refresh: bool = False,
    model_type: str = 'logreg',
    meta_threshold: float = 0.0,
) -> list[Pick]:
    """
    Return picks for one sport on one date/week.

    Training data = all cached entries in the same season, strictly before
    date_or_week — identical to the Backtester's walk-forward logic so that
    live predictions are comparable to backtest performance.
    """
    key = _cache_key(sport, date_or_week)

    if force_refresh or not store.exists(sport, key):
        df_today = _fetch_live(sport, date_or_week)
        store.save(sport, key, df_today)
    else:
        df_today = store.load(sport, key)

    training_keys = _training_keys_for_date(sport, key)
    training_frames = []
    for tk in training_keys:
        df = store.load(sport, tk)
        if df is not None:
            training_frames.append(df)

    engine = PickEngine(sport, model_type=model_type, meta_threshold=meta_threshold)
    if training_frames:
        historical = pd.concat(training_frames, ignore_index=True)
        engine.train(historical)

    return engine.predict_all(df_today)


def run_all_sports(
    date: str,
    model_type: str = 'logreg',
    meta_threshold: float = 0.0,
) -> dict[str, list[Pick]]:
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
            results[sport] = get_daily_picks(
                sport, date_or_week,
                model_type=model_type, meta_threshold=meta_threshold,
            )
        except Exception as exc:
            print(f'[runner] {sport} failed: {exc}')
            results[sport] = []

    return results


def _is_score_present(value) -> bool:
    """True iff value is a non-empty string/number that parses as a number."""
    if value is None:
        return False
    if isinstance(value, float) and pd.isna(value):
        return False
    s = str(value).strip()
    if not s:
        return False
    try:
        float(s)
    except ValueError:
        return False
    return True


def _completed_indices(df: pd.DataFrame) -> set[int]:
    """Row positions in df where both Away Score and Home Score are present numbers."""
    if df is None or df.empty:
        return set()
    away = df.get('Away Score')
    home = df.get('Home Score')
    if away is None or home is None:
        return set()
    completed: set[int] = set()
    for i in range(len(df)):
        if _is_score_present(away.iloc[i]) and _is_score_present(home.iloc[i]):
            completed.add(i)
    return completed


def _picks_for_date(
    sport: str,
    d: datetime.date,
    filter_completed: bool,
    model_type: str = 'logreg',
    meta_threshold: float = 0.0,
) -> list[Pick]:
    """
    Return picks for one sport on one calendar date.
    If filter_completed is True, drop picks whose game already has both final scores.
    """
    cfg = config.SPORTS.get(sport)
    if cfg is None or not config.is_in_season(sport, d):
        return []

    if cfg['date_type'] == 'week':
        date_or_week = config.date_to_week(sport, d)
        if date_or_week is None:
            return []
    else:
        date_or_week = d.isoformat()

    try:
        picks = get_daily_picks(
            sport, date_or_week,
            model_type=model_type, meta_threshold=meta_threshold,
        )
    except Exception as exc:
        print(f'[runner] {sport} {d} failed: {exc}')
        return []

    if not filter_completed:
        return picks

    key = _cache_key(sport, date_or_week)
    df = store.load(sport, key)
    completed = _completed_indices(df)
    if not completed:
        return picks
    return [p for p in picks if p.game_index not in completed]


def get_upcoming_picks(
    sport: str,
    today_iso: str,
    model_type: str = 'logreg',
    meta_threshold: float = 0.0,
) -> dict[str, list[Pick]]:
    """
    Return {'today': [...], 'tomorrow': [...]} for one sport.

    'today' is the unplayed-only slice for today_iso.
    'tomorrow' is the full slate for the day after — no completion filter
    (these games haven't happened yet by definition).

    Out-of-season days yield an empty list for that bucket.
    """
    today_d = datetime.date.fromisoformat(today_iso)
    tomorrow_d = today_d + datetime.timedelta(days=1)
    return {
        'today': _picks_for_date(
            sport, today_d, filter_completed=True,
            model_type=model_type, meta_threshold=meta_threshold,
        ),
        'tomorrow': _picks_for_date(
            sport, tomorrow_d, filter_completed=False,
            model_type=model_type, meta_threshold=meta_threshold,
        ),
    }


def run_all_sports_upcoming(
    today_iso: str,
    model_type: str = 'logreg',
    meta_threshold: float = 0.0,
) -> dict[str, dict[str, list[Pick]]]:
    """Return {sport: {'today': [...], 'tomorrow': [...]}} for every sport in SPORTS."""
    return {
        sport: get_upcoming_picks(
            sport, today_iso,
            model_type=model_type, meta_threshold=meta_threshold,
        )
        for sport in config.SPORTS
    }
