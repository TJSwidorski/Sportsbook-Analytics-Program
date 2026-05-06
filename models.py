"""
Model registry for win-probability prediction.

All models conform to a common interface:

    model.train(packaged_df)
    p_home = model.predict_home_prob(away_lines, home_lines)  # → [0,1] or None

`packaged_df` is a raw retrieve.py DataFrame with 'Away Lines', 'Home Lines',
'Away Score', 'Home Score' columns. Each model is responsible for its own
feature extraction so callers don't need to know which model they're using.

Available keys via `build_model(name)`:
  'nb'           — Naive Bayes on raw moneyline tokens (legacy behavior)
  'nb_bucketed'  — Naive Bayes on implied-probability buckets (smoothed)
  'logreg'       — Logistic regression on de-vigged consensus probability
  'logreg_v2'    — Logreg + meta-gate predicting realized flat-units.
  'logreg_v3'    — Logreg + meta-gate predicting realized kelly-units
                   (walk-forward trained on 7 seasons; pickles at
                   `data/meta_models/logreg_v3[.<year>].pkl`).
"""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression

import meta_models
from bayes import NaiveBayes
from betmath import is_valid_line
from package import Package


# ---------------------------------------------------------------------------
# Helpers shared across models
# ---------------------------------------------------------------------------

# 20 buckets of width 0.05 covering implied probabilities in [0, 1].
_BUCKET_WIDTH = 0.05


def _implied_prob(line: str) -> float | None:
    """Single-line implied probability with vig (no de-vigging)."""
    if not is_valid_line(line):
        return None
    sign = line[0]
    odds = int(line[1:])
    if sign == '+':
        return 100.0 / (100.0 + odds)
    return odds / (100.0 + odds)


def _bucket_token(line: str) -> str:
    """
    Map a moneyline string to an implied-prob bucket token. Lines whose
    implied probabilities fall in the same 5%-wide bucket share a token, so
    NB stops treating -110 and -115 as unrelated features.

    Outlier or unparseable lines collapse to a single 'IP_NA' token so they
    don't pollute the feature space.
    """
    p = _implied_prob(line)
    if p is None:
        return 'IP_NA'
    lo = int(p / _BUCKET_WIDTH) * _BUCKET_WIDTH
    hi = lo + _BUCKET_WIDTH
    return f'IP_{lo:.2f}_{hi:.2f}'


def _bucket_lines(lines: list[str]) -> list[str]:
    return [_bucket_token(l) for l in lines]


# ---------------------------------------------------------------------------
# Base interface
# ---------------------------------------------------------------------------

class _ModelBase:
    name: str = ''

    def train(self, packaged_df: pd.DataFrame) -> None:
        raise NotImplementedError

    def predict_home_prob(
        self,
        away_lines: list[str],
        home_lines: list[str],
    ) -> float | None:
        raise NotImplementedError

    def predict_pick_value(self, candidate: dict[str, Any]) -> float | None:
        """
        Predicted flat-units-per-bet for a candidate Pick. Default: `None`,
        meaning the model has no opinion and the legacy `EV >= 0` gate
        applies. Models that override this (e.g. `LogregV2Model`) replace
        the EV gate with `predicted_units > engine.meta_threshold`.

        `candidate` carries the fields needed to build a feature row — see
        `meta_models.feature_vector` for the contract.
        """
        return None

    def set_evaluation_context(self, season_year: int | None = None) -> None:
        """
        Optional hook so season-aware models (e.g. `LogregV2Model`) can swap
        in a leak-free per-season meta-gate before predictions are issued.

        Default: no-op. Backtester calls this once per test_key with the
        season the key falls into; live runners pass `None` to use the gate
        trained on every completed season.
        """
        return None


# ---------------------------------------------------------------------------
# Naive Bayes wrapper (raw + bucketed)
# ---------------------------------------------------------------------------

