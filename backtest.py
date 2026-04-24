"""
Walk-forward backtester.

Backtester iterates every cached date/week in [start, end] for a sport.
For each date D:
  - Training data = cached entries from [D - window, D-1]
  - Test data     = cached entry for D (raises RuntimeError if absent)
  - Picks are generated and compared against actual scores.

No live network requests are made during backtesting.

Units calculation (moneyline odds-adjusted):
  - Correct pick on -200 line → +0.5 units (100 / 200)
  - Correct pick on +150 line → +1.5 units (150 / 100)
  - Wrong pick                → -1.0 units
  - No Pick or Tie            →  0.0 units
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

import pandas as pd

import config
import store
from package import Package
from picks import PickEngine


@dataclass
class GameResult:
    game_index: int
    date_or_week: str
    pick: str        # 'Away' | 'Home' | 'No Pick'
    actual: str      # 'Away' | 'Home' | 'Tie'
    correct: bool
    units: float
    away_lines: list
    home_lines: list


@dataclass
class BacktestResult:
    sport: str
    start: str
    end: str
    total_games: int
    games_picked: int
    correct_picks: int
    accuracy: float
    total_units: float
    game_log: list[GameResult] = field(default_factory=list)


def _moneyline_units(pick: str, actual: str, away_lines: list, home_lines: list) -> float:
    """Return units won/lost for one game."""
    if pick == 'No Pick' or actual == 'Tie':
        return 0.0

    picked_line = away_lines[0] if pick == 'Away' else home_lines[0]

    if pick != actual:
        return -1.0

    # Correct pick — calculate payout
    if picked_line.startswith('+'):
        return int(picked_line[1:]) / 100.0
    else:
        return 100.0 / int(picked_line[1:])


def _actual_result(scores_row: list) -> str:
    """Return 'Away', 'Home', or 'Tie' from [away_score, home_score]."""
    try:
        away = float(scores_row[0])
        home = float(scores_row[1])
    except (ValueError, IndexError, TypeError):
        return 'Tie'
    if away > home:
        return 'Away'
    if home > away:
        return 'Home'
    return 'Tie'


def _date_keys_in_range(sport: str, start: str, end: str) -> list[str]:
    """
    Return sorted list of cached date/week keys for sport in [start, end].
    For date-based sports the keys are 'YYYY-MM-DD' strings; for week-based
    sports the keys are week number strings (sorted numerically).
    """
    available = store.list_available(sport)
    cfg = config.SPORTS[sport]

    if cfg['date_type'] == 'date':
        filtered = [
            k for k in available
            if start <= k <= end
        ]
        return sorted(filtered)
    else:
        # Week-based: filter by converting start/end to weeks
        start_d = datetime.date.fromisoformat(start)
        end_d = datetime.date.fromisoformat(end)
        start_week = config.date_to_week(sport, start_d)
        end_week = config.date_to_week(sport, end_d)
        if start_week is None or end_week is None:
            return []
        filtered = [
            k for k in available
            if k.isdigit() and start_week <= int(k) <= end_week
        ]
        return sorted(filtered, key=int)


def _training_keys_before(sport: str, test_key: str, window_days: int) -> list[str]:
    """
    Return cached keys for sport within window_days before test_key.
    For date-based sports, test_key is 'YYYY-MM-DD'.
    For week-based sports, test_key is a week number string — we approximate
    by returning the subset of cached week keys numerically before test_key.
    """
    available = store.list_available(sport)
    cfg = config.SPORTS[sport]

    if cfg['date_type'] == 'date':
        test_d = datetime.date.fromisoformat(test_key)
        cutoff = test_d - datetime.timedelta(days=window_days)
        return [
            k for k in available
            if cutoff.strftime('%Y-%m-%d') <= k < test_key
        ]
    else:
        test_week = int(test_key)
        # Approximate: include up to window_days // 7 weeks before test week
        weeks_back = max(1, window_days // 7)
        return [
            k for k in available
            if k.isdigit() and (test_week - weeks_back) <= int(k) < test_week
        ]


class Backtester:
    def __init__(
        self,
        sport: str,
        start: str,
        end: str,
        training_window_days: int = 60,
    ):
        self.sport = sport
        self.start = start
        self.end = end
        self.training_window_days = training_window_days

    def run(self) -> BacktestResult:
        test_keys = _date_keys_in_range(self.sport, self.start, self.end)
        if not test_keys:
            return BacktestResult(
                sport=self.sport, start=self.start, end=self.end,
                total_games=0, games_picked=0, correct_picks=0,
                accuracy=0.0, total_units=0.0,
            )

        game_log: list[GameResult] = []

        for key in test_keys:
            df = store.load(self.sport, key)
            if df is None:
                raise RuntimeError(
                    f'Cache miss for {self.sport}/{key}. '
                    'Run the daily runner to populate the cache first.'
                )

            # Build training set from cached data before this key
            train_keys = _training_keys_before(self.sport, key, self.training_window_days)
            frames = [store.load(self.sport, k) for k in train_keys]
            frames = [f for f in frames if f is not None]

            engine = PickEngine(self.sport)
            if frames:
                historical = pd.concat(frames, ignore_index=True)
                engine.train(historical)

            picks = engine.predict_all(df)

            # Derive actual results from the scores columns in df
            for pick_obj in picks:
                idx = pick_obj.game_index
                try:
                    row = df.iloc[idx]
                    actual = _actual_result([row.get('Away Score'), row.get('Home Score')])
                except IndexError:
                    actual = 'Tie'

                units = _moneyline_units(
                    pick_obj.pick, actual,
                    pick_obj.away_lines, pick_obj.home_lines,
                )
                correct = (
                    pick_obj.pick != 'No Pick'
                    and actual != 'Tie'
                    and pick_obj.pick == actual
                )

                game_log.append(GameResult(
                    game_index=idx,
                    date_or_week=key,
                    pick=pick_obj.pick,
                    actual=actual,
                    correct=correct,
                    units=units,
                    away_lines=pick_obj.away_lines,
                    home_lines=pick_obj.home_lines,
                ))

        total_games = len(game_log)
        games_picked = sum(1 for g in game_log if g.pick != 'No Pick' and g.actual != 'Tie')
        correct_picks = sum(1 for g in game_log if g.correct)
        accuracy = correct_picks / games_picked if games_picked > 0 else 0.0
        total_units = sum(g.units for g in game_log)

        return BacktestResult(
            sport=self.sport,
            start=self.start,
            end=self.end,
            total_games=total_games,
            games_picked=games_picked,
            correct_picks=correct_picks,
            accuracy=accuracy,
            total_units=total_units,
            game_log=game_log,
        )
