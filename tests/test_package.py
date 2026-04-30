import math
import unittest
import pandas as pd
from package import Package
from bayes import NaiveBayes

# Synthetic 3-game raw DataFrame matching the shape retrieve.py produces.
_RAW_DF = pd.DataFrame({
    'Date': ['2024-11-15', '2024-11-15', '2024-11-15'],
    'Away Lines': [
        ['+110', '-120', '+105'],
        ['+150', '-200', '+130'],
        ['-110', '+120', '-105'],
    ],
    'Home Lines': [
        ['-110', '+120', '-105'],
        ['-150', '+200', '-130'],
        ['+110', '-120', '+105'],
    ],
    'Away Score': ['21', '88', '105'],
    'Home Score': ['33', '102',  '98'],
})


class TestImpliedProb(unittest.TestCase):
    def setUp(self):
        # Bypass __init__ — we only need the method
        self.pkg = Package.__new__(Package)

    def test_positive_odds(self):
        self.assertAlmostEqual(self.pkg.implied_prob('+110'), 100 / 210)

    def test_negative_odds(self):
        self.assertAlmostEqual(self.pkg.implied_prob('-220'), 220 / 320)

    def test_even_odds(self):
        self.assertAlmostEqual(self.pkg.implied_prob('+100'), 100 / 200)

    def test_invalid_sign_raises(self):
        with self.assertRaises(ValueError):
            self.pkg.implied_prob('110')

    def test_sign_only_raises(self):
        with self.assertRaises(ValueError):
            self.pkg.implied_prob('+')


class TestTrueProb(unittest.TestCase):
    def setUp(self):
        self.pkg = Package.__new__(Package)

    def test_sums_to_one_even(self):
        a, h = self.pkg.true_prob('+110', '-110')
        self.assertAlmostEqual(a + h, 1.0, places=10)

    def test_sums_to_one_asymmetric(self):
        a, h = self.pkg.true_prob('+150', '-200')
        self.assertAlmostEqual(a + h, 1.0, places=10)

    def test_favorite_has_higher_prob(self):
        # Home is -200 favourite; away is +150 underdog
        away_p, home_p = self.pkg.true_prob('+150', '-200')
        self.assertGreater(home_p, away_p)

    def test_symmetric_odds_equal_prob(self):
        a, h = self.pkg.true_prob('+100', '-100')
        self.assertAlmostEqual(a, h, places=10)


class TestWinLoss(unittest.TestCase):
    def setUp(self):
        self.pkg = Package.__new__(Package)

    def test_home_win(self):
        self.assertEqual(self.pkg.win_loss(['90', '100']), (0, 1))

    def test_away_win(self):
        self.assertEqual(self.pkg.win_loss(['100', '90']), (1, 0))

    def test_tie(self):
        self.assertEqual(self.pkg.win_loss(['90', '90']), (None, None))

    def test_zero_zero(self):
        # 0-0 is a tie
        self.assertEqual(self.pkg.win_loss(['0', '0']), (None, None))


class TestToValues(unittest.TestCase):
    def setUp(self):
        self.pkg = Package(_RAW_DF.copy(), true_prob=True)
        self.df = self.pkg.return_df()

    def test_output_columns(self):
        self.assertEqual(
            set(self.df.columns),
            {'Date', 'Away Odds', 'Home Odds', 'Away W/L', 'Home W/L'},
        )

    def test_raw_lines_removed(self):
        self.assertNotIn('Away Lines', self.df.columns)
        self.assertNotIn('Home Lines', self.df.columns)

    def test_raw_scores_removed(self):
        self.assertNotIn('Away Score', self.df.columns)
        self.assertNotIn('Home Score', self.df.columns)

    def test_wl_values_are_binary(self):
        for val in self.df['Away W/L'].dropna():
            self.assertIn(val, (0, 1))
        for val in self.df['Home W/L'].dropna():
            self.assertIn(val, (0, 1))

    def test_odds_pairs_sum_to_one(self):
        for _, row in self.df.iterrows():
            for a, h in zip(row['Away Odds'], row['Home Odds']):
                self.assertAlmostEqual(a + h, 1.0, places=10)

    def test_row_count_preserved(self):
        # All 3 games have valid scores so no rows should be dropped
        self.assertEqual(len(self.df), 3)


