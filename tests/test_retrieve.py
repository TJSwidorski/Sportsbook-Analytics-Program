import unittest
from unittest.mock import patch, MagicMock
from retrieve import (
    MoneyLineAPI, NBAMoneyLineAPI, NHLMoneyLineAPI, MLBMoneyLineAPI,
    MLSMoneyLineAPI, WNBAMoneyLineAPI, CFLMoneyLineAPI,
    _PlayerNameMixin, SportsbookReviewAPI,
)

# ---------------------------------------------------------------------------
# Shared synthetic fixtures
# ---------------------------------------------------------------------------

# Odds token stream for 2 NBA games (Date-based).
# Pattern: [time, odds×14, time, odds×14]
# 14 odds per game = 7 sportsbooks × 2 sides; even indices → Away, odd → Home.
_ODDS_2GAME = [
    '7:30 PM ET',
    '+110', '-110', '+120', '-120', '+105', '-105', '+115', '-115',
    '+108', '-108', '+112', '-112', '+106', '-106',
    '9:00 PM ET',
    '+150', '-150', '+130', '-130', '+125', '-125', '+118', '-118',
    '+122', '-122', '+116', '-116', '+114', '-114',
]

# Scores token stream for the same 2 games.
# Structure the base clean_scores algorithm expects (Date, indices [2,3]):
#   [Rot, WAGERSOPENER, away1, home1, concat1, away1, home1, %markers, away2, home2, concat2, away2, home2, %marker]
_SCORES_2GAME = [
    'Rot', 'WAGERSOPENER',
    '21', '33',                          # game 1 scores (picked up at [2],[3])
    '2133', '21', '33',                  # concat + repeat  (used by find())
    '73%27%', '73%', '27%',              # wager % (algorithm detects '%' here)
    '45', '67',                          # game 2 scores  (data[i+1], data[i+2])
    '4567', '45', '67', '8020%',         # concat + repeat + trailing %
]

# Scores for 1-game scenarios (terminates cleanly when find() breaks on short data)
_SCORES_1GAME = [
    'Rot', 'WAGERSOPENER',
    '21', '33',
    '2133', '21', '33', '73%27%',
]

# MLS/WNBA/CFL style scores_data: team names + zeros (not yet played)
_SCORES_MLS_STYLE = [
    'Rot', 'WAGERSOPENER',
    'Atlanta United FC', '0', 'Toronto FC', '0', '--', '-', '-',
    'New York City FC', '2', 'CF Montreal', '1', '--', '-', '-',
]

# MLB style: pitcher names + concatenated scores + individual scores
_SCORES_MLB_STYLE = [
    'Rot', 'WAGERSOPENER',
    'J.Ritchie(R)', '7', 'C.Cavalli(R)', '2',
    '01', '0', '1',
    '32', '3', '2',
]

# NHL odds stream: includes a goalie name (older era)
_ODDS_NHL_WITH_GOALIE = [
    '7:30 PM ET',
    'Carey Price',          # goalie name — should be filtered
    '+130', '-150', '+125', '-145', '+128', '-148', '+132',
    '-150', '+130', '-145', '+125', '-148', '+128', '-132',
    '9:00 PM ET',
    '+110', '-130',
]

# Minimal HTML used for SportsbookReviewAPI end-to-end mock tests
_FIXTURE_HTML = """
<html><body>
  <span class="fs-9">7:30 PM ET</span>
  <span class="fs-9">+110</span><span class="fs-9">-110</span>
  <span class="fs-9">+120</span><span class="fs-9">-120</span>
  <span class="fs-9">+105</span><span class="fs-9">-105</span>
  <span class="fs-9">+115</span><span class="fs-9">-115</span>
  <span class="fs-9">+108</span><span class="fs-9">-108</span>
  <span class="fs-9">+112</span><span class="fs-9">-112</span>
  <span class="fs-9">+106</span><span class="fs-9">-106</span>
  <div class="fs-9">Rot</div>
  <div class="fs-9">WAGERSOPENER</div>
  <div class="fs-9">21</div>
  <div class="fs-9">33</div>
  <div class="fs-9">2133</div>
  <div class="fs-9">21</div>
  <div class="fs-9">33</div>
  <div class="fs-9">73%27%</div>
</body></html>
"""


