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


# Terms the reader has to find written exactly this way somewhere else - in
# Binance's interface, in a config file, or as a product name. Translating them
# would send someone hunting for something that does not exist under that name.
_LITERAL_TERMS = {
    "Portfolio", "Spot", "Testnet", "Mainnet", "Binance ID", "Binance bot ID",
    "Symbol", "Symbol *", "Stop loss", "Stop loss *", "Take profit", "Take profit *",
    "TP / SL", "Spot Grid", "Rebalancing", "Endpoint", "Model", "Grid", "Python",
    "Binance Spot Testnet", "Coinductor", "Binance", "USDC", "OCO", "AI Assistant",
    # Product and section names that read the same in Czech.
    "BINANCE", "AI", "Binance API",
}


def _tables():
    from coinductor.service_strings import SERVICE_STRINGS
    from coinductor.ui_strings import APP_STRINGS, WIZARD_STRINGS

    return (("APP_STRINGS", APP_STRINGS), ("WIZARD_STRINGS", WIZARD_STRINGS),
            ("SERVICE_STRINGS", SERVICE_STRINGS))


def test_no_table_entry_is_missing_a_translation() -> None:
    missing = [
        f"{name}.{key}"
        for name, table in _tables()
        for key, tr in table.items()
        if not (tr.get("en") or "").strip() or not (tr.get("cs") or "").strip()
    ]
    assert missing == [], f"entries with an empty side: {missing}"


def test_czech_is_not_silently_a_copy_of_the_english() -> None:
    """The failure mode that kept reaching the user.

    A copied string passes every presence check and looks translated to
    anything automated, so it was only ever found by someone reading the
    screen - the navigation sat in English for eight releases that way.
    """
    copied = [
        f"{name}.{key} = {tr['en']!r}"
        for name, table in _tables()
        for key, tr in table.items()
        if tr.get("en", "").strip() == tr.get("cs", "").strip()
        and tr.get("en", "").strip() not in _LITERAL_TERMS
    ]
    assert copied == [], "Czech is a copy of the English for:\n  " + "\n  ".join(copied)


def _engine_message_keys() -> set[str]:
    """Every key the engine can emit, read from the engine itself."""
    emitted: set[str] = set()
    for path in ROOT.joinpath("trading_agent").glob("*.py"):
        if path.name == "messages.py":
            continue
        source = path.read_text(encoding="utf-8")
        emitted |= set(re.findall(r'Message\(\s*\n?\s*"([a-z0-9_]+)"', source))
        emitted |= set(re.findall(r'ManualStep\(\s*\n?\s*"([a-z0-9_]+)"', source))
    return emitted


def test_every_engine_message_key_has_text() -> None:
    """The engine renders an unknown key as the key itself.

    Right at runtime, and the reason a missing entry is invisible: the screen
    shows `action_run_again` instead of a sentence and nothing raises.
    """
    from trading_agent.messages import MESSAGE_TEXT

    emitted = _engine_message_keys()
    assert emitted, "the extraction pattern is stale"
    missing = sorted(emitted - set(MESSAGE_TEXT))
    assert missing == [], f"engine emits keys with no text: {missing}"


def test_no_engine_prose_is_left_where_a_message_belongs() -> None:
    """The producers that reach the desktop must not compose sentences.

    Each of these was converted because a finished English sentence cannot be
    re-localized; a new f-string in one of them would quietly restart that.
    """
    converted = ("grid_advisor.py", "rebalancing_bot_advisor.py", "next_run.py",
                 "recommended_actions.py")
    # Why each funding source was picked. It appears in the Markdown report and
    # nowhere on screen - verified by grepping the desktop for it - so it stays
    # English with the rest of the report.
    report_only = ("Reserve source is capped", "Small legacy/speculative holding")
    offenders = []
    for name in converted:
        for line in _source("trading_agent", name).splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or "Message(" in stripped:
                continue
            if any(phrase in stripped for phrase in report_only):
                continue
            # A quoted string of several words being appended or assigned to a
            # user-facing field is the shape that started all of this.
            if re.search(r'(reason|summary|action|blockers)\w*\s*(=|\.append\()\s*f?"[A-Z][a-z]+ \w+ \w+', stripped):
                offenders.append(f"{name}: {stripped[:70]}")
    assert offenders == [], "prose where a message belongs:\n  " + "\n  ".join(offenders)
