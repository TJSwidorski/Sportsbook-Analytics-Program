"""
Sport configuration and calendar utilities.

SPORTS maps each sport key to its SBR date_type ('date' or 'week') and the
approximate season window as (MM-DD start, MM-DD end). Seasons that cross a
calendar year (e.g. NBA Oct-Jun) are handled by is_in_season().

date_to_week() converts a calendar date to a SBR week number for week-based
sports. _WEEK1_STARTS must be updated each season with the actual first-game
date of Week 1.
"""

import json as _json
import os as _os
from datetime import date

SPORTS: dict[str, dict] = {
    'nba':   {'date_type': 'date', 'season': ('10-01', '06-30')},
    'nfl':   {'date_type': 'week', 'season': ('09-01', '02-15')},
    'nhl':   {'date_type': 'date', 'season': ('10-01', '06-30')},
    'mlb':   {'date_type': 'date', 'season': ('03-20', '11-01')},
    'mls':   {'date_type': 'date', 'season': ('02-01', '12-01')},
    'ncaaf': {'date_type': 'week', 'season': ('08-20', '01-15')},
    'ncaab': {'date_type': 'date', 'season': ('11-01', '04-10')},
    'wnba':  {'date_type': 'date', 'season': ('05-01', '10-20')},
    'cfl':   {'date_type': 'date', 'season': ('06-01', '11-30')},
}

# First game date of Week 1 for each week-based sport and season year.
# Season year = the calendar year in which the regular season begins.
# Add new seasons here each year.
_WEEK1_STARTS: dict[str, dict[int, date]] = {
    'nfl': {
        2023: date(2023, 9, 7),
        2024: date(2024, 9, 5),
        2025: date(2025, 9, 4),
    },
    'ncaaf': {
        2023: date(2023, 8, 26),
        2024: date(2024, 8, 24),
        2025: date(2025, 8, 23),
    },
}


def is_in_season(sport: str, d: date) -> bool:
    """Return True if date *d* falls within the sport's season window."""
    cfg = SPORTS[sport]
    mm_dd_start, mm_dd_end = cfg['season']
    m_s, d_s = (int(x) for x in mm_dd_start.split('-'))
    m_e, d_e = (int(x) for x in mm_dd_end.split('-'))

    start = date(d.year, m_s, d_s)

    if m_e < m_s:
        # Season crosses a calendar year (e.g. Oct–Jun, Sep–Feb)
        end = date(d.year + 1, m_e, d_e)
        if d < start:
            # We're in the tail of the previous season (e.g. Jan playoffs)
            start = date(d.year - 1, m_s, d_s)
            end   = date(d.year,     m_e, d_e)
    else:
        end = date(d.year, m_e, d_e)

    return start <= d <= end


def season_window(sport: str, season_year: int) -> tuple[date, date]:
    """
    Return (start, end) calendar dates for the season of `sport` that *starts*
    in `season_year`. Cross-year seasons (NBA Oct-Jun, NFL Sep-Feb) end in
    `season_year + 1`.

    The `season_year` convention matches `_WEEK1_STARTS` and the rest of the
    pipeline: it is always the calendar year in which the regular season
    begins, even when most of the schedule plays out in the following year.
    """
    mm_dd_start, mm_dd_end = SPORTS[sport]['season']
    m_s, d_s = (int(x) for x in mm_dd_start.split('-'))
    m_e, d_e = (int(x) for x in mm_dd_end.split('-'))
    start = date(season_year, m_s, d_s)
    end_year = season_year + 1 if m_e < m_s else season_year
    end = date(end_year, m_e, d_e)
    return start, end


def last_completed_season(
    sport: str,
    today: date | None = None,
    lookback_years: int = 6,
) -> tuple[int, date, date] | None:
    """
    Return (season_year, start, end) for the most recent season whose end
    date is strictly before `today`. Used by backtest_history.py to pick a
    stable, fully-played window per sport regardless of where in the calendar
    we are. Returns None if no completed season is found within `lookback_years`.
    """
    today = today or date.today()
    for offset in range(0, lookback_years):
        season_year = today.year - offset
        start, end = season_window(sport, season_year)
        if end < today:
            return season_year, start, end
    return None


def date_to_week(sport: str, d: date) -> int | None:
    """
    Convert a calendar date to a SBR week number for week-based sports.

    Returns None when:
    - the sport is date-based
    - the date predates Week 1
    - the season year is not in _WEEK1_STARTS (add it manually)
    """
    if SPORTS[sport]['date_type'] != 'week':
        return None

    # Determine the season year. Seasons that start mid-year (Sep for NFL,
    # Aug for NCAAF, Jun for CFL): if the current month is before the start
    # month we are in the previous season's end (e.g. Jan playoffs).
    m_s = int(SPORTS[sport]['season'][0].split('-')[0])
    season_year = d.year if d.month >= m_s else d.year - 1

    week1 = _WEEK1_STARTS.get(sport, {}).get(season_year)
    if week1 is None:
        return None

    delta = (d - week1).days
    if delta < 0:
        return None

    return delta // 7 + 1


def _thresholds_path(gate_name: str) -> str:
    """Return the thresholds JSON path for a given gate name."""
    fname = 'thresholds.json' if gate_name == 'logreg_v2' else f'thresholds_{gate_name}.json'
    return _os.path.join(_os.path.dirname(__file__), 'data', 'meta_models', fname)


def load_gate_thresholds(gate_name: str) -> tuple[dict[str, float], dict[str, dict[int, float]]]:
    """
    Load per-sport meta-gate thresholds for a specific gate.

    logreg_v2 reads from thresholds.json (backward-compat).
    All other gate names read from thresholds_<gate_name>.json.

    Handles two JSON formats:
      Flat (old):   {sport: float, ...}
      Nested (new): {sport: {"live": float, "seasons": {year_str: float}}, ...}

    Returns:
      live_thresholds       — {sport: float} for daily picks (season_year=None)
      per_season_thresholds — {sport: {season_year_int: float}} for backtests
    """
    path = _thresholds_path(gate_name)
    if not _os.path.exists(path):
        return {}, {}
    with open(path) as f:
        raw = _json.load(f)

    live: dict[str, float] = {}
    per_season: dict[str, dict[int, float]] = {}

    for k, v in raw.items():
        if k.startswith('_'):
            continue
        if isinstance(v, (int, float)):
            live[k] = float(v)
        elif isinstance(v, dict):
            if 'live' in v:
                live[k] = float(v['live'])
            if 'seasons' in v and isinstance(v['seasons'], dict):
                per_season[k] = {int(yr): float(t) for yr, t in v['seasons'].items()}

    return live, per_season


def _load_per_sport_thresholds() -> tuple[dict[str, float], dict[str, dict[int, float]]]:
    return load_gate_thresholds('logreg_v2')


_PER_SPORT_THRESHOLDS, _PER_SPORT_SEASON_THRESHOLDS = _load_per_sport_thresholds()

# Live threshold per sport — used for daily picks (no season context).
# Loaded once at import from data/meta_models/thresholds.json.
PER_SPORT_THRESHOLDS: dict[str, float] = _PER_SPORT_THRESHOLDS

# Per-season threshold — used by Backtester/PickEngine when season_year is known.
# For season Y: threshold was selected using only seasons before Y (no lookahead).
# Seasons not present fall back to T=0.0 in PickEngine (not the live threshold).
PER_SPORT_SEASON_THRESHOLDS: dict[str, dict[int, float]] = _PER_SPORT_SEASON_THRESHOLDS
