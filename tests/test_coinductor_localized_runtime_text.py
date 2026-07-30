"""Runtime text the user meets after an action, not on a static screen.

These strings were composed in Python at the moment something finished, which
is exactly why they survived every earlier localization pass: nothing renders
them until a run completes.
"""

from datetime import UTC, datetime, timedelta, timezone

import pytest

pytest.importorskip("PySide6")

from coinductor.controller import AppController
from coinductor.desktop_store import DesktopStore
from coinductor.service_strings import SERVICE_STRINGS, service_text


def _controller(monkeypatch, tmp_path) -> AppController:
    monkeypatch.chdir(tmp_path)
    return AppController()


def _completion_keys() -> set[str]:
    from pathlib import Path
    import re

    source = Path(__file__).resolve().parents[1] / "coinductor" / "controller.py"
    return set(re.findall(r'completion_message="([^"]+)"', source.read_text(encoding="utf-8")))


def test_every_completion_toast_key_resolves() -> None:
    """service_text returns "" for an unknown key.

    A typo would therefore show an empty toast - the user is told nothing at
    all, and no exception marks the spot.
    """
    keys = _completion_keys()
    assert keys, "no completion messages found; the extraction pattern is stale"
    missing = sorted(key for key in keys if not service_text(key, "en").strip())
    assert missing == [], f"completion keys with no text: {missing}"
    untranslated = sorted(key for key in keys if not SERVICE_STRINGS[key].get("cs", "").strip())
    assert untranslated == [], f"completion keys with no Czech: {untranslated}"


