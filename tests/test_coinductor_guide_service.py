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

    assert "subscriptions and API usage are usually separate products with separate pricing" in guide["body"]
    assert "may cost money separately" in guide["warning"]
    assert "Privacy note" in guide["body"]


def test_guides_include_local_image_assets() -> None:
    guides = {guide["id"]: guide for guide in GuideService().list_guides()}

    assert len(guides["local-ai"]["images"]) == 2
    assert "14B-class models are the preferred minimum" in guides["local-ai"]["body"]
    assert "does not upload hardware details" in guides["local-ai"]["body"]
    assert len(guides["binance-api"]["images"]) == 2
    assert all(image["source"].startswith("file:///") for image in guides["binance-api"]["images"])


def test_portfolio_roles_guide_covers_all_ui_roles() -> None:
    guide = next(guide for guide in GuideService().list_guides() if guide["id"] == "portfolio-roles")

    for label in (
        "System default",
        "Protected core",
        "Protected utility",
        "Trading allowed",
        "Grid candidate",
        "Rebalancing candidate",
        "Funding source",
        "Dust/airdrop funding",
        "Active strategy",
        "Stable",
        "Unclassified",
    ):
        assert label in guide["body"]
