"""Tests for models.py — registry, NB bucketing, LogReg behavior."""

import unittest

import pandas as pd

from models import (
    LogisticRegressionModel,
    NaiveBayesModel,
    _bucket_token,
    available_models,
    build_model,
)


def _historical_df(n: int = 30) -> pd.DataFrame:
    """Synthetic frame: 15 home wins on -150 lines, 15 away wins on +200 lines."""
    rows = []
    for _ in range(n // 2):
        rows.append({
            'Away Lines': ['+130', '+140', '+135'],
            'Home Lines': ['-150', '-160', '-155'],
            'Away Score': '95',
            'Home Score': '105',
        })
    for _ in range(n // 2):
        rows.append({
            'Away Lines': ['+200', '+210', '+205'],
            'Home Lines': ['-220', '-230', '-225'],
            'Away Score': '110',
            'Home Score': '95',
        })
    return pd.DataFrame(rows)


class TestRegistry(unittest.TestCase):
    def test_all_keys_resolve(self):
        for key in available_models():
            model = build_model(key)
            self.assertIsNotNone(model)

    def test_unknown_raises(self):
        with self.assertRaises(KeyError):
            build_model('not-a-model')


class TestBucketing(unittest.TestCase):
    def test_close_lines_share_bucket(self):
        # -110 → implied 0.524; -115 → 0.535. Bucket width 0.05 → both in [0.50, 0.55).
        self.assertEqual(_bucket_token('-110'), _bucket_token('-115'))

    def test_distant_lines_differ(self):
        self.assertNotEqual(_bucket_token('+100'), _bucket_token('-200'))

    def test_outlier_collapses_to_na(self):
        self.assertEqual(_bucket_token('-10000'), 'IP_NA')


class TestNaiveBayesModel(unittest.TestCase):
    def test_untrained_returns_none(self):
        model = NaiveBayesModel(bucketed=False)
        result = model.predict_home_prob(['+130'], ['-150'])
        self.assertIsNone(result)

    def test_trained_predicts_in_range(self):
        model = NaiveBayesModel(bucketed=True)
        model.train(_historical_df())
        prob = model.predict_home_prob(['+135', '+140', '+138'], ['-155', '-160', '-158'])
        self.assertIsNotNone(prob)
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)

    def test_bucketed_handles_unseen_close_lines(self):
        # -150 and -148 are in the same bucket; bucketed NB should still classify.
        model = NaiveBayesModel(bucketed=True)
        model.train(_historical_df())
        prob = model.predict_home_prob(['+131'], ['-148'])
        self.assertIsNotNone(prob)


class TestLogisticRegressionModel(unittest.TestCase):
    def test_untrained_falls_back_to_consensus(self):
        # When no fit has happened, the model returns the de-vigged consensus
        # itself rather than crashing — useful for cold-start inference.
        model = LogisticRegressionModel()
        prob = model.predict_home_prob(['+200', '+205', '+210'], ['-220', '-225', '-230'])
        self.assertIsNotNone(prob)
        # Home is heavy favorite → consensus > 0.5
        self.assertGreater(prob, 0.5)

    def test_trained_predicts_in_range(self):
        model = LogisticRegressionModel()
        model.train(_historical_df())
        prob = model.predict_home_prob(['+200', '+205', '+210'], ['-220', '-225', '-230'])
        self.assertIsNotNone(prob)
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)

    def test_returns_none_when_no_valid_lines(self):
        model = LogisticRegressionModel()
        model.train(_historical_df())
        # All outliers → no valid books to compute consensus from.
        prob = model.predict_home_prob(['-10000'], ['+10000'])
        self.assertIsNone(prob)


if __name__ == '__main__':
    unittest.main()
