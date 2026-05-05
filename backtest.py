"""
Walk-forward backtester.

Backtester iterates every cached date/week in [start, end] for a sport.
For each date D:
  - Training data = all cached entries in the same season as D, strictly before D
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
from betmath import settle_pick
from package import Package
from picks import PickEngine


@dataclass
class GameResult:
    game_index: int
    date_or_week: str
    pick: str        # 'Away' | 'Home' | 'No Pick'
    actual: str      # 'Away' | 'Home' | 'Tie'
    correct: bool
    units: float            # flat (1u per pick) — kept for back-compat
    kelly_units: float      # weighted by Pick.unit_size
    bet_line: str | None    # the line we'd actually bet at (best book, not opener)
    unit_size: float        # fractional Kelly bet size, 0 on No Pick
    ev: float | None        # EV at the time of pick
    away_lines: list
    home_lines: list
    confidence: float | None = None     # P(picked side wins) from the base model
    home_prob: float | None = None      # P(home wins) from the base model
    predicted_units: float | None = None  # meta-gate output, None when no gate ran


@dataclass
class BacktestResult:
    sport: str
    start: str
    end: str
    total_games: int
    games_picked: int
    correct_picks: int
    accuracy: float
    total_units: float       # flat staking
    flat_units: float        # explicit alias
    kelly_units: float       # fractional-Kelly staking
    max_drawdown: float = 0.0   # peak-to-trough drop in flat cumulative units, positive magnitude
    model: str = 'logreg'
    game_log: list[GameResult] = field(default_factory=list)


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


def _season_window_for(sport: str, test_date: datetime.date) -> tuple[datetime.date, datetime.date]:
    """
    Return (season_start, season_end) for the season that contains test_date.
    Mirrors the cross-year handling in config.is_in_season().
    """
    cfg = config.SPORTS[sport]
    mm_dd_start, mm_dd_end = cfg['season']
    m_s, d_s = (int(x) for x in mm_dd_start.split('-'))
    m_e, d_e = (int(x) for x in mm_dd_end.split('-'))

    start = datetime.date(test_date.year, m_s, d_s)

    if m_e < m_s:
        # Cross-year season (e.g. NBA Oct-Jun, NFL Sep-Feb)
        end = datetime.date(test_date.year + 1, m_e, d_e)
        if test_date < start:
            # Tail of the previous season (e.g. Jan playoffs)
            start = datetime.date(test_date.year - 1, m_s, d_s)
            end   = datetime.date(test_date.year,     m_e, d_e)
    else:
        end = datetime.date(test_date.year, m_e, d_e)

    return start, end


def _season_year_for_key(
    sport: str,
    test_key: str,
    fallback_date: datetime.date,
) -> int:
    """
    Return the season_year (per `config.season_window` convention: the
    calendar year the regular season begins) for a given test_key.

    Date-based sports parse the key directly. Week-based sports have no
    date in the key, so we fall back to the date the caller passed in
    (typically `Backtester.start` — week-based caches only ever hold one
    season's weeks at a time).
    """
    cfg = config.SPORTS[sport]
    if cfg['date_type'] == 'date':
        try:
            d = datetime.date.fromisoformat(test_key)
        except ValueError:
            d = fallback_date
    else:
        d = fallback_date
    season_start, _ = _season_window_for(sport, d)
    return season_start.year


def _training_keys_in_season(sport: str, test_key: str) -> list[str]:
    """
    Return all cached keys for sport within the same season as test_key,
    strictly before test_key. Walk-forward safe.

    For date-based sports, test_key is 'YYYY-MM-DD' and the season window is
    derived from config.SPORTS[sport]['season'].
    For week-based sports, test_key is a week number string; the cache only
    holds one season's worth of week keys (each save replaces prior weeks
    with the same number), so we just return all earlier numeric weeks.
    """
    available = store.list_available(sport)
    cfg = config.SPORTS[sport]

    if cfg['date_type'] == 'date':
        test_d = datetime.date.fromisoformat(test_key)
        season_start, _ = _season_window_for(sport, test_d)
        season_start_iso = season_start.strftime('%Y-%m-%d')
        return [
            k for k in available
            if season_start_iso <= k < test_key
        ]

    test_week = int(test_key)
    return [
        k for k in available
        if k.isdigit() and int(k) < test_week
    ]


class Backtester:
    def __init__(
        self,
        sport: str,
        start: str,
        end: str,
        model_type: str = 'logreg',
        meta_threshold: float = 0.0,
    ):
        self.sport = sport
        self.start = start
        self.end = end
        self.model_type = model_type
        self.meta_threshold = meta_threshold

    def _empty_result(self) -> BacktestResult:
        return BacktestResult(
            sport=self.sport, start=self.start, end=self.end,
            total_games=0, games_picked=0, correct_picks=0,
            accuracy=0.0, total_units=0.0,
            flat_units=0.0, kelly_units=0.0,
            model=self.model_type,
        )

    def run(self) -> BacktestResult:
        test_keys = _date_keys_in_range(self.sport, self.start, self.end)
        if not test_keys:
            return self._empty_result()

        try:
            fallback_date = datetime.date.fromisoformat(self.start)
        except ValueError:
            fallback_date = datetime.date.today()

        game_log: list[GameResult] = []

        for key in test_keys:
            df = store.load(self.sport, key)
            if df is None:
                raise RuntimeError(
                    f'Cache miss for {self.sport}/{key}. '
                    'Run the daily runner to populate the cache first.'
                )

            # Build training set from cached data in the same season, before this key
            train_keys = _training_keys_in_season(self.sport, key)
            frames = [store.load(self.sport, k) for k in train_keys]
            frames = [f for f in frames if f is not None]

            # Derive the season this test_key falls into so season-aware
            # models (logreg_v2) can load the leak-free per-season meta-gate
            # trained without seeing this season's data.
            season_year = _season_year_for_key(self.sport, key, fallback_date)

            cfg = config.SPORTS[self.sport]
            if cfg['date_type'] == 'date':
                try:
                    current_date = datetime.date.fromisoformat(key)
                except ValueError:
                    current_date = fallback_date
            else:
                current_date = fallback_date

            engine = PickEngine(
                self.sport,
                model_type=self.model_type,
                meta_threshold=self.meta_threshold,
                season_year=season_year,
                current_date=current_date,
            )
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

                flat, kelly, _result = settle_pick(
                    pick_obj.pick, actual, pick_obj.bet_line, pick_obj.unit_size,
                )
                correct = _result == 'W'

                game_log.append(GameResult(
                    game_index=idx,
                    date_or_week=key,
                    pick=pick_obj.pick,
                    actual=actual,
                    correct=correct,
                    units=flat,
                    kelly_units=kelly,
                    bet_line=pick_obj.bet_line,
                    unit_size=pick_obj.unit_size,
                    ev=pick_obj.ev,
                    away_lines=pick_obj.away_lines,
                    home_lines=pick_obj.home_lines,
                    confidence=pick_obj.confidence,
                    home_prob=pick_obj.home_prob,
                    predicted_units=pick_obj.predicted_units,
                ))

        total_games = len(game_log)
        games_picked = sum(1 for g in game_log if g.pick != 'No Pick' and g.actual != 'Tie')
        correct_picks = sum(1 for g in game_log if g.correct)
        accuracy = correct_picks / games_picked if games_picked > 0 else 0.0
        flat_units = sum(g.units for g in game_log)
        kelly_units = sum(g.kelly_units for g in game_log)
        max_drawdown = _max_drawdown(g.units for g in game_log)

        return BacktestResult(
            sport=self.sport,
            start=self.start,
            end=self.end,
            total_games=total_games,
            games_picked=games_picked,
            correct_picks=correct_picks,
            accuracy=accuracy,
            total_units=flat_units,
            flat_units=flat_units,
            kelly_units=kelly_units,
            max_drawdown=max_drawdown,
            model=self.model_type,
            game_log=game_log,
        )


def _max_drawdown(unit_series) -> float:
    """
    Furthest the cumulative flat-units curve dips below the starting
    bankroll of zero, returned as a positive magnitude. If the curve never
    goes negative, drawdown is 0.0.

    This intentionally measures absolute floor (worst red on the ledger),
    not peak-to-trough — readers consistently interpret "max drawdown" on a
    units chart as "how far below break-even did we get."
    """
    running = 0.0
    worst = 0.0
    for u in unit_series:
        running += u
        if running < worst:
            worst = running
    return abs(worst)
