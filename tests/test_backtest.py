import datetime
import unittest
from unittest.mock import patch

from backtest import _max_drawdown, _season_window_for, _training_keys_in_season


class TestSeasonWindow(unittest.TestCase):
    def test_nba_mid_season(self):
        # NBA season window is 10-01 to 06-30 (cross-year).
        # Jan 15 2025 is the tail of the 2024-25 season.
        start, end = _season_window_for('nba', datetime.date(2025, 1, 15))
        self.assertEqual(start, datetime.date(2024, 10, 1))
        self.assertEqual(end, datetime.date(2025, 6, 30))

    def test_nba_early_season(self):
        # Nov 5 2024 is in the start of the 2024-25 season.
        start, end = _season_window_for('nba', datetime.date(2024, 11, 5))
        self.assertEqual(start, datetime.date(2024, 10, 1))
        self.assertEqual(end, datetime.date(2025, 6, 30))

    def test_mlb_within_year(self):
        # MLB season window is 03-20 to 11-01 (same year).
        start, end = _season_window_for('mlb', datetime.date(2024, 7, 4))
        self.assertEqual(start, datetime.date(2024, 3, 20))
        self.assertEqual(end, datetime.date(2024, 11, 1))

    def test_nfl_january_tail(self):
        # NFL season window is 09-01 to 02-15 (cross-year).
        # Jan 20 2025 is the tail of the 2024 NFL season.
        start, end = _season_window_for('nfl', datetime.date(2025, 1, 20))
        self.assertEqual(start, datetime.date(2024, 9, 1))
        self.assertEqual(end, datetime.date(2025, 2, 15))


class TestTrainingKeysInSeason(unittest.TestCase):
    @patch('backtest.store.list_available')
    def test_date_based_filters_to_season(self, mock_list):
        # Simulate an NBA cache that contains entries from two seasons
        # plus an out-of-season summer day. The 2025-01-15 test date should
        # only see entries within the 2024-25 season window, strictly before it.
        mock_list.return_value = [
            '2023-12-20',  # previous season — must be excluded
            '2024-08-15',  # offseason — must be excluded
            '2024-10-05',  # in this season, before test
            '2024-11-20',  # in this season, before test
            '2025-01-15',  # the test key itself — must be excluded
            '2025-02-10',  # after test — must be excluded
        ]
        keys = _training_keys_in_season('nba', '2025-01-15')
        self.assertEqual(keys, ['2024-10-05', '2024-11-20'])

    @patch('backtest.store.list_available')
    def test_week_based_keeps_earlier_weeks(self, mock_list):
        # Week-based sports: cache only ever holds one season's weeks
        # (later saves overwrite same-numbered keys), so we just keep
        # numerically earlier weeks.
        mock_list.return_value = ['1', '2', '3', '5', 'bad']
        keys = _training_keys_in_season('nfl', '5')
        self.assertEqual(sorted(keys), ['1', '2', '3'])

    @patch('backtest.store.list_available')
    def test_first_day_of_season_returns_empty(self, mock_list):
        mock_list.return_value = ['2024-10-01']
        keys = _training_keys_in_season('nba', '2024-10-01')
        self.assertEqual(keys, [])


class TestMaxDrawdown(unittest.TestCase):
    def test_empty_series(self):
        self.assertEqual(_max_drawdown([]), 0.0)

    def test_monotonic_up_no_drawdown(self):
        # Cumulative climbs 0 → 1 → 2 → 3 with no drops below zero.
        self.assertEqual(_max_drawdown([1.0, 1.0, 1.0]), 0.0)

    def test_drop_below_zero_from_flat_start(self):
        # Cumulative: -1, -2.5; floor = -2.5; drawdown = 2.5
        self.assertAlmostEqual(_max_drawdown([-1.0, -1.5]), 2.5)

    def test_curve_stays_above_zero(self):
        # Cumulative: 1, 3, 5, 4, 2, 0, 1 — never negative; drawdown = 0.
        series = [1.0, 2.0, 2.0, -1.0, -2.0, -2.0, 1.0]
        self.assertAlmostEqual(_max_drawdown(series), 0.0)

    def test_dip_then_recover(self):
        # Cumulative: -2, -1, 1, 5, 8 — floor = -2; drawdown = 2.
        series = [-2.0, 1.0, 2.0, 4.0, 3.0]
        self.assertAlmostEqual(_max_drawdown(series), 2.0)

    def test_double_dip_takes_lower_floor(self):
        # Cumulative: -1, -3, 1, -2, -5, 0 — floor = -5; drawdown = 5.
        series = [-1.0, -2.0, 4.0, -3.0, -3.0, 5.0]
        self.assertAlmostEqual(_max_drawdown(series), 5.0)


if __name__ == '__main__':
    unittest.main()
