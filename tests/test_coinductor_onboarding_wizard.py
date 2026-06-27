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
    assert controller.onboardingWizardVisible is False

    controller.openOnboardingWizard()

    assert controller.onboardingWizardVisible is True

    controller.closeOnboardingWizard()

    assert controller.onboardingWizardVisible is False

    controller.deleteUserProfile()

    assert controller.userProfileConfigured is False
    assert controller.onboardingWizardVisible is True
