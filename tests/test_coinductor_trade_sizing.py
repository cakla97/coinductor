"""Order sizing, read and written from the app instead of from config.toml.

Three of these settings had no home at all: nothing wrote them, and until
sizing started reading them, nothing read them either. They were visible only
in a file this app tells people they never have to open.
"""

import shutil
from decimal import Decimal
from pathlib import Path

import pytest

from coinductor.trade_sizing import (
    apply_sizing_to_config,
    ensure_keys,
    read_sizing,
    valid_sizing,
)

TEMPLATE = Path(__file__).resolve().parents[1] / "config.example.toml"


@pytest.fixture
def config(tmp_path) -> Path:
    path = tmp_path / "config.toml"
    shutil.copy(TEMPLATE, path)
    return path


def _values(**overrides) -> dict[str, str]:
    values = {
        "tradePct": "3",
        "tradeAmount": "250",
        "positionPct": "10",
        "capitalPct": "20",
        "riskPct": "0.25",
    }
    values.update(overrides)
    return values


def test_the_shipped_template_reads_back(config: Path) -> None:
    values = read_sizing(config)

    assert values["tradePct"] == "3"
    assert values["tradeAmount"] == "250"
    assert values["positionPct"] == "10"
    assert values["capitalPct"] == "20"
    assert values["riskPct"] == "0.25"


def test_saving_writes_every_section_it_touches(config: Path) -> None:
    """Two sections, one save: [strategy] and [risk] both move."""
    changed = apply_sizing_to_config(config, _values(tradePct="5", riskPct="0.5"))

    assert "strategy.max_trade_pct_of_portfolio" in changed
    assert "risk.max_risk_per_trade_pct" in changed
    assert read_sizing(config)["tradePct"] == "5"
    assert read_sizing(config)["riskPct"] == "0.5"


def test_saving_the_same_values_twice_changes_nothing(config: Path) -> None:
    """Kept apart from "invalid", which is a different message to the user."""
    apply_sizing_to_config(config, _values())

    assert apply_sizing_to_config(config, _values()) == {}


def test_a_config_predating_the_percentage_gains_the_key(tmp_path) -> None:
    """`_apply` only edits keys that exist, so a new one must be created first.

    Without this the setting is accepted, reported as saved, and silently
    discarded - the trap the [automation] section already had to be taught.
    """
    path = tmp_path / "config.toml"
    text = TEMPLATE.read_text(encoding="utf-8").replace(
        "max_trade_pct_of_portfolio = 3.0\n", ""
    )
    path.write_text(text, encoding="utf-8")
    assert "max_trade_pct_of_portfolio" not in path.read_text(encoding="utf-8")

    assert ensure_keys(path) is True
    apply_sizing_to_config(path, _values(tradePct="7"))

    assert read_sizing(path)["tradePct"] == "7"


def test_the_added_key_lands_inside_its_own_section(tmp_path) -> None:
    """A key appended after the wrong header belongs to the wrong table."""
    path = tmp_path / "config.toml"
    text = TEMPLATE.read_text(encoding="utf-8").replace(
        "max_trade_pct_of_portfolio = 3.0\n", ""
    )
    path.write_text(text, encoding="utf-8")

    ensure_keys(path)

    from trading_agent.config import load_config

    assert "max_trade_pct_of_portfolio" in load_config(str(path)).raw["strategy"]


@pytest.mark.parametrize("field", ["tradePct", "tradeAmount", "positionPct", "capitalPct", "riskPct"])
def test_zero_is_refused_rather_than_written(config: Path, field: str) -> None:
    """The validator treats a non-positive value as an error, and a saved zero
    would size every order to nothing with no visible cause."""
    assert valid_sizing(_values(**{field: "0"})) is False
    assert apply_sizing_to_config(config, _values(**{field: "0"})) == {}


@pytest.mark.parametrize("field", ["tradePct", "positionPct", "capitalPct", "riskPct"])
def test_a_percentage_above_one_hundred_is_a_typo(config: Path, field: str) -> None:
    assert valid_sizing(_values(**{field: "150"})) is False


def test_the_flat_amount_may_exceed_one_hundred(config: Path) -> None:
    """It is money, not a percentage - 250 USDC is the shipped default."""
    assert valid_sizing(_values(tradeAmount="5000")) is True


