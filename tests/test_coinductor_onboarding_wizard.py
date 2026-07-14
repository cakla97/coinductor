import pytest

pytest.importorskip("PySide6")

from coinductor.controller import AppController


def test_onboarding_wizard_is_first_run_gate(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    controller = AppController()

    assert controller.onboardingWizardVisible is True

    controller.selectOnboardingPath("FIRST_PORTFOLIO")
    controller.useSafeDefaultProfile()

    assert controller.userProfileConfigured is True
    assert controller.onboardingWizardVisible is True

    controller.setCurrentPage(4)
    controller.finishOnboardingWizard()

    assert controller.onboardingWizardVisible is False
    assert controller.currentPage == 0
    assert controller.appTourVisible is True
    assert controller.appTourStep == 0

    controller.setCurrentPage(3)

    assert controller.currentPage == 0

    controller.nextAppTourStep()

    assert controller.appTourStep == 1
    assert controller.currentPage == 1

    controller.skipAppTour()

    assert controller.appTourVisible is False
    assert (tmp_path / "state" / "app_ui_state.toml").exists()

    restarted_controller = AppController()

    assert restarted_controller.onboardingWizardVisible is False
    assert restarted_controller.appTourVisible is False
    assert restarted_controller.currentPage == 0

    controller.setCurrentPage(8)
    controller.startAppTour()

    assert controller.appTourVisible is True
    assert controller.currentPage == 0

    controller.deleteUserProfile()

    assert controller.userProfileConfigured is False
    assert controller.onboardingWizardVisible is True
    assert controller.appTourVisible is False
    assert not (tmp_path / "state" / "app_ui_state.toml").exists()
