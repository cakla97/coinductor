from coinductor.service_strings import SERVICE_STRINGS, normalize_language, service_text


def test_every_service_string_has_english_and_czech() -> None:
    for key, entry in SERVICE_STRINGS.items():
        assert entry.get("en"), f"{key} is missing English"
        assert entry.get("cs"), f"{key} is missing Czech"


def test_service_text_resolves_language_and_falls_back() -> None:
    assert service_text("status_not_checked", "en") == "Not checked"
    assert service_text("status_not_checked", "cs") == "Nezkontrolováno"
    # Unknown languages fall back to English.
    assert service_text("status_not_checked", "de") == "Not checked"
    # Unknown keys resolve to empty rather than leaking the key into the UI.
    assert service_text("no_such_key", "cs") == ""


def test_normalize_language() -> None:
    assert normalize_language("cs") == "cs"
    assert normalize_language("cs-CZ") == "cs"
    assert normalize_language("en") == "en"
    assert normalize_language("pt-BR") == "en"


def test_placeholder_templates_keep_their_tokens_in_both_languages() -> None:
    for key in ("setup_config_errors", "setup_config_valid_with_warnings", "setup_folders_created", "setup_ai_configured_model"):
        entry = SERVICE_STRINGS[key]
        for language in ("en", "cs"):
            rendered = entry[language]
            assert "{" in rendered, f"{key}/{language} lost its placeholder"


def test_setup_service_checks_are_localized(tmp_path, monkeypatch) -> None:
    from coinductor.setup_service import SetupService

    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.toml"
    config.write_text(
        """
[app]
mode = "DRY_RUN"
mock_data = true
database_path = "work/trading_agent.sqlite3"
reports_dir = "outputs/reports"

[strategy]
allowed_symbols = ["BTCUSDC"]
""",
        encoding="utf-8",
    )

    english = SetupService(config, tmp_path / ".env", language="en").inspect()
    czech = SetupService(config, tmp_path / ".env", language="cs").inspect()

    assert any(check["name"] == "Environment file" for check in english.checks)
    assert any(check["name"] == "Soubor s proměnnými prostředí" for check in czech.checks)


def test_user_profile_fields_are_localized(tmp_path) -> None:
    from coinductor.user_profile_service import UserProfileService

    path = tmp_path / "user_profile.toml"
    UserProfileService(path).save_safe_default("EXISTING_PORTFOLIO")

    english = UserProfileService(path, language="en").inspect()
    czech = UserProfileService(path, language="cs").inspect()

    assert english.fields[0]["name"] == "Exchange"
    assert czech.fields[0]["name"] == "Burza"
    assert czech.fields[0]["detail"] == "Kde bude portfolio spravováno."
    # Enum-like values stay untranslated so backend comparisons keep working.
    assert english.fields[0]["value"] == czech.fields[0]["value"]


def test_safety_checks_and_stage_detail_are_localized(tmp_path) -> None:
    from coinductor.safety_service import SafetyService
    from trading_agent.safety_state import SafetyState, SafetyStateStore

    path = tmp_path / "app_safety_state.toml"
    SafetyStateStore(path).save(SafetyState(stage="PREVIEW_ONLY", detail="stored English detail"))

    english = SafetyService(path, language="en").inspect()
    czech = SafetyService(path, language="cs").inspect()

    assert english.checks[0]["name"] == "Orders"
    assert czech.checks[0]["name"] == "Příkazy"
    # Stage detail is resolved from the stage, not the persisted English text,
    # so switching language re-renders it.
    assert "stored English detail" not in czech.detail
    assert "zamčená" in czech.detail


def test_connection_check_messages_are_localized(tmp_path) -> None:
    from coinductor.connection_check import ConnectionCheckService

    missing = tmp_path / "nope.toml"
    english = ConnectionCheckService(missing, tmp_path / ".env", language="en").check_binance_read_only()
    czech = ConnectionCheckService(missing, tmp_path / ".env", language="cs").check_binance_read_only()

    assert english.detail.startswith("Missing config:")
    assert czech.detail.startswith("Chybí konfigurace:")
    assert str(missing) in czech.detail


def test_safety_confirmation_phrases_are_never_translated() -> None:
    from coinductor.service_strings import SERVICE_STRINGS

    # These are compared verbatim by safety_service; they must not appear as
    # translatable strings.
    for phrase in ("Enable mainnet preview", "Arm guarded actions", "Enable guarded live submit"):
        for entry in SERVICE_STRINGS.values():
            assert entry["cs"] != phrase


def test_local_data_reset_groups_are_localized_but_codes_are_not(tmp_path) -> None:
    from coinductor.local_data_reset import LocalDataResetService

    english = LocalDataResetService(tmp_path, language="en").preview()
    czech = LocalDataResetService(tmp_path, language="cs").preview()

    assert english.items[0]["name"] == "Onboarding profile"
    assert czech.items[0]["name"] == "Onboarding profil"
    # Group codes are passed back to executeLocalDataReset, so they stay stable.
    assert [item["code"] for item in english.items] == [item["code"] for item in czech.items]


def test_ai_provider_context_sections_are_localized() -> None:
    from coinductor.ai_provider import AiProviderService

    english = AiProviderService(language="en")._context_sections()
    czech = AiProviderService(language="cs")._context_sections()

    assert english[0]["name"] == "Safety contract"
    assert czech[0]["name"] == "Bezpečnostní kontrakt"
    assert len(english) == len(czech) == 4
