from coinductor.guide_service import GuideService


def test_guide_service_exposes_core_setup_guides() -> None:
    guides = GuideService().list_guides()
    ids = {guide["id"] for guide in guides}

    assert {"local-ai", "cloud-ai", "binance-api", "binance-live-api", "safety-model", "portfolio-roles"} <= ids
    assert all(guide["title"] for guide in guides)
    assert all(guide["summary"] for guide in guides)
    # Setup walkthroughs are numbered step-by-step; portfolio-roles and the
    # per-page "Using Coinductor" guides are descriptive instead.
    for guide in guides:
        if guide["section"] == "Using Coinductor" or guide["id"] == "portfolio-roles":
            continue
        assert "1." in guide["body"]


def test_guide_service_covers_every_app_page() -> None:
    ids = {guide["id"] for guide in GuideService().list_guides()}

    assert {
        "page-overview",
        "page-portfolio",
        "page-live-actions",
        "page-action-plan",
        "page-active-strategies",
        "page-run-history",
        "page-ai-assistant",
        "page-settings",
        "page-help-guides",
    } <= ids


def test_every_guide_has_a_czech_translation() -> None:
    from coinductor.guide_strings_cs import GUIDES_CS

    guides = GuideService().list_guides()
    for guide in guides:
        translation = GUIDES_CS.get(guide["id"])
        assert translation, f"missing Czech translation for guide '{guide['id']}'"
        for field in ("title", "summary", "body"):
            assert translation.get(field), f"{guide['id']} is missing Czech {field}"
        if guide.get("warning"):
            assert translation.get("warning"), f"{guide['id']} is missing Czech warning"
        if guide.get("images"):
            assert len(translation.get("images") or []) == len(guide["images"])


def test_list_guides_returns_czech_and_falls_back_to_english() -> None:
    service = GuideService()
    english = {guide["id"]: guide for guide in service.list_guides("en")}
    czech = {guide["id"]: guide for guide in service.list_guides("cs")}

    assert czech["local-ai"]["title"] == "Lokální AI s Ollamou"
    assert "Přehled" in czech["page-overview"]["title"]
    # Unknown languages fall back to English.
    assert service.list_guides("de")[0]["title"] == english["local-ai"]["title"]


def test_czech_guides_keep_cross_links_and_literal_labels() -> None:
    czech = {guide["id"]: guide for guide in GuideService().list_guides("cs")}
    ids = set(czech)

    import re

    for guide in czech.values():
        for target in re.findall(r'href="guide:([^"]+)"', guide["body"]):
            assert target in ids, f"{guide['id']} links to unknown guide '{target}'"
    # Literal Binance/Ollama labels the user must match stay in English.
    assert "API Management" in czech["binance-api"]["body"]
    assert "ollama pull qwen3:14b" in czech["local-ai"]["body"]


def test_internal_guide_cross_links_resolve_to_real_guides() -> None:
    import re

    guides = GuideService().list_guides()
    ids = {guide["id"] for guide in guides}
    for guide in guides:
        for target in re.findall(r'href="guide:([^"]+)"', guide["body"]):
            assert target in ids, f"{guide['id']} links to unknown guide '{target}'"


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
    assert "Vision model" in guides["local-ai"]["body"]
    assert "routes only image messages" in guides["local-ai"]["body"]
    assert len(guides["binance-api"]["images"]) == 2
    assert len(guides["binance-live-api"]["images"]) == 2
    assert any(
        "binance_live_trading_restrictions_sanitized.png" in image["source"]
        for image in guides["binance-live-api"]["images"]
    )
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


def test_live_api_guide_covers_ip_restriction_and_permissions() -> None:
    guide = next(guide for guide in GuideService().list_guides() if guide["id"] == "binance-live-api")

    assert "coinductor-live-trading" in guide["body"]
    assert "Restrict access to trusted IPs only" in guide["body"]
    assert "https://ifconfig.me/" in guide["body"]
    assert guide["body"].index("trusted-IP restriction is configured") < guide["body"].index("Enable Spot")
    assert "Coinductor Live Actions" in guide["body"]
    assert "withdrawals disabled" in guide["body"].lower()
    assert "separate key" in guide["body"].lower()
    assert "can place/cancel Spot orders" in guide["warning"]