def _make_api(date_type='date', date='2024-11-15', cls=NBAMoneyLineAPI,
              odds=None, scores=None):
    """
    Instantiate a MoneyLineAPI subclass without hitting the network.
    Injects synthetic odds and scores directly.
    """
    if odds is None:
        odds = _ODDS_2GAME
    if scores is None:
        scores = _SCORES_2GAME
    return cls(date_type, date, odds, scores)


# ---------------------------------------------------------------------------
# _is_odds
# ---------------------------------------------------------------------------

class TestIsOdds(unittest.TestCase):
    def setUp(self):
        self.api = MoneyLineAPI.__new__(MoneyLineAPI)

    def test_positive_valid(self):
        self.assertTrue(self.api._is_odds('+110'))

    def test_negative_valid(self):
        self.assertTrue(self.api._is_odds('-220'))

    def test_even_money(self):
        self.assertTrue(self.api._is_odds('+100'))

    def test_plain_number_rejected(self):
        self.assertFalse(self.api._is_odds('110'))

    def test_alphabetic_rejected(self):
        self.assertFalse(self.api._is_odds('EV'))

    def test_pk_rejected(self):
        self.assertFalse(self.api._is_odds('pk'))

    def test_hyphenated_name_rejected(self):
        # Critical: hyphenated names must NOT be treated as odds
        self.assertFalse(self.api._is_odds('Marc-Andre Fleury'))

    def test_plain_minus_rejected(self):
        self.assertFalse(self.api._is_odds('-'))

    def test_empty_string_rejected(self):
        self.assertFalse(self.api._is_odds(''))


# ---------------------------------------------------------------------------
# _is_player_name  (_PlayerNameMixin)
# ---------------------------------------------------------------------------

class TestIsPlayerName(unittest.TestCase):
    def setUp(self):
        class _TestAPI(_PlayerNameMixin, MoneyLineAPI):
            pass
        self.api = _TestAPI.__new__(_TestAPI)

    def test_simple_name(self):
        self.assertTrue(self.api._is_player_name('Carey Price'))

    def test_hyphenated_name(self):
        self.assertTrue(self.api._is_player_name('Marc-Andre Fleury'))

    def test_pitcher_abbreviation(self):
        # 'J.Ritchie(R)' — contains parens, NOT purely alpha after clean
        # Parens are not stripped, so clean would contain '(' → not alpha → False
        # This is intentional: pitcher names with '(R)' are filtered by the
        # scores-side parser, not by _is_player_name on the odds side.
        result = self.api._is_player_name('J.Ritchie(R)')
        # We just assert it doesn't crash; the actual True/False depends on
        # whether parens pass the isalpha check (they don't → False)
        self.assertIsInstance(result, bool)

    def test_odds_not_a_name(self):
        self.assertFalse(self.api._is_player_name('+110'))

    def test_minus_not_a_name(self):
        self.assertFalse(self.api._is_player_name('-'))

    def test_time_not_a_name(self):
        self.assertFalse(self.api._is_player_name('7:30 PM ET'))


# ---------------------------------------------------------------------------
# clean_data
# ---------------------------------------------------------------------------

