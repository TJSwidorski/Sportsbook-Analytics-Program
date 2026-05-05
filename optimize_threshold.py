"""
Threshold grid search for the logreg_v2 meta-gate.

Reads the existing per-(sport, season) corpus cache files and the trained
per-season gates to evaluate what results would look like at different
meta_threshold values — without re-running the Backtester at all.

Since the corpus cache only contains rows that were picked at threshold=0.0
(the default), this script can only evaluate thresholds >= 0.0. It applies
each gate's predicted_units to every stored feature vector and computes
realized units for whichever rows survive the threshold filter.

Usage:
    python optimize_threshold.py                               # all sports, all seasons
    python optimize_threshold.py --sport nba,nhl               # subset
    python optimize_threshold.py --objective sharpe            # minimize variance
    python optimize_threshold.py --test-holdout 1 --objective sharpe
    python optimize_threshold.py --test-holdout 1 --objective sharpe --save
    python optimize_threshold.py --name logreg_v2             # default gate name
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pickle as _pkl
import sys
from collections import defaultdict
from typing import Optional

import numpy as np

import config
from meta_models import load_meta_gate
from train_meta_model import _CORPUS_CACHE_DIR, _corpus_cache_path

_THRESHOLDS = [0.0, 0.025, 0.05, 0.075, 0.10, 0.125, 0.15, 0.175, 0.20, 0.25, 0.30]
_THRESHOLDS_JSON_PATH = os.path.join(os.path.dirname(__file__), 'data', 'meta_models', 'thresholds.json')

# (sport, season_year, fvec, realized_units, predicted_units)
_Row = tuple[str, int, np.ndarray, float, float]


def _load_corpus(base_model: str, sport: str, season_year: int) -> list[tuple[np.ndarray, float]] | None:
    path = _corpus_cache_path(base_model, sport, season_year)
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return _pkl.load(f)


def _split_holdout(
    all_data: list[_Row],
    sports: list[str],
    n_holdout: int,
) -> tuple[list[_Row], list[_Row], dict[str, list[int]]]:
    """Split corpus temporally: N most recent seasons per sport become the test set.

    Returns (train_data, test_data, held_out_seasons_per_sport).
    When n_holdout == 0 returns (all_data, [], {}).
    """
    if n_holdout == 0:
        return all_data, [], {}

    test_keys: set[tuple[str, int]] = set()
    held_out: dict[str, list[int]] = {}
    for sport in sports:
        seasons = sorted(
            set(sy for s, sy, _, _, _ in all_data if s == sport),
            reverse=True,
        )
        held = seasons[:n_holdout]
        if held:
            held_out[sport] = sorted(held)
            for sy in held:
                test_keys.add((sport, sy))

    train_data = [r for r in all_data if (r[0], r[1]) not in test_keys]
    test_data  = [r for r in all_data if (r[0], r[1]) in test_keys]
    return train_data, test_data, held_out


def _season_stats(
    all_data: list[_Row],
    threshold: float,
    min_picks_per_season: int = 2,
) -> dict[str, float]:
    """Compute variance metrics for one threshold level across all (sport, year) groups."""
    groups: dict[tuple[str, int], list[float]] = defaultdict(list)
    for sport, season_year, _, realized, pred in all_data:
        if pred > threshold:
            groups[(sport, season_year)].append(realized)

    if not groups:
        return {'seasons': 0, 'pos_seasons': 0, 'sea_std': 0.0, 'sharpe': 0.0}

    seasons = len(groups)
    pos_seasons = sum(1 for units in groups.values() if sum(units) > 0)

    qualifying = [sum(units) for units in groups.values() if len(units) >= min_picks_per_season]
    if len(qualifying) < 2:
        return {'seasons': seasons, 'pos_seasons': pos_seasons, 'sea_std': 0.0, 'sharpe': 0.0}

    arr = np.array(qualifying, dtype=float)
    sea_std = float(np.std(arr))
    sharpe = float(np.mean(arr) / sea_std) if sea_std > 0 else 0.0
    return {'seasons': seasons, 'pos_seasons': pos_seasons, 'sea_std': sea_std, 'sharpe': sharpe}


def _compute_best_thresholds(
    all_data: list[_Row],
    thresholds: list[float],
    min_picks: int,
    min_picks_per_season: int,
    sport_filter: Optional[str] = None,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Return (best_t_upc, best_t_sharpe, best_t_units) across the threshold sweep."""
    subset = [r for r in all_data if sport_filter is None or r[0] == sport_filter]

    best_t_upc: Optional[float] = None
    best_t_sharpe: Optional[float] = None
    best_t_units: Optional[float] = None
    best_upc = -999.0
    best_sharpe = -999.0
    best_units = -999.0

    for t in thresholds:
        survived = [(r, p) for _, _, _, r, p in subset if p > t]
        n = len(survived)
        if n < min_picks:
            continue
        total = sum(r for r, _ in survived)
        upc = total / n
        stats = _season_stats(subset, t, min_picks_per_season)
        sharpe = stats['sharpe']

        if upc > best_upc:
            best_upc = upc
            best_t_upc = t
        # Only count this threshold as a Sharpe candidate when sea_std > 0,
        # meaning at least 2 qualifying seasons contributed. sea_std == 0 means
        # either only 1 season (Sharpe undefined) or all seasons tied (degenerate).
        if stats['sea_std'] > 0 and sharpe > best_sharpe:
            best_sharpe = sharpe
            best_t_sharpe = t
        if total > best_units:
            best_units = total
            best_t_units = t

    return best_t_upc, best_t_sharpe, best_t_units


