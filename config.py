"""
Sport configuration and calendar utilities.

SPORTS maps each sport key to its SBR date_type ('date' or 'week') and the
approximate season window as (MM-DD start, MM-DD end). Seasons that cross a
calendar year (e.g. NBA Oct-Jun) are handled by is_in_season().

date_to_week() converts a calendar date to a SBR week number for week-based
sports. _WEEK1_STARTS must be updated each season with the actual first-game
date of Week 1.
"""

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
    'cfl':   {'date_type': 'week', 'season': ('06-01', '11-30')},
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
    'cfl': {
        2023: date(2023, 6, 8),
        2024: date(2024, 6, 6),
        2025: date(2025, 6, 5),
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
