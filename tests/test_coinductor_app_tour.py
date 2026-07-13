from coinductor.app_tour_service import AppTourService


def test_app_tour_completion_is_persisted_and_reset(tmp_path) -> None:
    service = AppTourService(tmp_path / "state" / "app_ui_state.toml")

    assert service.is_completed() is False

    service.mark_completed()

    assert service.is_completed() is True

    service.reset()

    assert service.is_completed() is False
