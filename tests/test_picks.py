"""Tests for picks.py — EV pick rule, Kelly sizing, dataclass shape."""

import unittest

import pandas as pd

from picks import Pick, PickEngine


def _games_df() -> pd.DataFrame:
    """One game; lines designed so Home is the underdog at +200 (best book)."""
    return pd.DataFrame([{
        'Away Lines': ['-220', '-200', '-210'],
        'Home Lines': ['+200', '+220', '+210'],
        'Away Score': '',
        'Home Score': '',
        'Away Team': 'Away Team',
        'Home Team': 'Home Team',
        'Away Abbr': 'AWY',
        'Home Abbr': 'HOM',
        'Sportsbooks': ['Open', 'BookA', 'BookB'],
    }])


class TestPickRule(unittest.TestCase):
    def test_no_pick_when_model_returns_none(self):
        engine = PickEngine('nba', model_type='logreg')
        # Untrained logreg falls back to consensus; force None by passing
        # only outlier lines.
        df = pd.DataFrame([{
            'Away Lines': ['-10000'], 'Home Lines': ['+10000'],
            'Away Score': '', 'Home Score': '',
            'Sportsbooks': ['Open'],
        }])
        picks = engine.predict_all(df)
        self.assertEqual(picks[0].pick, 'No Pick')
        self.assertEqual(picks[0].unit_size, 0.0)
        self.assertIsNone(picks[0].bet_line)

    def test_pick_threads_ev_unit_size_and_bet_line(self):
        engine = PickEngine('nba', model_type='logreg')
        picks = engine.predict_all(_games_df())
        p = picks[0]
        # When picked, all three EV-related fields must be populated together.
        if p.pick != 'No Pick':
            self.assertIsNotNone(p.ev)
            self.assertIsNotNone(p.bet_line)
            self.assertGreaterEqual(p.unit_size, 0.0)
            self.assertLessEqual(p.unit_size, 0.05)
            # bet_line must be one of the non-Open lines on the picked side.
            picked_lines = p.away_lines if p.pick == 'Away' else p.home_lines
            self.assertIn(p.bet_line, picked_lines[1:])

    def test_emits_no_pick_on_negative_ev(self):
        # Construct a game where the consensus is well below 0.5 for the
        # home favourite — model probably agrees with the market and there's
        # no edge → No Pick.
        df = pd.DataFrame([{
            # Heavy favorite home; market efficient.
            'Away Lines': ['+500', '+510', '+505'],
            'Home Lines': ['-700', '-720', '-710'],
            'Away Score': '', 'Home Score': '',
            'Sportsbooks': ['Open', 'BookA', 'BookB'],
        }])
        engine = PickEngine('nba', model_type='logreg')
        # Without training, untrained logreg returns the market consensus
        # itself → EV ≈ 0 on both sides → No Pick.
        picks = engine.predict_all(df)
        self.assertEqual(picks[0].pick, 'No Pick')
        self.assertEqual(picks[0].unit_size, 0.0)


class TestPickDataclassDefaults(unittest.TestCase):
    def test_required_only(self):
        p = Pick(
            game_index=0, pick='No Pick',
            confidence=None, away_prob=None, home_prob=None,
            away_lines=[], home_lines=[],
        )
        self.assertEqual(p.unit_size, 0.0)
        self.assertIsNone(p.ev)
        self.assertIsNone(p.bet_line)
        self.assertEqual(p.model, 'logreg')


if __name__ == '__main__':
    unittest.main()