def _group_by_season(subset: list[_Row], threshold: float) -> dict[tuple[str, int], list[float]]:
    groups: dict[tuple[str, int], list[float]] = defaultdict(list)
    for sport, season_year, _, realized, pred in subset:
        if pred > threshold:
            groups[(sport, season_year)].append(realized)
    return groups


def _print_sport_optimization(
    all_data: list[_Row],
    sports: list[str],
    thresholds: list[float],
    min_picks_per_season: int,
) -> dict[str, float]:
    """Print per-sport threshold sweep and return the sharpe-optimal threshold per sport."""
    _MIN_PICKS = 30
    print('\n' + '=' * 90)
    print(f'PER-SPORT THRESHOLD OPTIMIZATION  (min_picks={_MIN_PICKS} per sport)')

    sport_thresholds: dict[str, float] = {}

    for sport in sports:
        subset = [r for r in all_data if r[0] == sport]
        if not subset:
            continue

        season_count = len(set((r[0], r[1]) for r in subset))
        print(f'\n[{sport.upper()}]  {season_count} season(s)  ({len(subset):,} corpus rows)')
        print(f'  {"THRESHOLD":>10} | {"PICKS":>6} | {"UNITS":>8} | {"U/PICK":>7} | {"SEAS":>5} | {"+SEAS":>5} | {"SHARPE":>7}')
        print('  ' + '-' * 68)

        for t in thresholds:
            survived_rows = [(r, p) for _, _, _, r, p in subset if p > t]
            n = len(survived_rows)
            total = sum(r for r, _ in survived_rows)
            upc = total / n if n else 0.0
            stats = _season_stats(subset, t, min_picks_per_season)
            print(
                f'  {t:>10.3f} | {n:>6,} | {total:>+8.2f} | {upc:>+7.4f} |'
                f' {stats["seasons"]:>5} | {stats["pos_seasons"]:>5} | {stats["sharpe"]:>+7.3f}'
            )

        best_t_upc, best_t_sharpe, best_t_units = _compute_best_thresholds(
            all_data, thresholds, min_picks=_MIN_PICKS,
            min_picks_per_season=min_picks_per_season, sport_filter=sport,
        )

        def _fmt(t: Optional[float]) -> str:
            return f'T={t:.3f}' if t is not None else 'n/a'

        def _stats_at(t: Optional[float]) -> str:
            if t is None:
                return ''
            s = [r for _, _, _, r, p in subset if p > t]
            n = len(s)
            total = sum(s)
            upc = total / n if n else 0.0
            st = _season_stats(subset, t, min_picks_per_season)
            return f'units={total:+.2f}, upc={upc:+.4f}, sharpe={st["sharpe"]:+.3f}, picks={n}'

        print(f'  Best UPC:    {_fmt(best_t_upc)}  ({_stats_at(best_t_upc)})')

        sharpe_note = ''
        if best_t_sharpe is None and season_count < 2:
            sharpe_note = f'  (sharpe undefined — {season_count} season only; using upc fallback)'
            best_t_sharpe = best_t_upc
        elif best_t_sharpe is None:
            sharpe_note = '  (no threshold meets min_picks floor)'
            best_t_sharpe = best_t_upc

        print(f'  Best Sharpe: {_fmt(best_t_sharpe)}  ({_stats_at(best_t_sharpe)}){sharpe_note}')
        print(f'  Best Units:  {_fmt(best_t_units)}  ({_stats_at(best_t_units)})')

        if best_t_sharpe is not None:
            sport_thresholds[sport] = best_t_sharpe

    # Summary dict
    print('\n' + '-' * 90)
    print('RECOMMENDED PER-SPORT THRESHOLDS (sharpe-optimal):')
    for sport, t in sport_thresholds.items():
        subset = [r for r in all_data if r[0] == sport]
        season_count = len(set((r[0], r[1]) for r in subset))
        st = _season_stats(subset, t, min_picks_per_season)
        sharpe_str = (
            f'sharpe={st["sharpe"]:+.3f}'
            if st['sharpe'] != 0.0
            else f'sharpe undefined — {season_count} season(s) only; using upc fallback'
        )
        print(f"    '{sport}':   {t:.3f}   ({sharpe_str}, {season_count} seasons)")

    return sport_thresholds


