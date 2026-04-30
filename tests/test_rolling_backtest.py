"""Tests for rolling_backtest.py — windowed Backtester driver + cache hooks."""

import datetime
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import store
import rolling_backtest


class _RollingTestBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, 'cache.db')
        self._patcher = patch.object(store, '_DB_PATH', self.db_path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)


def _fake_result(units_per_day):
    """Build a minimal BacktestResult-like object for compute_rolling tests.

    game_log entries are dicts so store._game_log_to_json can JSON-encode them.
    """
    log_entries = []
    correct = 0
    for day, units in units_per_day:
        log_entries.append({
            'game_index': 0,
            'date_or_week': day,
            'pick': 'Home',
            'actual': 'Home' if units > 0 else 'Away',
            'correct': units > 0,
            'units': units,
            'kelly_units': units * 0.01,
            'bet_line': '-110',
            'unit_size': 0.01,
            'ev': 0.04,
            'away_lines': ['+100'],
            'home_lines': ['-110'],
        })
        if units > 0:
            correct += 1
    res = MagicMock()
    res.total_games = len(log_entries)
    res.games_picked = len(log_entries)
    res.correct_picks = correct
    res.flat_units = sum(u for _, u in units_per_day)
    res.kelly_units = sum(u * 0.01 for _, u in units_per_day)
    res.max_drawdown = 0.5
    res.start = '2026-03-31'
    res.end = '2026-04-29'
    res.model = 'logreg'
    res.game_log = log_entries
    return res


class TestComputeRolling(_RollingTestBase):
    def test_skips_out_of_season_sport(self):
        # NCAAF is week-based, season Sep-Feb. April 29 is offseason.
        with patch('rolling_backtest.config.is_in_season', return_value=False):
            row = rolling_backtest.compute_rolling(
                'nfl', datetime.date(2026, 4, 29), window_days=30,
            )
        self.assertIsNone(row)

    def test_persists_row_for_in_season_sport(self):
        units_per_day = [
            ('2026-04-27', 1.0),
            ('2026-04-28', -0.5),
            ('2026-04-29', 0.8),
        ]
        with patch('rolling_backtest.config.is_in_season', return_value=True), \
             patch('rolling_backtest.Backtester') as MockBt:
            MockBt.return_value.run.return_value = _fake_result(units_per_day)
            row = rolling_backtest.compute_rolling(
                'nba', datetime.date(2026, 4, 29), window_days=30,
            )

        self.assertIsNotNone(row)
        self.assertEqual(row['sport'], 'nba')
        self.assertEqual(row['window_days'], 30)
        self.assertAlmostEqual(row['flat_units'], 1.3)

        cached = store.load_rolling_backtest(window_days=30)
        self.assertEqual(len(cached), 1)
        # daily_units should reflect the per-day buckets.
        self.assertEqual(len(cached[0]['daily_units']), 3)

    def test_returns_none_when_backtester_raises_cache_miss(self):
        with patch('rolling_backtest.config.is_in_season', return_value=True), \
             patch('rolling_backtest.Backtester') as MockBt:
            MockBt.return_value.run.side_effect = RuntimeError('cache miss')
            row = rolling_backtest.compute_rolling(
                'nba', datetime.date(2026, 4, 29), window_days=30,
            )
        self.assertIsNone(row)

    def test_returns_none_when_no_games_in_window(self):
        with patch('rolling_backtest.config.is_in_season', return_value=True), \
             patch('rolling_backtest.Backtester') as MockBt:
            MockBt.return_value.run.return_value = _fake_result([])
            row = rolling_backtest.compute_rolling(
                'nba', datetime.date(2026, 4, 29), window_days=30,
            )
        self.assertIsNone(row)


class TestComputeAllRolling(_RollingTestBase):
    def test_skips_already_computed_when_not_forced(self):
        # Pre-seed a row for today so rolling_computed_today returns True.
        store.save_rolling_backtest(
            sport='nba',
            end_date=datetime.date.today().isoformat(),
            window_days=30,
            start_date='2026-03-31',
            model='logreg',
            total_games=10, games_picked=10, correct_picks=5,
            win_rate=0.5, flat_units=0.0, kelly_units=0.0, max_drawdown=0.0,
            daily_units=[], game_log=[],
        )
        with patch('rolling_backtest.config.is_in_season', return_value=True), \
             patch('rolling_backtest.compute_rolling') as mock_compute:
            statuses = rolling_backtest.compute_all_rolling(
                window_days=30, sports=['nba'], force=False,
            )
        self.assertEqual(statuses['nba'], 'cached')
        mock_compute.assert_not_called()

    def test_force_recomputes_even_when_cached(self):
        store.save_rolling_backtest(
            sport='nba',
            end_date=datetime.date.today().isoformat(),
            window_days=30,
            start_date='2026-03-31',
            model='logreg',
            total_games=10, games_picked=10, correct_picks=5,
            win_rate=0.5, flat_units=0.0, kelly_units=0.0, max_drawdown=0.0,
            daily_units=[], game_log=[],
        )
        with patch('rolling_backtest.config.is_in_season', return_value=True), \
             patch('rolling_backtest.compute_rolling', return_value={'sport': 'nba'}) as mock_compute:
            statuses = rolling_backtest.compute_all_rolling(
                window_days=30, sports=['nba'], force=True,
            )
        self.assertEqual(statuses['nba'], 'computed')
        mock_compute.assert_called_once()

    def test_marks_out_of_season_sports(self):
        with patch('rolling_backtest.config.is_in_season', return_value=False):
            statuses = rolling_backtest.compute_all_rolling(
                window_days=30, sports=['nba', 'nfl'],
            )
        self.assertEqual(statuses['nba'], 'out-of-season')
        self.assertEqual(statuses['nfl'], 'out-of-season')


if __name__ == '__main__':
    unittest.main()
