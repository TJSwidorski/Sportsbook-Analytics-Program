"""
Flask API server for Axiom Picks.

Run from the project root:
    python api.py

Endpoints:
    GET  /api/sports
    GET  /api/picks?sport=nba&date=YYYY-MM-DD
    GET  /api/picks/all?date=YYYY-MM-DD
    GET  /api/picks/upcoming?date=YYYY-MM-DD
    POST /api/backtest  { sport, start, end }
    GET  /api/history?model=logreg
    GET  /api/history/recent-picks?limit=50
    GET  /api/history/performance?days=30
    GET  /api/history/rolling?days=30&model=logreg
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime
import math
import sys
import os

# Ensure project root is on path when run from anywhere
sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)


def _safe_num(value):
    """Return None for NaN floats so the JSON response stays parseable in browsers."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _pick_to_dict(p):
    return {
        'game_index': p.game_index,
        'pick': p.pick,
        'confidence': _safe_num(p.confidence),
        'away_prob': _safe_num(p.away_prob),
        'home_prob': _safe_num(p.home_prob),
        'away_lines': p.away_lines,
        'home_lines': p.home_lines,
        'away_team': getattr(p, 'away_team', '') or '',
        'home_team': getattr(p, 'home_team', '') or '',
        'away_abbr': getattr(p, 'away_abbr', '') or '',
        'home_abbr': getattr(p, 'home_abbr', '') or '',
        'sportsbooks': getattr(p, 'sportsbooks', []) or [],
        'ev': _safe_num(getattr(p, 'ev', None)),
        'unit_size': _safe_num(getattr(p, 'unit_size', 0.0)) or 0.0,
        'bet_line': getattr(p, 'bet_line', None),
        'model': getattr(p, 'model', 'logreg_v2'),
        'predicted_units': _safe_num(getattr(p, 'predicted_units', None)),
    }


def _meta_threshold_arg(default: float = 0.0) -> float:
    """Read `meta_threshold` from a query string, returning `default` on error."""
    raw = request.args.get('meta_threshold')
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


@app.route('/api/sports')
def sports_list():
    from config import SPORTS, is_in_season
    today = datetime.date.today()
    return jsonify({
        'sports': [
            {
                'key': k,
                'date_type': v['date_type'],
                'in_season': is_in_season(k, today),
            }
            for k, v in SPORTS.items()
        ]
    })


@app.route('/api/picks')
def picks():
    sport = request.args.get('sport', 'nba')
    date_str = request.args.get('date', datetime.date.today().isoformat())
    model_type = request.args.get('model', 'logreg_v2')
    meta_threshold = _meta_threshold_arg()

    try:
        import config
        from runner import get_daily_picks

        d = datetime.date.fromisoformat(date_str)
        cfg = config.SPORTS.get(sport)
        if cfg is None:
            return jsonify({'error': f'Unknown sport: {sport}'}), 400

        if cfg['date_type'] == 'week':
            date_or_week = config.date_to_week(sport, d)
            if date_or_week is None:
                return jsonify({'sport': sport, 'date': date_str, 'picks': [],
                                'error': 'Season week not configured for this date'})
        else:
            date_or_week = date_str

        pick_list = get_daily_picks(
            sport, date_or_week,
            model_type=model_type, meta_threshold=meta_threshold,
        )
        return jsonify({
            'sport': sport,
            'date': date_str,
            'model': model_type,
            'meta_threshold': meta_threshold,
            'picks': [_pick_to_dict(p) for p in pick_list],
        })

    except Exception as exc:
        return jsonify({'sport': sport, 'date': date_str, 'picks': [],
                        'error': str(exc)}), 500


@app.route('/api/picks/all')
def picks_all():
    date_str = request.args.get('date', datetime.date.today().isoformat())
    model_type = request.args.get('model', 'logreg_v2')
    meta_threshold = _meta_threshold_arg()
    try:
        from runner import run_all_sports
        results = run_all_sports(
            date_str, model_type=model_type, meta_threshold=meta_threshold,
        )
        return jsonify({
            'date': date_str,
            'model': model_type,
            'meta_threshold': meta_threshold,
            'sports': {
                sport: [_pick_to_dict(p) for p in pick_list]
                for sport, pick_list in results.items()
            },
        })
    except Exception as exc:
        return jsonify({'date': date_str, 'sports': {}, 'error': str(exc)}), 500


@app.route('/api/picks/upcoming')
def picks_upcoming():
    """
    Today's unplayed picks plus tomorrow's full slate, grouped by sport.

    Response shape:
      {
        "date": "YYYY-MM-DD",
        "tomorrow_date": "YYYY-MM-DD",
        "sports": {
          "nba": {"today": [pick, ...], "tomorrow": [pick, ...]},
          ...
        }
      }
    """
    date_str = request.args.get('date', datetime.date.today().isoformat())
    model_type = request.args.get('model', 'logreg_v2')
    meta_threshold = _meta_threshold_arg()
    try:
        from runner import run_all_sports_upcoming
        results = run_all_sports_upcoming(
            date_str, model_type=model_type, meta_threshold=meta_threshold,
        )
        tomorrow_str = (
            datetime.date.fromisoformat(date_str) + datetime.timedelta(days=1)
        ).isoformat()
        return jsonify({
            'date': date_str,
            'tomorrow_date': tomorrow_str,
            'model': model_type,
            'meta_threshold': meta_threshold,
            'sports': {
                sport: {
                    'today': [_pick_to_dict(p) for p in buckets['today']],
                    'tomorrow': [_pick_to_dict(p) for p in buckets['tomorrow']],
                }
                for sport, buckets in results.items()
            },
        })
    except Exception as exc:
        return jsonify({
            'date': date_str,
            'sports': {},
            'error': str(exc),
        }), 500