class NaiveBayesModel(_ModelBase):
    """
    Wraps two `bayes.NaiveBayes` instances (one for Away, one for Home).
    Normalizes the two independent NB outputs into a proper distribution
    so the result behaves like a probability rather than two unrelated
    likelihoods that may both be high or both be low.

    With bucketed=True, every line passed to the underlying NB is first
    converted to an implied-probability bucket token; this collapses
    near-equivalent prices (e.g. -110 / -115) onto the same feature value
    and dramatically reduces the "every game is 0% or 100%" failure mode.
    """

    def __init__(self, bucketed: bool = False):
        self.bucketed = bucketed
        self.name = 'nb_bucketed' if bucketed else 'nb'
        self._away: NaiveBayes | None = None
        self._home: NaiveBayes | None = None

    def _maybe_bucket(self, lines: list[str]) -> list[str]:
        return _bucket_lines(lines) if self.bucketed else list(lines)

    def train(self, packaged_df: pd.DataFrame) -> None:
        pkg = Package(packaged_df.copy(), true_prob=False)
        away_df = pkg.return_away()
        home_df = pkg.return_home()

        if self.bucketed and away_df is not None and not away_df.empty:
            away_df = away_df.copy()
            away_df['Away Lines'] = away_df['Away Lines'].apply(_bucket_lines)
        if self.bucketed and home_df is not None and not home_df.empty:
            home_df = home_df.copy()
            home_df['Home Lines'] = home_df['Home Lines'].apply(_bucket_lines)

        if away_df is not None and not away_df.empty:
            self._away = NaiveBayes('Away', away_df)
        if home_df is not None and not home_df.empty:
            self._home = NaiveBayes('Home', home_df)

    def predict_home_prob(
        self,
        away_lines: list[str],
        home_lines: list[str],
    ) -> float | None:
        a_feats = self._maybe_bucket(away_lines)
        h_feats = self._maybe_bucket(home_lines)
        p_away = self._away.probability(a_feats) if self._away and a_feats else None
        p_home = self._home.probability(h_feats) if self._home and h_feats else None

        if p_home is None and p_away is None:
            return None
        if p_away is None:
            return float(p_home)
        if p_home is None:
            return float(1.0 - p_away)
        # Normalize the two independent estimates onto a proper distribution.
        total = p_home + p_away
        if total <= 0:
            return None
        return float(p_home / total)


# ---------------------------------------------------------------------------
# Logistic regression on the de-vigged consensus probability
# ---------------------------------------------------------------------------

class LogisticRegressionModel(_ModelBase):
    """
    One feature: the median across non-Open books of the de-vigged true
    probability that the home team wins. This treats the market as the prior
    and lets logistic regression learn a small, calibrated tilt — it can
    correct systemic biases (favorite-longshot bias, home-field skew) while
    inheriting all the information the books already priced in.

    The model trains on all rows where at least one valid (away, home) line
    pair survives outlier filtering. Sample weight is 1 per game.
    """

    name = 'logreg'

    def __init__(self):
        self._clf: LogisticRegression | None = None

    @staticmethod
    def _consensus_home_prob(
        away_lines: list[str],
        home_lines: list[str],
    ) -> float | None:
        """Median de-vigged P(home wins) across valid book pairs (skips Open).

        Thin wrapper around `meta_models.consensus_home_prob_stats` so the
        de-vigging math has a single source of truth shared with the
        meta-gate's `book_disagreement` and `model_market_gap` features.
        """
        return meta_models.consensus_home_prob_stats(
            list(away_lines), list(home_lines),
        )['median']

    def train(self, packaged_df: pd.DataFrame) -> None:
        X: list[list[float]] = []
        y: list[int] = []
        for _, row in packaged_df.iterrows():
            away = row.get('Away Lines') or []
            home = row.get('Home Lines') or []
            consensus = self._consensus_home_prob(list(away), list(home))
            if consensus is None:
                continue
            try:
                a_score = float(row.get('Away Score'))
                h_score = float(row.get('Home Score'))
            except (TypeError, ValueError):
                continue
            if a_score == h_score:
                continue  # ties carry no signal
            X.append([consensus])
            y.append(1 if h_score > a_score else 0)

        if len(set(y)) < 2:
            # Need at least one win and one loss to fit a binary classifier.
            self._clf = None
            return

        X_arr = np.array(X)
        y_arr = np.array(y)
        base_clf = LogisticRegression()
        # Platt scaling (sigmoid) calibrates raw logistic probabilities to
        # match observed win frequencies. Requires ≥ 5 samples per class for
        # 5-fold CV; fall back to uncalibrated when the training window is small
        # (common during the first few weeks of a season).
        n_minority = int(min(y_arr.sum(), len(y_arr) - y_arr.sum()))
        if n_minority >= 5:
            clf = CalibratedClassifierCV(base_clf, cv=min(5, n_minority), method='sigmoid')
        else:
            clf = base_clf
        clf.fit(X_arr, y_arr)
        self._clf = clf

    def predict_home_prob(
        self,
        away_lines: list[str],
        home_lines: list[str],
    ) -> float | None:
        consensus = self._consensus_home_prob(list(away_lines), list(home_lines))
        if consensus is None:
            return None
        if self._clf is None:
            # Untrained — defer to the market consensus directly.
            return consensus
        return float(self._clf.predict_proba(np.array([[consensus]]))[0, 1])


