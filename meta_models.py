"""
Meta-gate components for `logreg_v2` — a gradient-boosted-tree that predicts
realized flat-units-per-bet from a candidate Pick's features. The gate is
offline-trained by `train_meta_model.py` and persisted to
`data/meta_models/<name>.pkl`. `load_meta_gate(name)` is lru-cached so the
pickle deserializes once per process.

Feature vector (length 15):
    [ev, confidence, line_magnitude, book_disagreement, book_count,
     model_market_gap,
     sport_nba, sport_nfl, sport_nhl, sport_mlb, sport_mls,
     sport_ncaaf, sport_ncaab, sport_wnba, sport_cfl]

Target: `GameResult.units` (signed flat-units, +0.5 / +1.5 / -1.0 / 0).
"""

from __future__ import annotations

import json
import os
import pickle
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import numpy as np
import sklearn

import config
from betmath import decimal_odds, is_valid_line


# ---------------------------------------------------------------------------
# Feature ordering — frozen at module load. The pickle bundle records the
# order it was trained against; load-time mismatch is a hard error.
# ---------------------------------------------------------------------------

SPORT_COLUMNS: list[str] = list(config.SPORTS.keys())

NUMERIC_FEATURES: list[str] = [
    'ev',
    'confidence',
    'line_magnitude',
    'book_disagreement',
    'book_count',
    'model_market_gap',
    'opening_line_edge',  # CLV: decimal_odds(best_close) - decimal_odds(open); positive = sharp money agrees
    'season_fraction',    # 0.0 = season start (noisy), 1.0 = season end (well-calibrated model)
]

FEATURE_NAMES: list[str] = NUMERIC_FEATURES + [f'sport_{s}' for s in SPORT_COLUMNS]


_DEFAULT_META_DIR = os.path.join(os.path.dirname(__file__), 'data', 'meta_models')


# ---------------------------------------------------------------------------
# De-vigging math (shared with models.LogisticRegressionModel)
# ---------------------------------------------------------------------------

def implied_prob(line: str) -> float | None:
    """Implied probability with vig for a single American moneyline, or None
    if the line is invalid (per `betmath.is_valid_line`)."""
    if not is_valid_line(line):
        return None
    sign = line[0]
    odds = int(line[1:])
    if sign == '+':
        return 100.0 / (100.0 + odds)
    return odds / (100.0 + odds)


def consensus_home_prob_stats(
    away_lines: list[str],
    home_lines: list[str],
) -> dict[str, Any]:
    """
    De-vigged P(home wins) statistics across non-Open book pairs.

    Returns {'median': float|None, 'std': float, 'n': int}:
      - median: float median of de-vigged P(home); None if no valid pairs
      - std:    population std-dev across pairs; 0.0 when n < 2
      - n:      number of valid (away, home) book pairs

    Skips the leading 'Open' column (index 0) per the SBR convention used
    throughout the codebase.
    """
    a_books = away_lines[1:] if len(away_lines) > 1 else list(away_lines)
    h_books = home_lines[1:] if len(home_lines) > 1 else list(home_lines)
    probs: list[float] = []
    for a, h in zip(a_books, h_books):
        if not (is_valid_line(a) and is_valid_line(h)):
            continue
        ap = implied_prob(a)
        hp = implied_prob(h)
        if ap is None or hp is None:
            continue
        vig = ap + hp - 1.0
        probs.append(hp - 0.5 * vig)
    if not probs:
        return {'median': None, 'std': 0.0, 'n': 0}
    median = float(np.median(probs))
    std = float(np.std(probs)) if len(probs) >= 2 else 0.0
    return {'median': median, 'std': std, 'n': len(probs)}


# ---------------------------------------------------------------------------
# Feature extraction (one row per candidate Pick)
# ---------------------------------------------------------------------------

