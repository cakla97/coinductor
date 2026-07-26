"""The submit gates must fail closed however the flags arrive."""

from dataclasses import replace

from trading_agent.runtime_flags import RuntimeFlags


def test_a_config_without_runtime_flags_grants_no_authority() -> None:
    flags = RuntimeFlags.from_config({})

    assert flags.live_submit is False
    assert flags.earn_redeem_submit is False
    assert flags.oco_protection_submit is False
    assert flags.mainnet_confirm == ""
    assert flags.mainnet_oco_confirm == ""
    assert flags.earn_redeem_confirm == ""
    assert flags.testnet_confirm == ""


def test_a_misspelled_key_does_not_authorise_a_submit() -> None:
    flags = RuntimeFlags.from_config({"_runtime": {"live_submitt": True, "manet_confirm": "CONFIRM_MAINNET_ORDER"}})

    assert flags.live_submit is False
    assert flags.mainnet_confirm == ""


def test_a_malformed_runtime_section_is_ignored_rather_than_trusted() -> None:
    for broken in ("live_submit", ["live_submit"], 1, None):
        flags = RuntimeFlags.from_config({"_runtime": broken})

        assert flags == RuntimeFlags()


def test_flags_survive_a_round_trip_through_the_config_mapping() -> None:
    original = RuntimeFlags(
        live_submit=True,
        mainnet_confirm="CONFIRM_MAINNET_ORDER",
        earn_redeem_submit=True,
        earn_redeem_confirm="CONFIRM_EARN_REDEEM",
        oco_protection_submit=True,
        mainnet_oco_confirm="CONFIRM_MAINNET_OCO",
        testnet_confirm="CONFIRM_TESTNET_ORDER",
        manual_override_symbol="ETHUSDC",
    )
    config: dict = {}

    original.store_in(config)

    assert RuntimeFlags.from_config(config) == original


def test_narrowing_one_gate_leaves_the_others_untouched() -> None:
    """first_portfolio_executor rewrites only the live buy gate per tranche."""
    config: dict = {}
    RuntimeFlags(oco_protection_submit=True, mainnet_oco_confirm="CONFIRM_MAINNET_OCO").store_in(config)

    replace(RuntimeFlags.from_config(config), live_submit=True, mainnet_confirm="CONFIRM_MAINNET_ORDER").store_in(config)

    flags = RuntimeFlags.from_config(config)
    assert flags.live_submit is True
    assert flags.oco_protection_submit is True
    assert flags.mainnet_oco_confirm == "CONFIRM_MAINNET_OCO"


def test_flags_are_immutable_so_a_run_cannot_widen_its_own_authority() -> None:
    flags = RuntimeFlags()

    try:
        flags.live_submit = True  # type: ignore[misc]
    except AttributeError:
        return
    raise AssertionError("RuntimeFlags must be frozen")
