"""Earn funding limits, read and written from the app instead of config.toml.

Separate from the order-sizing panel on purpose: sizing decides how large an
order is worth making, this decides how much of the user's savings the app may
reach for to pay for one. Merging them would repeat the confusion that had an
Earn redemption limit capping trade size.
"""

import shutil
from pathlib import Path

import pytest

from coinductor.earn_funding import (
    apply_funding_to_config,
    ensure_keys,
    read_funding,
    valid_funding,
)

TEMPLATE = Path(__file__).resolve().parents[1] / "config.example.toml"


@pytest.fixture
def config(tmp_path) -> Path:
    path = tmp_path / "config.toml"
    shutil.copy(TEMPLATE, path)
    return path


def _values(**overrides) -> dict[str, str]:
    values = {"runPct": "2", "runAmount": "100", "dayPct": "5", "dayAmount": "250", "reserve": "0"}
    values.update(overrides)
    return values


def test_the_shipped_template_reads_back(config: Path) -> None:
    assert read_funding(config) == _values()


def test_saving_reaches_the_config(config: Path) -> None:
    changed = apply_funding_to_config(config, _values(runPct="3", dayAmount="400"))

    assert "earn.max_auto_redeem_pct_of_portfolio" in changed
    assert "earn.max_redeem_per_day_usdt" in changed
    assert read_funding(config)["runPct"] == "3"
    assert read_funding(config)["dayAmount"] == "400"


def test_saving_the_same_values_twice_changes_nothing(config: Path) -> None:
    apply_funding_to_config(config, _values())

    assert apply_funding_to_config(config, _values()) == {}


def test_a_zero_reserve_is_a_real_answer(config: Path) -> None:
    """The template ships zero: draw the balance down to nothing if needed."""
    assert valid_funding(_values(reserve="0")) is True
    assert read_funding(config)["reserve"] == "0"


@pytest.mark.parametrize("field", ["runPct", "runAmount", "dayPct", "dayAmount"])
def test_a_zero_limit_is_refused(config: Path, field: str) -> None:
    """For a limit, zero means "stop everything" and reads as a slip."""
    assert valid_funding(_values(**{field: "0"})) is False
    assert apply_funding_to_config(config, _values(**{field: "0"})) == {}


def test_a_negative_reserve_is_refused(config: Path) -> None:
    assert valid_funding(_values(reserve="-5")) is False


@pytest.mark.parametrize("field", ["runPct", "dayPct"])
def test_a_percentage_above_one_hundred_is_a_typo(config: Path, field: str) -> None:
    assert valid_funding(_values(**{field: "150"})) is False


def test_a_flat_amount_may_exceed_one_hundred(config: Path) -> None:
    assert valid_funding(_values(runAmount="5000", dayAmount="9000")) is True


def test_a_config_predating_the_percentages_gains_them(tmp_path) -> None:
    """`_apply` only edits keys that exist; without this they are discarded."""
    path = tmp_path / "config.toml"
    text = TEMPLATE.read_text(encoding="utf-8")
    for key in ("max_auto_redeem_pct_of_portfolio = 2.0\n", "max_redeem_pct_of_portfolio_per_day = 5.0\n"):
        text = text.replace(key, "")
    path.write_text(text, encoding="utf-8")

    assert ensure_keys(path) is True
    apply_funding_to_config(path, _values(runPct="4", dayPct="7"))

    assert read_funding(path)["runPct"] == "4"
    assert read_funding(path)["dayPct"] == "7"


def test_the_added_keys_land_in_the_earn_section(tmp_path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        TEMPLATE.read_text(encoding="utf-8").replace("max_auto_redeem_pct_of_portfolio = 2.0\n", ""),
        encoding="utf-8",
    )

    ensure_keys(path)

    from trading_agent.config import load_config

    assert "max_auto_redeem_pct_of_portfolio" in load_config(str(path)).raw["earn"]


def test_a_missing_config_writes_nothing(tmp_path) -> None:
    assert apply_funding_to_config(tmp_path / "absent.toml", _values()) == {}


# ---------------------------------------------------------------------------
# The screen.
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


def test_the_screen_reads_what_the_config_holds(controller) -> None:
    assert controller.earnFunding["runPct"] == "2"
    assert controller.earnFunding["dayAmount"] == "250"


def test_saving_from_the_screen_reaches_the_config(controller) -> None:
    controller.saveEarnFunding(_values(runPct="4"))

    assert controller.earnFunding["runPct"] == "4"


