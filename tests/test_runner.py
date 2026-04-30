import unittest
from unittest.mock import patch

import pandas as pd

import runner
from picks import Pick


class TestIsScorePresent(unittest.TestCase):
    def test_none(self):
        self.assertFalse(runner._is_score_present(None))

    def test_nan_float(self):
        self.assertFalse(runner._is_score_present(float('nan')))

    def test_empty_string(self):
        self.assertFalse(runner._is_score_present(''))
        self.assertFalse(runner._is_score_present('   '))

    def test_non_numeric_string(self):
        self.assertFalse(runner._is_score_present('TBD'))

    def test_numeric_string(self):
        self.assertTrue(runner._is_score_present('98'))
        self.assertTrue(runner._is_score_present('0'))

    def test_int(self):
        self.assertTrue(runner._is_score_present(105))


class TestCompletedIndices(unittest.TestCase):
    def test_mixed_rows(self):
        df = pd.DataFrame({
            'Away Score': ['98', None, '110', ''],
            'Home Score': ['101', '95', None, '108'],
        })
        # Row 0: both present → completed
        # Row 1: away missing → not completed
        # Row 2: home missing → not completed
        # Row 3: away empty → not completed
        self.assertEqual(runner._completed_indices(df), {0})

    def test_all_unplayed(self):
        df = pd.DataFrame({
            'Away Score': [None, None],
            'Home Score': [None, None],
        })
        self.assertEqual(runner._completed_indices(df), set())

    def test_empty_df(self):
        self.assertEqual(runner._completed_indices(pd.DataFrame()), set())

    def test_none(self):
        self.assertEqual(runner._completed_indices(None), set())


def _pick(idx: int) -> Pick:
    return Pick(
        game_index=idx, pick='Away', confidence=0.6,
        away_prob=0.6, home_prob=0.4,
        away_lines=['-110'], home_lines=['-110'],
    )


class TestGetUpcomingPicks(unittest.TestCase):
    @patch('runner.store.load')
    @patch('runner.get_daily_picks')
    def test_filters_completed_today_only(self, mock_picks, mock_load):
        # Today: 3 games, game_index 0 is completed (must be filtered out).
        # Tomorrow: 2 games, no completion filter applied.
        today_df = pd.DataFrame({
            'Away Lines': [['-110'], ['-105'], ['-120']],
            'Home Lines': [['-110'], ['-115'], ['+100']],
            'Away Score': ['98', None, None],
            'Home Score': ['101', None, None],
        })
        tomorrow_df = pd.DataFrame({
            'Away Lines': [['-110'], ['-105']],
            'Home Lines': [['-110'], ['-115']],
            'Away Score': [None, None],
            'Home Score': [None, None],
        })

        # store.load returns today's df for today_iso, tomorrow_df otherwise
        def load_side_effect(sport, key):
            if key == '2026-04-27':
                return today_df
            return tomorrow_df
        mock_load.side_effect = load_side_effect

        # get_daily_picks returns 3 picks for today, 2 for tomorrow
        def picks_side_effect(sport, date_or_week, *args, **kwargs):
            if date_or_week == '2026-04-27':
                return [_pick(0), _pick(1), _pick(2)]
            return [_pick(0), _pick(1)]
        mock_picks.side_effect = picks_side_effect

        with patch('runner.config.is_in_season', return_value=True):
            result = runner.get_upcoming_picks('nba', '2026-04-27')

        # Today: game_index 0 was completed → only 1 and 2 remain
        self.assertEqual([p.game_index for p in result['today']], [1, 2])
        # Tomorrow: no filter → both picks present
        self.assertEqual(len(result['tomorrow']), 2)

    @patch('runner.config.is_in_season', return_value=False)
    def test_out_of_season_returns_empty_buckets(self, _):
        result = runner.get_upcoming_picks('nba', '2026-04-27')
        self.assertEqual(result, {'today': [], 'tomorrow': []})


class TestRunAllSportsUpcoming(unittest.TestCase):
    @patch('runner.get_upcoming_picks')
    def test_iterates_every_sport(self, mock_upcoming):
        mock_upcoming.return_value = {'today': [], 'tomorrow': []}
        result = runner.run_all_sports_upcoming('2026-04-27')
        # Every key in config.SPORTS should be present
        from config import SPORTS
        self.assertEqual(set(result.keys()), set(SPORTS.keys()))


if __name__ == '__main__':
    unittest.main()
