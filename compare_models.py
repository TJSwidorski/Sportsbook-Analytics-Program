"""
Backtest every (sport, model) combo over a window and print a comparison table.

Examples:
  py compare_models.py --sport nba --start 2024-10-01 --end 2025-04-30
  py compare_models.py --sport all --start 2024-10-01 --end 2025-04-30 \
      --models nb,nb_bucketed,logreg

Picks where pick == 'No Pick' are excluded from accuracy and ROI denominators.
Settles each bet at the same line the pick rule chose (Pick.bet_line).
"""

from __future__ import annotations

import argparse
import sys

import config
from backtest import Backtester
from models import available_models


def _parse_sports(arg: str) -> list[str]:
    if arg.lower() == 'all':
        return list(config.SPORTS)
    keys = [s.strip() for s in arg.split(',') if s.strip()]
    unknown = [k for k in keys if k not in config.SPORTS]
    if unknown:
        raise SystemExit(f'Unknown sports: {unknown}. Valid: {sorted(config.SPORTS)}')
    return keys


def _parse_models(arg: str | None) -> list[str]:
    valid = available_models()
    if not arg:
        return valid
    keys = [m.strip() for m in arg.split(',') if m.strip()]
    unknown = [k for k in keys if k not in valid]
    if unknown:
        raise SystemExit(f'Unknown models: {unknown}. Valid: {valid}')
    return keys


def _format_row(
    sport: str,
    model: str,
    games_picked: int,
    accuracy: float,
    flat: float,
    kelly: float,
) -> str:
    roi = (100.0 * flat / games_picked) if games_picked else 0.0
    return (
        f'{sport:<6} {model:<13} {games_picked:>5}  '
        f'{accuracy * 100:>5.1f}   '
        f'{flat:>+10.2f}   {kelly:>+10.4f}   {roi:>+5.2f}%'
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sport', required=True,
                        help="Sport key, comma list, or 'all'")
    parser.add_argument('--start', required=True, help='YYYY-MM-DD')
    parser.add_argument('--end', required=True, help='YYYY-MM-DD')
    parser.add_argument('--models', default=None,
                        help='Comma-separated subset of: ' + ','.join(available_models()))
    args = parser.parse_args(argv)

    sports = _parse_sports(args.sport)
    models = _parse_models(args.models)

    header = (
        f'{"sport":<6} {"model":<13} {"picks":>5}  {"acc%":>5}   '
        f'{"flat_u":>10}   {"kelly_u":>10}   {"ROI":>6}'
    )
    print(header)
    print('-' * len(header))

    for sport in sports:
        for model in models:
            try:
                result = Backtester(sport, args.start, args.end, model_type=model).run()
            except RuntimeError as exc:
                print(f'{sport:<6} {model:<13} SKIPPED — {exc}')
                continue
            print(_format_row(
                sport, model,
                result.games_picked, result.accuracy,
                result.flat_units, result.kelly_units,
            ))

    return 0


if __name__ == '__main__':
    sys.exit(main())
