"""Telling someone what ran while the window was closed.

A schedule whose results appear with no announcement feels broken even when it
worked, so this exists to say "three analyses ran". Its own failure mode is
worse than silence: claiming runs happened that did not, or announcing the
entire history the first time someone opens the app.
"""

from pathlib import Path

from coinductor.catch_up import CatchUpService


def _service(tmp_path: Path) -> CatchUpService:
    return CatchUpService(tmp_path / "last_seen_run.toml")


def _runs(*ids: int) -> list[dict[str, object]]:
    return [{"id": run_id, "decision": "HOLD"} for run_id in ids]


def test_a_first_launch_announces_nothing_and_records_where_it_is(tmp_path) -> None:
    """Everything in the journal would otherwise count as news."""
    service = _service(tmp_path)

    result = service.since_last_seen(_runs(9, 8, 7))

    assert result.any is False
    assert result.count == 0
    assert service.last_seen() == 9


def test_runs_recorded_since_the_marker_are_reported(tmp_path) -> None:
    service = _service(tmp_path)
    service.mark_seen(7)

    result = service.since_last_seen(_runs(10, 9, 8, 7, 6))

    assert result.count == 3
    assert result.latest_run_id == 10
    assert result.latest_decision == "HOLD"


def test_nothing_new_reports_nothing(tmp_path) -> None:
    service = _service(tmp_path)
    service.mark_seen(10)

    assert service.since_last_seen(_runs(10, 9)).any is False


def test_an_empty_journal_is_not_an_error(tmp_path) -> None:
    service = _service(tmp_path)
    service.mark_seen(5)

    assert service.since_last_seen([]).any is False


def test_the_marker_never_moves_backwards(tmp_path) -> None:
    """A stale snapshot would otherwise make reported runs unseen again."""
    service = _service(tmp_path)
    service.mark_seen(10)

    service.mark_seen(4)

    assert service.last_seen() == 10


def test_a_corrupt_marker_file_reads_as_never_seen(tmp_path) -> None:
    path = tmp_path / "last_seen_run.toml"
    path.write_text("this is not toml [[[", encoding="utf-8")

    # Reads as 0, which makes the next pass a first launch: it records where it
    # is and stays quiet, rather than announcing the whole history.
    service = CatchUpService(path)
    assert service.last_seen() == 0
    assert service.since_last_seen(_runs(3, 2)).any is False
    assert service.last_seen() == 3


def test_nonsense_run_ids_are_skipped_not_crashed_on(tmp_path) -> None:
    service = _service(tmp_path)
    service.mark_seen(1)

    result = service.since_last_seen(
        [{"id": "not a number"}, {"id": 5, "decision": "BUY"}, {"decision": "HOLD"}]
    )

    assert result.count == 1
    assert result.latest_run_id == 5
    assert result.latest_decision == "BUY"


def test_marking_a_nonsense_id_changes_nothing(tmp_path) -> None:
    service = _service(tmp_path)
    service.mark_seen(4)

    service.mark_seen("later")
    service.mark_seen(None)

    assert service.last_seen() == 4


def test_the_marker_survives_a_restart(tmp_path) -> None:
    _service(tmp_path).mark_seen(12)

    assert _service(tmp_path).last_seen() == 12


def test_it_does_not_share_a_file_with_the_app_tour(tmp_path) -> None:
    """AppTourService rewrites its file wholesale; a section here would go."""
    from coinductor.app_tour_service import AppTourService

    tour = AppTourService(tmp_path / "app_ui_state.toml")
    service = _service(tmp_path)
    service.mark_seen(12)

    tour.mark_completed()

    assert service.last_seen() == 12
    assert tour.is_completed() is True
