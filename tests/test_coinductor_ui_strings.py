from coinductor.ui_strings import APP_STRINGS, WIZARD_STRINGS, UiStringsService


def test_every_wizard_string_has_english_and_czech() -> None:
    for key, variants in WIZARD_STRINGS.items():
        assert "en" in variants, f"{key} is missing an English translation"
        assert "cs" in variants, f"{key} is missing a Czech translation"
        assert variants["en"].strip(), f"{key} has an empty English translation"
        assert variants["cs"].strip(), f"{key} has an empty Czech translation"


def test_every_app_string_has_english_and_czech() -> None:
    for key, variants in APP_STRINGS.items():
        assert "en" in variants, f"{key} is missing an English translation"
        assert "cs" in variants, f"{key} is missing a Czech translation"
        assert variants["en"].strip(), f"{key} has an empty English translation"
        assert variants["cs"].strip(), f"{key} has an empty Czech translation"


def test_app_text_returns_czech_when_requested() -> None:
    text = UiStringsService().app_text("cs")

    assert text["overview_title"] == "Přehled portfolia"
    assert text["overview_run_analysis_button"] == "Spustit analýzu"


def test_app_text_portfolio_toast_supports_placeholder_substitution() -> None:
    text = UiStringsService().app_text("cs")
    rendered = text["portfolio_policy_changed_toast"].replace("{asset}", "BTC").replace("{role}", "Core")

    assert rendered == "Politika pro BTC změněna na Core"


def test_app_text_grid_import_notice_supports_placeholder_substitution() -> None:
    text = UiStringsService().app_text("cs")
    rendered = text["grid_import_notice_template"].replace("{run}", "42")

    assert "z běhu 42" in rendered


def test_app_text_deploy_tranche_title_supports_placeholder_substitution() -> None:
    text = UiStringsService().app_text("cs")
    rendered = text["deploy_tranche_dialog_title_template"].replace("{asset}", "BTC")

    assert rendered == "Nasadit tranši BTC"


def test_the_confirmation_phrase_is_shown_to_be_copied_not_retyped() -> None:
    """The phrase used to be interpolated into this sentence and retyped by eye.

    It now sits beside the instruction as a copyable value, so the sentence
    itself must not carry a token placeholder - a translation that kept one
    would put the phrase back inside prose where it cannot be clicked.
    """
    for language in ("en", "cs"):
        prefix = UiStringsService().app_text(language)["submit_for_real_prefix"]
        assert prefix.strip(), f"no {language} text"
        assert "{token}" not in prefix
        assert "CONFIRM_" not in prefix


def test_app_text_translates_sidebar_navigation_labels() -> None:
    text = UiStringsService().app_text("cs")

    assert text["nav_overview"] == "Přehled"
    assert text["nav_active_strategies"] == "Aktivní strategie"
    assert text["nav_settings"] == "Nastavení"


def test_app_text_falls_back_to_english_for_unknown_language() -> None:
    text = UiStringsService().app_text("fr")

    assert text["overview_title"] == "Portfolio Overview"


def test_wizard_text_returns_english_by_default() -> None:
    text = UiStringsService().wizard_text("en")

    assert text["welcome_title"] == "Welcome to Coinductor"
    assert text["back_button"] == "Back"


def test_wizard_text_returns_czech_when_requested() -> None:
    text = UiStringsService().wizard_text("cs")

    assert text["welcome_title"] == "Vítejte v Coinductoru"
    assert text["back_button"] == "Zpět"


def test_wizard_text_falls_back_to_english_for_unknown_language() -> None:
    text = UiStringsService().wizard_text("fr")

    assert text["welcome_title"] == "Welcome to Coinductor"


def test_wizard_text_includes_ai_provider_status_strings() -> None:
    text_en = UiStringsService().wizard_text("en")
    text_cs = UiStringsService().wizard_text("cs")

    assert text_en["ask_ai_provider_status_configured"] == "AI provider configured:"
    assert "step 4" in text_en["ask_ai_provider_status_missing"]
    assert "kroku 4" in text_cs["ask_ai_provider_status_missing"]


def test_wizard_text_covers_the_same_keys_for_every_language() -> None:
    english_keys = set(UiStringsService().wizard_text("en"))
    czech_keys = set(UiStringsService().wizard_text("cs"))

    assert english_keys == czech_keys
