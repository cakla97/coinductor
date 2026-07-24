"""Translations for user-facing strings produced by backend services.

The QML chrome is translated via ``ui_strings``; this module covers the text
that services and the controller generate (status details, check names, context
sections). Services take a ``language`` and resolve through :func:`service_text`
so the controller can re-resolve them when the user switches language.

Identifiers the user must match literally - environment variable names, file
paths, config keys, Binance/Ollama labels - stay in English in both variants.
"""

from __future__ import annotations


SERVICE_STRINGS: dict[str, dict[str, str]] = {
    # --- idle status defaults (controller) ---
    "status_not_checked": {
        "en": "Not checked",
        "cs": "Nezkontrolováno",
    },
    "connection_idle_detail": {
        "en": "Run the read-only check from Settings before live analysis.",
        "cs": "Před živou analýzou spusťte read-only kontrolu v Nastavení.",
    },
    "live_trading_idle_detail": {
        "en": "Verify live-key permissions before arming guarded execution.",
        "cs": "Než povolíte zabezpečené provádění, ověřte oprávnění živého klíče.",
    },
    "testnet_idle_detail": {
        "en": "Optional but recommended: verify Spot Testnet access before any real mainnet action.",
        "cs": "Volitelné, ale doporučené: před jakoukoliv skutečnou mainnet akcí ověřte přístup ke Spot Testnetu.",
    },
    "ai_provider_idle_detail": {
        "en": "Run an AI provider check after configuring LLM_BASE_URL and LLM_MODEL.",
        "cs": "Po nastavení LLM_BASE_URL a LLM_MODEL spusťte kontrolu poskytovatele AI.",
    },
    "hardware_not_scanned": {
        "en": "Hardware has not been scanned yet.",
        "cs": "Hardware zatím nebyl naskenován.",
    },
    "ai_discovery_idle_detail": {
        "en": "Detect which models the endpoint currently reports as installed.",
        "cs": "Zjistěte, které modely endpoint aktuálně hlásí jako nainstalované.",
    },
    # --- AI provider context sections ---
    "ai_context_safety_name": {
        "en": "Safety contract",
        "cs": "Bezpečnostní kontrakt",
    },
    "ai_context_safety_detail": {
        "en": "AI can explain, summarize, rank bounded options, and prepare intents; deterministic code owns execution limits.",
        "cs": "AI umí vysvětlovat, shrnovat, řadit ohraničené možnosti a připravovat záměry; limity provádění vlastní deterministický kód.",
    },
    "ai_context_portfolio_name": {
        "en": "Portfolio context",
        "cs": "Kontext portfolia",
    },
    "ai_context_portfolio_detail": {
        "en": "Assistant context includes latest real run, portfolio roles, strategy recommendations, and local report paths.",
        "cs": "Kontext asistenta zahrnuje poslední skutečný běh, role v portfoliu, doporučení strategií a cesty k lokálním reportům.",
    },
    "ai_context_privacy_name": {
        "en": "Privacy boundary",
        "cs": "Hranice soukromí",
    },
    "ai_context_privacy_detail": {
        "en": "Local providers keep prompts on this machine; cloud providers may receive selected report and portfolio context.",
        "cs": "Lokální poskytovatelé nechávají dotazy na tomto počítači; cloudoví poskytovatelé mohou dostat vybraný report a kontext portfolia.",
    },
    "ai_context_action_name": {
        "en": "Action boundary",
        "cs": "Hranice akcí",
    },
    "ai_context_action_detail": {
        "en": "Changing policy, funding, or execution state will require structured intents, validation, and confirmation.",
        "cs": "Změna politiky, financování nebo stavu provádění vyžaduje strukturované záměry, validaci a potvrzení.",
    },
    # --- setup service check names ---
    "setup_check_python": {"en": "Python", "cs": "Python"},
    "setup_check_configuration": {"en": "Configuration", "cs": "Konfigurace"},
    "setup_check_env_file": {"en": "Environment file", "cs": "Soubor s proměnnými prostředí"},
    "setup_check_binance_readonly": {"en": "Binance read-only", "cs": "Binance read-only"},
    "setup_check_binance_testnet": {"en": "Binance Spot Testnet", "cs": "Binance Spot Testnet"},
    "setup_check_binance_live": {"en": "Binance live trading", "cs": "Binance živé obchodování"},
    "setup_check_local_ai": {"en": "Local AI endpoint", "cs": "Lokální AI endpoint"},
    "setup_check_data_folders": {"en": "Local data folders", "cs": "Lokální datové složky"},
    # --- setup service groups ---
    "setup_group_runtime": {"en": "Runtime", "cs": "Běhové prostředí"},
    "setup_group_binance": {"en": "Binance", "cs": "Binance"},
    "setup_group_ai": {"en": "AI", "cs": "AI"},
    "setup_group_storage": {"en": "Storage", "cs": "Úložiště"},
    # --- setup service details ---
    "setup_config_valid": {"en": "Valid", "cs": "Platná"},
    # "label: count" wording in Czech avoids plural agreement (1 chyba / 2-4 chyby / 5+ chyb).
    "setup_config_errors": {
        "en": "{errors} error(s), {warnings} warning(s)",
        "cs": "chyb: {errors}, varování: {warnings}",
    },
    "setup_config_valid_with_warnings": {
        "en": "Valid with {warnings} warning(s)",
        "cs": "Platná, varování: {warnings}",
    },
    "setup_folders_created": {
        "en": "Created on first run: {paths}",
        "cs": "Vytvoří se při prvním spuštění: {paths}",
    },
    "setup_ai_configured_model": {
        "en": "Configured model: {model}",
        "cs": "Nastavený model: {model}",
    },
    "setup_env_present": {"en": "Present", "cs": "Přítomen"},
    "setup_env_missing": {
        "en": "Create .env before connecting services",
        "cs": "Před připojením služeb vytvořte .env",
    },
    "setup_credentials_configured": {"en": "Configured", "cs": "Nastaveno"},
    "setup_binance_readonly_missing": {
        "en": "Required for real portfolio analysis",
        "cs": "Nutné pro skutečnou analýzu portfolia",
    },
    "setup_binance_testnet_missing": {
        "en": "Recommended before mainnet",
        "cs": "Doporučené před mainnetem",
    },
    "setup_binance_live_missing": {
        "en": "Optional; guarded execution only",
        "cs": "Volitelné; pouze pro zabezpečené provádění",
    },
    "setup_ai_missing": {
        "en": "Optional; offline help remains available",
        "cs": "Volitelné; offline nápověda zůstává dostupná",
    },
    "setup_folders_ready": {"en": "Ready", "cs": "Připraveno"},
}


def service_text(key: str, language: str = "en") -> str:
    """Resolve a service string, falling back to English for unknown languages."""
    entry = SERVICE_STRINGS.get(key)
    if entry is None:
        return ""
    if str(language).strip().lower().startswith("cs"):
        return entry.get("cs") or entry["en"]
    return entry["en"]


def normalize_language(language: str) -> str:
    return "cs" if str(language).strip().lower().startswith("cs") else "en"
