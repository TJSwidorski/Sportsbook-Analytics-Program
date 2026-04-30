"""Tests for store.py — schema migration, metadata, history, and picks_log."""

import datetime
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

import store


class _StoreTestBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, 'cache.db')
        self._patcher = patch.object(store, '_DB_PATH', self.db_path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)


class TestMigrationIdempotent(_StoreTestBase):
    def test_alter_columns_added_once(self):
        # Simulate an old schema without the new columns.
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
        CREATE TABLE games (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          sport TEXT NOT NULL, cache_key TEXT NOT NULL,
          date TEXT, week INTEGER, row_index INTEGER NOT NULL,
          away_lines TEXT NOT NULL, home_lines TEXT NOT NULL,
          away_score TEXT, home_score TEXT
        );
        CREATE TABLE cached_keys (
          sport TEXT NOT NULL, cache_key TEXT NOT NULL,
          fetched_at TEXT NOT NULL,
          PRIMARY KEY (sport, cache_key)
        );
        """)
        conn.commit()
        conn.close()

        # First _connect() runs the ALTERs.
        c1 = store._connect()
        cols = [r[1] for r in c1.execute("PRAGMA table_info(games)").fetchall()]
        c1.close()
        for col in ('away_team', 'home_team', 'away_abbr', 'home_abbr', 'sportsbooks'):
            self.assertIn(col, cols)

        # Second _connect() must not raise: ALTERs are wrapped in try/except.
        c2 = store._connect()
        c2.close()


class TestMetadataRoundTrip(_StoreTestBase):
    def test_save_load_preserves_team_and_books(self):
        df = pd.DataFrame({
            'Date': ['2024-11-15'],
            'Away Lines': [['+110', '-105']],
            'Home Lines': [['-120', '+100']],
            'Away Score': ['101'],
            'Home Score': ['99'],
            'Away Team': ['Detroit Pistons'],
            'Home Team': ['Orlando Magic'],
            'Away Abbr': ['DET'],
            'Home Abbr': ['ORL'],
            'Sportsbooks': [['Open', 'BetMGM']],
        })
        store.save('nba', '2024-11-15', df)
        loaded = store.load('nba', '2024-11-15')
        self.assertEqual(loaded.iloc[0]['Away Team'], 'Detroit Pistons')
        self.assertEqual(loaded.iloc[0]['Home Abbr'], 'ORL')
        self.assertEqual(loaded.iloc[0]['Sportsbooks'], ['Open', 'BetMGM'])

    def test_load_old_rows_returns_empty_metadata(self):
        # Save without metadata columns (mimicking pre-migration cached rows).
        df = pd.DataFrame({
            'Date': ['2024-11-15'],
            'Away Lines': [['+110']],
            'Home Lines': [['-110']],
            'Away Score': ['101'],
            'Home Score': ['99'],
        })
        store.save('nba', '2024-11-15', df)
        loaded = store.load('nba', '2024-11-15')
        self.assertEqual(loaded.iloc[0]['Away Team'], '')
        self.assertEqual(loaded.iloc[0]['Sportsbooks'], [])


class TestBacktestHistory(_StoreTestBase):
    def _save(self, sport='nba', season_year=2025, model='logreg', **overrides):
        defaults = dict(
            sport=sport, season_year=season_year, model=model,
            start_date='2024-10-01', end_date='2025-06-30',
            total_games=200, games_picked=120, correct_picks=72,
            win_rate=0.6, flat_units=4.5, kelly_units=0.18,
            roi_flat=0.0375, roi_kelly=0.0015,
            game_log=[],
        )
        defaults.update(overrides)
        store.save_backtest_history(**defaults)

    def test_save_then_load_round_trip(self):
        self._save()
        rows = store.load_backtest_history()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['sport'], 'nba')
        self.assertEqual(rows[0]['season_year'], 2025)
        self.assertAlmostEqual(rows[0]['win_rate'], 0.6)
        self.assertNotIn('game_log_json', rows[0])
        self.assertNotIn('game_log', rows[0])

    def test_upsert_replaces_existing(self):
        self._save(flat_units=1.0)
        self._save(flat_units=9.9)
        rows = store.load_backtest_history(sport='nba')
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]['flat_units'], 9.9)

    def test_filter_by_sport(self):
        self._save(sport='nba', season_year=2025)
        self._save(sport='nfl', season_year=2024)
        rows = store.load_backtest_history(sport='nfl')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['sport'], 'nfl')

    def test_include_game_log_returns_list(self):
        self._save(game_log=[{
            'game_index': 0, 'date_or_week': '2024-10-15',
            'pick': 'Home', 'actual': 'Home', 'correct': True,
            'units': 1.0, 'kelly_units': 0.05,
            'bet_line': '+100', 'unit_size': 0.05, 'ev': 0.05,
            'away_lines': ['+110'], 'home_lines': ['-100'],
        }])
        rows = store.load_backtest_history(include_game_log=True)
        self.assertEqual(len(rows[0]['game_log']), 1)
        self.assertEqual(rows[0]['game_log'][0]['pick'], 'Home')

    def test_max_drawdown_round_trips(self):
        self._save(max_drawdown=3.25)
        rows = store.load_backtest_history()
        self.assertAlmostEqual(rows[0]['max_drawdown'], 3.25)


class TestRollingBacktestCache(_StoreTestBase):
    def _save(self, sport='nba', end_date='2026-04-29', window_days=30, **overrides):
        defaults = dict(
            sport=sport,
            end_date=end_date,
            window_days=window_days,
            start_date='2026-03-31',
            model='logreg',
            total_games=100,
            games_picked=60,
            correct_picks=33,
            win_rate=0.55,
            flat_units=4.2,
            kelly_units=0.12,
            max_drawdown=2.5,
            daily_units=[
                {'day': '2026-04-28', 'units': 0.5, 'kelly_units': 0.01,
                 'cum_units': 0.5, 'cum_kelly_units': 0.01},
                {'day': '2026-04-29', 'units': 1.0, 'kelly_units': 0.02,
                 'cum_units': 1.5, 'cum_kelly_units': 0.03},
            ],
            game_log=[],
        )
        defaults.update(overrides)
        store.save_rolling_backtest(**defaults)

    def test_save_and_load_round_trip(self):
        self._save()
        rows = store.load_rolling_backtest(window_days=30)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['sport'], 'nba')
        self.assertEqual(row['window_days'], 30)
        self.assertAlmostEqual(row['max_drawdown'], 2.5)
        self.assertEqual(len(row['daily_units']), 2)
        self.assertNotIn('daily_units_json', row)

    def test_upsert_replaces_row_for_same_window(self):
        self._save(flat_units=1.0)
        self._save(flat_units=8.8)
        rows = store.load_rolling_backtest(window_days=30)
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]['flat_units'], 8.8)

    def test_separate_windows_coexist(self):
        self._save(window_days=7, flat_units=1.5)
        self._save(window_days=30, flat_units=4.2)
        seven = store.load_rolling_backtest(window_days=7)
        thirty = store.load_rolling_backtest(window_days=30)
        self.assertAlmostEqual(seven[0]['flat_units'], 1.5)
        self.assertAlmostEqual(thirty[0]['flat_units'], 4.2)

    def test_rolling_computed_today_true_after_save(self):
        self._save()
        # Saved row has computed_at = utcnow().isoformat() — starts with today.
        self.assertTrue(store.rolling_computed_today('nba', 30))

    def test_rolling_computed_today_false_for_unknown_sport(self):
        self.assertFalse(store.rolling_computed_today('nfl', 30))


class _FakePick:
    def __init__(self, **kw):
        self.game_index = kw.get('game_index', 0)
        self.pick = kw.get('pick', 'Home')
        self.confidence = kw.get('confidence', 0.6)
        self.away_prob = kw.get('away_prob', 0.4)
        self.home_prob = kw.get('home_prob', 0.6)
        self.away_lines = kw.get('away_lines', ['+100', '+110'])
        self.home_lines = kw.get('home_lines', ['-110', '-105'])
        self.away_team = kw.get('away_team', 'Boston Celtics')
        self.home_team = kw.get('home_team', 'Denver Nuggets')
        self.away_abbr = kw.get('away_abbr', 'BOS')
        self.home_abbr = kw.get('home_abbr', 'DEN')
        self.bet_line = kw.get('bet_line', '-105')
        self.ev = kw.get('ev', 0.04)
        self.unit_size = kw.get('unit_size', 0.03)


class TestPicksLog(_StoreTestBase):
    def test_log_picks_inserts_rows(self):
        n = store.log_picks('nba', '2026-04-27', '2026-04-27',
                            [_FakePick(), _FakePick(game_index=1, pick='Away')])
        self.assertEqual(n, 2)
        unsettled = store.unsettled_picks(sport='nba')
        self.assertEqual(len(unsettled), 2)
        self.assertEqual(unsettled[0]['away_team'], 'Boston Celtics')

    def test_log_picks_idempotent(self):
        store.log_picks('nba', '2026-04-27', '2026-04-27', [_FakePick()])
        again = store.log_picks('nba', '2026-04-27', '2026-04-27', [_FakePick()])
        self.assertEqual(again, 0)

    def test_settle_correct_pick(self):
        store.log_picks('nba', '2026-04-27', '2026-04-27',
                        [_FakePick(pick='Home', bet_line='+200', unit_size=0.04)])
        unsettled = store.unsettled_picks()
        pid = unsettled[0]['id']
        ok = store.settle_pick_record(pid, away_score='99', home_score='105')
        self.assertTrue(ok)
        recent = store.recent_settled_picks(limit=10)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]['result'], 'W')
        self.assertAlmostEqual(recent[0]['flat_units'], 2.0)
        self.assertAlmostEqual(recent[0]['kelly_units'], 0.08)

    def test_settle_is_idempotent(self):
        store.log_picks('nba', '2026-04-27', '2026-04-27', [_FakePick()])
        pid = store.unsettled_picks()[0]['id']
        self.assertTrue(store.settle_pick_record(pid, 100, 105))
        self.assertFalse(store.settle_pick_record(pid, 100, 105))

    def test_unsettled_max_age_filter(self):
        # An old game past the cutoff should be omitted.
        old_day = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
        store.log_picks('nba', old_day, old_day, [_FakePick()])
        recent_day = datetime.date.today().isoformat()
        store.log_picks('nba', recent_day, recent_day,
                        [_FakePick(game_index=1)])
        rows = store.unsettled_picks(max_age_days=30)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['game_date'], recent_day)

    def test_daily_performance_includes_zero_days(self):
        # No settled picks: every day in window still present.
        series = store.daily_performance(days=5)
        self.assertEqual(len(series), 5)
        for entry in series:
            self.assertEqual(entry['units'], 0.0)
            self.assertEqual(entry['cum_units'], 0.0)

    def test_daily_performance_cumulative(self):
        today = datetime.date.today().isoformat()
        store.log_picks('nba', today, today,
                        [_FakePick(pick='Home', bet_line='+100', unit_size=0.05)])
        pid = store.unsettled_picks()[0]['id']
        store.settle_pick_record(pid, away_score=100, home_score=110)
        series = store.daily_performance(days=3)
        # last day is today
        self.assertEqual(series[-1]['day'], today)
        self.assertAlmostEqual(series[-1]['units'], 1.0)
        self.assertAlmostEqual(series[-1]['cum_units'], 1.0)


if __name__ == '__main__':
    unittest.main()