def feature_vector(candidate: dict[str, Any]) -> np.ndarray:
    """
    Build the meta-gate feature row for a candidate Pick.

    `candidate` must contain:
        sport: str (key into config.SPORTS)
        ev: float
        confidence: float (P(picked side wins) from base model)
        bet_line: str | None (American moneyline used to size + settle)
        away_lines, home_lines: list[str] (full book chain incl. Open at idx 0)
        home_prob: float | None (P(home wins) from base model)

    Missing/invalid values collapse to 0 — never NaN. The returned array's
    layout matches `FEATURE_NAMES`.
    """
    ev = float(candidate.get('ev') or 0.0)
    confidence = float(candidate.get('confidence') or 0.0)

    bet_line = candidate.get('bet_line')
    if bet_line and is_valid_line(bet_line):
        try:
            line_magnitude = decimal_odds(bet_line) - 1.0
        except ValueError:
            line_magnitude = 0.0
    else:
        line_magnitude = 0.0

    away_lines = list(candidate.get('away_lines') or [])
    home_lines = list(candidate.get('home_lines') or [])
    stats = consensus_home_prob_stats(away_lines, home_lines)
    book_disagreement = float(stats['std'])
    book_count = float(stats['n'])

    home_prob = candidate.get('home_prob')
    market_median = stats['median']
    if home_prob is None or market_median is None:
        model_market_gap = 0.0
    else:
        model_market_gap = float(home_prob) - float(market_median)

    sport = candidate.get('sport') or ''
    sport_one_hot = [1.0 if s == sport else 0.0 for s in SPORT_COLUMNS]

    opening_line_edge = float(candidate.get('opening_line_edge') or 0.0)
    season_fraction = float(candidate.get('season_fraction') or 0.5)

    return np.array(
        [
            ev,
            confidence,
            line_magnitude,
            book_disagreement,
            book_count,
            model_market_gap,
            opening_line_edge,
            season_fraction,
        ] + sport_one_hot,
        dtype=np.float64,
    )


# ---------------------------------------------------------------------------
# MetaGate — wrapper around a fitted regressor + provenance metadata
# ---------------------------------------------------------------------------

@dataclass
class MetaGate:
    estimator: Any
    feature_names: list[str]
    sport_columns: list[str]
    base_model: str
    name: str
    trained_at: str
    sklearn_version: str
    train_rows_per_sport: dict[str, int]
    holdout_seasons: dict[str, Any] | None = None

    def predict(self, features: np.ndarray) -> float:
        """Predicted flat-units-per-bet for a single candidate (scalar out)."""
        x = np.asarray(features, dtype=np.float64).reshape(1, -1)
        return float(self.estimator.predict(x)[0])

    def to_bundle(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'base_model': self.base_model,
            'estimator': self.estimator,
            'feature_names': self.feature_names,
            'sport_columns': self.sport_columns,
            'trained_at': self.trained_at,
            'sklearn_version': self.sklearn_version,
            'train_rows_per_sport': self.train_rows_per_sport,
            'holdout_seasons': self.holdout_seasons,
        }

    @classmethod
    def from_bundle(cls, bundle: dict[str, Any]) -> 'MetaGate':
        return cls(
            estimator=bundle['estimator'],
            feature_names=list(bundle['feature_names']),
            sport_columns=list(bundle['sport_columns']),
            base_model=bundle['base_model'],
            name=bundle['name'],
            trained_at=bundle.get('trained_at', ''),
            sklearn_version=bundle.get('sklearn_version', ''),
            train_rows_per_sport=dict(bundle.get('train_rows_per_sport') or {}),
            holdout_seasons=bundle.get('holdout_seasons'),
        )


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _pickle_path(
    name: str,
    season_year: int | None = None,
    base_dir: str | None = None,
) -> str:
    """Resolve the pickle path for a (name, season_year) pair.

    `season_year=None` is the "live" gate trained on every completed season —
    used for daily picks and current/in-progress-season rolling backtests
    (both leak-free by construction since the trainer never includes
    incomplete seasons in its corpus). `season_year=Y` is the gate trained
    with Y excluded — used to evaluate season Y honestly out-of-sample.
    """
    base = base_dir or _DEFAULT_META_DIR
    if season_year is None:
        return os.path.join(base, f'{name}.pkl')
    return os.path.join(base, f'{name}.{season_year}.pkl')


