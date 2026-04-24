"""
SQLite-backed cache for scraped game data.

Single database file at `data/cache.db` with two tables:

    games         one row per game — odds lists are JSON-encoded
    cached_keys   one row per (sport, cache_key) that has been fetched,
                  including empty days, so we don't re-fetch them forever

Public API preserves the shape the old parquet store exposed, so all callers
in runner.py, backtest.py, and prefetch.py continue to work:

    save(sport, key, df)
    load(sport, key) -> DataFrame | None
    exists(sport, key) -> bool
    list_available(sport) -> list[str]

`max_cached_date(sport)` is new — prefetch uses it for incremental gap-fill.
"""

from __future__ import annotations

import datetime
import json
import os
import sqlite3
from typing import Optional

import pandas as pd

import config

_DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'cache.db')

_SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  sport        TEXT    NOT NULL,
  cache_key    TEXT    NOT NULL,
  date         TEXT,
  week         INTEGER,
  row_index    INTEGER NOT NULL,
  away_lines   TEXT    NOT NULL,
  home_lines   TEXT    NOT NULL,
  away_score   TEXT,
  home_score   TEXT
);

CREATE TABLE IF NOT EXISTS cached_keys (
  sport        TEXT NOT NULL,
  cache_key    TEXT NOT NULL,
  fetched_at   TEXT NOT NULL,
  PRIMARY KEY (sport, cache_key)
);

CREATE INDEX IF NOT EXISTS idx_games_sport_key  ON games(sport, cache_key);
CREATE INDEX IF NOT EXISTS idx_games_sport_date ON games(sport, date);
"""


def _connect() -> sqlite3.Connection:
    """Open the cache DB, creating the schema on first touch."""
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.executescript(_SCHEMA)
    return conn


def _label_column(sport: str) -> tuple[str, str]:
    """Return (column_name, column_value) for the Date/Week column of a sport."""
    if config.SPORTS[sport]['date_type'] == 'date':
        return 'Date', ''
    return 'Week', ''


def _derive_date_week(sport: str, cache_key: str) -> tuple[Optional[str], Optional[int]]:
    """Split a cache_key into (date, week) columns for the games table."""
    if config.SPORTS[sport]['date_type'] == 'date':
        return cache_key, None
    try:
        return None, int(cache_key)
    except ValueError:
        return None, None


def _coerce_score(value) -> Optional[str]:
    """Normalize a score cell to a TEXT value or NULL."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    return str(value)


