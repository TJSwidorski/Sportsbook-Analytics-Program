"""
Pick generation.

PickEngine wraps a swappable model (Naive Bayes, bucketed NB, logistic
regression, or the meta-gated `logreg_v2` — see models.py) and converts the
model's home-win probability into an EV-maximizing pick with fractional Kelly
bet sizing.

The pick rule is:
  1. Get P(home) from the model.
  2. Compute EV per $1 staked at the BEST non-Open line for each side.
  3. Pick the side with the higher EV.
  4. Apply the gate:
       - If `model.predict_pick_value(candidate)` returns a float (e.g.
         `logreg_v2`), keep the bet iff that predicted-units value exceeds
         `engine.meta_threshold`. This REPLACES the legacy EV check —
         a -EV bet that the meta-gate predicts will return positive units
         is still placed (the meta has, by design, learned that the
         baseline EV model misjudged it).
       - If `predict_pick_value` returns None, fall back to the legacy
         `EV >= 0` gate.
  5. Bet size = fractional Kelly (default 0.25× Kelly, capped at 5%) for the
     picked side at the best line.

This matches the user's framing: "leverage the books' priced-in injuries /
schedule / advanced stats — only fire when our number says they mispriced".
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

import pandas as pd

import config
from betmath import best_line_for_side, decimal_odds, ev_per_unit, is_valid_line, kelly_fraction
from models import build_model


@dataclass
class Pick:
    game_index: int
    pick: str               # 'Away' | 'Home' | 'No Pick'
    confidence: float | None
    away_prob: float | None
    home_prob: float | None
    away_lines: list
    home_lines: list
    away_team: str = ''
    home_team: str = ''
    away_abbr: str = ''
    home_abbr: str = ''
    sportsbooks: list = field(default_factory=list)
    ev: float | None = None        # EV per $1 staked at bet_line on a real pick
    unit_size: float = 0.0         # fractional Kelly bet size in [0, 0.05]
    bet_line: str | None = None    # the actual line used to size + settle the bet
    model: str = 'logreg'          # which model generated this pick
    predicted_units: float | None = None  # meta-gate output; None when no gate runs


class PickEngine:
    def __init__(
        self,
        sport: str,
        model_type: str = 'logreg',
        meta_threshold: float = 0.0,
        season_year: int | None = None,
        current_date: datetime.date | None = None,
    ):
        """
        `season_year`, when given, tells season-aware models (e.g.
        `logreg_v2`) which leak-free per-season meta-gate to load. Live
        runners leave it `None` so the live gate (`<name>.pkl`, trained on
        every completed season) is used. The Backtester sets it per
        test_key.

        `current_date` is used to compute `season_fraction` for the
        meta-gate feature vector. Defaults to today when None.
        """
        self.sport = sport
        self.model_type = model_type
        _gate_models = ('logreg_v2', 'logreg_v3')
        if model_type in _gate_models:
            # Walk-forward threshold resolution — always out-of-sample:
            #   - Backtest (season_year set): use the threshold selected from
            #     seasons strictly before season_year. If no prior-season data
            #     existed when the threshold was computed, fall back to T=0.0
            #     (meta-gate natural signal, no lookahead bias).
            #   - Live picks (season_year=None): use the sport-level live
            #     threshold trained on all completed seasons.
            # Each gate reads from its own thresholds file (logreg_v2 →
            # thresholds.json, logreg_v3 → thresholds_logreg_v3.json).
            _live_t, _season_t = config.load_gate_thresholds(model_type)
            _season_thresholds = _season_t.get(sport, {})
            if season_year is not None:
                self.meta_threshold = _season_thresholds.get(season_year, 0.0)
            else:
                self.meta_threshold = _live_t.get(sport, meta_threshold)
        else:
            self.meta_threshold = meta_threshold
        self.season_year = season_year
        self.current_date = current_date
        self._model = build_model(model_type)
        self._model.set_evaluation_context(season_year=season_year)

    def train(self, historical_df: pd.DataFrame) -> None:
        """Fit the underlying model on a raw retrieve.py historical DataFrame."""
        self._model.train(historical_df)

    def predict_all(self, games_df: pd.DataFrame) -> list[Pick]:
        """Return one Pick per row in the raw retrieve.py DataFrame."""
        picks: list[Pick] = []
        for _, row in games_df.iterrows():
            away_lines = list(row.get('Away Lines') or [])
            home_lines = list(row.get('Home Lines') or [])

            p_home = self._model.predict_home_prob(away_lines, home_lines)
            picks.append(self._build_pick(
                index=len(picks),
                row=row,
                away_lines=away_lines,
                home_lines=home_lines,
                p_home=p_home,
            ))
        return picks

    def _build_pick(
        self,
        index: int,
        row: pd.Series,
        away_lines: list[str],
        home_lines: list[str],
        p_home: float | None,
    ) -> Pick:
        sportsbooks = row.get('Sportsbooks', [])
        meta = dict(
            away_team=str(row.get('Away Team', '') or ''),
            home_team=str(row.get('Home Team', '') or ''),
            away_abbr=str(row.get('Away Abbr', '') or ''),
            home_abbr=str(row.get('Home Abbr', '') or ''),
            sportsbooks=list(sportsbooks) if sportsbooks else [],
        )

        if p_home is None:
            return Pick(
                game_index=index, pick='No Pick',
                confidence=None, away_prob=None, home_prob=None,
                away_lines=away_lines, home_lines=home_lines,
                ev=None, unit_size=0.0, bet_line=None, model=self.model_type,
                predicted_units=None,
                **meta,
            )

        p_away = 1.0 - p_home
        away_best = best_line_for_side(away_lines)
        home_best = best_line_for_side(home_lines)

        ev_away = ev_per_unit(p_away, away_best) if away_best else None
        ev_home = ev_per_unit(p_home, home_best) if home_best else None

        # Pick the side with the higher EV. Gate decisions happen below.
        candidate: tuple[str, float, float, str] | None = None  # (side, p, ev, line)
        if ev_away is not None and (ev_home is None or ev_away >= ev_home):
            candidate = ('Away', p_away, ev_away, away_best)  # type: ignore[arg-type]
        elif ev_home is not None:
            candidate = ('Home', p_home, ev_home, home_best)  # type: ignore[arg-type]

        if candidate is None:
            # No valid line on either side — can't bet, can't even score.
            return Pick(
                game_index=index, pick='No Pick',
                confidence=p_home, away_prob=p_away, home_prob=p_home,
                away_lines=away_lines, home_lines=home_lines,
                ev=None, unit_size=0.0, bet_line=None, model=self.model_type,
                predicted_units=None,
                **meta,
            )

        side, side_prob, side_ev, side_line = candidate

        # CLV: closing line moved in our direction = sharp money agreed
        open_lines = away_lines if side == 'Away' else home_lines
        open_line = open_lines[0] if open_lines else None
        if open_line and is_valid_line(open_line) and is_valid_line(side_line):
            try:
                opening_line_edge = decimal_odds(side_line) - decimal_odds(open_line)
            except (ValueError, ZeroDivisionError):
                opening_line_edge = 0.0
        else:
            opening_line_edge = 0.0

        # Season fraction: 0.0 = first day (noisy), 1.0 = last day (well-calibrated)
        season_fraction = 0.5
        try:
            effective_date = self.current_date or datetime.date.today()
            sy = self.season_year
            if sy is None:
                cfg_sport = config.SPORTS[self.sport]
                mm_dd_start = cfg_sport['season'][0]
                m_s, d_s = (int(x) for x in mm_dd_start.split('-'))
                season_start_this_year = datetime.date(effective_date.year, m_s, d_s)
                sy = effective_date.year if effective_date >= season_start_this_year else effective_date.year - 1
            start, end = config.season_window(self.sport, sy)
            total_days = (end - start).days
            if total_days > 0:
                season_fraction = max(0.0, min(1.0, (effective_date - start).days / total_days))
        except Exception:
            pass

        # Ask the model for a meta-gate opinion on this candidate. Models
        # without a meta-gate (`nb`, `logreg`, …) return None and fall back
        # to the legacy `EV >= 0` rule. `logreg_v2` returns a float and the
        # gate becomes `predicted_units > meta_threshold`, replacing EV.
        candidate_features = {
            'sport': self.sport,
            'ev': side_ev,
            'confidence': side_prob,
            'bet_line': side_line,
            'away_lines': away_lines,
            'home_lines': home_lines,
            'home_prob': p_home,
            'opening_line_edge': opening_line_edge,
            'season_fraction': season_fraction,
        }
        predicted_units = self._model.predict_pick_value(candidate_features)
        if predicted_units is None:
            gate_passes = side_ev >= 0
        else:
            gate_passes = predicted_units > self.meta_threshold

        if not gate_passes:
            return Pick(
                game_index=index, pick='No Pick',
                confidence=side_prob, away_prob=p_away, home_prob=p_home,
                away_lines=away_lines, home_lines=home_lines,
                ev=side_ev, unit_size=0.0, bet_line=None, model=self.model_type,
                predicted_units=predicted_units,
                **meta,
            )

        return Pick(
            game_index=index, pick=side,
            confidence=side_prob, away_prob=p_away, home_prob=p_home,
            away_lines=away_lines, home_lines=home_lines,
            ev=side_ev,
            unit_size=kelly_fraction(side_prob, side_line),
            bet_line=side_line,
            model=self.model_type,
            predicted_units=predicted_units,
            **meta,
        )
