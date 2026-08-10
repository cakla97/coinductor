"""A starting point for the limits, sized to the portfolio.

Nobody opening these screens knows whether 3% is cautious or reckless, and the
honest answer depends on what they hold. The per-order cap already suggests a
portfolio-derived number and warns rather than refuses; this does the same for
the limits added since.
"""

import shutil
from decimal import Decimal
from pathlib import Path

import pytest

from coinductor.suggested_limits import money_for_percent, suggested_limits

TEMPLATE = Path(__file__).resolve().parents[1] / "config.example.toml"


def test_percentages_do_not_move_with_the_portfolio() -> None:
    """That is the whole point of expressing them as percentages."""
    small = suggested_limits("500")
    large = suggested_limits("500000")

    for field in ("tradePct", "positionPct", "capitalPct", "riskPct", "runPct", "dayPct"):
        assert small[field] == large[field]


def test_the_flat_backstops_scale_with_the_portfolio() -> None:
    small = suggested_limits("1000")
    large = suggested_limits("100000")

    for field in ("tradeAmount", "runAmount", "dayAmount"):
        assert Decimal(large[field]) > Decimal(small[field])


def test_a_backstop_sits_above_where_the_percentage_binds() -> None:
    """Otherwise the flat number decides and the percentage is decoration."""
    suggested = suggested_limits("10000")
    trade_pct_amount = Decimal("10000") * Decimal(suggested["tradePct"]) / 100

    assert Decimal(suggested["tradeAmount"]) > trade_pct_amount


def test_a_tiny_portfolio_still_suggests_something_usable() -> None:
    """A percentage of very little is below anything an exchange accepts."""
    assert Decimal(suggested_limits("50")["tradeAmount"]) >= Decimal("25")


def test_no_portfolio_falls_back_to_the_floor(tmp_path) -> None:
    suggested = suggested_limits("0")

    assert Decimal(suggested["tradeAmount"]) == Decimal("25")
    assert suggested["tradePct"] == "3"


def test_backstops_are_whole_units() -> None:
    """A suggestion of 83.61 implies a precision nobody has."""
    for value in suggested_limits("8361").values():
        assert "." not in value or Decimal(value) < 1


def test_a_reserve_is_not_guessed_from_the_portfolio() -> None:
    """Leaving nothing back is as reasonable as leaving a lot; neither follows."""
    assert suggested_limits("100000")["reserve"] == "0"


def test_money_for_percent_is_what_the_share_is_worth() -> None:
    assert money_for_percent("859.62", "3") == "25.79"


def test_money_for_percent_says_nothing_without_a_portfolio() -> None:
    """A screen opened before the first run must not read "0.00 USDC"."""
    assert money_for_percent("0", "3") == ""


def test_nonsense_does_not_raise() -> None:
    assert money_for_percent("abc", "3") == ""
    assert suggested_limits(None)["tradePct"] == "3"


# ---------------------------------------------------------------------------
# On the screens.
# ---------------------------------------------------------------------------

pytest.importorskip("PySide6")

from coinductor.controller import AppController  # noqa: E402


@pytest.fixture
def controller(monkeypatch, tmp_path) -> "AppController":
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])
    shutil.copy(TEMPLATE, tmp_path / "config.toml")
    monkeypatch.chdir(tmp_path)
    return AppController()


def test_both_panels_offer_a_suggestion(controller) -> None:
    assert controller.tradeSizing["tradePctSuggested"] == "3"
    assert controller.earnFunding["runPctSuggested"] == "2"


def test_a_fresh_install_says_to_run_an_analysis_first(controller) -> None:
    """No portfolio yet, so there is nothing to derive a suggestion from."""
    controller.setWizardLanguage("cs")

    assert controller.tradeSizing["hasPortfolio"] is False
    assert "spusťte analýzu" in controller.tradeSizing["suggestionHint"]


def test_applying_the_suggestion_writes_it(controller, monkeypatch) -> None:
    monkeypatch.setattr(controller, "_portfolio_value_amount", lambda: Decimal("10000"))

    controller.applySuggestedSizing()

    assert controller.tradeSizing["tradePct"] == "3"
    assert controller.tradeSizing["tradeAmount"] == "900"


def test_applying_the_funding_suggestion_writes_it(controller, monkeypatch) -> None:
    monkeypatch.setattr(controller, "_portfolio_value_amount", lambda: Decimal("10000"))

    controller.applySuggestedFunding()

    assert controller.earnFunding["runPct"] == "2"
    assert controller.earnFunding["dayPct"] == "5"


def test_the_money_a_percentage_is_worth_is_shown(controller, monkeypatch) -> None:
    monkeypatch.setattr(controller, "_portfolio_value_amount", lambda: Decimal("2000"))

    assert controller.tradeSizing["tradePctMoney"] == "60.00"
    assert controller.earnFunding["runPctMoney"] == "40.00"


def test_the_suggestion_follows_the_language(controller, monkeypatch) -> None:
    monkeypatch.setattr(controller, "_portfolio_value_amount", lambda: Decimal("2000"))

    controller.setWizardLanguage("en")
    assert "cautious starting point" in controller.tradeSizing["suggestionHint"]

    controller.setWizardLanguage("cs")
    assert "opatrný začátek" in controller.tradeSizing["suggestionHint"]


def test_the_buttons_are_on_both_panels() -> None:
    qml = (Path(__file__).parents[1] / "coinductor" / "qml" / "Main.qml").read_text(encoding="utf-8")

    assert "appController.applySuggestedSizing()" in qml
    assert "appController.applySuggestedFunding()" in qml
    # Disabled without a portfolio, or it writes the floor over a real setting.
    assert "enabled: appController.tradeSizing.hasPortfolio" in qml
    assert "enabled: appController.earnFunding.hasPortfolio" in qml