# ---------------------------------------------------------------------------
# Logreg + meta-gate composite (`logreg_v2`)
# ---------------------------------------------------------------------------

class LogregV2Model(_ModelBase):
    """
    Composite model: a `LogisticRegressionModel` for P(home wins) plus a
    pickled `meta_models.MetaGate` that predicts realized flat-units from
    a candidate Pick's features. The `PickEngine` consults
    `predict_pick_value` AFTER selecting the higher-EV side and uses its
    output (instead of the legacy `EV >= 0` check) to decide whether to
    actually place the bet.

    `train()` only fits the base logistic regression — the meta-gate is a
    frozen offline-trained artifact, loaded lazily on first prediction so
    a missing pickle does NOT break `available_models()` or registry
    instantiation.
    """

    name = 'logreg_v2'

    def __init__(self, gate_name: str = 'logreg_v2'):
        self._base = LogisticRegressionModel()
        self._gate_name = gate_name
        self._gate: meta_models.MetaGate | None = None
        self._season_year: int | None = None

    def train(self, packaged_df: pd.DataFrame) -> None:
        self._base.train(packaged_df)

    def predict_home_prob(
        self,
        away_lines: list[str],
        home_lines: list[str],
    ) -> float | None:
        return self._base.predict_home_prob(away_lines, home_lines)

    def set_evaluation_context(self, season_year: int | None = None) -> None:
        """
        Bind the season being evaluated. Backtester calls this once per
        test_key so the model can load the leak-free per-season gate
        (`logreg_v2.<season>.pkl`). Resets the cached gate only when the
        season actually changes, so tests can inject `_gate` directly and
        reuse it across calls with the same context.
        """
        if season_year != self._season_year:
            self._gate = None
        self._season_year = season_year

    def _ensure_gate(self) -> meta_models.MetaGate:
        if self._gate is None:
            self._gate = meta_models.load_meta_gate(
                self._gate_name, season_year=self._season_year,
            )
        return self._gate

    def predict_pick_value(self, candidate: dict[str, Any]) -> float | None:
        gate = self._ensure_gate()
        return gate.predict(meta_models.feature_vector(candidate))


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_MODEL_REGISTRY: dict[str, Callable[[], _ModelBase]] = {
    'nb':           lambda: NaiveBayesModel(bucketed=False),
    'nb_bucketed':  lambda: NaiveBayesModel(bucketed=True),
    'logreg':       lambda: LogisticRegressionModel(),
    'logreg_v2':    lambda: LogregV2Model(gate_name='logreg_v2'),
    'logreg_v3':    lambda: LogregV2Model(gate_name='logreg_v3'),
}


def build_model(name: str) -> _ModelBase:
    """Instantiate a fresh model by registry name. Raises KeyError if unknown."""
    if name not in _MODEL_REGISTRY:
        raise KeyError(
            f'Unknown model {name!r}. Valid: {sorted(_MODEL_REGISTRY)}'
        )
    return _MODEL_REGISTRY[name]()


def available_models() -> list[str]:
    return list(_MODEL_REGISTRY)
