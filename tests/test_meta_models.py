"""Tests for meta_models.py and the LogregV2Model gate behavior in PickEngine."""

import os
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

import meta_models
import models
from meta_models import (
    FEATURE_NAMES,
    SPORT_COLUMNS,
    MetaGate,
    consensus_home_prob_stats,
    feature_vector,
    load_meta_gate,
    save_meta_gate,
)
from picks import PickEngine


# ---------------------------------------------------------------------------
# De-vigging stats
# ---------------------------------------------------------------------------

class TestConsensusStats(unittest.TestCase):
    def test_skips_open_and_invalid(self):
        # Open at index 0 must be ignored; -10000 is filtered by is_valid_line.
        away = ['+150', '+150', '+155', '-10000']
        home = ['-170', '-170', '-175', '+10000']
        stats = consensus_home_prob_stats(away, home)
        # Three valid pairs after dropping Open + outlier.
        # Wait — Open is at 0 so it's already skipped by `[1:]`. The outlier
        # pair at index 3 is filtered by is_valid_line. Two valid pairs left.
        self.assertEqual(stats['n'], 2)
        self.assertIsNotNone(stats['median'])
        # Two pairs at -170 / -175 are very close → small std.
        self.assertLess(stats['std'], 0.02)

    def test_no_valid_pairs_returns_none_median(self):
        stats = consensus_home_prob_stats(['Open'], ['Open'])
        self.assertIsNone(stats['median'])
        self.assertEqual(stats['std'], 0.0)
        self.assertEqual(stats['n'], 0)

    def test_single_pair_has_zero_std(self):
        stats = consensus_home_prob_stats(['Open', '+150'], ['Open', '-170'])
        self.assertEqual(stats['n'], 1)
        self.assertEqual(stats['std'], 0.0)
        self.assertIsNotNone(stats['median'])


# ---------------------------------------------------------------------------
# Feature vector
# ---------------------------------------------------------------------------

class TestFeatureVector(unittest.TestCase):
    def _candidate(self, sport='nba', **overrides):
        base = {
            'sport': sport,
            'ev': 0.05,
            'confidence': 0.55,
            'bet_line': '+120',
            'away_lines': ['Open', '+120', '+125'],
            'home_lines': ['Open', '-140', '-145'],
            'home_prob': 0.42,
            'opening_line_edge': 0.05,
            'season_fraction': 0.6,
        }
        base.update(overrides)
        return base

    def test_shape_and_no_nan(self):
        x = feature_vector(self._candidate())
        self.assertEqual(x.shape, (len(FEATURE_NAMES),))
        self.assertEqual(x.shape, (17,))
        self.assertFalse(np.isnan(x).any())

    def test_sport_one_hot_position(self):
        x = feature_vector(self._candidate(sport='ncaab'))
        # The sport column for 'ncaab' must be 1; all other sports must be 0.
        for i, sport in enumerate(SPORT_COLUMNS):
            value = x[len(FEATURE_NAMES) - len(SPORT_COLUMNS) + i]
            expected = 1.0 if sport == 'ncaab' else 0.0
            self.assertEqual(value, expected, f'sport={sport}')

    def test_handles_missing_lines(self):
        x = feature_vector(self._candidate(away_lines=[], home_lines=[]))
        self.assertFalse(np.isnan(x).any())
        # book_disagreement (idx 3) and book_count (idx 4) collapse to 0.
        self.assertEqual(x[3], 0.0)
        self.assertEqual(x[4], 0.0)
        # model_market_gap (idx 5) collapses to 0 when consensus is None.
        self.assertEqual(x[5], 0.0)

    def test_invalid_bet_line_collapses_line_magnitude(self):
        x = feature_vector(self._candidate(bet_line='-99999'))
        self.assertEqual(x[2], 0.0)

    def test_unknown_sport_yields_zero_one_hot(self):
        x = feature_vector(self._candidate(sport='cricket'))
        # All sport columns should be 0 — unknown sport doesn't break the row.
        sport_cols = x[len(FEATURE_NAMES) - len(SPORT_COLUMNS):]
        self.assertTrue(np.all(sport_cols == 0.0))

    def test_signed_model_market_gap(self):
        # home_prob > consensus → positive gap (model bullish on home vs market).
        bullish = feature_vector(self._candidate(home_prob=0.70))
        bearish = feature_vector(self._candidate(home_prob=0.20))
        self.assertGreater(bullish[5], 0.0)
        self.assertLess(bearish[5], 0.0)


# ---------------------------------------------------------------------------
# MetaGate fit + pickle roundtrip
# ---------------------------------------------------------------------------