class TestToNbValues(unittest.TestCase):
    def setUp(self):
        self.pkg = Package(_RAW_DF.copy(), true_prob=False)

    def test_away_df_not_none(self):
        self.assertIsNotNone(self.pkg.return_away())

    def test_home_df_not_none(self):
        self.assertIsNotNone(self.pkg.return_home())

    def test_away_df_columns(self):
        df = self.pkg.return_away()
        self.assertIn('Away Lines', df.columns)
        self.assertIn('Away W/L', df.columns)

    def test_home_df_columns(self):
        df = self.pkg.return_home()
        self.assertIn('Home Lines', df.columns)
        self.assertIn('Home W/L', df.columns)

    def test_away_df_row_count(self):
        self.assertEqual(len(self.pkg.return_away()), 3)

    def test_home_df_row_count(self):
        self.assertEqual(len(self.pkg.return_home()), 3)

    def test_away_wl_binary(self):
        for val in self.pkg.return_away()['Away W/L'].dropna():
            self.assertIn(val, (0, 1))

    def test_home_wl_binary(self):
        for val in self.pkg.return_home()['Home W/L'].dropna():
            self.assertIn(val, (0, 1))


class TestTieRowsExcludedFromNbTraining(unittest.TestCase):
    """Regression: ties leak NaN into Naive Bayes via the W/L float column."""

    def test_to_nb_values_drops_ties(self):
        # 2 wins, 1 tie, 1 loss for the home side.
        df = pd.DataFrame({
            'Date': ['d'] * 4,
            'Away Lines': [['+100'], ['-110'], ['-110'], ['+150']],
            'Home Lines': [['-110'], ['+100'], ['-110'], ['-170']],
            'Away Score': ['98',  '110', '88',  '120'],
            'Home Score': ['101', '95',  '88',  '102'],  # row 2 is a tie
        })
        pkg = Package(df, true_prob=False)
        home = pkg.return_home()
        # 4 input rows minus 1 tie => 3 training rows
        self.assertEqual(len(home), 3)
        # No NaN snuck into the W/L column
        self.assertTrue(home['Home W/L'].notna().all())

    def test_naive_bayes_never_returns_nan_with_ties(self):
        df = pd.DataFrame({
            'Date': ['d'] * 3,
            'Away Lines': [['-110'], ['-110'], ['+200']],
            'Home Lines': [['-110'], ['-110'], ['-250']],
            'Away Score': ['100', '100', '90'],
            'Home Score': ['100', '100', '95'],  # rows 0 and 1 are ties
        })
        pkg = Package(df, true_prob=False)
        model = NaiveBayes('Home', pkg.return_home())
        result = model.probability(['-250'])
        # With ties stripped, the only training row is a 1-of-1 home win at -250.
        # The model should produce a real number (or None), never NaN.
        if result is not None:
            self.assertFalse(math.isnan(result))


class TestOutlierClipping(unittest.TestCase):
    """Pairs with |line| > 1000 must be dropped from both training paths."""

    def _df_with_outlier_first_book(self):
        return pd.DataFrame({
            'Date': ['2024-11-15'],
            'Away Lines': [['-10000', '+150', '+148']],
            'Home Lines': [['+5000',  '-160', '-158']],
            'Away Score': ['98'],
            'Home Score': ['101'],
        })

    def test_to_nb_values_drops_outlier_pair(self):
        df = self._df_with_outlier_first_book()
        pkg = Package(df, true_prob=False)
        away = pkg.return_away()
        home = pkg.return_home()
        # First (outlier) pair stripped; only the two valid pairs remain.
        self.assertEqual(away.iloc[0]['Away Lines'], ['+150', '+148'])
        self.assertEqual(home.iloc[0]['Home Lines'], ['-160', '-158'])

    def test_to_values_drops_outlier_pair(self):
        df = self._df_with_outlier_first_book()
        pkg = Package(df, true_prob=True)
        out = pkg.return_df()
        # Only the two valid pairs survive into the true-prob arrays.
        self.assertEqual(len(out.iloc[0]['Away Odds']), 2)
        self.assertEqual(len(out.iloc[0]['Home Odds']), 2)

    def test_clean_rows_pass_through_unchanged(self):
        df = pd.DataFrame({
            'Date': ['2024-11-15'],
            'Away Lines': [['+110', '-120']],
            'Home Lines': [['-110', '+120']],
            'Away Score': ['98'],
            'Home Score': ['101'],
        })
        pkg = Package(df, true_prob=False)
        self.assertEqual(pkg.return_away().iloc[0]['Away Lines'], ['+110', '-120'])


if __name__ == '__main__':
    unittest.main()
