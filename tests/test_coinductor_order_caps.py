"""The per-order cap: read, suggested, warned about, and written.

The cap ships at 10 and was only editable by opening config.toml. A tranche
planned at 66.67 USDT submitted 9.70 and counted itself complete, because the
cap truncates with min() rather than refusing - so the number has to be visible
and adjustable where the user already is.
"""

from decimal import Decimal

from coinductor.order_caps import (
    apply_order_caps_to_config,
    exceeds_suggestion,
    read_order_caps,
    suggested_mainnet_cap,
)

CONFIG = """\
# A comment that must survive.
[testnet_execution]
enabled = false
max_quote_amount_usdt = 10.0
allowed_symbols = ["BTCUSDT"]

[live_confirm]
enabled = false
preview_only = true
max_quote_amount_usdt = 10.0
funding_buffer_usdt = 1.0
quote_asset = "USDC"
"""


def _config(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(CONFIG, encoding="utf-8")
    return path


def test_both_caps_are_read_from_the_config(tmp_path) -> None:
    caps = read_order_caps(_config(tmp_path))

    assert caps["testnet"] == Decimal("10.0")
    assert caps["mainnet"] == Decimal("10.0")


def test_a_missing_config_reads_as_zero_rather_than_raising(tmp_path) -> None:
    """Settings opens before a config exists on a fresh install."""
    caps = read_order_caps(tmp_path / "absent.toml")

    assert caps == {"testnet": Decimal("0"), "mainnet": Decimal("0")}


def test_the_suggestion_scales_with_the_portfolio_but_never_goes_below_ten() -> None:
    assert suggested_mainnet_cap(836) == Decimal("84")
    assert suggested_mainnet_cap(5000) == Decimal("500")
    # A tiny or unknown portfolio keeps the shipped default rather than
    # suggesting something smaller than any order could be.
    assert suggested_mainnet_cap(20) == Decimal("10")
    assert suggested_mainnet_cap(0) == Decimal("10")
    assert suggested_mainnet_cap("not a number") == Decimal("10")


def test_the_suggestion_lets_a_planned_tranche_through() -> None:
    """The case that started this: 400 budget, BTC at 50%, three tranches.

    66.67 per tranche. A suggestion that sat below it would recommend the exact
    silent truncation this whole change exists to stop.
    """
    assert suggested_mainnet_cap(836) >= Decimal("66.67")


def test_only_a_cap_above_the_suggestion_warns() -> None:
    assert exceeds_suggestion(200, 836) is True
    assert exceeds_suggestion(84, 836) is False
    assert exceeds_suggestion(10, 836) is False
    # Nothing to compare against yet: no analysis has run.
    assert exceeds_suggestion(10_000, 0) is False


def test_saving_moves_both_caps_and_leaves_the_rest_of_the_file_alone(tmp_path) -> None:
    path = _config(tmp_path)

    changed = apply_order_caps_to_config(path, 200, 84)

    assert set(changed) == {
        "testnet_execution.max_quote_amount_usdt",
        "live_confirm.max_quote_amount_usdt",
    }
    written = path.read_text(encoding="utf-8")
    assert "# A comment that must survive." in written
    assert 'quote_asset = "USDC"' in written
    assert "funding_buffer_usdt = 1.0" in written
    caps = read_order_caps(path)
    assert caps["testnet"] == Decimal("200")
    assert caps["mainnet"] == Decimal("84")


def test_a_zero_or_negative_cap_is_refused_rather_than_written(tmp_path) -> None:
    """The config validator treats zero as an error.

    Saving one would block every order with nothing on screen to explain it, so
    the value never reaches the file.
    """
    path = _config(tmp_path)

    assert apply_order_caps_to_config(path, 0, -5) == {}
    caps = read_order_caps(path)
    assert caps["testnet"] == Decimal("10.0")
    assert caps["mainnet"] == Decimal("10.0")


def test_one_bad_value_does_not_stop_the_other_being_saved(tmp_path) -> None:
    path = _config(tmp_path)

    changed = apply_order_caps_to_config(path, 0, 84)

    assert list(changed) == ["live_confirm.max_quote_amount_usdt"]
    assert read_order_caps(path)["mainnet"] == Decimal("84")


def test_a_decimal_comma_is_accepted(tmp_path) -> None:
    """A Czech keyboard types 84,5 - and str() of that is not a number."""
    path = _config(tmp_path)

    apply_order_caps_to_config(path, "200", "84,5")

    assert read_order_caps(path)["mainnet"] == Decimal("84.5")
