"""
Pick generation via Naive Bayes.

PickEngine trains separate home and away NaiveBayes models on historical data
and predicts the likely winner for each game in a raw retrieve.py DataFrame.
"""

from dataclasses import dataclass

import pandas as pd

from bayes import NaiveBayes
from package import Package


@dataclass
class Pick:
    game_index: int
    pick: str               # 'Away' | 'Home' | 'No Pick'
    confidence: float | None
    away_prob: float | None
    home_prob: float | None
    away_lines: list
    home_lines: list


class PickEngine:
    def __init__(self, sport: str):
        self.sport = sport
        self._away_model: NaiveBayes | None = None
        self._home_model: NaiveBayes | None = None

    def train(self, historical_df: pd.DataFrame) -> None:
        """Package historical raw DataFrame and fit home/away Naive Bayes models."""
        pkg = Package(historical_df.copy(), true_prob=False)
        away_df = pkg.return_away()
        home_df = pkg.return_home()
        if away_df is not None and not away_df.empty:
            self._away_model = NaiveBayes('Away', away_df)
        if home_df is not None and not home_df.empty:
            self._home_model = NaiveBayes('Home', home_df)

    def predict_all(self, games_df: pd.DataFrame) -> list[Pick]:
        """Return one Pick per row in the raw retrieve.py DataFrame."""
        picks = []
        for idx, row in games_df.iterrows():
            away_lines = row.get('Away Lines', [])
            home_lines = row.get('Home Lines', [])

            away_prob = (
                self._away_model.probability(away_lines)
                if self._away_model and away_lines
                else None
            )
            home_prob = (
                self._home_model.probability(home_lines)
                if self._home_model and home_lines
                else None
            )

            if away_prob is None and home_prob is None:
                pick = 'No Pick'
                confidence = None
            elif away_prob is None:
                pick = 'Home'
                confidence = home_prob
            elif home_prob is None:
                pick = 'Away'
                confidence = away_prob
            elif away_prob > home_prob:
                pick = 'Away'
                confidence = away_prob
            else:
                pick = 'Home'
                confidence = home_prob

            picks.append(Pick(
                game_index=len(picks),
                pick=pick,
                confidence=confidence,
                away_prob=away_prob,
                home_prob=home_prob,
                away_lines=list(away_lines),
                home_lines=list(home_lines),
            ))
        return picks