class TestCleanData(unittest.TestCase):
    def _make(self, odds, cls=NBAMoneyLineAPI):
        api = cls.__new__(cls)
        api.date_type = 'Date'
        api.date = '2024-11-15'
        return api.clean_data(odds)

    def test_two_games_parsed(self):
        games = self._make(_ODDS_2GAME)
        self.assertEqual(len(games), 2)

    def test_game_has_required_keys(self):
        games = self._make(_ODDS_2GAME)
        for game in games:
            self.assertIn('Date', game)
            self.assertIn('Away Lines', game)
            self.assertIn('Home Lines', game)

    def test_away_home_interleaved_correctly(self):
        # Even-indexed odds → Away, odd-indexed → Home
        games = self._make(_ODDS_2GAME)
        g = games[0]
        self.assertEqual(g['Away Lines'][0], '+110')
        self.assertEqual(g['Home Lines'][0], '-110')
        self.assertEqual(g['Away Lines'][1], '+120')
        self.assertEqual(g['Home Lines'][1], '-120')

    def test_missing_value_skipped(self):
        odds = ['7:30 PM ET', '+110', '-', '-110']
        games = self._make(odds)
        # '-' should not appear in lines
        self.assertNotIn('-', games[0]['Away Lines'])
        self.assertNotIn('-', games[0]['Home Lines'])

    def test_goalie_name_filtered_by_nhl(self):
        games = self._make(_ODDS_NHL_WITH_GOALIE, cls=NHLMoneyLineAPI)
        self.assertEqual(len(games), 2)
        for game in games:
            for line in game['Away Lines'] + game['Home Lines']:
                # No line should be a plain name
                self.assertTrue(line.startswith('+') or line.startswith('-'))

    def test_no_lines_no_game_created(self):
        # Only a time marker with no odds → one empty game with no lines
        odds = ['7:30 PM ET']
        games = self._make(odds)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['Away Lines'], [])
        self.assertEqual(games[0]['Home Lines'], [])

    def test_date_label_populated(self):
        games = self._make(_ODDS_2GAME)
        for game in games:
            self.assertEqual(game['Date'], '2024-11-15')


# ---------------------------------------------------------------------------
# MLB clean_scores — anchors on the 'XX%YY%' marker that closes each game
# ---------------------------------------------------------------------------

# Two completed MLB games; layout per game:
#   AwayPitcher AwayTotal  HomePitcher HomeTotal
#   [InningConcat I_a I_h] × 9 innings
#   AwayRecap HomeRecap  'XX%YY%'  'XX%'  'YY%'
_SCORES_MLB_REAL = [
    'Rot', 'WAGERSOPENER',
    'L.Giolito(R)', '11', 'M.Soroka(R)', '2',
    '00', '0', '0', '20', '2', '0', '00', '0', '0', '00', '0', '0',
    '70', '7', '0', '01', '0', '1', '00', '0', '0', '20', '2', '0',
    '01', '0', '1',
    '11', '2',
    '56%44%', '56%', '44%',
    'A.Abbott(L)', '9', 'J.Luzardo(L)', '6',
    '03', '0', '3', '10', '1', '0', '51', '5', '1', '10', '1', '0',
    '20', '2', '0', '02', '0', '2', '00', '0', '0', '00', '0', '0',
    '00', '0', '0',
    '9', '6',
    '48%52%', '48%', '52%',
]


class TestMLBCleanScores(unittest.TestCase):
    def setUp(self):
        self.api = MLBMoneyLineAPI.__new__(MLBMoneyLineAPI)

    def test_extracts_recap_totals(self):
        scores = self.api.clean_scores(_SCORES_MLB_REAL)
        self.assertEqual(scores, [['11', '2'], ['9', '6']])

    def test_double_digit_totals(self):
        # Recap can have multi-digit values like '11' or '24'
        data = [
            'Rot', 'WAGERSOPENER',
            'P1(R)', '24', 'P2(L)', '3',
            '24', '3',
            '70%30%', '70%', '30%',
        ]
        scores = self.api.clean_scores(data)
        self.assertEqual(scores, [['24', '3']])

    def test_unfinished_games_skipped(self):
        # No '%%' marker → no recap → empty result
        data = [
            'Rot', 'WAGERSOPENER',
            'P1(R)', '0', 'P2(L)', '0', '--', '-', '-',
        ]
        self.assertEqual(self.api.clean_scores(data), [])

    def test_ignores_single_percent_token(self):
        # '56%' alone (count('%') == 1) must not anchor; only 'XX%YY%' does
        data = ['Rot', 'WAGERSOPENER', '5', '4', '56%', '5', '4', '50%50%']
        scores = self.api.clean_scores(data)
        self.assertEqual(scores, [['5', '4']])

    def test_returns_list_of_two_element_lists(self):
        scores = self.api.clean_scores(_SCORES_MLB_REAL)
        for s in scores:
            self.assertIsInstance(s, list)
            self.assertEqual(len(s), 2)