@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    try:
        body = request.get_json(silent=True) or {}
        sport = body.get('sport', 'nba')
        start = body.get('start', '2024-01-01')
        end = body.get('end', '2024-12-31')
        model_type = body.get('model', 'logreg_v2')
        try:
            meta_threshold = float(body.get('meta_threshold', 0.0))
        except (TypeError, ValueError):
            meta_threshold = 0.0

        from backtest import Backtester
        result = Backtester(
            sport, start, end,
            model_type=model_type, meta_threshold=meta_threshold,
        ).run()
        return jsonify({
            'sport': result.sport,
            'model': result.model,
            'meta_threshold': meta_threshold,
            'start': result.start,
            'end': result.end,
            'total_games': result.total_games,
            'games_picked': result.games_picked,
            'correct_picks': result.correct_picks,
            'accuracy': result.accuracy,
            'total_units': result.total_units,
            'flat_units': result.flat_units,
            'kelly_units': result.kelly_units,
            'max_drawdown': result.max_drawdown,
            'game_log': [
                {
                    'game_index': g.game_index,
                    'date_or_week': g.date_or_week,
                    'pick': g.pick,
                    'actual': g.actual,
                    'correct': g.correct,
                    'units': g.units,
                    'kelly_units': g.kelly_units,
                    'bet_line': g.bet_line,
                    'unit_size': g.unit_size,
                    'ev': _safe_num(g.ev),
                    'confidence': _safe_num(g.confidence),
                    'home_prob': _safe_num(g.home_prob),
                    'predicted_units': _safe_num(g.predicted_units),
                    'away_lines': g.away_lines,
                    'home_lines': g.home_lines,
                }
                for g in result.game_log
            ],
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


def _format_matchup(row):
    """Build 'AWAY @ HOME' from a picks_log row, falling back to team names."""
    away = row.get('away_abbr') or row.get('away_team') or '?'
    home = row.get('home_abbr') or row.get('home_team') or '?'
    return f'{away} @ {home}'


@app.route('/api/history')
def history_summary():
    """
    Aggregate per-sport, every-cached-season backtest stats. Read-only —
    populate this table by running `python backtest_history.py`.

    `totals` are computed across the merged chronological pick stream so
    `max_drawdown` is the true all-time floor (not the max of per-season
    floors), and `earliest_year` is sourced from the actual game logs.
    """
    model_type = request.args.get('model', 'logreg_v2')
    import store
    rows = store.load_backtest_history(model=model_type, include_game_log=True)
    if not rows:
        return jsonify({
            'model': model_type,
            'sports': [],
            'totals': None,
            'error': (
                'No backtest history yet. '
                'Run `python backtest_history.py` to populate it.'
            ),
        }), 404

    total_picked = sum(r['games_picked'] for r in rows)
    total_correct = sum(r['correct_picks'] for r in rows)
    total_flat = sum(r['flat_units'] for r in rows)
    total_kelly = sum(r['kelly_units'] for r in rows)

    # Merge every season's per-game log into one chronological stream and
    # compute the running cumulative-units floor for the true all-time
    # max-drawdown. Date keys for week-based sports (numeric strings) are
    # bucketed at the end so they don't pollute the chronological merge of
    # date-based seasons.
    merged: list[tuple[str, float]] = []
    for r in rows:
        for g in r.get('game_log') or []:
            key = g.get('date_or_week') or ''
            units = float(g.get('units') or 0.0)
            merged.append((key, units))

    def _sort_key(item):
        key, _ = item
        # Date strings sort before numeric weeks; both stable internally.
        return (0, key) if '-' in key else (1, key.zfill(6))
    merged.sort(key=_sort_key)

    cum = 0.0
    floor = 0.0
    earliest_date = None
    for key, units in merged:
        cum += units
        if cum < floor:
            floor = cum
        if '-' in key and (earliest_date is None or key < earliest_date):
            earliest_date = key

    earliest_year = None
    if earliest_date:
        try:
            earliest_year = int(earliest_date[:4])
        except (TypeError, ValueError):
            earliest_year = None
    if earliest_year is None and rows:
        # Fallback: derive from the earliest start_date / season_year.
        years = []
        for r in rows:
            sd = r.get('start_date') or ''
            if len(sd) >= 4 and sd[:4].isdigit():
                years.append(int(sd[:4]))
            elif r.get('season_year'):
                years.append(int(r['season_year']))
        if years:
            earliest_year = min(years)

    max_dd_overall = abs(floor)

    # Strip the heavy game logs out of the per-sport rows we send back.
    sports_rows = [{k: v for k, v in r.items() if k != 'game_log'} for r in rows]

    totals = {
        'games_picked': total_picked,
        'correct_picks': total_correct,
        'win_rate': (total_correct / total_picked) if total_picked else None,
        'flat_units': total_flat,
        'kelly_units': total_kelly,
        'roi_flat': (total_flat / total_picked) if total_picked else None,
        'roi_kelly': (total_kelly / total_picked) if total_picked else None,
        'max_drawdown': max_dd_overall,
        'earliest_year': earliest_year,
    }
    return jsonify({
        'model': model_type,
        'sports': sports_rows,
        'totals': totals,
    })


@app.route('/api/history/recent-picks')
def history_recent_picks():
    try:
        limit = max(1, min(int(request.args.get('limit', 50)), 200))
    except (TypeError, ValueError):
        limit = 50
    import store
    rows = store.recent_settled_picks(limit=limit)
    picks = [
        {
            'date': r['game_date'],
            'sport': r['sport'],
            'matchup': _format_matchup(r),
            'pick': r['pick'],
            'bet_line': r.get('bet_line'),
            'result': r['result'],
            'actual': r['actual'],
            'units': _safe_num(r.get('flat_units')),
            'kelly_units': _safe_num(r.get('kelly_units')),
            'unit_size': _safe_num(r.get('unit_size')),
            'ev': _safe_num(r.get('ev')),
        }
        for r in rows
    ]
    return jsonify({'picks': picks})


@app.route('/api/history/performance')
def history_performance():
    try:
        days = max(1, min(int(request.args.get('days', 30)), 365))
    except (TypeError, ValueError):
        days = 30
    import store
    return jsonify({'days': days, 'series': store.daily_performance(days=days)})


@app.route('/api/history/rolling')
def history_rolling():
    """
    Rolling N-day backtest results per in-season sport, plus a combined
    daily cumulative-units series for charting. Reads the cache populated by
    `rolling_backtest.compute_all_rolling()` (refreshed daily by the prefetch
    thread). On cache miss this endpoint computes synchronously for the
    requested window so first-time loads still work.
    """
    try:
        days = max(1, min(int(request.args.get('days', 30)), 180))
    except (TypeError, ValueError):
        days = 30
    model_type = request.args.get('model', 'logreg_v2')

    import store
    rows = store.load_rolling_backtest(window_days=days, model=model_type)

    if not rows:
        # First-time hit (or a freshly-imported DB) — compute now.
        try:
            from rolling_backtest import compute_all_rolling
            compute_all_rolling(window_days=days, model=model_type)
        except Exception as exc:
            return jsonify({
                'days': days,
                'sports': [],
                'totals': None,
                'series': [],
                'error': f'Rolling backtest failed: {exc}',
            }), 500
        rows = store.load_rolling_backtest(window_days=days, model=model_type)

    total_picked = sum(r['games_picked'] for r in rows)
    total_correct = sum(r['correct_picks'] for r in rows)
    total_flat = sum(r['flat_units'] for r in rows)
    total_kelly = sum(r['kelly_units'] for r in rows)
    total_max_dd = max((r.get('max_drawdown') or 0.0) for r in rows) if rows else 0.0

    # Combine per-sport daily series into a single chart-friendly cumulative
    # series. Use the union of all days seen across sports.
    by_day_flat = {}
    by_day_kelly = {}
    for row in rows:
        for entry in row.get('daily_units', []):
            day = entry.get('day')
            if not day:
                continue
            by_day_flat[day] = by_day_flat.get(day, 0.0) + float(entry.get('units', 0.0))
            by_day_kelly[day] = by_day_kelly.get(day, 0.0) + float(entry.get('kelly_units', 0.0))

    series = []
    cum_flat = 0.0
    cum_kelly = 0.0
    for day in sorted(by_day_flat.keys()):
        cum_flat += by_day_flat[day]
        cum_kelly += by_day_kelly[day]
        series.append({
            'day': day,
            'units': round(by_day_flat[day], 4),
            'kelly_units': round(by_day_kelly[day], 6),
            'cum_units': round(cum_flat, 4),
            'cum_kelly_units': round(cum_kelly, 6),
        })

    return jsonify({
        'days': days,
        'model': model_type,
        'sports': rows,
        'totals': {
            'games_picked': total_picked,
            'correct_picks': total_correct,
            'win_rate': (total_correct / total_picked) if total_picked else None,
            'flat_units': total_flat,
            'kelly_units': total_kelly,
            'max_drawdown': total_max_dd,
        },
        'series': series,
    })


if __name__ == '__main__':
    from prefetch import start_background_prefetch
    from waitress import serve
    start_background_prefetch(fallback_days_back=60)
    # waitress handles long requests + concurrent threads more reliably than
    # Werkzeug's dev server, which drops connections on Windows during multi-
    # second requests like /api/backtest.
    serve(app, host='127.0.0.1', port=5000, threads=8, channel_timeout=600)