def test_a_comma_decimal_is_accepted(config: Path) -> None:
    """A Czech keyboard produces 0,5 and the user meant 0.5."""
    assert valid_sizing(_values(riskPct="0,5")) is True

    apply_sizing_to_config(config, _values(riskPct="0,5"))

    assert read_sizing(config)["riskPct"] == "0.5"


def test_nonsense_reads_as_zero_and_is_refused(config: Path) -> None:
    assert valid_sizing(_values(tradePct="abc")) is False


def test_a_missing_config_writes_nothing(tmp_path) -> None:
    assert apply_sizing_to_config(tmp_path / "absent.toml", _values()) == {}


# ---------------------------------------------------------------------------
# The controller and the screen. Skipped without the desktop extra, like the
# rest of the Qt suite.
# ---------------------------------------------------------------------------

pytest.importorskip("PySide6")

from coinductor.controller import AppController  # noqa: E402
from coinductor.models import DesktopRunResult  # noqa: E402


@pytest.fixture
def controller(monkeypatch, tmp_path) -> "AppController":
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])
    shutil.copy(TEMPLATE, tmp_path / "config.toml")
    monkeypatch.chdir(tmp_path)
    return AppController()


def test_the_screen_reads_what_the_config_holds(controller) -> None:
    assert controller.tradeSizing["tradePct"] == "3"
    assert controller.tradeSizing["riskPct"] == "0.25"


def test_saving_from_the_screen_reaches_the_config(controller) -> None:
    controller.saveTradeSizing(_values(tradePct="4"))

    assert controller.tradeSizing["tradePct"] == "4"


def test_an_invalid_value_is_reported_and_not_written(controller) -> None:
    controller.setWizardLanguage("cs")
    notes: list[str] = []
    controller.notificationRequested.connect(notes.append)

    controller.saveTradeSizing(_values(riskPct="0"))

    assert "větší než nula" in notes[-1]
    assert controller.tradeSizing["riskPct"] == "0.25"


def test_saving_the_same_values_twice_says_nothing_changed(controller) -> None:
    """Distinct from the invalid message, which sends people hunting a typo."""
    controller.setWizardLanguage("cs")
    notes: list[str] = []
    controller.notificationRequested.connect(notes.append)

    controller.saveTradeSizing(_values(tradePct="6"))
    controller.saveTradeSizing(_values(tradePct="6"))

    assert "uloženy" in notes[0].lower()
    assert "Nic se nezměnilo" in notes[-1]


def test_the_binding_limit_is_explained_in_the_current_language(controller) -> None:
    """Rendered at read time, so it follows the language rather than the run."""
    controller._snapshot = controller._snapshot.__class__(
        **{
            **controller._snapshot.__dict__,
            "latest_run": DesktopRunResult(
                run_id=1, status="OK", report_path="", decision="BUY",
                decision_summary="", risk_approved=True, risk_reason="",
                portfolio_value=Decimal("1000"), liquid_value=Decimal("1000"),
                locked_value=Decimal("0"), ai_summary="", actions=(),
                binding_limit="funding",
            ),
        }
    )

    controller.setWizardLanguage("en")
    assert "actually pay" in controller.tradeSizing["lastBoundBy"]

    controller.setWizardLanguage("cs")
    assert "reálně mohl zaplatit" in controller.tradeSizing["lastBoundBy"]


def test_a_run_without_a_recorded_limit_explains_nothing(controller) -> None:
    """Every run from before the column exists; silence beats a guess."""
    assert controller.tradeSizing["lastBoundBy"] == ""


def test_the_panel_is_on_the_live_actions_page() -> None:
    qml = (Path(__file__).parents[1] / "coinductor" / "qml" / "Main.qml").read_text(encoding="utf-8")

    assert 'objectName: "tradeSizingPanel"' in qml
    assert "appController.saveTradeSizing" in qml
    # Every field the slot expects has to be sent, or the save silently
    # rewrites the missing ones to zero and is refused as invalid.
    for field in ("tradePct", "tradeAmount", "positionPct", "capitalPct", "riskPct"):
        assert f'"{field}":' in qml
