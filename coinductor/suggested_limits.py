"""A starting point for the sizing and funding limits, sized to the portfolio.

Nobody opening these screens for the first time knows whether 3% is cautious
or reckless, and the honest answer is that it depends on what they hold. The
existing per-order cap already solves this by suggesting a number derived from
the portfolio and warning, never refusing, when the user goes above it. This
does the same for the limits added since.

Two rules shape every number here.

Percentages do not depend on the portfolio - that is the whole point of
expressing them as percentages - so their suggestions are constants, chosen to
be unremarkable rather than clever. What each one *means in money* does depend
on the portfolio, and that is worth showing, because "3%" and "26 USDC" land
very differently.

The flat amounts are backstops for the far end, so they are suggested well
above where the percentage would bind. A flat number small enough to bind on
an ordinary portfolio is exactly how these settings stopped reacting to
portfolio size in the first place.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# Conservative, and deliberately round. These are a place to start an argument
# from, not an optimum: a suggestion of 2.7% would imply a precision nobody has.
SUGGESTED_PERCENTAGES: dict[str, str] = {
    "tradePct": "3",
    "positionPct": "10",
    "capitalPct": "20",
    "riskPct": "0.25",
    "runPct": "2",
    "dayPct": "5",
}

# How far above the percentage a flat backstop is suggested. Three times, so
# the percentage decides across the ordinary range and the flat amount is left
# doing the job it is for - bounding the far end.
_BACKSTOP_MULTIPLE = Decimal("3")

# Below this a percentage of the portfolio is smaller than anything an
# exchange will accept, and a suggestion of "1 USDC" helps nobody.
_FLOOR = Decimal("25")

_BACKSTOPS: tuple[tuple[str, str], ...] = (
    ("tradeAmount", "tradePct"),
    ("runAmount", "runPct"),
    ("dayAmount", "dayPct"),
)


def suggested_limits(portfolio_value: object) -> dict[str, str]:
    """Every suggestion, keyed by the screen name the panels already use."""
    value = _decimal(portfolio_value)
    suggestions = dict(SUGGESTED_PERCENTAGES)
    for flat, percent in _BACKSTOPS:
        suggestions[flat] = _whole(
            max(_FLOOR, _share(value, SUGGESTED_PERCENTAGES[percent]) * _BACKSTOP_MULTIPLE)
        )
    # A reserve is a preference with no defensible default: leaving nothing
    # behind is as reasonable as leaving a month of expenses, and neither
    # follows from the portfolio.
    suggestions["reserve"] = "0"
    return suggestions


def money_for_percent(portfolio_value: object, percent: object) -> str:
    """What a percentage is worth right now, for showing beside the field.

    Empty when there is no portfolio to take a share of, so a screen opened
    before the first run says nothing rather than "0.00 USDC".
    """
    value = _decimal(portfolio_value)
    if value <= 0:
        return ""
    return _two_places(_share(value, percent))


def _share(portfolio_value: Decimal, percent: object) -> Decimal:
    return portfolio_value * _decimal(percent) / Decimal("100")


def _decimal(value: object) -> Decimal:
    try:
        return Decimal(str(value if value is not None else "0").strip().replace(",", "."))
    except (InvalidOperation, ValueError, AttributeError):
        return Decimal("0")


def _whole(value: Decimal) -> str:
    """Whole units: a backstop is a judgement call, and 83.61 reads as if it
    had been calculated to the cent from something meaningful."""
    return format(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP), "f")


def _two_places(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")
