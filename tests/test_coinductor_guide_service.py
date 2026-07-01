from coinductor.guide_service import GuideService


def test_guide_service_exposes_core_setup_guides() -> None:
    guides = GuideService().list_guides()
    ids = {guide["id"] for guide in guides}

    assert {"local-ai", "cloud-ai", "binance-api", "safety-model", "portfolio-roles"} <= ids
    assert all(guide["title"] for guide in guides)
    assert all(guide["summary"] for guide in guides)
    assert all("1." in guide["body"] or guide["id"] == "portfolio-roles" for guide in guides)


def test_cloud_ai_guide_warns_about_subscription_and_api_pricing() -> None:
    guide = next(guide for guide in GuideService().list_guides() if guide["id"] == "cloud-ai")

    assert "subscriptions and API usage are usually separate" in guide["body"]
    assert "Privacy note" in guide["body"]