def _coerce_lines(value) -> Optional[list]:
    """Return a list of line strings, or None for missing/NaN cells."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    try:
        return list(value)
    except TypeError:
        return None


def save(sport: str, key: str, df: pd.DataFrame) -> None:
    """Replace any existing rows for (sport, key) with the new DataFrame.

    Rows with NaN/missing Away Lines or Home Lines are skipped — without odds
    there's nothing to predict on, and upstream pd.concat() can pad rows when
    the scores frame is longer than the lines frame.
    """
    cache_key = str(key)
    date_col, week_col = _derive_date_week(sport, cache_key)
    now = datetime.datetime.utcnow().isoformat(timespec='seconds')

    rows = []
    for i, row in df.iterrows():
        away_lines = _coerce_lines(row.get('Away Lines'))
        home_lines = _coerce_lines(row.get('Home Lines'))
        if away_lines is None or home_lines is None:
            continue
        rows.append((
            sport,
            cache_key,
            date_col,
            week_col,
            int(i),
            json.dumps(away_lines),
            json.dumps(home_lines),
            _coerce_score(row.get('Away Score')),
            _coerce_score(row.get('Home Score')),
        ))

    conn = _connect()
    try:
        with conn:
            conn.execute(
                'DELETE FROM games WHERE sport = ? AND cache_key = ?',
                (sport, cache_key),
            )
            if rows:
                conn.executemany(
                    'INSERT INTO games '
                    '(sport, cache_key, date, week, row_index, '
                    ' away_lines, home_lines, away_score, home_score) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    rows,
                )
            conn.execute(
                'INSERT INTO cached_keys (sport, cache_key, fetched_at) '
                'VALUES (?, ?, ?) '
                'ON CONFLICT(sport, cache_key) DO UPDATE SET fetched_at = excluded.fetched_at',
                (sport, cache_key, now),
            )
    finally:
        conn.close()


def load(sport: str, key: str) -> Optional[pd.DataFrame]:
    """Return the cached DataFrame for (sport, key), or None if never fetched."""
    cache_key = str(key)

    conn = _connect()
    try:
        fetched = conn.execute(
            'SELECT 1 FROM cached_keys WHERE sport = ? AND cache_key = ?',
            (sport, cache_key),
        ).fetchone()
        if fetched is None:
            return None

        rows = conn.execute(
            'SELECT away_lines, home_lines, away_score, home_score '
            'FROM games WHERE sport = ? AND cache_key = ? '
            'ORDER BY row_index',
            (sport, cache_key),
        ).fetchall()
    finally:
        conn.close()

    date_type = config.SPORTS[sport]['date_type']
    label_col = 'Date' if date_type == 'date' else 'Week'
    label_val = cache_key if date_type == 'date' else f'Week {cache_key}'

    away_lines: list = []
    home_lines: list = []
    away_scores: list = []
    home_scores: list = []
    for away_json, home_json, away_score, home_score in rows:
        away_lines.append(json.loads(away_json))
        home_lines.append(json.loads(home_json))
        away_scores.append(away_score)
        home_scores.append(home_score)

    df = pd.DataFrame({
        label_col: [label_val] * len(rows),
        'Away Lines': away_lines,
        'Home Lines': home_lines,
        'Away Score': away_scores,
        'Home Score': home_scores,
    })
    return df


def exists(sport: str, key: str) -> bool:
    """True if (sport, key) has ever been fetched (even if it had zero games)."""
    conn = _connect()
    try:
        row = conn.execute(
            'SELECT 1 FROM cached_keys WHERE sport = ? AND cache_key = ?',
            (sport, str(key)),
        ).fetchone()
    finally:
        conn.close()
    return row is not None


def list_available(sport: str) -> list[str]:
    """Return every cache_key that has been fetched for sport."""
    conn = _connect()
    try:
        rows = conn.execute(
            'SELECT cache_key FROM cached_keys WHERE sport = ?',
            (sport,),
        ).fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def max_cached_date(sport: str) -> Optional[datetime.date]:
    """
    Latest calendar date we have cached for a sport, across both date- and
    week-based sports. Returns None if nothing is cached.

    For week-based sports the returned date is an approximation: Week1-start
    plus 7*(week-1) days. That's close enough for the prefetch "start here"
    calculation — over-fetching by a few days is cheap.
    """
    date_type = config.SPORTS[sport]['date_type']

    conn = _connect()
    try:
        if date_type == 'date':
            row = conn.execute(
                'SELECT MAX(date) FROM games WHERE sport = ? AND date IS NOT NULL',
                (sport,),
            ).fetchone()
            value = row[0] if row else None
            if not value:
                return None
            try:
                return datetime.date.fromisoformat(value)
            except ValueError:
                return None

        row = conn.execute(
            'SELECT MAX(week) FROM games WHERE sport = ? AND week IS NOT NULL',
            (sport,),
        ).fetchone()
        max_week = row[0] if row else None
        if max_week is None:
            return None
    finally:
        conn.close()

    # Find the most recent season that has Week1 defined and whose Week1 date
    # plus (max_week - 1) * 7 days is plausible.
    starts = getattr(config, '_WEEK1_STARTS', {}).get(sport, {})
    if not starts:
        return None
    today = datetime.date.today()
    best: Optional[datetime.date] = None
    for season_year, week1 in starts.items():
        candidate = week1 + datetime.timedelta(days=7 * (max_week - 1))
        if candidate <= today and (best is None or candidate > best):
            best = candidate
    return best
