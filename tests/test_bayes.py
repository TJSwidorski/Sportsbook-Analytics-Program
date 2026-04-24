import unittest
import pandas as pd
from bayes import NaiveBayes

# Synthetic 10-game dataset.
# 6 wins always showing ['+110', '-120', '+105'].
# 4 losses always showing ['-150', '+130', '-110'].
# Lines are mutually exclusive so the model can give clean extreme outputs.
_WINS = pd.DataFrame({
    'Home Lines': [['+110', '-120', '+105']] * 6,
    'Home W/L':   [1] * 6,
})
_LOSSES = pd.DataFrame({
    'Home Lines': [['-150', '+130', '-110']] * 4,
    'Home W/L':   [0] * 4,
})
_SYNTHETIC_DF = pd.concat([_WINS, _LOSSES], ignore_index=True)


class TestNaiveBayesCounts(unittest.TestCase):
    def setUp(self):
        self.model = NaiveBayes('Home', _SYNTHETIC_DF)

    def test_number_wins(self):
        self.assertEqual(self.model.number_wins(), 6)

    def test_number_losses(self):
        self.assertEqual(self.model.number_losses(), 4)

    def test_win_data_length(self):
        self.assertEqual(len(self.model.win_data()), 6)

    def test_loss_data_length(self):
        self.assertEqual(len(self.model.loss_data()), 4)

    def test_win_data_all_ones(self):
        for v in self.model.win_data()['Home W/L']:
            self.assertEqual(v, 1)

    def test_loss_data_all_zeros(self):
        for v in self.model.loss_data()['Home W/L']:
            self.assertEqual(v, 0)


class TestNaiveBayesProbability(unittest.TestCase):
    def setUp(self):
        self.model = NaiveBayes('Home', _SYNTHETIC_DF)

    def test_return_type_is_float_or_none(self):
        prob = self.model.probability(['+110', '-120', '+105'])
        self.assertTrue(isinstance(prob, float) or prob is None)

    def test_always_win_lines_give_prob_one(self):
        # Lines seen only in wins → P(Win|lines) should be 1.0
        prob = self.model.probability(['+110', '-120', '+105'])
        self.assertIsNotNone(prob)
        self.assertAlmostEqual(prob, 1.0, places=5)

    def test_always_loss_lines_give_prob_zero(self):
        # Lines seen only in losses → P(Win|lines) should be 0.0
        prob = self.model.probability(['-150', '+130', '-110'])
        self.assertIsNotNone(prob)
        self.assertAlmostEqual(prob, 0.0, places=5)

    def test_mixed_lines_prob_in_open_interval(self):
        # Build a dataset where the line is seen in both wins and losses
        mixed = pd.concat([
            pd.DataFrame({'Home Lines': [['+110', '-120']] * 4, 'Home W/L': [1]*4}),
            pd.DataFrame({'Home Lines': [['+110', '+150']] * 2, 'Home W/L': [1]*2}),
            pd.DataFrame({'Home Lines': [['+110', '-120']] * 4, 'Home W/L': [0]*4}),
        ], ignore_index=True)
        model = NaiveBayes('Home', mixed)
        prob = model.probability(['+110', '-120'])
        self.assertIsNotNone(prob)
        self.assertGreater(prob, 0.0)
        self.assertLess(prob, 1.0)

    def test_unseen_line_returns_none_or_zero(self):
        # A line never observed in history should not crash; returns None or 0
        prob = self.model.probability(['+999', '-999', '+888'])
        self.assertTrue(prob is None or prob == 0.0)

    def test_probability_bounded(self):
        # Any valid probability must be in [0, 1]
        prob = self.model.probability(['+110', '-120', '+105'])
        if prob is not None:
            self.assertGreaterEqual(prob, 0.0)
            self.assertLessEqual(prob, 1.0)

    def test_away_model_works(self):
        # Verify the model works for 'Away' designator too
        away_df = pd.DataFrame({
            'Away Lines': [['+110', '-120']] * 5 + [['-150', '+130']] * 5,
            'Away W/L':   [1]*5 + [0]*5,
        })
        model = NaiveBayes('Away', away_df)
        prob = model.probability(['+110', '-120'])
        self.assertIsNotNone(prob)
        self.assertAlmostEqual(prob, 1.0, places=5)


if __name__ == '__main__':
    unittest.main()
