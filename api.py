"""
Flask API server for Axiom Picks.

Run from the project root:
    python api.py

Endpoints:
    GET  /api/sports
    GET  /api/picks?sport=nba&date=YYYY-MM-DD
    GET  /api/picks/all?date=YYYY-MM-DD
    POST /api/backtest  { sport, start, end, training_window_days }
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime
import sys
import os

# Ensure project root is on path when run from anywhere
sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)


def _pick_to_dict(p):
    return {
        'game_index': p.game_index,
        'pick': p.pick,
        'confidence': p.confidence,
        'away_prob': p.away_prob,
        'home_prob': p.home_prob,
        'away_lines': p.away_lines,
        'home_lines': p.home_lines,
    }


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

        pick_list = get_daily_picks(sport, date_or_week)
        return jsonify({
            'sport': sport,
            'date': date_str,
            'picks': [_pick_to_dict(p) for p in pick_list],
        })

    except Exception as exc:
        return jsonify({'sport': sport, 'date': date_str, 'picks': [],
                        'error': str(exc)}), 500


@app.route('/api/picks/all')
def picks_all():
    date_str = request.args.get('date', datetime.date.today().isoformat())
    try:
        from runner import run_all_sports
        results = run_all_sports(date_str)
        return jsonify({
            'date': date_str,
            'sports': {
                sport: [_pick_to_dict(p) for p in pick_list]
                for sport, pick_list in results.items()
            },
        })
    except Exception as exc:
        return jsonify({'date': date_str, 'sports': {}, 'error': str(exc)}), 500


@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    body = request.json or {}
    sport = body.get('sport', 'nba')
    start = body.get('start', '2024-01-01')
    end = body.get('end', '2024-12-31')
    window = int(body.get('training_window_days', 60))

    try:
        from backtest import Backtester
        result = Backtester(sport, start, end, window).run()
        return jsonify({
            'sport': result.sport,
            'start': result.start,
            'end': result.end,
            'total_games': result.total_games,
            'games_picked': result.games_picked,
            'correct_picks': result.correct_picks,
            'accuracy': result.accuracy,
            'total_units': result.total_units,
            'game_log': [
                {
                    'game_index': g.game_index,
                    'date_or_week': g.date_or_week,
                    'pick': g.pick,
                    'actual': g.actual,
                    'correct': g.correct,
                    'units': g.units,
                    'away_lines': g.away_lines,
                    'home_lines': g.home_lines,
                }
                for g in result.game_log
            ],
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
