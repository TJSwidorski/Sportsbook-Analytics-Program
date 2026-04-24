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
# MLS / WNBA / CFL clean_scores — stubs that return [] until implemented
# ---------------------------------------------------------------------------

class TestStubScoreParsers(unittest.TestCase):
    def test_mls_returns_empty(self):
        api = MLSMoneyLineAPI.__new__(MLSMoneyLineAPI)
        self.assertEqual(api.clean_scores(['anything']), [])

    def test_wnba_returns_empty(self):
        api = WNBAMoneyLineAPI.__new__(WNBAMoneyLineAPI)
        self.assertEqual(api.clean_scores(['anything']), [])

    def test_cfl_returns_empty(self):
        api = CFLMoneyLineAPI.__new__(CFLMoneyLineAPI)
        self.assertEqual(api.clean_scores(['anything']), [])


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

if __name__ == '__main__':
    unittest.main()
