from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def display(value: Decimal, places: str = "0.1") -> str:
    """Round a computed value for a sentence a person reads.

    Indicators come out of division at full precision - an RSI printed raw
    runs to twenty-odd decimals - and every gate compares the exact value, so
    the rounding belongs here at the display edge and nowhere earlier.
    """
    return str(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))


def floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        return value
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step