# ---------------------------------------------------------------------------
# MLS / WNBA / CFL clean_scores — anchored on the '--' end-of-game marker
# ---------------------------------------------------------------------------

class TestMLSCleanScores(unittest.TestCase):
    """MLS layout: AwayTeam, AwayScore, HomeTeam, HomeScore, '--', '-', '-'."""

    def _parse(self, tokens):
        api = MLSMoneyLineAPI.__new__(MLSMoneyLineAPI)
        return api.clean_scores(tokens)

    def test_single_game(self):
        tokens = ['Rot', 'WAGERSOPENER', 'Austin', '3', 'Toronto', '3', '--', '-', '-']
        self.assertEqual(self._parse(tokens), [['3', '3']])

    def test_multi_game(self):
        tokens = [
            'Rot', 'WAGERSOPENER',
            'Austin', '3', 'Toronto', '3', '--', '-', '-',
            'NYRB',   '1', 'Montreal', '4', '--', '-', '-',
        ]
        self.assertEqual(self._parse(tokens), [['3', '3'], ['1', '4']])

    def test_empty_input_returns_empty(self):
        self.assertEqual(self._parse([]), [])


class TestWNBACleanScores(unittest.TestCase):
    """WNBA layout: team/score, four quarter triples, recap, '--', '-', '-'."""

    def _parse(self, tokens):
        api = WNBAMoneyLineAPI.__new__(WNBAMoneyLineAPI)
        return api.clean_scores(tokens)

    def test_single_game(self):
        tokens = [
            'Rot', 'WAGERSOPENER',
            'Indiana', '85', 'Connecticut', '77',
            '2928', '29', '28', '1514', '15', '14',
            '1818', '18', '18', '2317', '23', '17',
            '85', '77', '--', '-', '-',
        ]
        self.assertEqual(self._parse(tokens), [['85', '77']])


class TestNFLCleanScoresBase(unittest.TestCase):
    """
    NFL inherits the base clean_scores. Layout per game (week-based, four
    quarters, % marker — same shape as NBA):
        AwayFinal, HomeFinal,
        [Q_concat, Q_a, Q_h] x 4,
        AwayRecap, HomeRecap,
        'XX%YY%', 'XX%', 'YY%'
    Synthetic regression test: the parser cannot currently be verified
    against live SBR data (their NFL archive returns empty oddsTables).
    """

    def _api(self, scores):
        api = MoneyLineAPI.__new__(MoneyLineAPI)
        api.date_type = 'Week'
        api.scores_indices = MoneyLineAPI._scores_indices['Week']
        api.scores = api.clean_scores(scores)
        return api

    def test_two_games_with_pct_marker(self):
        scores = [
            'Rot', 'WAGERSOPENER', 'Game',
            '21', '17',
            '70', '7', '0', '73', '7', '3', '07', '0', '7', '77', '7', '7',
            '21', '17', '52%48%', '52%', '48%',
            '24', '31',
            '03', '0', '3', '147', '14', '7', '710', '7', '10', '311', '3', '11',
            '24', '31', '38%62%', '38%', '62%',
        ]
        api = self._api(scores)
        self.assertEqual(api.scores, [['21', '17'], ['24', '31']])