def _sidecar_path(
    name: str,
    season_year: int | None = None,
    base_dir: str | None = None,
) -> str:
    base = base_dir or _DEFAULT_META_DIR
    if season_year is None:
        return os.path.join(base, f'{name}.meta.json')
    return os.path.join(base, f'{name}.{season_year}.meta.json')


def save_meta_gate(
    gate: MetaGate,
    season_year: int | None = None,
    base_dir: str | None = None,
) -> str:
    """Pickle the gate + write a human-readable sidecar JSON. Returns pkl path.

    When `season_year` is given, writes to the season-keyed path so the
    backtester can pick the right leak-free gate per evaluation season.
    """
    base = base_dir or _DEFAULT_META_DIR
    os.makedirs(base, exist_ok=True)
    pkl_path = _pickle_path(gate.name, season_year=season_year, base_dir=base)
    with open(pkl_path, 'wb') as f:
        pickle.dump(gate.to_bundle(), f, protocol=pickle.HIGHEST_PROTOCOL)
    sidecar = {k: v for k, v in gate.to_bundle().items() if k != 'estimator'}
    with open(_sidecar_path(gate.name, season_year=season_year, base_dir=base), 'w') as f:
        json.dump(sidecar, f, indent=2, default=str)
    return pkl_path


def _load_bundle(path: str) -> MetaGate:
    with open(path, 'rb') as f:
        bundle = pickle.load(f)
    saved_version = bundle.get('sklearn_version') or ''
    if saved_version and saved_version != sklearn.__version__:
        # Soft-warn; pickle may still load. Users should retrain on mismatch.
        print(
            f'[meta_models] WARNING: {path} trained with sklearn '
            f'{saved_version}, runtime is {sklearn.__version__}. '
            f'Consider retraining via train_meta_model.py.'
        )
    return MetaGate.from_bundle(bundle)


@lru_cache(maxsize=64)
def load_meta_gate(
    name: str,
    season_year: int | None = None,
    base_dir: str | None = None,
) -> MetaGate:
    """
    Load a fitted MetaGate from disk. lru-cached on (name, season_year,
    base_dir) so each pickle deserializes once per process.

    When `season_year` is given, prefer `<name>.<season_year>.pkl` (the
    leak-free per-season gate trained with that season excluded). Fall back
    to the plain `<name>.pkl` ONLY when no season-specific pickle exists —
    this is the documented behavior for the current/in-progress season,
    which is naturally leak-free because the trainer never includes
    incomplete seasons in its corpus.

    Raises FileNotFoundError with a pointer to the training script when
    neither gate is available.
    """
    if season_year is not None:
        season_path = _pickle_path(name, season_year=season_year, base_dir=base_dir)
        if os.path.exists(season_path):
            return _load_bundle(season_path)
        # Season-specific gate missing — live gate is a fallback but it was trained on
        # ALL completed seasons, so predictions for season_year are IN-SAMPLE.
        print(
            f'[meta_models] WARNING: no per-season gate found for {name!r} season {season_year}. '
            f'Falling back to live gate, which was trained on ALL completed seasons '
            f'(IN-SAMPLE for season {season_year}). '
            f'Run `python train_meta_model.py --walk-forward` to create leak-free per-season gates.',
            flush=True,
        )
    base_path = _pickle_path(name, season_year=None, base_dir=base_dir)
    if not os.path.exists(base_path):
        raise FileNotFoundError(
            f'Meta-gate pickle not found at {base_path!r}. '
            f'Run `python train_meta_model.py --base-model logreg` '
            f'(add --walk-forward for leak-free per-season gates) to create it.'
        )
    return _load_bundle(base_path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