def test_completion_toast_is_emitted_in_the_users_language(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    controller._pending_completion_message = "toast_monitoring_refreshed"
    seen: list[str] = []
    controller.notificationRequested.connect(seen.append)

    controller._on_completed(_run())

    assert seen == ["Sledování aktivních strategií bylo obnoveno."]


def test_active_strategies_summary_is_localized(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    controller._active_strategies = [
        {"type": "Spot Grid", "name": "A", "health": "Healthy"},
        {"type": "Spot Grid", "name": "B", "health": "Review"},
        {"type": "Rebalancing", "name": "C", "health": "Action required"},
    ]
    controller._registered_strategy_count = 4

    summary = controller.activeStrategiesSummary

    assert "Aktivních strategií: 3" in summary
    assert "1 v pořádku" in summary
    assert "1 ke kontrole" in summary
    assert "1 vyžaduje zásah" in summary
    assert "čekajících na nové vyhodnocení: 1" in summary


def test_empty_active_strategies_summary_is_localized(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    controller._active_strategies = []
    controller._registered_strategy_count = 0

    assert controller.activeStrategiesSummary.startswith("V posledním běhu")


def test_ai_summary_says_no_provider_rather_than_echoing_the_engine(monkeypatch, tmp_path) -> None:
    """With no provider the engine records that it asked nothing.

    That is true, and in English, and next to a heading reading "AI summary" it
    reads as a malfunction. The desktop knows the provider is unset without
    matching on the stored wording.
    """
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    controller._ai_summary = "AI commentary could not be generated: boom."

    assert controller.activeAiProviderKind == "NONE"
    assert controller.aiSummary.startswith("Není nastavený žádný AI provider")


def test_a_run_without_ai_says_so_instead_of_showing_the_engines_note(monkeypatch, tmp_path) -> None:
    """Unticking the AI summary is a choice, not a failure.

    It showed the engine's English "AI commentary is disabled." under a heading
    reading "Shrnuti od AI", which looks like something went wrong. Checked
    before the provider branch: with no provider configured the run is also
    without AI, and the reason the user picked is the more useful one.
    """
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    controller._ai_enabled = False
    controller._ai_summary = "AI commentary is disabled."

    assert controller.aiSummary.startswith("Tato analýza běžela bez hodnocení od AI")

    controller.setWizardLanguage("en")
    assert controller.aiSummary.startswith("This analysis ran without AI commentary")


def test_switching_language_notifies_the_properties_that_compose_when_read(monkeypatch, tmp_path) -> None:
    """Composing at read time is only half of it.

    riskState, decisionSummary and aiSummary were changed to compose when read
    so a language switch would reach them - but setWizardLanguage never emitted
    their notify signal, so QML never read them again and all three kept the
    old language. It showed up as the AI summary's "written in another
    language" line appearing at the next analysis rather than at the switch.
    """
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("en")

    fired: set[str] = set()
    for name in ("stateChanged", "assistantChanged", "localAiRecommendationChanged"):
        getattr(controller, name).connect(lambda n=name: fired.add(n))

    controller.setWizardLanguage("cs")

    assert fired == {"stateChanged", "assistantChanged", "localAiRecommendationChanged"}


def test_a_summary_written_in_another_language_says_so(monkeypatch, tmp_path) -> None:
    """The model's prose is the one thing here that cannot be re-translated.

    It was written once, during the run. Switching to English left a Czech
    paragraph under a heading reading "AI summary", with nothing to distinguish
    that from a broken translation.
    """
    import coinductor.controller as controller_module

    # A stored summary is the model's prose, so a provider was configured when
    # the run happened; without one the earlier branch answers instead. Patched
    # at the function rather than on the snapshot, which a language switch
    # reloads.
    monkeypatch.setattr(controller_module, "provider_kind", lambda _base_url: "LOCAL")

    controller = _controller(monkeypatch, tmp_path)
    controller._ai_summary = "Nedostatek kapitálu pro založení gridu."
    controller._ai_language = "cs"

    controller.setWizardLanguage("cs")
    assert controller.aiSummary == "Nedostatek kapitálu pro založení gridu."

    controller.setWizardLanguage("en")
    assert controller.aiSummary.startswith("Nedostatek kapitálu pro založení gridu.")
    assert "the model's own words" in controller.aiSummary

    # A run recorded before the language was written down: say nothing rather
    # than guess which language the stored prose is in.
    controller._ai_language = ""
    assert controller.aiSummary == "Nedostatek kapitálu pro založení gridu."


def test_run_history_start_times_are_converted_to_local(tmp_path) -> None:
    """SQLite's `default current_timestamp` writes UTC with no offset.

    Run History printed that string verbatim, so every run looked hours old
    while the Action Plan's next-review line - which already converted -
    disagreed with it on the same screen.
    """
    store = DesktopStore(tmp_path / "journal.sqlite3", tmp_path / "reports")

    rendered = store._local_started_at("2026-07-28 09:35:26")

    expected = datetime(2026, 7, 28, 9, 35, 26, tzinfo=UTC).astimezone()
    assert rendered.startswith(f"{expected:%Y-%m-%d %H:%M:%S}")
    assert "UTC" in rendered, "a converted time must say which clock it is on"


def test_unparsable_start_time_is_passed_through(tmp_path) -> None:
    store = DesktopStore(tmp_path / "journal.sqlite3", tmp_path / "reports")

    assert store._local_started_at("not a date") == "not a date"
    assert store._local_started_at("") == ""
    assert store._local_started_at(None) == ""


def test_offset_aware_start_time_is_not_shifted_twice(tmp_path) -> None:
    store = DesktopStore(tmp_path / "journal.sqlite3", tmp_path / "reports")

    rendered = store._local_started_at("2026-07-28T09:35:26+02:00")

    expected = datetime(2026, 7, 28, 9, 35, 26, tzinfo=timezone(timedelta(hours=2))).astimezone()
    assert rendered.startswith(f"{expected:%Y-%m-%d %H:%M:%S}")


def _run():
    from decimal import Decimal

    from coinductor.models import DesktopRunResult

    return DesktopRunResult(
        run_id=1,
        status="OK",
        report_path="report.md",
        decision="HOLD",
        decision_summary="HOLD.",
        risk_approved=True,
        risk_reason="Within limits.",
        portfolio_value=Decimal("500"),
        liquid_value=Decimal("100"),
        locked_value=Decimal("400"),
        ai_summary="",
        actions=(),
    )


def test_run_history_rows_carry_their_own_report(tmp_path) -> None:
    """Run History listed thirty runs and could open none of them.

    The only report reachable from the UI was the newest, via the Action Plan.
    """
    import sqlite3

    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "2026-07-28_09-35-26_run-1.md").write_text("# Run 1", encoding="utf-8")
    database = tmp_path / "journal.sqlite3"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        create table runs (id integer primary key, started_at text, status text, summary text);
        create table market_research_reports (run_id integer, status text);
        create table strategy_decisions (run_id integer, decision_type text, summary text);
        insert into runs values (1, '2026-07-28 09:35:26', 'OK', 'done');
        insert into runs values (2, '2026-07-28 11:04:27', 'OK', 'done');
        insert into market_research_reports values (1, 'OK'), (2, 'OK');
        insert into strategy_decisions values (1, 'HOLD', 'No action.'), (2, 'HOLD', 'No action.');
        """
    )
    connection.commit()
    connection.row_factory = sqlite3.Row
    store = DesktopStore(database, reports)

    history = store._history(connection)
    connection.close()

    by_id = {row["runId"]: row for row in history}
    assert by_id["1"]["reportPath"].endswith("2026-07-28_09-35-26_run-1.md")
    assert by_id["2"]["reportPath"] == "", "a run with no report file offers no button"
    assert "UTC" in by_id["1"]["startedAt"]


def test_opening_a_vanished_report_notifies_instead_of_failing(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    seen: list[str] = []
    controller.notificationRequested.connect(seen.append)

    controller.openRunReport(str(tmp_path / "gone.md"))
    controller.openRunReport("")

    assert seen == ["Soubor s reportem tohoto běhu už na disku není."] * 2


def test_copying_the_steps_produces_a_numbered_block(monkeypatch, tmp_path) -> None:
    """Every price and count had to be retyped by eye against Binance."""
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    seen: list[str] = []
    controller.notificationRequested.connect(seen.append)

    controller.copyManualSteps(["Otevřete Binance Home.", "Vyberte ETH/USDC."])

    clipboard = QGuiApplication.clipboard()
    assert clipboard.text() == "1. Otevřete Binance Home.\n2. Vyberte ETH/USDC."
    assert seen == ["Zkopírováno 2 kroků nastavení. Vložte si je vedle Binance a projděte je shora dolů."]


def test_copying_nothing_says_nothing(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    seen: list[str] = []
    controller.notificationRequested.connect(seen.append)

    controller.copyManualSteps([])

    assert seen == [], "an empty list is not a failure worth a toast"


def test_clicking_a_value_copies_just_that_value(monkeypatch, tmp_path) -> None:
    """Card values are elided, which rules out drag-selection."""
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    seen: list[str] = []
    controller.notificationRequested.connect(seen.append)

    controller.copyValue("1675.87 - 2040.57")
    controller.copyValue("   ")

    assert QGuiApplication.clipboard().text() == "1675.87 - 2040.57"
    assert seen == ["Zkopírováno: 1675.87 - 2040.57"], "blank values are not worth a toast"


def test_run_decision_is_spelled_for_a_reader(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")

    assert controller._decision_label("GRID_BOT_RECOMMENDATION") == "Doporučen Spot Grid"
    assert controller._decision_label("HOLD") == "Žádná akce"
    # An enum nobody has mapped yet still reads better than SHOUTING_SNAKE_CASE.
    assert controller._decision_label("SOME_NEW_TYPE") == "Some new type"


def test_parameter_labels_are_translated_on_every_card(monkeypatch, tmp_path) -> None:
    """DesktopStore composes these and has no language of its own.

    The Trade card built its labels in the controller and was translated; the
    bot cards took theirs from the store and were not, so one screen showed
    "Akce / Symbol / Jistota" beside "Symbol / Range / Grids".
    """
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    controller._strategies = [
        {
            "type": "Spot Grid",
            "status": "READY",
            "detail": "x",
            "parameters": [
                {"label": "Range", "value": "1675 - 2040"},
                {"label": "Grids", "value": "10"},
                {"label": "Blockers", "value": "-"},
                {"label": "Totally New Label", "value": "y"},
            ],
            "manualSteps": (),
        }
    ]

    card = next(i for i in controller._build_action_plan_items() if i["title"] == "Spot Grid")

    labels = [p["label"] for p in card["parameters"]]
    assert labels[:3] == ["Rozsah", "Počet gridů", "Blokátory"]
    assert labels[3] == "Totally New Label", "an unmapped label passes through, it does not vanish"
    assert [p["value"] for p in card["parameters"]][:2] == ["1675 - 2040", "10"]


def test_english_keeps_the_stored_labels(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller._strategies = [
        {"type": "Spot Grid", "status": "READY", "detail": "x",
         "parameters": [{"label": "Range", "value": "1675 - 2040"}], "manualSteps": ()}
    ]

    card = next(i for i in controller._build_action_plan_items() if i["title"] == "Spot Grid")

    assert card["parameters"][0]["label"] == "Range"


def test_switching_language_relanguages_the_cached_next_review(monkeypatch, tmp_path) -> None:
    """nextReview is composed once when a snapshot loads.

    Nothing recomposed it on a language change, so the panel kept the language
    the app started in - and the property it hangs on, dataChanged, was not
    emitted either.
    """
    controller = _controller(monkeypatch, tmp_path)
    controller._snapshot = replace_next_review(
        controller._snapshot,
        {"state": "MANUAL_STEP", "status": "Manual step before rerun", "tone": "blocked",
         "headline": "A fresh run can update market data.", "hours": 0,
         "timing": "After the manual step", "urgency": "Action Required"},
    )
    controller._next_review = controller._enrich_next_review(controller._snapshot.next_review)
    seen: list[int] = []
    controller.dataChanged.connect(lambda: seen.append(1))

    controller.setWizardLanguage("cs")

    assert controller.nextReview["status"] == "Ruční krok před dalším během"
    assert controller.nextReview["timing"] == "Po ručním kroku"
    assert controller.nextReview["urgency"] == "Vyžaduje zásah"
    assert seen, "QML re-reads these only on dataChanged"


def replace_next_review(snapshot, review):
    from dataclasses import replace

    return replace(snapshot, next_review=review)


def test_the_run_carries_the_ui_language_to_the_model(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    captured = {}

    def stub(options):
        captured["options"] = options
        return _StubWorker()

    monkeypatch.setattr("coinductor.controller.AnalysisWorker", stub)
    monkeypatch.setattr(AppController, "_start_worker", lambda self, *_args: None)

    controller._start_analysis("MOCK", False, False, False, result_page=3, completion_message="toast_analysis_done")

    assert captured["options"].response_language == "cs"


class _StubWorker:
    class _Sig:
        def connect(self, *_args, **_kwargs):
            return None

    progress = completed = failed = finished = _Sig()

    def moveToThread(self, *_args):
        return None