def _print_test_results(
    test_data: list[_Row],
    held_out: dict[str, list[int]],
    best_t_sharpe: Optional[float],
    best_t_upc: Optional[float],
    best_t_units: Optional[float],
    min_picks_per_season: int,
    sport_thresholds: dict[str, float],
    primary_objective: str,
) -> None:
    """Print the out-of-sample test section."""
    if not test_data:
        return

    held_label = '  '.join(
        f'{sport}/{sy}' for sport, seasons in sorted(held_out.items()) for sy in seasons
    )
    total_rows = len(test_data)

    print('\n' + '=' * 90)
    print(f'OUT-OF-SAMPLE TEST RESULTS  (N={len(next(iter(held_out.values()), []))} holdout per sport)')
    print(f'Held-out seasons: {held_label}')
    print(f'Test rows: {total_rows:,}')

    parts = []
    if best_t_sharpe is not None:
        parts.append(f'[SHARPE] T={best_t_sharpe:.3f}')
    if best_t_upc is not None:
        parts.append(f'[UPC] T={best_t_upc:.3f}')
    if best_t_units is not None:
        parts.append(f'[UNITS] T={best_t_units:.3f}')
    print(f'Selected thresholds (from train data): {" | ".join(parts)}')

    # Performance at each objective's threshold on the test set
    print(f'\n{"THRESHOLD":>10} | {"OBJECTIVE":>9} | {"PICKS":>7} | {"UNITS":>8} | {"U/PICK":>7} | {"SEAS":>5} | {"+SEAS":>5} | {"SHARPE":>7}')
    print('-' * 90)

    seen: set[float] = set()
    recs = [('SHARPE', best_t_sharpe), ('UPC', best_t_upc), ('UNITS', best_t_units)]
    for label, t in recs:
        if t is None or t in seen:
            continue
        seen.add(t)
        survived = [(r, p) for _, _, _, r, p in test_data if p > t]
        n = len(survived)
        total = sum(r for r, _ in survived)
        upc = total / n if n else 0.0
        stats = _season_stats(test_data, t, min_picks_per_season)
        print(
            f'{t:>10.3f} | {label:>9} | {n:>7,} | {total:>+8.2f} | {upc:>+7.4f} |'
            f' {stats["seasons"]:>5} | {stats["pos_seasons"]:>5} | {stats["sharpe"]:>+7.3f}'
        )

    # Per-sport breakdown at the primary objective's threshold
    primary_t = {'sharpe': best_t_sharpe, 'upc': best_t_upc, 'units': best_t_units}.get(
        primary_objective, best_t_sharpe
    )
    if primary_t is None:
        primary_t = best_t_sharpe or best_t_upc or best_t_units
    if primary_t is None:
        return

    print(f'\nPer-sport test breakdown at {primary_objective.upper()} threshold (T={primary_t:.3f}):')
    sports_in_test = sorted(set(r[0] for r in test_data))
    for sport in sports_in_test:
        subset = [(r, p) for s, _, _, r, p in test_data if s == sport]
        # Also break down by season
        seasons_in_sport = sorted(set(sy for s, sy, _, _, _ in test_data if s == sport))
        for sy in seasons_in_sport:
            season_rows = [(r, p) for s, ssy, _, r, p in test_data if s == sport and ssy == sy]
            survived = [r for r, p in season_rows if p > primary_t]
            n = len(survived)
            total = sum(survived)
            print(f'  {sport}/{sy}:   picks={n:>4}   units={total:>+8.2f}')

    # Per-sport test results using the sport-specific thresholds selected from train
    if sport_thresholds:
        print(f'\nPer-sport test breakdown using per-sport thresholds:')
        for sport in sports_in_test:
            t = sport_thresholds.get(sport)
            if t is None:
                continue
            seasons_in_sport = sorted(set(sy for s, sy, _, _, _ in test_data if s == sport))
            for sy in seasons_in_sport:
                season_rows = [(r, p) for s, ssy, _, r, p in test_data if s == sport and ssy == sy]
                survived = [r for r, p in season_rows if p > t]
                n = len(survived)
                total = sum(survived)
                print(f'  {sport}/{sy}  (T={t:.3f}):   picks={n:>4}   units={total:>+8.2f}')