def test_an_invalid_value_is_reported_and_not_written(controller) -> None:
    controller.setWizardLanguage("cs")
    notes: list[str] = []
    controller.notificationRequested.connect(notes.append)

    controller.saveEarnFunding(_values(runAmount="0"))

    assert "větší než nula" in notes[-1]
    assert controller.earnFunding["runAmount"] == "100"


def test_the_panel_is_on_the_live_actions_page() -> None:
    qml = (Path(__file__).parents[1] / "coinductor" / "qml" / "Main.qml").read_text(encoding="utf-8")

    assert 'objectName: "earnFundingPanel"' in qml
    assert "appController.saveEarnFunding" in qml
    # Every field the slot expects must be sent, or the save rewrites the
    # missing ones to zero and is refused as invalid.
    for field in ("runPct", "runAmount", "dayPct", "dayAmount", "reserve"):
        assert f'"{field}":' in qml


# ---------------------------------------------------------------------------
# The unattended-funding switch. It shipped in 1.4.0 readable only in
# config.toml - a whole panel for the limits, and the switch itself left in
# the file this app promises nobody has to open.
# ---------------------------------------------------------------------------

from coinductor.earn_funding import (  # noqa: E402
    apply_auto_funding,
    ensure_auto_key,
    read_auto_funding,
)


def test_it_is_off_in_the_shipped_template(config: Path) -> None:
    assert read_auto_funding(config) is False


def test_an_absent_key_reads_as_off(tmp_path) -> None:
    """Fail closed: the dangerous direction is reading absence as permission."""
    path = tmp_path / "config.toml"
    path.write_text(
        TEMPLATE.read_text(encoding="utf-8").replace("auto_funding_enabled = false\n", ""),
        encoding="utf-8",
    )

    assert read_auto_funding(path) is False


def test_turning_it_on_and_off_round_trips(config: Path) -> None:
    assert apply_auto_funding(config, True)
    assert read_auto_funding(config) is True

    assert apply_auto_funding(config, False)
    assert read_auto_funding(config) is False


def test_setting_it_to_what_it_already_is_changes_nothing(config: Path) -> None:
    assert apply_auto_funding(config, False) == {}


def test_a_config_predating_the_switch_gains_it(tmp_path) -> None:
    """`_apply` only edits existing keys, so without this the toggle would
    report success and change nothing - and silently failing to turn this
    *off* is the direction that matters."""
    path = tmp_path / "config.toml"
    path.write_text(
        TEMPLATE.read_text(encoding="utf-8").replace("auto_funding_enabled = false\n", ""),
        encoding="utf-8",
    )

    assert ensure_auto_key(path) is True
    apply_auto_funding(path, True)

    assert read_auto_funding(path) is True


def test_the_key_lands_in_the_earn_section(tmp_path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        TEMPLATE.read_text(encoding="utf-8").replace("auto_funding_enabled = false\n", ""),
        encoding="utf-8",
    )

    ensure_auto_key(path)

    from trading_agent.config import load_config

    assert load_config(str(path)).raw["earn"]["auto_funding_enabled"] is False


def test_the_screen_shows_and_sets_it(controller) -> None:
    assert controller.earnFunding["autoEnabled"] is False

    controller.setAutoFunding(True)

    assert controller.earnFunding["autoEnabled"] is True


def test_switching_it_says_what_it_did(controller) -> None:
    """It changes what happens while nobody is watching; "saved" is not enough."""
    controller.setWizardLanguage("cs")
    notes: list[str] = []
    controller.notificationRequested.connect(notes.append)

    controller.setAutoFunding(True)
    assert "zapnuté" in notes[-1]

    controller.setAutoFunding(False)
    assert "vypnuté" in notes[-1]


def test_the_screen_reports_whether_the_stage_permits_it(controller) -> None:
    """On below LIVE_ENABLED does nothing, and a switch that silently does
    nothing is worse than one that is not there."""
    assert controller.earnFunding["autoArmed"] is False

    controller._safety_snapshot = controller._safety_snapshot.__class__(
        **{**controller._safety_snapshot.__dict__, "stage": "LIVE_ENABLED"}
    )

    assert controller.earnFunding["autoArmed"] is True


def test_the_toggle_is_on_the_panel() -> None:
    qml = (Path(__file__).parents[1] / "coinductor" / "qml" / "Main.qml").read_text(encoding="utf-8")

    assert "appController.setAutoFunding" in qml
    assert "earn_funding_auto_label" in qml
    # The warning only makes sense while it is on but cannot act.
    assert "earnFunding.autoEnabled && !appController.earnFunding.autoArmed" in qml