def _synthetic_corpus(n: int = 400, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Synthesize (X, y) with a learnable target = 2*ev - 0.5*line_mag + noise."""
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, len(FEATURE_NAMES)))
    # Force ev (col 0) and line_magnitude (col 2) into reasonable ranges.
    X[:, 0] = rng.uniform(-0.2, 0.3, size=n)
    X[:, 2] = rng.uniform(0.5, 3.0, size=n)
    y = 2.0 * X[:, 0] - 0.5 * X[:, 2] + rng.normal(scale=0.3, size=n)
    return X, y


class TestMetaGate(unittest.TestCase):
    def _fit_gate(self) -> MetaGate:
        X, y = _synthetic_corpus()
        est = GradientBoostingRegressor(
            max_depth=3, n_estimators=100, learning_rate=0.05,
            random_state=0,
        ).fit(X, y)
        return MetaGate(
            estimator=est,
            feature_names=FEATURE_NAMES,
            sport_columns=SPORT_COLUMNS,
            base_model='logreg',
            name='unit_test_gate',
            trained_at=meta_models.now_iso(),
            sklearn_version='unit-test',
            train_rows_per_sport={'nba': 400},
        )

    def test_fit_and_predict_in_range(self):
        gate = self._fit_gate()
        X, _ = _synthetic_corpus(n=10, seed=99)
        for row in X:
            pred = gate.predict(row)
            self.assertIsInstance(pred, float)

    def test_pickle_roundtrip(self):
        gate = self._fit_gate()
        with tempfile.TemporaryDirectory() as tmp:
            save_meta_gate(gate, base_dir=tmp)
            # Confirm both files written.
            self.assertTrue(os.path.exists(os.path.join(tmp, 'unit_test_gate.pkl')))
            self.assertTrue(os.path.exists(os.path.join(tmp, 'unit_test_gate.meta.json')))
            # Clear lru_cache so the load actually re-deserializes.
            load_meta_gate.cache_clear()
            loaded = load_meta_gate('unit_test_gate', base_dir=tmp)
            self.assertEqual(loaded.name, 'unit_test_gate')
            self.assertEqual(loaded.feature_names, FEATURE_NAMES)
            self.assertEqual(loaded.sport_columns, SPORT_COLUMNS)
            # Predictions match the original.
            X, _ = _synthetic_corpus(n=5, seed=42)
            for row in X:
                self.assertAlmostEqual(gate.predict(row), loaded.predict(row), places=8)

    def test_load_missing_file_raises_with_helpful_message(self):
        load_meta_gate.cache_clear()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError) as ctx:
                load_meta_gate('does_not_exist', base_dir=tmp)
            self.assertIn('train_meta_model.py', str(ctx.exception))

    def test_season_keyed_pickle_preferred_over_live(self):
        """When a season-specific pickle exists, load_meta_gate(season_year=Y) must use it."""
        live = self._fit_gate()
        # Build a slightly different gate so we can detect which one is loaded.
        X, y = _synthetic_corpus(n=300, seed=7)
        est = GradientBoostingRegressor(
            max_depth=2, n_estimators=50, learning_rate=0.10,
            random_state=1,
        ).fit(X, y)
        season_gate = MetaGate(
            estimator=est, feature_names=FEATURE_NAMES, sport_columns=SPORT_COLUMNS,
            base_model='logreg', name='unit_test_gate',
            trained_at=meta_models.now_iso(), sklearn_version='unit-test',
            train_rows_per_sport={'nba': 300},
            holdout_seasons={'nba': 2024},
        )
        with tempfile.TemporaryDirectory() as tmp:
            save_meta_gate(live, base_dir=tmp)
            save_meta_gate(season_gate, season_year=2024, base_dir=tmp)
            self.assertTrue(os.path.exists(os.path.join(tmp, 'unit_test_gate.pkl')))
            self.assertTrue(os.path.exists(os.path.join(tmp, 'unit_test_gate.2024.pkl')))

            load_meta_gate.cache_clear()
            loaded_live = load_meta_gate('unit_test_gate', base_dir=tmp)
            loaded_2024 = load_meta_gate('unit_test_gate', season_year=2024, base_dir=tmp)

            # Predictions on the same row should differ (different estimators).
            row, _ = _synthetic_corpus(n=1, seed=11)
            self.assertNotAlmostEqual(
                loaded_live.predict(row[0]),
                loaded_2024.predict(row[0]),
                places=4,
            )
            # And loaded_2024 matches the season_gate originally saved.
            self.assertAlmostEqual(
                season_gate.predict(row[0]),
                loaded_2024.predict(row[0]),
                places=8,
            )

    def test_season_load_falls_back_to_live(self):
        """If `<name>.<Y>.pkl` is absent, season_year=Y must fall back to `<name>.pkl`."""
        live = self._fit_gate()
        with tempfile.TemporaryDirectory() as tmp:
            save_meta_gate(live, base_dir=tmp)
            # No season-specific pickle written.
            load_meta_gate.cache_clear()
            loaded = load_meta_gate('unit_test_gate', season_year=2099, base_dir=tmp)
            row, _ = _synthetic_corpus(n=1, seed=12)
            self.assertAlmostEqual(
                live.predict(row[0]),
                loaded.predict(row[0]),
                places=8,
            )


# ---------------------------------------------------------------------------
# LogregV2Model + PickEngine gate behavior
# ---------------------------------------------------------------------------

def _games_df() -> pd.DataFrame:
    """One game where Home is the +200 underdog (best book)."""
    return pd.DataFrame([{
        'Away Lines': ['-220', '-200', '-210'],
        'Home Lines': ['+200', '+220', '+210'],
        'Away Score': '',
        'Home Score': '',
        'Away Team': 'Away',
        'Home Team': 'Home',
        'Away Abbr': 'AWY',
        'Home Abbr': 'HOM',
        'Sportsbooks': ['Open', 'BookA', 'BookB'],
    }])


class TestLogregV2Composite(unittest.TestCase):
    def test_train_only_fits_base_not_gate(self):
        """LogregV2Model.train() must fit the base logreg but never touch the gate."""
        m = models.LogregV2Model()
        # Stub the gate so its `.fit` would explode if called.
        sentinel = object()
        m._gate = sentinel  # any attempt to load would replace this
        with patch.object(meta_models, 'load_meta_gate') as mock_load:
            df = pd.DataFrame([
                {'Away Lines': ['+150'], 'Home Lines': ['-170'],
                 'Away Score': '100', 'Home Score': '110'},
                {'Away Lines': ['+200'], 'Home Lines': ['-220'],
                 'Away Score': '110', 'Home Score': '95'},
            ])
            m.train(df)
            # No gate load should happen during training.
            mock_load.assert_not_called()
        # Sentinel preserved — train didn't replace it.
        self.assertIs(m._gate, sentinel)

    def test_predict_pick_value_uses_gate(self):
        m = models.LogregV2Model()

        class FakeGate:
            def predict(self, features):
                # Echo back EV (column 0) so the test can assert the wiring.
                return float(features[0]) * 10.0

        m._gate = FakeGate()
        candidate = {
            'sport': 'nba', 'ev': 0.05, 'confidence': 0.55,
            'bet_line': '+150',
            'away_lines': ['Open', '+150'], 'home_lines': ['Open', '-170'],
            'home_prob': 0.45,
        }
        out = m.predict_pick_value(candidate)
        self.assertAlmostEqual(out, 0.5, places=6)

    def test_set_evaluation_context_resets_gate_on_season_change(self):
        m = models.LogregV2Model()
        sentinel = object()
        m._gate = sentinel
        # Same season → gate kept (so injected fakes survive across calls).
        m.set_evaluation_context(season_year=None)
        self.assertIs(m._gate, sentinel)
        # New season → gate cleared so the next predict_pick_value reloads.
        m.set_evaluation_context(season_year=2024)
        self.assertIsNone(m._gate)
        self.assertEqual(m._season_year, 2024)
        # Same season again → gate stays None (we just cleared it) but
        # context is preserved.
        m.set_evaluation_context(season_year=2024)
        self.assertEqual(m._season_year, 2024)

    def test_ensure_gate_passes_season_to_loader(self):
        captured = {}

        class FakeGate:
            def predict(self, _features):
                return 0.0

        def fake_loader(name, season_year=None, base_dir=None):
            captured['name'] = name
            captured['season_year'] = season_year
            return FakeGate()

        m = models.LogregV2Model()
        m.set_evaluation_context(season_year=2023)
        with patch.object(meta_models, 'load_meta_gate', side_effect=fake_loader):
            m._ensure_gate()
        self.assertEqual(captured['name'], 'logreg_v2')
        self.assertEqual(captured['season_year'], 2023)


class TestPickEngineMetaGate(unittest.TestCase):
    def test_logreg_default_unchanged(self):
        """Models without a meta-gate fall back to the legacy EV>=0 rule and stamp predicted_units=None."""
        engine = PickEngine('nba', model_type='logreg')
        picks = engine.predict_all(_games_df())
        self.assertIsNone(picks[0].predicted_units)

    def _logreg_v2_engine_with_fake_gate(self, predicted_value: float, threshold: float = 0.0):
        engine = PickEngine('nba', model_type='logreg_v2', meta_threshold=threshold)

        class FakeGate:
            def predict(self, _features):
                return predicted_value

        engine._model._gate = FakeGate()
        return engine

    def test_meta_gate_blocks_when_predicted_negative(self):
        engine = self._logreg_v2_engine_with_fake_gate(predicted_value=-0.5)
        picks = engine.predict_all(_games_df())
        p = picks[0]
        self.assertEqual(p.pick, 'No Pick')
        self.assertEqual(p.predicted_units, -0.5)
        self.assertEqual(p.unit_size, 0.0)
        self.assertIsNone(p.bet_line)
        # Confidence + ev preserved for transparency.
        self.assertIsNotNone(p.confidence)
        self.assertIsNotNone(p.ev)

    def test_meta_gate_allows_when_predicted_positive(self):
        engine = self._logreg_v2_engine_with_fake_gate(predicted_value=0.5)
        picks = engine.predict_all(_games_df())
        p = picks[0]
        self.assertIn(p.pick, ('Away', 'Home'))
        self.assertEqual(p.predicted_units, 0.5)
        self.assertGreater(p.unit_size, 0.0)
        self.assertIsNotNone(p.bet_line)

    def test_meta_threshold_respected(self):
        # Predicted=0.05; threshold=0.10 → blocked
        blocked = self._logreg_v2_engine_with_fake_gate(predicted_value=0.05, threshold=0.10)
        self.assertEqual(blocked.predict_all(_games_df())[0].pick, 'No Pick')
        # Predicted=0.05; threshold=0.0 → allowed (strict >)
        allowed = self._logreg_v2_engine_with_fake_gate(predicted_value=0.05, threshold=0.0)
        self.assertIn(allowed.predict_all(_games_df())[0].pick, ('Away', 'Home'))
        # Predicted=0.0; threshold=0.0 → blocked (strict >, not >=)
        edge = self._logreg_v2_engine_with_fake_gate(predicted_value=0.0, threshold=0.0)
        self.assertEqual(edge.predict_all(_games_df())[0].pick, 'No Pick')

    def test_meta_gate_can_override_negative_ev(self):
        """The meta-gate replaces (not stacks atop) the EV>=0 rule.

        A bet with model-EV slightly below 0 that the gate predicts will return
        positive units must still be placed — this is the whole point of the
        meta-correction.
        """
        # Build a game where untrained logreg returns the consensus directly,
        # so EV is ~0 on both sides (perfectly priced) and the legacy gate
        # would emit No Pick. With meta=+1.0 the bet should still fire.
        df = pd.DataFrame([{
            'Away Lines': ['-110', '-110', '-110'],
            'Home Lines': ['-110', '-110', '-110'],
            'Away Score': '', 'Home Score': '',
            'Sportsbooks': ['Open', 'A', 'B'],
        }])
        engine = self._logreg_v2_engine_with_fake_gate(predicted_value=1.0)
        picks = engine.predict_all(df)
        p = picks[0]
        # With ev <= 0 and meta saying go, the pick fires.
        self.assertIn(p.pick, ('Away', 'Home'))
        self.assertEqual(p.predicted_units, 1.0)


class TestBacktesterSeasonPlumbing(unittest.TestCase):
    """Backtester must call set_evaluation_context with the right season per test_key."""

    def test_set_evaluation_context_called_per_test_key(self):
        import backtest as backtest_mod
        from backtest import Backtester

        # Two NBA dates: one in the 2024 season tail, one in the 2024 season opener.
        # Both should resolve to season_year=2024 (NBA Oct-Jun crosses years).
        keys = ['2024-11-05', '2025-01-15']

        scores_df = pd.DataFrame([{
            'Away Lines': ['-110', '-110'],
            'Home Lines': ['-110', '-110'],
            'Away Score': '100', 'Home Score': '110',
            'Sportsbooks': ['Open', 'A'],
        }])

        captured_seasons: list = []

        original_set = models.LogregV2Model.set_evaluation_context

        def spy_set(self, season_year=None):
            captured_seasons.append(season_year)
            original_set(self, season_year=season_year)

        with patch.object(backtest_mod.store, 'list_available', return_value=keys), \
             patch.object(backtest_mod.store, 'load', return_value=scores_df), \
             patch.object(models.LogregV2Model, 'set_evaluation_context', spy_set):
            # Stub the gate so no pickle is required.
            with patch.object(models.LogregV2Model, 'predict_pick_value', return_value=0.5):
                bt = Backtester(
                    'nba', '2024-10-22', '2025-06-22',
                    model_type='logreg_v2',
                )
                bt.run()

        # Each test_key constructs a fresh PickEngine which calls
        # set_evaluation_context once. Both should be 2024.
        self.assertEqual(len(captured_seasons), 2)
        self.assertEqual(set(captured_seasons), {2024})


if __name__ == '__main__':
    unittest.main()
