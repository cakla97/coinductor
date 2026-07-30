"""The manual-setup procedure is the one thing the assistant cannot do for you.

Binance has no public API for creating bots, so these steps are what the user
actually carries out by hand - which makes a silently untranslated or
misspelled step worse here than anywhere else in the app.
"""

from decimal import Decimal

import pytest

from trading_agent.grid_advisor import GridBotAdvisor
from trading_agent.messages import (
    MANUAL_STEP_TEXT,
    ManualStep,
    manual_steps_from_json,
    manual_steps_to_json,
    render_manual_step,
    render_manual_steps,
)
from trading_agent.models import ActiveStrategiesReport, Balance

from test_grid_advisor import _config, _research, _research_report, _risk_state, _snapshot
from test_rebalancing_bot_advisor import _asset, _config as _rebalance_config, _portfolio

LANGUAGES = ("en", "cs")


def _grid(blocked: bool):
    args = (
        [_snapshot("BTCUSDC"), _snapshot("ETHUSDC", regime="RISK_ON")],
        _research_report((_research("BTCUSDC"), _research("ETHUSDC", "9"))),
        ActiveStrategiesReport(True, (), "none"),
    )
    config = _config()
    if not blocked:
        # The shipped defaults cannot fund a grid Binance would accept, so with
        # them every case lands in the blocked branch and the twelve-step
        # procedure below stops being exercised at all.
        config["grid_bot"]["default_investment_usdt"] = 120
        config["grid_bot"]["max_grid_capital_usdt"] = 200
    portfolio = Decimal("800") if blocked else Decimal("4000")
    recommendation = GridBotAdvisor(config).recommend(*args, _risk_state(blocked=blocked), portfolio)
    assert recommendation.deployment_allowed is not blocked, "fixture no longer covers this branch"
    return recommendation


def _rebalancing(blocked: bool):
    from trading_agent.rebalancing_bot_advisor import RebalancingBotAdvisor

    if blocked:
        portfolio = _portfolio(
            _asset("BTC", "CORE", "214", "26.5"),
            _asset("SOL", "CAPITAL_SOURCE", "96", "11.9"),
            _asset("USDC", "STABLE", "12", "1.5"),
        )
        balances = [Balance("USDC", Decimal("0"), flexible_amount=Decimal("12"))]
    else:
        portfolio = _portfolio(
            _asset("BTC", "CORE", "300", "50"),
            _asset("ETH", "CORE", "150", "25"),
            _asset("SOL", "CAPITAL_SOURCE", "75", "12.5"),
        )
        balances = [Balance("USDC", Decimal("200"))]
    return RebalancingBotAdvisor(_rebalance_config()).recommend(portfolio, balances)


def _every_emitted_step() -> list[ManualStep]:
    steps: list[ManualStep] = []
    for blocked in (True, False):
        steps.extend(_grid(blocked).manual_step_specs)
        steps.extend(_rebalancing(blocked).manual_step_specs)
    return steps


def test_every_emitted_key_exists_in_the_text_table() -> None:
    """A typo renders the raw identifier at the user, not a sentence.

    render_manual_step falls back to the key rather than crashing, which is the
    right behaviour at runtime and exactly why nothing else would catch this.
    """
    unknown = sorted({step.key for step in _every_emitted_step()} - set(MANUAL_STEP_TEXT))
    assert unknown == [], f"advisors emit keys with no text: {unknown}"


def test_every_template_is_translated_into_every_language() -> None:
    missing = [
        f"{key}/{language}"
        for key, translations in MANUAL_STEP_TEXT.items()
        for language in LANGUAGES
        if not translations.get(language, "").strip()
    ]
    assert missing == [], f"untranslated manual steps: {missing}"


