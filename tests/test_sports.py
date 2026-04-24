import unittest
import sports


class TestBetTypes(unittest.TestCase):
    """Ported from tests.py — URL generation for BetTypes base class."""

    def setUp(self):
        base_url = 'https://www.sportsbookreview.com/betting-odds/nfl-football/?week=Week'
        self.bet_types = sports.BetTypes(base_url, '10')

    def test_spread_url(self):
        expected = ('https://www.sportsbookreview.com/betting-odds/nfl-football'
                    '/pointspread/full-game/?week=Week10')
        self.assertEqual(self.bet_types.spread, expected)

    def test_money_line_url(self):
        expected = ('https://www.sportsbookreview.com/betting-odds/nfl-football'
                    '/money-line/full-game/?week=Week10')
        self.assertEqual(self.bet_types.money_line, expected)

    def test_totals_url(self):
        expected = ('https://www.sportsbookreview.com/betting-odds/nfl-football'
                    '/totals/full-game/?week=Week10')
        self.assertEqual(self.bet_types.totals, expected)

    def test_quarters_url(self):
        spread, money_line, totals = self.bet_types.quarters(1)
        self.assertEqual(
            spread,
            'https://www.sportsbookreview.com/betting-odds/nfl-football'
            '/pointspread/1st-quarter/?week=Week10',
        )
        self.assertEqual(
            money_line,
            'https://www.sportsbookreview.com/betting-odds/nfl-football'
            '/money-line/1st-quarter/?week=Week10',
        )
        self.assertEqual(
            totals,
            'https://www.sportsbookreview.com/betting-odds/nfl-football'
            '/totals/1st-quarter/?week=Week10',
        )


class TestAllSportsInstantiate(unittest.TestCase):
    """Every sport class must instantiate without errors."""

    def test_nfl(self):
        sports.NFL(9)

    def test_nba(self):
        sports.NBA('2024-11-15')

    def test_nhl(self):
        sports.NHL('2024-11-15')

    def test_mlb(self):
        sports.MLB('2024-05-15')

    def test_mls(self):
        sports.MLS('2024-05-15')

    def test_ncaaf(self):
        sports.NCAAF(5)

    def test_ncaab(self):
        sports.NCAAB('2024-12-01')

    def test_wnba(self):
        sports.WNBA('2024-07-15')

    def test_cfl(self):
        sports.CFL(5)


class TestDateBasedURLFormat(unittest.TestCase):
    """Date-based sports must embed the date in their money-line URL."""

    def _assert_date_in_url(self, url, date):
        self.assertIn(f'?date={date}', url)

    def test_nba_date_in_url(self):
        self._assert_date_in_url(sports.NBA('2024-11-15').money_line, '2024-11-15')

    def test_nhl_date_in_url(self):
        self._assert_date_in_url(sports.NHL('2024-11-15').money_line, '2024-11-15')

    def test_mlb_date_in_url(self):
        self._assert_date_in_url(sports.MLB('2024-05-15').money_line, '2024-05-15')

    def test_mls_date_in_url(self):
        self._assert_date_in_url(sports.MLS('2024-05-15').money_line, '2024-05-15')

    def test_ncaab_date_in_url(self):
        self._assert_date_in_url(sports.NCAAB('2024-12-01').money_line, '2024-12-01')

    def test_wnba_date_in_url(self):
        self._assert_date_in_url(sports.WNBA('2024-07-15').money_line, '2024-07-15')


class TestWeekBasedURLFormat(unittest.TestCase):
    """Week-based sports must embed the week number in their money-line URL."""

    def _assert_week_in_url(self, url, week):
        self.assertIn(f'?week=Week{week}', url)

    def test_nfl_week_in_url(self):
        self._assert_week_in_url(sports.NFL(9).money_line, 9)

    def test_ncaaf_week_in_url(self):
        self._assert_week_in_url(sports.NCAAF(5).money_line, 5)

    def test_cfl_week_in_url(self):
        self._assert_week_in_url(sports.CFL(5).money_line, 5)


class TestNCAAFHalvesBugRegression(unittest.TestCase):
    """
    Regression test for the copy-paste bug where NCAAF.halves() called
    self.links.halves(2) twice, giving h1 == h2.
    """

    def setUp(self):
        self.ncaaf = sports.NCAAF(5)

    def test_h1_money_line_differs_from_h2(self):
        self.assertNotEqual(self.ncaaf.h1_money_line, self.ncaaf.h2_money_line)

    def test_h1_spread_differs_from_h2(self):
        self.assertNotEqual(self.ncaaf.h1_spread, self.ncaaf.h2_spread)

    def test_h1_totals_differs_from_h2(self):
        self.assertNotEqual(self.ncaaf.h1_totals, self.ncaaf.h2_totals)

    def test_h1_contains_1st_half(self):
        self.assertIn('1st-half', self.ncaaf.h1_money_line)

    def test_h2_contains_2nd_half(self):
        self.assertIn('2nd-half', self.ncaaf.h2_money_line)


class TestHalvesURLs(unittest.TestCase):
    """Other sports with halves should also produce distinct h1/h2 URLs."""

    def test_nfl_halves_distinct(self):
        nfl = sports.NFL(9)
        self.assertNotEqual(nfl.h1_money_line, nfl.h2_money_line)

    def test_nba_halves_distinct(self):
        nba = sports.NBA('2024-11-15')
        self.assertNotEqual(nba.h1_money_line, nba.h2_money_line)

    def test_cfl_halves_distinct(self):
        cfl = sports.CFL(5)
        self.assertNotEqual(cfl.h1_money_line, cfl.h2_money_line)


if __name__ == '__main__':
    unittest.main()
