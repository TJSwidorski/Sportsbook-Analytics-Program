"""Tests for betmath — odds conversion, EV, Kelly, line filtering."""

import unittest

from betmath import (
    best_line_for_side,
    decimal_odds,
    ev_per_unit,
    is_valid_line,
    kelly_fraction,
    settle_pick,
)


class TestIsValidLine(unittest.TestCase):
    def test_accepts_normal_lines(self):
        self.assertTrue(is_valid_line('+150'))
        self.assertTrue(is_valid_line('-200'))
        self.assertTrue(is_valid_line('+1000'))
        self.assertTrue(is_valid_line('-1000'))

    def test_rejects_outliers(self):
        self.assertFalse(is_valid_line('-10000'))
        self.assertFalse(is_valid_line('+5000'))

    def test_rejects_malformed(self):
        self.assertFalse(is_valid_line(''))
        self.assertFalse(is_valid_line('150'))      # missing sign
        self.assertFalse(is_valid_line('+abc'))
        self.assertFalse(is_valid_line('+0'))       # no zero lines
        self.assertFalse(is_valid_line(None))       # type: ignore[arg-type]

    def test_custom_max_abs(self):
        self.assertTrue(is_valid_line('-5000', max_abs=10000))


class TestDecimalOdds(unittest.TestCase):
    def test_underdog(self):
        self.assertAlmostEqual(decimal_odds('+150'), 2.5)

    def test_favorite(self):
        self.assertAlmostEqual(decimal_odds('-200'), 1.5)

    def test_pickem(self):
        self.assertAlmostEqual(decimal_odds('+100'), 2.0)
        self.assertAlmostEqual(decimal_odds('-100'), 2.0)

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            decimal_odds('garbage')


class TestEv(unittest.TestCase):
    def test_break_even_at_implied_prob(self):
        # +100 → decimal 2.0 → break-even at p = 0.5
        self.assertAlmostEqual(ev_per_unit(0.5, '+100'), 0.0)

    def test_positive_ev_when_p_exceeds_implied(self):
        # -200 → implied 2/3. With p = 0.75 we have edge.
        self.assertGreater(ev_per_unit(0.75, '-200'), 0)

    def test_negative_ev_below_implied(self):
        self.assertLess(ev_per_unit(0.4, '-200'), 0)


class TestKellyFraction(unittest.TestCase):
    def test_zero_when_negative_ev(self):
        self.assertEqual(kelly_fraction(0.4, '-200'), 0.0)

    def test_capped(self):
        # Massively +EV bet → full Kelly would be huge; capped at 0.05.
        self.assertEqual(kelly_fraction(0.95, '+200', cap=0.05), 0.05)

    def test_fractional_scaling(self):
        # At exactly break-even, full Kelly == 0 → fractional == 0.
        self.assertEqual(kelly_fraction(0.5, '+100', fraction=0.25), 0.0)

    def test_partial_edge_below_cap(self):
        # +100 at p=0.6 → full Kelly = (0.6*1 - 0.4)/1 = 0.2.
        # 0.25 fraction → 0.05. With default cap 0.05, lands exactly at cap.
        self.assertAlmostEqual(kelly_fraction(0.6, '+100'), 0.05)


class TestBestLineForSide(unittest.TestCase):
    def test_skips_first(self):
        # Open is best on paper but we skip index 0 by convention.
        lines = ['+200', '+150', '+140']
        self.assertEqual(best_line_for_side(lines), '+150')

    def test_picks_underdog_when_higher(self):
        # Among -110 / -105 / -120, -105 is most favorable.
        lines = ['-110', '-110', '-105', '-120']
        self.assertEqual(best_line_for_side(lines), '-105')

    def test_skips_outliers(self):
        # -10000 is filtered; -150 wins among remaining.
        lines = ['-110', '-10000', '-150', '-200']
        self.assertEqual(best_line_for_side(lines), '-150')

    def test_returns_none_when_all_invalid(self):
        self.assertIsNone(best_line_for_side(['+10000', '-10000']))

    def test_returns_none_on_empty(self):
        self.assertIsNone(best_line_for_side([]))
        self.assertIsNone(best_line_for_side(['+150']))  # only opener


class TestSettlePick(unittest.TestCase):
    """Settlement at Pick.bet_line — the line the EV rule chose."""

    def test_correct_underdog_pays_per_line(self):
        flat, kelly, result = settle_pick('Home', 'Home', '+200', unit_size=0.03)
        self.assertEqual(flat, 2.0)
        self.assertAlmostEqual(kelly, 0.06)
        self.assertEqual(result, 'W')

    def test_correct_favorite_pays_proportionally(self):
        flat, kelly, result = settle_pick('Away', 'Away', '-200', unit_size=0.04)
        self.assertAlmostEqual(flat, 0.5)
        self.assertAlmostEqual(kelly, 0.02)
        self.assertEqual(result, 'W')

    def test_wrong_pick_loses_one_flat_unit(self):
        flat, kelly, result = settle_pick('Home', 'Away', '+200', unit_size=0.03)
        self.assertEqual(flat, -1.0)
        self.assertAlmostEqual(kelly, -0.03)
        self.assertEqual(result, 'L')

    def test_no_pick_returns_zero(self):
        self.assertEqual(settle_pick('No Pick', 'Away', None), (0.0, 0.0, 'NP'))

    def test_tie_pushes(self):
        self.assertEqual(settle_pick('Home', 'Tie', '+200', 0.03), (0.0, 0.0, 'Push'))

    def test_missing_bet_line_returns_zero(self):
        self.assertEqual(settle_pick('Home', 'Home', None), (0.0, 0.0, 'NP'))

    def test_default_unit_size_yields_zero_kelly(self):
        flat, kelly, _ = settle_pick('Home', 'Home', '+150')
        self.assertEqual(flat, 1.5)
        self.assertEqual(kelly, 0.0)


if __name__ == '__main__':
    unittest.main()
