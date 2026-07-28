"""Guard the lookup tables against the producers that feed them.

Every table added while finishing the Czech screen maps a value produced
elsewhere - a label literal in the journal reader, a branch code, an engine
enum. All of them fall back to English rather than crashing, which is right at
runtime and exactly why drift is invisible: a value added later simply appears
untranslated and nothing says so.

These tests read the producers, not a hand-kept list, so adding a value without
its translation fails here.
"""

import re
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from coinductor.controller import AppController
from coinductor.service_strings import PARAMETER_LABELS, SERVICE_STRINGS, service_text

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "cs")


def _source(*parts: str) -> str:
    return ROOT.joinpath(*parts).read_text(encoding="utf-8")


def test_every_parameter_label_the_reader_emits_is_translated() -> None:
    """Labels are literals in DesktopStore; the values beside them vary per run.

    So a run cannot break the mapping - but a new card can, silently.
    """
    emitted = set(re.findall(r'"label": "([^"]+)"', _source("coinductor", "desktop_store.py")))
    assert emitted, "the extraction pattern is stale"
    missing = sorted(emitted - set(PARAMETER_LABELS))
    assert missing == [], f"parameter labels with no Czech: {missing}"


def test_no_parameter_label_is_translated_to_itself_by_accident() -> None:
    """A copied English string passes a presence check and fails the reader.

    Except where the label is the name of a control in Binance's own interface,
    which the reader has to find there written exactly this way - translating
    those would send someone hunting for a setting that does not exist.
    """
    binance_terms = {"TP / SL", "Stop loss", "Take profit"}
    suspicious = [
        label
        for label, czech in PARAMETER_LABELS.items()
        if czech == label and len(label.split()) > 1 and label not in binance_terms
    ]
    assert suspicious == [], f"multi-word labels left in English: {suspicious}"


def test_every_next_review_state_has_its_three_strings() -> None:
    states = set(re.findall(r'state = "([A-Z_]+)"', _source("coinductor", "desktop_store.py")))
    assert states, "the extraction pattern is stale"
    missing = [
        f"{state}/{part}/{language}"
        for state in states
        for part in ("status", "headline", "timing")
        for language in LANGUAGES
        if not service_text(f"next_review_{part}_{state.lower()}", language).strip()
    ]
    assert missing == [], f"next-review strings missing: {missing}"


def test_every_decision_type_the_engine_emits_has_a_label() -> None:
    """A decision type is an enum the engine picks per run.

    SPOT_TRADE_RECOMMENDATION was mapped as SPOT_TRADE and fell through to the
    generic fallback, which is how this test came to exist.
    """
    emitted: set[str] = set()
    for path in ROOT.joinpath("trading_agent").glob("*.py"):
        emitted |= set(re.findall(r'decision_type\s*=\s*"([A-Z_]+)"', path.read_text(encoding="utf-8")))
    assert emitted, "the extraction pattern is stale"
    missing = sorted(emitted - set(AppController._DECISION_LABELS))
    assert missing == [], f"decision types with no label: {missing}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_mapped_decision_label_resolves(language: str) -> None:
    missing = [
        key
        for key in AppController._DECISION_LABELS.values()
        if not SERVICE_STRINGS.get(key, {}).get(language, "").strip()
    ]
    assert missing == [], f"decision label keys with no {language} text: {missing}"


def test_every_urgency_and_cadence_value_is_translated() -> None:
    urgencies = set(re.findall(r'urgency\s*=\s*"([A-Z_]+)"', _source("trading_agent", "next_run.py")))
    cadences = {"DAILY", "TWICE_WEEKLY", "WEEKLY", "MANUAL"}
    missing = [
        f"urgency_{value.lower()}"
        for value in urgencies
        if not service_text(f"urgency_{value.lower()}", "cs").strip()
    ] + [
        f"cadence_{value.lower()}"
        for value in cadences
        if not service_text(f"cadence_{value.lower()}", "cs").strip()
    ]
    assert missing == [], f"missing translations: {missing}"