def run(
    gate_name: str,
    base_model: str,
    sports: list[str],
    objective: str = 'upc',
    min_picks_per_season: int = 2,
    n_holdout: int = 0,
    save: bool = False,
) -> None:
    all_data: list[_Row] = []

    print(f'[optimize] Loading corpus cache from {_CORPUS_CACHE_DIR}')
    for sport in sports:
        for fname in os.listdir(_CORPUS_CACHE_DIR):
            prefix = f'{base_model}_{sport}_'
            if not fname.startswith(prefix) or not fname.endswith('.pkl'):
                continue
            try:
                season_year = int(fname[len(prefix):-4])
            except ValueError:
                continue

            rows = _load_corpus(base_model, sport, season_year)
            if not rows:
                continue

            try:
                gate = load_meta_gate(gate_name, season_year=season_year)
            except FileNotFoundError:
                try:
                    gate = load_meta_gate(gate_name)
                except FileNotFoundError:
                    print(f'[optimize] {sport} {season_year}: no gate found — skipping')
                    continue

            for fvec, realized in rows:
                pred = gate.predict(fvec)
                all_data.append((sport, season_year, fvec, realized, pred))

        sport_rows = [(s, sy, r, p) for s, sy, _, r, p in all_data if s == sport]
        if sport_rows:
            print(f'[optimize]   {sport}: {len(sport_rows)} corpus rows')

    if not all_data:
        print('[optimize] No corpus data found. Run train_meta_model.py first.')
        return

    total_rows = len(all_data)
    print(f'\n[optimize] Total corpus rows: {total_rows}')

    # --- Train / test split ---
    train_data, test_data, held_out = _split_holdout(all_data, sports, n_holdout)

    if n_holdout > 0:
        held_label = '  '.join(
            f'{sport}/{sy}' for sport, seasons in sorted(held_out.items()) for sy in seasons
        )
        print(f'\n[optimize] Holdout: {held_label}')
        print(f'[optimize] Train rows: {len(train_data):,}   Test rows: {len(test_data):,}')
        print('\nAll analysis below uses TRAIN DATA only. Test results follow at the end.')

    # Use train_data for all selection logic
    data = train_data

    # --- Pre-compute best thresholds for table markers ---
    best_t_upc, best_t_sharpe, best_t_units = _compute_best_thresholds(
        data, _THRESHOLDS, min_picks=100, min_picks_per_season=min_picks_per_season,
    )

    # --- Collect all row data first (two-pass for markers) ---
    table_rows = []
    for t in _THRESHOLDS:
        survived = [(r, p) for _, _, _, r, p in data if p > t]
        n = len(survived)
        units = sum(r for r, _ in survived)
        upc = units / n if n else 0.0
        drop_pct = (1 - n / total_rows) * 100 if total_rows else 0.0
        stats = _season_stats(data, t, min_picks_per_season)
        table_rows.append((t, n, units, upc, drop_pct, stats))

    # --- Main threshold table ---
    label_suffix = ' (TRAIN)' if n_holdout > 0 else ''
    print('\n' + '=' * 90)
    print(
        f'{"THRESHOLD":>10} | {"PICKS":>7} | {"UNITS":>8} | {"U/PICK":>7} |'
        f' {"DROP%":>6} | {"SEAS":>5} | {"+SEAS":>5} | {"SEA_STD":>8} | {"SHARPE":>7}{label_suffix}'
    )
    print('-' * 90)

    for t, n, units, upc, drop_pct, stats in table_rows:
        markers = []
        if t == best_t_upc:
            markers.append('[upc]')
        if t == best_t_sharpe:
            markers.append('[sha]')
        if t == best_t_units:
            markers.append('[unt]')
        marker_str = ' ' + ' '.join(markers) if markers else ''
        print(
            f'{t:>10.3f} | {n:>7,} | {units:>+8.2f} | {upc:>+7.4f} |'
            f' {drop_pct:>5.1f}% | {stats["seasons"]:>5} | {stats["pos_seasons"]:>5} |'
            f' {stats["sea_std"]:>+8.2f} | {stats["sharpe"]:>+7.3f}{marker_str}'
        )

    # --- Per-season breakdown ---
    key_thresholds = [0.0, 0.05, 0.10, 0.15, 0.20]
    seasons = sorted(set((s, sy) for s, sy, _, _, _ in data))

    print('\n' + '=' * 90)
    print(f'PER-SEASON BREAKDOWN{label_suffix}')
    header = f'{"SPORT/YR":<12}' + ''.join(f'  T={t:.2f}(u)' for t in key_thresholds)
    print(header)
    print('-' * 90)

    for sport, season_year in seasons:
        subset = [(r, p) for s, sy, _, r, p in data if s == sport and sy == season_year]
        if not subset:
            continue
        row_str = f'{sport}/{season_year:<6}'
        for t in key_thresholds:
            survived = [r for r, p in subset if p > t]
            u = sum(survived)
            row_str += f'  {u:>+8.2f}({len(survived):>4})'
        print(row_str)

    # --- Per-sport totals ---
    print('\n' + '=' * 90)
    print(f'PER-SPORT TOTALS (all seasons){label_suffix}')
    sport_header = f'{"SPORT":<10}' + ''.join(f'  T={t:.2f}(u)' for t in key_thresholds)
    print(sport_header)
    print('-' * 90)

    for sport in sports:
        subset = [(r, p) for s, sy, _, r, p in data if s == sport]
        if not subset:
            continue
        row_str = f'{sport:<10}'
        for t in key_thresholds:
            survived = [r for r, p in subset if p > t]
            u = sum(survived)
            row_str += f'  {u:>+8.2f}({len(survived):>4})'
        print(row_str)

    # --- Per-sport optimization section ---
    sport_thresholds = _print_sport_optimization(data, sports, _THRESHOLDS, min_picks_per_season)

    # --- Recommendation block ---
    def _rec_stats(t: Optional[float]) -> tuple[int, float, float, dict]:
        if t is None:
            return 0, 0.0, 0.0, {'seasons': 0, 'pos_seasons': 0, 'sea_std': 0.0, 'sharpe': 0.0}
        survived = [(r, p) for _, _, _, r, p in data if p > t]
        n = len(survived)
        total = sum(r for r, _ in survived)
        upc = total / n if n else 0.0
        stats = _season_stats(data, t, min_picks_per_season)
        return n, total, upc, stats

    objective_label = {'upc': 'UPC', 'sharpe': 'SHARPE', 'units': 'UNITS'}[objective]

    print('\n' + '=' * 90)
    print(f'RECOMMENDATIONS{label_suffix}  (primary objective: {objective_label})')

    recs = [
        ('SHARPE', best_t_sharpe, objective == 'sharpe'),
        ('UPC',    best_t_upc,    objective == 'upc'),
        ('UNITS',  best_t_units,  objective == 'units'),
    ]

    for label, t, is_primary in recs:
        n, total, upc, stats = _rec_stats(t)
        prefix = '  ***' if is_primary else '     '
        t_str = f'{t:.3f}' if t is not None else 'n/a'
        print(f'{prefix} [{label}]  meta_threshold = {t_str}')
        if t is not None:
            print(f'         Picks: {n:,} / {len(data):,} ({n / len(data) * 100:.1f}%)   '
                  f'Seasons: {stats["pos_seasons"]} pos / {stats["seasons"]}')
            print(f'         Total units: {total:+.2f}   U/Pick: {upc:+.4f}   Sharpe: {stats["sharpe"]:+.3f}')

    primary_t = {'upc': best_t_upc, 'sharpe': best_t_sharpe, 'units': best_t_units}[objective]
    live_t = primary_t if primary_t is not None else best_t_upc
    t_str = f'{live_t:.3f}' if live_t is not None else '0.000'
    if n_holdout == 0:
        print(f'\n  Backtest with: py backtest_history.py --model logreg_v2  (then set default threshold)')
        print(f'  Live picks:    /api/picks?model=logreg_v2&meta_threshold={t_str}')

    # --- Out-of-sample test results ---
    if n_holdout > 0 and test_data:
        _print_test_results(
            test_data=test_data,
            held_out=held_out,
            best_t_sharpe=best_t_sharpe,
            best_t_upc=best_t_upc,
            best_t_units=best_t_units,
            min_picks_per_season=min_picks_per_season,
            sport_thresholds=sport_thresholds,
            primary_objective=objective,
        )

    # --- Save thresholds ---
    if save:
        payload: dict = dict(sport_thresholds)
        payload['_meta'] = {
            'objective': objective,
            'test_holdout': n_holdout,
            'saved_at': datetime.datetime.now().isoformat(timespec='seconds'),
            'train_rows': len(train_data),
            'test_rows': len(test_data),
        }
        os.makedirs(os.path.dirname(_THRESHOLDS_JSON_PATH), exist_ok=True)
        with open(_THRESHOLDS_JSON_PATH, 'w') as f:
            json.dump(payload, f, indent=2)
        print(f'\n[optimize] Thresholds saved to {_THRESHOLDS_JSON_PATH}')
        print('[optimize] Restart the Flask API to pick up the new thresholds.')
        print('[optimize] Verify with: py -c "import config; print(config.PER_SPORT_THRESHOLDS)"')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', default='logreg_v2', help='Gate name (default: logreg_v2)')
    parser.add_argument('--base-model', default='logreg', help='Base model key in corpus cache (default: logreg)')
    parser.add_argument('--sport', help='Comma-separated sport filter (default: all)')
    parser.add_argument(
        '--objective', choices=['upc', 'sharpe', 'units'], default='upc',
        help='Primary optimization objective: upc=units/pick (default), sharpe=season Sharpe ratio, units=total units',
    )
    parser.add_argument(
        '--min-seasons', type=int, default=2, metavar='N', dest='min_seasons',
        help='Min picks per (sport, year) group to include in Sharpe computation (default: 2)',
    )
    parser.add_argument(
        '--test-holdout', type=int, default=0, metavar='N', dest='test_holdout',
        help='Reserve N most recent seasons per sport as an out-of-sample test set (default: 0 = no holdout). Recommended: 1.',
    )
    parser.add_argument(
        '--save', action='store_true', default=False,
        help=f'Write per-sport thresholds to {_THRESHOLDS_JSON_PATH} for use by the live pipeline.',
    )
    args = parser.parse_args(argv)

    if args.sport:
        sports = [s.strip().lower() for s in args.sport.split(',') if s.strip()]
        unknown = [s for s in sports if s not in config.SPORTS]
        if unknown:
            parser.error(f'Unknown sport(s): {", ".join(unknown)}')
    else:
        sports = list(config.SPORTS)

    if not os.path.isdir(_CORPUS_CACHE_DIR):
        print(f'[optimize] Corpus cache directory not found: {_CORPUS_CACHE_DIR}')
        print('[optimize] Run train_meta_model.py --walk-forward first.')
        return 1

    run(
        gate_name=args.name,
        base_model=args.base_model,
        sports=sports,
        objective=args.objective,
        min_picks_per_season=args.min_seasons,
        n_holdout=args.test_holdout,
        save=args.save,
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
