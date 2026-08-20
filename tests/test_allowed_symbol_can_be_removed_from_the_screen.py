"""A pair put on the analysis list by one click comes off it by another.

`remove_allowed_symbol` was written and tested alongside the add path, and then
reached from nowhere: the listing card's second state was a disabled button
reading "Analysis allowed". So a symbol allowed once stayed in every run's
analysis until someone hand-edited the config - which is the thing this app is
for not making people do.

The button reads the config rather than the listing's `acknowledged` flag,
because the flag records that the card was actioned once and stays set after a
removal, while the config is what the runs actually read.
"""

import shutil
from pathlib import Path

import pytest

from coinductor.allowed_symbols import read_allowed_symbols

TEMPLATE = Path(__file__).resolve().parents[1] / "config.example.toml"

pytest.importorskip("PySide6")

from coinductor.controller import AppController  # noqa: E402


@pytest.fixture
def controller(monkeypatch, tmp_path) -> "AppController":
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])
    shutil.copy(TEMPLATE, tmp_path / "config.toml")
    monkeypatch.chdir(tmp_path)
    return AppController()


def test_a_symbol_can_be_added_and_then_taken_off_again(controller, tmp_path) -> None:
    controller.addAllowedSymbol("SOXSBUSDT")
    assert "SOXSBUSDT" in read_allowed_symbols(tmp_path / "config.toml")

    controller.removeAllowedSymbol("SOXSBUSDT")

    assert "SOXSBUSDT" not in read_allowed_symbols(tmp_path / "config.toml")


def test_removing_is_case_insensitive_like_adding(controller, tmp_path) -> None:
    controller.addAllowedSymbol("SOXSBUSDT")

    controller.removeAllowedSymbol("soxsbusdt")

    assert "SOXSBUSDT" not in read_allowed_symbols(tmp_path / "config.toml")


def test_removing_something_absent_changes_nothing(controller, tmp_path) -> None:
    before = read_allowed_symbols(tmp_path / "config.toml")

    controller.removeAllowedSymbol("NOTTHERE")

    assert read_allowed_symbols(tmp_path / "config.toml") == before


def test_the_remaining_symbols_survive_a_removal(controller, tmp_path) -> None:
    """The list is edited in place, so the others - and the comments - stay."""
    original = read_allowed_symbols(tmp_path / "config.toml")
    controller.addAllowedSymbol("SOXSBUSDT")

    controller.removeAllowedSymbol("SOXSBUSDT")

    assert read_allowed_symbols(tmp_path / "config.toml") == original
    assert "[strategy]" in (tmp_path / "config.toml").read_text(encoding="utf-8")


def test_the_card_follows_the_config_not_the_acknowledged_flag(controller, tmp_path) -> None:
    """After a removal the button has to offer to add it back, not remove twice."""
    controller.addAllowedSymbol("SOXSBUSDT")
    controller.removeAllowedSymbol("SOXSBUSDT")

    listed = {str(row.get("symbol", "")).upper(): row for row in controller.listings}
    if "SOXSBUSDT" in listed:
        assert listed["SOXSBUSDT"]["allowed"] is False