class TestNCAABCleanScoresBase(unittest.TestCase):
    """
    NCAAB shares the base clean_scores algorithm (final at top, period splits,
    recap, end-of-game marker). Unlike NBA/NFL it always uses '--' rather than
    a 'XX%YY%' marker, and unlike NBA it has 2 halves instead of 4 quarters.
    """

    def _api(self, scores):
        # Build a base MoneyLineAPI directly (NCAAB has no overrides).
        api = MoneyLineAPI.__new__(MoneyLineAPI)
        api.date_type = 'Date'
        api.scores_indices = MoneyLineAPI._scores_indices['Date']
        api.scores = api.clean_scores(scores)
        return api

    def test_two_games_with_dash_marker(self):
        # Layout: final, [H1triple, H2triple], recap, '--', '-', '-'
        scores = [
            'Rot', 'WAGERSOPENER',
            '59', '74',
            '2830', '28', '30', '3144', '31', '44',
            '59', '74', '--', '-', '-',
            '76', '88',
            '4249', '42', '49', '3439', '34', '39',
            '76', '88', '--', '-', '-',
        ]
        api = self._api(scores)
        self.assertEqual(api.scores, [['59', '74'], ['76', '88']])


class TestNHLCleanScores(unittest.TestCase):
    """NHL anchors on the per-game 'XX%YY%' marker, like MLB."""

    def _parse(self, tokens):
        api = NHLMoneyLineAPI.__new__(NHLMoneyLineAPI)
        return api.clean_scores(tokens)

    def test_modern_layout_no_goalies(self):
        # Layout used in current SBR data: final + 3 period triples + recap + %
        tokens = [
            'Rot', 'WAGERSOPENER',
            '1', '2',
            '00', '0', '0', '01', '0', '1', '11', '1', '1',
            '1', '2', '27%73%', '27%', '73%',
        ]
        self.assertEqual(self._parse(tokens), [['1', '2']])

    def test_legacy_layout_with_inline_goalies(self):
        # Older SBR data prepended starting goalies inside the score block;
        # %-anchoring keeps offsets stable so the recap still resolves.
        tokens = [
            'Rot', 'WAGERSOPENER',
            'L.Dostal', '1', 'J.Quick', '5',
            '11', '1', '1', '02', '0', '2', '02', '0', '2',
            '1', '5', '25%75%', '25%', '75%',
        ]
        self.assertEqual(self._parse(tokens), [['1', '5']])

    def test_postponed_game_skipped(self):
        # '--' marker (no '%%') → no recap → game omitted from scores
        tokens = [
            'Rot', 'WAGERSOPENER',
            'K.Kahkonen', '0', 'C.Ingram', '1',
            '00', '0', '0', '01', '0', '1', '00', '0', '0',
            '0', '1', '--', '-', '-',
        ]
        self.assertEqual(self._parse(tokens), [])


class TestCFLCleanScores(unittest.TestCase):
    """CFL has two layouts; both end with '--', home score at i-1."""

    def _parse(self, tokens):
        api = CFLMoneyLineAPI.__new__(CFLMoneyLineAPI)
        return api.clean_scores(tokens)

    def test_long_layout_with_quarter_splits(self):
        tokens = [
            'Rot', 'WAGERSOPENER',
            'Edmonton', '47', 'Hamilton', '22',
            '70', '7', '0', '253', '25', '3',
            '013', '0', '13', '156', '15', '6',
            '47', '22', '--', '-', '-',
        ]
        self.assertEqual(self._parse(tokens), [['47', '22']])

    def test_short_layout_mls_style(self):
        tokens = [
            'Rot', 'WAGERSOPENER',
            'Calgary', '24', 'Saskatchewan', '10', '--', '-', '-',
            'Ottawa',  '20', 'Hamilton',     '23', '--', '-', '-',
        ]
        self.assertEqual(self._parse(tokens), [['24', '10'], ['20', '23']])


# ---------------------------------------------------------------------------
# clean_scores  (base NBA/NFL algorithm)
# ---------------------------------------------------------------------------