def test_czech_text_is_actually_translated_not_copied() -> None:
    """A copied English string passes a presence check and fails the user.

    Except where the whole message is an indicator name and its number, which
    is written the same way in both languages.
    """
    # Pure placeholders and indicator names, with no words of their own.
    identical_by_design = {"grid_reason_rsi", "trade_observed_symbol"}
    copied = [
        key
        for key, translations in MANUAL_STEP_TEXT.items()
        if translations["cs"].strip() == translations["en"].strip()
        and key not in identical_by_design
    ]
    assert copied == [], f"Czech is identical to English for: {copied}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_emitted_step_renders_without_leftover_placeholders(language: str) -> None:
    """A parameter the template asks for but the call site never passes.

    Rendering falls back to the unfilled sentence, so the user would be told to
    "set lower price {low}".
    """
    for step in _every_emitted_step():
        rendered = render_manual_step(step, language)
        assert "{" not in rendered and "}" not in rendered, f"{step.key} in {language}: {rendered}"
        assert rendered != step.key, f"{step.key} rendered as its own identifier in {language}"


def test_czech_steps_differ_from_english_end_to_end() -> None:
    recommendation = _rebalancing(blocked=True)
    steps = recommendation.manual_step_specs
    english = render_manual_steps(steps, "en")
    czech = render_manual_steps(steps, "cs")

    assert len(czech) == len(english)
    assert all(a != b for a, b in zip(english, czech)), "some steps came back in English"
    # The numbers the user has to type must survive translation untouched.
    amount = str(recommendation.funding_plan.items[0].value_usdt)
    assert any(amount in step for step in czech), f"the {amount} conversion vanished from the Czech text"
    # Binance's own control labels stay verbatim: translating "By Ratio" would
    # send someone hunting for a setting that does not exist in their client.
    assert any("By Ratio" in step for step in czech)
    assert any("Auto Rebalance" in step for step in czech)


def test_unknown_language_falls_back_to_english() -> None:
    step = ManualStep("grid_open_menu")
    assert render_manual_step(step, "pt-BR") == MANUAL_STEP_TEXT["grid_open_menu"]["en"]


def test_steps_survive_a_round_trip_through_storage() -> None:
    original = _rebalancing(blocked=True).manual_step_specs

    restored = manual_steps_from_json(manual_steps_to_json(original))

    assert restored == original
    assert render_manual_steps(restored, "cs") == render_manual_steps(original, "cs")


def test_rows_written_before_this_format_still_render() -> None:
    """0.1.3 stored newline-separated English prose in the same column.

    Those rows carry no key to translate, so they must come back verbatim
    rather than disappearing from the dialog after an upgrade.
    """
    legacy = "Open Binance Home > Trading Bots > Spot Grid.\nSelect BTCUSDC and choose Manual parameters."

    steps = manual_steps_from_json(legacy)

    assert render_manual_steps(steps, "cs") == (
        "Open Binance Home > Trading Bots > Spot Grid.",
        "Select BTCUSDC and choose Manual parameters.",
    )


def test_empty_and_malformed_payloads_are_survivable() -> None:
    assert manual_steps_from_json("") == ()
    assert manual_steps_from_json("   ") == ()
    assert manual_steps_from_json('{"not": "a list"}') == ()
    assert manual_steps_from_json('[{"params": {}}]') == (), "a step with no key is unrenderable"


def test_symbol_is_written_as_a_pair() -> None:
    """The API says ETHUSDC; the Binance screen the reader is matching says ETH/USDC."""
    steps = {step.key: step.params for step in _grid(blocked=False).manual_step_specs}

    assert steps["grid_select_symbol"]["symbol"] == "BTC/USDC"
    assert "/" in render_manual_step(
        ManualStep("grid_select_symbol", steps["grid_select_symbol"]), "cs"
    )


def test_registration_step_points_at_the_dialog_not_a_toml_file() -> None:
    """It told a desktop user to copy a TOML file and fill in values by hand.

    The app has had a registration dialog since active-strategy monitoring was
    added; the step was simply never updated to point at it.
    """
    for language in LANGUAGES:
        text = render_manual_step(ManualStep("grid_register_locally"), language)
        assert ".toml" not in text, f"{language} still sends the reader to a file"
        assert "Coinductor" in text or "Aktivní strategie" in text
