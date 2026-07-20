from decimal import Decimal

from trading_agent.decimal_utils import floor_to_step, money


def test_money_rounds_half_up_to_two_decimals():
    assert money(Decimal("1.005")) == Decimal("1.01")
    assert money(Decimal("1.004")) == Decimal("1.00")


def test_floor_to_step_rounds_down_to_the_nearest_step():
    assert floor_to_step(Decimal("1.0049"), Decimal("0.001")) == Decimal("1.004")


def test_floor_to_step_passes_through_when_step_is_not_positive():
    assert floor_to_step(Decimal("1.23"), Decimal("0")) == Decimal("1.23")