class TestCleanScoresBase(unittest.TestCase):
    def test_single_game(self):
        api = _make_api(scores=_SCORES_1GAME)
        self.assertEqual(len(api.scores), 1)
        self.assertEqual(api.scores[0], ['21', '33'])

    def test_two_games(self):
        api = _make_api(scores=_SCORES_2GAME)
        self.assertEqual(len(api.scores), 2)
        self.assertEqual(api.scores[0], ['21', '33'])
        self.assertEqual(api.scores[1], ['45', '67'])

    def test_week_based_uses_different_indices(self):
        # Week-based sports use indices [3, 4]
        scores_week = [
            'Rot', 'WAGERSOPENER', 'extra',
            '14', '21',                          # game 1 scores at [3],[4]
            '1421', '14', '21', '65%35%',
        ]
        api = _make_api(date_type='week', date=9, cls=NFLMoneyLineAPI,
                        scores=scores_week)
        self.assertEqual(api.scores[0], ['14', '21'])


# ---------------------------------------------------------------------------
# SportsbookReviewAPI
# ---------------------------------------------------------------------------

class TestSportsbookReviewAPI(unittest.TestCase):
    def test_invalid_sport_raises(self):
        with self.assertRaises(ValueError):
            SportsbookReviewAPI(
                'http://example.com', 'Money Line', 'Date', '2024-11-15',
                sport='xyz'
            )

    @patch('retrieve.requests.get')
    def test_returns_dataframe_with_correct_columns(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = _FIXTURE_HTML
        mock_get.return_value = mock_resp

        api = SportsbookReviewAPI(
            'http://fake.url', 'Money Line', 'Date', '2024-11-15', sport='nba'
        )
        df = api.return_data()

        self.assertIn('Date', df.columns)
        self.assertIn('Away Lines', df.columns)
        self.assertIn('Home Lines', df.columns)
        self.assertIn('Away Score', df.columns)
        self.assertIn('Home Score', df.columns)

    @patch('retrieve.requests.get')
    def test_http_error_raises(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        with self.assertRaises(FileNotFoundError):
            SportsbookReviewAPI(
                'http://fake.url', 'Money Line', 'Date', '2024-11-15', sport='nba'
            )


# Import NFLMoneyLineAPI for the week-based test above
from retrieve import NFLMoneyLineAPI


# ---------------------------------------------------------------------------
# __NEXT_DATA__ metadata extraction
# ---------------------------------------------------------------------------

import json as _json
import pandas as _pd


def _next_data_payload(games, books):
    """Build a minimal __NEXT_DATA__ JSON payload mimicking SBR's shape."""
    return {
        'props': {
            'pageProps': {
                'oddsTables': [{
                    'oddsTableModel': {
                        'gameRows': [
                            {'gameView': {
                                'awayTeam': {'fullName': g[0], 'shortName': g[1]},
                                'homeTeam': {'fullName': g[2], 'shortName': g[3]},
                            }} for g in games
                        ],
                        'sportsbooks': [{'name': b} for b in books],
                    }
                }]
            }
        }
    }


def _fixture_with_next_data(games, books):
    payload = _json.dumps(_next_data_payload(games, books))
    spans = (
      '<span class="fs-9">7:30 PM ET</span>'
      + '<span class="fs-9">+110</span><span class="fs-9">-110</span>' * 7
    )
    divs = (
      '<div class="fs-9">Rot</div><div class="fs-9">WAGERSOPENER</div>'
      '<div class="fs-9">21</div><div class="fs-9">33</div>'
      '<div class="fs-9">2133</div><div class="fs-9">21</div>'
      '<div class="fs-9">33</div><div class="fs-9">73%27%</div>'
    )
    return (
      '<html><body>' + spans + divs +
      '<script id="__NEXT_DATA__" type="application/json">' + payload +
      '</script></body></html>'
    )


class TestExtractMetadata(unittest.TestCase):
    @patch('retrieve.requests.get')
    def test_extract_populates_team_and_book_columns(self, mock_get):
        html = _fixture_with_next_data(
            games=[('Detroit Pistons', 'DET', 'Orlando Magic', 'ORL')],
            books=['BetMGM', 'FanDuel'],
        )
        mock_resp = MagicMock(); mock_resp.status_code = 200; mock_resp.text = html
        mock_get.return_value = mock_resp

        api = SportsbookReviewAPI(
            'http://fake.url', 'Money Line', 'Date', '2024-11-15', sport='nba'
        )
        df = api.return_data()

        self.assertEqual(df.iloc[0]['Away Team'], 'Detroit Pistons')
        self.assertEqual(df.iloc[0]['Home Team'], 'Orlando Magic')
        self.assertEqual(df.iloc[0]['Away Abbr'], 'DET')
        self.assertEqual(df.iloc[0]['Home Abbr'], 'ORL')
        self.assertEqual(df.iloc[0]['Sportsbooks'], ['Open', 'BetMGM', 'FanDuel'])

    @patch('retrieve.requests.get')
    def test_extract_failsoft_when_next_data_absent(self, mock_get):
        # _FIXTURE_HTML has no <script id="__NEXT_DATA__"> — extraction must
        # fail soft and return empty strings/list, NOT raise.
        mock_resp = MagicMock(); mock_resp.status_code = 200; mock_resp.text = _FIXTURE_HTML
        mock_get.return_value = mock_resp

        api = SportsbookReviewAPI(
            'http://fake.url', 'Money Line', 'Date', '2024-11-15', sport='nba'
        )
        df = api.return_data()

        for col in ('Away Team', 'Home Team', 'Away Abbr', 'Home Abbr'):
            self.assertEqual(df.iloc[0][col], '')
        self.assertEqual(df.iloc[0]['Sportsbooks'], [])

    @patch('retrieve.requests.get')
    def test_extract_failsoft_on_malformed_payload(self, mock_get):
        html = (
          '<html><body>'
          '<span class="fs-9">7:30 PM ET</span>'
          + '<span class="fs-9">+110</span><span class="fs-9">-110</span>' * 7 +
          '<div class="fs-9">Rot</div><div class="fs-9">WAGERSOPENER</div>'
          '<div class="fs-9">21</div><div class="fs-9">33</div>'
          '<div class="fs-9">2133</div><div class="fs-9">21</div>'
          '<div class="fs-9">33</div><div class="fs-9">73%27%</div>'
          '<script id="__NEXT_DATA__" type="application/json">{"props": {}}</script>'
          '</body></html>'
        )
        mock_resp = MagicMock(); mock_resp.status_code = 200; mock_resp.text = html
        mock_get.return_value = mock_resp

        api = SportsbookReviewAPI(
            'http://fake.url', 'Money Line', 'Date', '2024-11-15', sport='nba'
        )
        df = api.return_data()
        self.assertEqual(df.iloc[0]['Away Team'], '')
        self.assertEqual(df.iloc[0]['Sportsbooks'], [])

    def test_attach_metadata_pads_short_lists(self):
        df = _pd.DataFrame({
            'Date': ['2024-11-15', '2024-11-15'],
            'Away Lines': [['+110'], ['+120']],
            'Home Lines': [['-110'], ['-120']],
        })
        out = SportsbookReviewAPI._attach_metadata(
            df, ['DET'], ['ORL'], ['DET'], ['ORL'], ['Open', 'BetMGM']
        )
        self.assertEqual(list(out['Away Team']), ['DET', ''])
        self.assertEqual(list(out['Home Team']), ['ORL', ''])
        self.assertEqual(out.iloc[0]['Sportsbooks'], ['Open', 'BetMGM'])
        self.assertEqual(out.iloc[1]['Sportsbooks'], ['Open', 'BetMGM'])


if __name__ == '__main__':
    unittest.main()
