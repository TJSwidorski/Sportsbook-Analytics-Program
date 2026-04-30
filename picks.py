"""
Pick generation.

PickEngine wraps a swappable model (Naive Bayes, bucketed NB, or logistic
regression — see models.py) and converts the model's home-win probability
into an EV-maximizing pick with fractional Kelly bet sizing.

The pick rule is:
  1. Get P(home) from the model.
  2. Compute EV per $1 staked at the BEST non-Open line for each side.
  3. Pick the side with the higher EV, but only if EV ≥ 0.
  4. Negative EV on both sides → 'No Pick'. We never stake on a -EV bet.
  5. Bet size = fractional Kelly (default 0.25× Kelly, capped at 5%) for the
     picked side at the best line.

This matches the user's framing: "leverage the books' priced-in injuries /
schedule / advanced stats — only fire when our number says they mispriced".
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from betmath import best_line_for_side, ev_per_unit, kelly_fraction
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


class PickEngine:
    def __init__(self, sport: str, model_type: str = 'logreg'):
        self.sport = sport
        self.model_type = model_type
        self._model = build_model(model_type)

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
                **meta,
            )

        p_away = 1.0 - p_home
        away_best = best_line_for_side(away_lines)
        home_best = best_line_for_side(home_lines)

        ev_away = ev_per_unit(p_away, away_best) if away_best else None
        ev_home = ev_per_unit(p_home, home_best) if home_best else None

        # Pick the side with the higher EV, only if it's non-negative.
        candidate: tuple[str, float, float, str] | None = None  # (side, p, ev, line)
        if ev_away is not None and (ev_home is None or ev_away >= ev_home) and ev_away >= 0:
            candidate = ('Away', p_away, ev_away, away_best)  # type: ignore[arg-type]
        elif ev_home is not None and ev_home >= 0:
            candidate = ('Home', p_home, ev_home, home_best)  # type: ignore[arg-type]

        if candidate is None:
            best_ev = max(
                ev_away if ev_away is not None else float('-inf'),
                ev_home if ev_home is not None else float('-inf'),
            )
            return Pick(
                game_index=index, pick='No Pick',
                confidence=p_home, away_prob=p_away, home_prob=p_home,
                away_lines=away_lines, home_lines=home_lines,
                ev=best_ev if best_ev != float('-inf') else None,
                unit_size=0.0, bet_line=None, model=self.model_type,
                **meta,
            )

        side, side_prob, side_ev, side_line = candidate
        return Pick(
            game_index=index, pick=side,
            confidence=side_prob, away_prob=p_away, home_prob=p_home,
            away_lines=away_lines, home_lines=home_lines,
            ev=side_ev,
            unit_size=kelly_fraction(side_prob, side_line),
            bet_line=side_line,
            model=self.model_type,
            **meta,
        )
