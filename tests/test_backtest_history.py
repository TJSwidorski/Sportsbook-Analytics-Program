"""Smoke tests for backtest_history.py CLI."""

import datetime
import os
import tempfile
import unittest
from unittest.mock import patch

import backtest_history
import store
from backtest import BacktestResult, GameResult


class _CliTestBase(unittest.TestCase):
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


def _fake_result(sport='nba', start='2024-10-01', end='2025-06-30'):
    log = [
        GameResult(
            game_index=0, date_or_week='2024-11-15',
            pick='Home', actual='Home', correct=True,
            units=1.0, kelly_units=0.04,
            bet_line='+100', unit_size=0.04, ev=0.02,
            away_lines=['+105'], home_lines=['-105'],
        ),
        GameResult(
            game_index=1, date_or_week='2024-11-15',
            pick='Away', actual='Home', correct=False,
            units=-1.0, kelly_units=-0.03,
            bet_line='+200', unit_size=0.03, ev=0.05,
            away_lines=['+205'], home_lines=['-220'],
        ),
    ]
    return BacktestResult(
        sport=sport, start=start, end=end,
        total_games=2, games_picked=2, correct_picks=1,
        accuracy=0.5, total_units=0.0,
        flat_units=0.0, kelly_units=0.01,
        max_drawdown=1.0,
        model='logreg', game_log=log,
    )


class TestAggregateOne(_CliTestBase):
    @patch('backtest_history.Backtester')
    def test_writes_history_row(self, mock_backtester):
        mock_backtester.return_value.run.return_value = _fake_result()
        start = datetime.date(2024, 10, 1)
        end = datetime.date(2025, 6, 30)

        changed, msg = backtest_history.aggregate_one(
            'nba', 2024, start, end, 'logreg',
            force=True, existing=set(),
        )
        self.assertTrue(changed, msg=msg)

        rows = store.load_backtest_history(sport='nba')
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['season_year'], 2024)
        self.assertEqual(row['games_picked'], 2)
        self.assertAlmostEqual(row['win_rate'], 0.5)
        self.assertAlmostEqual(row['max_drawdown'], 1.0)

    @patch('backtest_history.Backtester')
    def test_skip_existing_when_not_force(self, mock_bt):
        mock_bt.return_value.run.return_value = _fake_result()
        start = datetime.date(2024, 10, 1)
        end = datetime.date(2025, 6, 30)

        changed, msg = backtest_history.aggregate_one(
            'nba', 2024, start, end, 'logreg',
            force=False, existing={('nba', 2024)},
        )
        self.assertFalse(changed)
        self.assertIn('already aggregated', msg)
        mock_bt.return_value.run.assert_not_called()

    @patch('backtest_history.Backtester')
    def test_force_recomputes_existing(self, mock_bt):
        mock_bt.return_value.run.return_value = _fake_result()
        start = datetime.date(2024, 10, 1)
        end = datetime.date(2025, 6, 30)

        changed, _msg = backtest_history.aggregate_one(
            'nba', 2024, start, end, 'logreg',
            force=True, existing={('nba', 2024)},
        )
        self.assertTrue(changed)
        mock_bt.return_value.run.assert_called_once()


class TestCompletedSeasonsWithData(_CliTestBase):
    @patch('backtest_history._date_keys_in_range')
    def test_only_returns_seasons_with_cached_keys(self, mock_keys):
        # Pretend 2023 + 2024 had cached keys, 2022 did not.
        def keys_for(sport, start, end):
            if start.startswith('2024'):
                return ['2024-12-01']
            if start.startswith('2023'):
                return ['2023-12-01']
            return []
        mock_keys.side_effect = keys_for

        seasons = backtest_history._completed_seasons_with_data(
            'nba', datetime.date(2026, 4, 29), lookback_years=4,
        )
        years = [s[0] for s in seasons]
        self.assertIn(2023, years)
        self.assertIn(2024, years)
        self.assertNotIn(2022, years)

    @patch('backtest_history._date_keys_in_range', return_value=['2024-11-15'])
    def test_skips_unfinished_current_season(self, _mock_keys):
        # NBA 2025 season runs Oct 2025 → Jun 2026. On 2026-04-29 it has not
        # ended yet, so it should be excluded.
        seasons = backtest_history._completed_seasons_with_data(
            'nba', datetime.date(2026, 4, 29), lookback_years=3,
        )
        years = [s[0] for s in seasons]
        self.assertNotIn(2025, years)


class TestMain(_CliTestBase):
    def test_unknown_sport_argparse_error(self):
        with self.assertRaises(SystemExit):
            backtest_history.main(['--sport', 'cricket'])

    @patch('backtest_history.aggregate_one',
           return_value=(True, 'nba season 2024: ok'))
    @patch('backtest_history._completed_seasons_with_data',
           return_value=[(2024, datetime.date(2024, 10, 1), datetime.date(2025, 6, 30))])
    def test_returns_zero_on_success(self, _mock_seasons, mock_agg):
        rc = backtest_history.main(['--sport', 'nba'])
        self.assertEqual(rc, 0)
        self.assertEqual(mock_agg.call_count, 1)


if __name__ == '__main__':
    unittest.main()
