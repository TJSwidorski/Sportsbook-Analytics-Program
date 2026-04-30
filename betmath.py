"""
Bet math primitives — decimal odds, expected value, fractional Kelly,
outlier filtering, and best-line selection. Pure functions; no I/O.

American moneyline conventions throughout:
  - '+150' means a $100 bet wins $150 (decimal 2.50, implied prob 0.40).
  - '-200' means a $200 bet wins $100 (decimal 1.50, implied prob 0.6667).
"""

from __future__ import annotations

from typing import Iterable


# ---------------------------------------------------------------------------
# Line parsing + filtering
# ---------------------------------------------------------------------------

def _parse_line(line: str) -> int | None:
    """Return signed integer for a moneyline string, or None if unparseable."""
    if not line or len(line) < 2 or line[0] not in ('+', '-'):
        return None
    body = line[1:]
    if not body.isdigit():
        return None
    n = int(body)
    if n == 0:
        return None
    return n if line[0] == '+' else -n


def is_valid_line(line: str, max_abs: int = 1000) -> bool:
    """
    True if `line` is a parseable American moneyline within ±max_abs.

    Lines like '-10000' are technically valid odds but represent so much vig
    or a stale opener that they pollute training and skew best-line lookups.
    Treat anything past `max_abs` as missing data.
    """
    n = _parse_line(line)
    if n is None:
        return False
    return abs(n) <= max_abs


# ---------------------------------------------------------------------------
# Odds conversions
# ---------------------------------------------------------------------------

def decimal_odds(line: str) -> float:
    """
    Convert an American moneyline to decimal odds (total return per $1 stake
    including the stake itself). Raises ValueError for malformed input.
    """
    n = _parse_line(line)
    if n is None:
        raise ValueError(f'Invalid moneyline: {line!r}')
    if n > 0:
        return 1.0 + n / 100.0
    return 1.0 + 100.0 / abs(n)


# ---------------------------------------------------------------------------
# Expected value + Kelly sizing
# ---------------------------------------------------------------------------

def ev_per_unit(prob: float, line: str) -> float:
    """
    Expected value per $1 staked at `line` when the true win probability is
    `prob`. Positive means +EV, zero means break-even (perfectly priced),
    negative means -EV.

    Formula: EV = p * (decimal - 1) - (1 - p)
    """
    d = decimal_odds(line)
    return prob * (d - 1.0) - (1.0 - prob)


def kelly_fraction(
    prob: float,
    line: str,
    fraction: float = 0.25,
    cap: float = 0.05,
) -> float:
    """
    Fractional-Kelly bet size as a share of bankroll.

    Full Kelly: f* = (p * b - q) / b   where b = decimal - 1, q = 1 - p
    Returned value is `fraction * f*`, clipped to [0, cap]. Returns 0 when
    the bet is -EV (full Kelly would short the bet, which we don't do).

    Defaults are conservative: 25% Kelly capped at 5% of bankroll. A wrong
    probability estimate at 0.25× compounds losses ~16× more slowly than
    full Kelly, which is what you want when `prob` is itself uncertain.
    """
    d = decimal_odds(line)
    b = d - 1.0
    if b <= 0:
        return 0.0
    q = 1.0 - prob
    full = (prob * b - q) / b
    if full <= 0:
        return 0.0
    return min(full * fraction, cap)


# ---------------------------------------------------------------------------
# Best-line lookup
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pick settlement
# ---------------------------------------------------------------------------

def settle_pick(
    pick: str,
    actual: str,
    bet_line: str | None,
    unit_size: float = 0.0,
) -> tuple[float, float, str]:
    """
    Settle a single pick once the actual game result is known.

    Returns (flat_units, kelly_units, result):
      - flat_units: units won/lost staking 1u flat at `bet_line`
      - kelly_units: flat_units * unit_size (fractional Kelly stake of bankroll)
      - result: 'W' (correct) | 'L' (wrong) | 'NP' (no pick) | 'Push' (tie/void)

    Settles at `bet_line` (the best non-Open line you'd actually take). Settling
    at the opener systematically underprices the favorable lines we never would
    have bet at. `unit_size` is `Pick.unit_size` (a fraction of bankroll, capped
    at 0.05); pass 0 if you only want flat-units accounting.
    """
    if pick == 'No Pick':
        return 0.0, 0.0, 'NP'
    if actual == 'Tie':
        return 0.0, 0.0, 'Push'
    if not bet_line:
        return 0.0, 0.0, 'NP'
    if pick != actual:
        return -1.0, -1.0 * unit_size, 'L'
    n = _parse_line(bet_line)
    if n is None:
        return 0.0, 0.0, 'NP'
    flat = n / 100.0 if n > 0 else 100.0 / abs(n)
    return flat, flat * unit_size, 'W'


# ---------------------------------------------------------------------------
# Best-line lookup
# ---------------------------------------------------------------------------

def best_line_for_side(lines: Iterable[str], skip_first: bool = True) -> str | None:
    """
    Return the most favorable (highest decimal odds) valid line for a bettor
    on this side. By default skips the first entry — by convention index 0
    is the 'Open' column from SBR which is informational, not bettable.

    Returns None if no entry parses or every entry is an outlier.
    """
    items = list(lines)
    if skip_first:
        items = items[1:]
    best_line: str | None = None
    best_decimal: float = -1.0
    for line in items:
        if not is_valid_line(line):
            continue
        try:
            d = decimal_odds(line)
        except ValueError:
            continue
        if d > best_decimal:
            best_decimal = d
            best_line = line
    return best_line
