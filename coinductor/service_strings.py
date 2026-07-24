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
    # --- check status values ---
    # These are display labels only. The controller keeps the underlying status
    # in English because guarded-action gates compare it verbatim (for example
    # `_live_trading_check_status == "Verified"`), so translation happens at the
    # display boundary and never touches the compared value.
    "status_not_checked": {
        "en": "Not checked",
        "cs": "Nezkontrolováno",
    },
    "status_checking": {"en": "Checking", "cs": "Kontroluji"},
    "status_connected": {"en": "Connected", "cs": "Připojeno"},
    "status_verified": {"en": "Verified", "cs": "Ověřeno"},
    "status_blocked": {"en": "Blocked", "cs": "Zablokováno"},
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
    # --- AI provider checks (env var names stay literal) ---
    "ai_check_configuration": {"en": "Configuration", "cs": "Konfigurace"},
    "ai_check_provider": {"en": "Provider", "cs": "Poskytovatel"},
    "ai_check_endpoint": {"en": "Endpoint", "cs": "Endpoint"},
    "ai_check_model": {"en": "Model", "cs": "Model"},
    "ai_check_vision_model": {"en": "Vision model", "cs": "Vision model"},
    "ai_check_api_key": {"en": "API key", "cs": "API klíč"},
    "ai_check_privacy_mode": {"en": "Privacy mode", "cs": "Režim soukromí"},
    "ai_group_ai": {"en": "AI", "cs": "AI"},
    "ai_group_privacy": {"en": "Privacy", "cs": "Soukromí"},
    "ai_config_missing_summary": {
        "en": "AI settings are unavailable because config is missing.",
        "cs": "Nastavení AI není dostupné, protože chybí konfigurace.",
    },
    "ai_set_env": {"en": "Set {key}", "cs": "Nastavte {key}"},
    "ai_vision_not_recognized": {
        "en": "{model} is not recognized as vision-capable",
        "cs": "{model} není rozpoznán jako model s podporou obrázků",
    },
    "ai_vision_optional": {
        "en": "Optional; set {key} to enable image input without replacing the text model",
        "cs": "Volitelné; nastavte {key} pro vstup obrázků bez nahrazení textového modelu",
    },
    "ai_api_key_configured": {"en": "Configured", "cs": "Nastaven"},
    "ai_api_key_optional": {
        "en": "Optional for local providers; set {key} for cloud providers",
        "cs": "Volitelné u lokálních poskytovatelů; pro cloudové nastavte {key}",
    },
    "ai_privacy_local": {"en": "Local endpoint", "cs": "Lokální endpoint"},
    "ai_privacy_external": {
        "en": "External/cloud endpoint or not configured",
        "cs": "Externí/cloudový endpoint nebo nenastaveno",
    },
    "ai_summary": {
        "en": "{provider}: text {model}, vision {vision} at {endpoint}",
        "cs": "{provider}: text {model}, vision {vision} na {endpoint}",
    },
    "ai_summary_not_set": {"en": "not set", "cs": "nenastaveno"},
    "ai_summary_not_configured": {"en": "not configured", "cs": "nenastaveno"},
    "ai_summary_no_endpoint": {"en": "no endpoint", "cs": "bez endpointu"},
    # --- onboarding profile fields (values stay as backend enums) ---
    "profile_field_exchange": {"en": "Exchange", "cs": "Burza"},
    "profile_field_exchange_detail": {
        "en": "Where the portfolio will be managed.",
        "cs": "Kde bude portfolio spravováno.",
    },
    "profile_field_locale": {"en": "Locale", "cs": "Lokalizace"},
    "profile_field_path": {"en": "Path", "cs": "Cesta"},
    "profile_field_path_detail": {
        "en": "Existing portfolio or first portfolio.",
        "cs": "Existující portfolio, nebo první portfolio.",
    },
    "profile_field_setup": {"en": "Setup", "cs": "Nastavení"},
    "profile_field_setup_detail": {
        "en": "Safe defaults, guided, or advanced.",
        "cs": "Bezpečné výchozí hodnoty, průvodce, nebo pokročilé.",
    },
    "profile_field_style": {"en": "Style", "cs": "Styl"},
    "profile_field_style_detail": {
        "en": "Portfolio management intensity.",
        "cs": "Intenzita správy portfolia.",
    },
    "profile_field_automation": {"en": "Automation", "cs": "Automatizace"},
    "profile_field_automation_detail": {
        "en": "How much the app may automate.",
        "cs": "Jak moc smí aplikace automatizovat.",
    },
    "profile_field_cadence": {"en": "Run cadence", "cs": "Frekvence běhů"},
    "profile_field_cadence_detail": {
        "en": "Suggested review rhythm.",
        "cs": "Doporučený rytmus kontrol.",
    },
    "profile_field_fiat": {"en": "Fiat funding", "cs": "Fiat financování"},
    "profile_field_funding_currency": {"en": "Funding currency", "cs": "Měna financování"},
    "profile_field_funding_currency_detail": {
        "en": "Internal strategy funding and reporting currency.",
        "cs": "Interní měna pro financování strategie a reporty.",
    },
    "profile_field_budget": {"en": "Starting budget", "cs": "Počáteční rozpočet"},
    "profile_field_budget_detail": {
        "en": "Used by first portfolio planner.",
        "cs": "Používá plánovač prvního portfolia.",
    },
    "profile_field_reserve": {"en": "Reserve", "cs": "Rezerva"},
    "profile_field_reserve_detail": {
        "en": "Capital kept outside active strategy use.",
        "cs": "Kapitál držený mimo aktivní použití strategií.",
    },
    "profile_field_drawdown": {"en": "Drawdown comfort", "cs": "Tolerance poklesu"},
    "profile_field_drawdown_detail": {
        "en": "Used for conservative strategy sizing.",
        "cs": "Používá se pro konzervativní velikost pozic.",
    },
    "profile_field_spot_trades": {"en": "Spot trades", "cs": "Spotové obchody"},
    "profile_field_spot_trades_detail": {
        "en": "Live execution still needs guard approval.",
        "cs": "Živé provádění stále vyžaduje schválení bezpečnostní bránou.",
    },
    "profile_field_grid": {"en": "Grid", "cs": "Grid"},
    "profile_field_grid_detail": {
        "en": "Manual Binance creation remains required.",
        "cs": "Ruční vytvoření v Binance je stále nutné.",
    },
    "profile_field_rebalancing": {"en": "Rebalancing", "cs": "Rebalancování"},
    "profile_field_rebalancing_detail": {
        "en": "Only when minimum capital and limits pass.",
        "cs": "Pouze když projde minimální kapitál a limity.",
    },
    "profile_value_allowed": {"en": "Allowed", "cs": "Povoleno"},
    "profile_value_disabled": {"en": "Disabled", "cs": "Vypnuto"},
    "profile_value_enabled": {"en": "Enabled", "cs": "Zapnuto"},
    "profile_value_auto": {"en": "Auto", "cs": "Automaticky"},
    # --- safety service checks ---
    "safety_check_orders": {"en": "Orders", "cs": "Příkazy"},
    "safety_check_orders_locked": {
        "en": "Live order submit is disabled",
        "cs": "Odesílání živých příkazů je vypnuté",
    },
    "safety_check_orders_available": {
        "en": "Guarded live submit workflows may be shown",
        "cs": "Zabezpečené postupy živého odeslání se mohou zobrazit",
    },
    "safety_check_preview": {"en": "Mainnet preview", "cs": "Náhled na mainnetu"},
    "safety_check_preview_locked": {
        "en": "Preview remains hidden until PREVIEW_ONLY",
        "cs": "Náhled zůstává skrytý až do fáze PREVIEW_ONLY",
    },
    "safety_check_preview_available": {
        "en": "Preview-only mainnet checks are available",
        "cs": "Mainnet kontroly pouze pro náhled jsou dostupné",
    },
    "safety_check_onboarding": {"en": "Onboarding", "cs": "Prvotní nastavení"},
    "safety_check_onboarding_detail": {
        "en": "Wizard steps cannot place orders or change exchange state.",
        "cs": "Kroky průvodce nemohou zadat příkaz ani změnit stav na burze.",
    },
    # Stage descriptions are resolved from the stage at read time, so switching
    # language re-renders them instead of showing the language used at transition.
    "safety_stage_detail_SETUP": {
        "en": "Local profile and configuration only; no exchange-changing actions are available.",
        "cs": "Pouze lokální profil a konfigurace; žádné akce měnící stav na burze nejsou dostupné.",
    },
    "safety_stage_detail_PREVIEW_ONLY": {
        "en": "Mainnet previews are available; all live submissions remain locked.",
        "cs": "Náhledy na mainnetu jsou dostupné; veškerá živá odeslání zůstávají zamčená.",
    },
    "safety_stage_detail_ARMED": {
        "en": "Live credentials are verified and guarded actions are armed; final live submission remains locked.",
        "cs": "Živé přihlašovací údaje jsou ověřené a zabezpečené akce připravené; finální živé odeslání zůstává zamčené.",
    },
    "safety_stage_detail_LIVE_ENABLED": {
        "en": "Guarded live submissions are enabled with fresh validation and explicit per-action confirmation.",
        "cs": "Zabezpečená živá odeslání jsou povolena s čerstvou validací a výslovným potvrzením u každé akce.",
    },
    # --- connection checks ---
    "conn_missing_config": {"en": "Missing config: {path}", "cs": "Chybí konfigurace: {path}"},
    "conn_missing_env_readonly": {
        "en": "Missing .env with Binance read-only keys",
        "cs": "Chybí .env s read-only klíči pro Binance",
    },
    "conn_missing_env_live": {
        "en": "Missing .env with Binance live trading keys",
        "cs": "Chybí .env s klíči pro živé obchodování na Binance",
    },
    "conn_missing_env_testnet": {
        "en": "Missing .env with Binance Spot Testnet keys",
        "cs": "Chybí .env s klíči pro Binance Spot Testnet",
    },
    "conn_readonly_failed": {
        "en": "Connection check failed: {error}",
        "cs": "Kontrola připojení selhala: {error}",
    },
    "conn_live_failed": {
        "en": "Live trading check failed: {error}",
        "cs": "Kontrola živého obchodování selhala: {error}",
    },
    "conn_testnet_failed": {
        "en": "Testnet check failed: {error}",
        "cs": "Kontrola Testnetu selhala: {error}",
    },
    "conn_readonly_ok": {
        "en": "Read-only API key is reachable and trading permissions are disabled",
        "cs": "Read-only API klíč je dostupný a obchodní oprávnění jsou vypnutá",
    },
    "conn_live_ok": {
        "en": "Live key is reachable: Reading + Spot trading enabled, trusted-IP restriction active, forbidden permissions disabled",
        "cs": "Živý klíč je dostupný: Reading + Spot trading zapnuté, omezení na důvěryhodné IP aktivní, zakázaná oprávnění vypnutá",
    },
    "conn_testnet_ok": {
        "en": "Spot Testnet key is reachable. Virtual funds are ready for safe testing.",
        "cs": "Klíč pro Spot Testnet je dostupný. Virtuální prostředky jsou připravené k bezpečnému testování.",
    },
    # --- local data reset (group codes stay as backend identifiers) ---
    "reset_summary_choose": {
        "en": "Choose specific local data groups to remove, or use Delete everything to select the full local reset preview.",
        "cs": "Vyberte konkrétní skupiny lokálních dat k odstranění, nebo použijte Smazat vše pro náhled úplného lokálního resetu.",
    },
    "reset_summary_nothing": {
        "en": "No selected local data group had anything to remove.",
        "cs": "Žádná z vybraných skupin lokálních dat neobsahovala nic k odstranění.",
    },
    "reset_summary_removed": {"en": "Removed: {paths}.", "cs": "Odstraněno: {paths}."},
    "reset_summary_blocked": {"en": "Could not remove: {paths}.", "cs": "Nepodařilo se odstranit: {paths}."},
    "reset_group_profile": {"en": "Onboarding profile", "cs": "Onboarding profil"},
    "reset_group_profile_detail": {
        "en": "Region, language, risk preference, automation preference, budget, planner settings, and first-use tour status.",
        "cs": "Region, jazyk, tolerance rizika, míra automatizace, rozpočet, nastavení plánovače a stav úvodní prohlídky.",
    },
    "reset_group_policy": {"en": "Policy and strategy settings", "cs": "Nastavení politik a strategií"},
    "reset_group_policy_detail": {
        "en": "Manual asset role overrides, safety stage, active strategy registry, Grid/Rebalancing local registries.",
        "cs": "Ruční přepsání rolí aktiv, bezpečnostní fáze, registr aktivních strategií, lokální registry Grid/Rebalancování.",
    },
    "reset_group_database": {"en": "Local database and run history", "cs": "Lokální databáze a historie běhů"},
    "reset_group_database_detail": {
        "en": "SQLite run history, portfolio snapshots, shadow signals, and local state derived from previous runs.",
        "cs": "SQLite historie běhů, snímky portfolia, shadow signály a lokální stav odvozený z předchozích běhů.",
    },
    "reset_group_reports": {"en": "Reports", "cs": "Reporty"},
    "reset_group_reports_detail": {
        "en": "Generated run reports and human-readable summaries.",
        "cs": "Vygenerované reporty z běhů a čitelná shrnutí.",
    },
    "reset_group_research": {"en": "Research notes and requests", "cs": "Výzkumné poznámky a požadavky"},
    "reset_group_research_detail": {
        "en": "Manual research notes, Binance Skills prompts, generated research requests, and optional AI context files.",
        "cs": "Ruční výzkumné poznámky, prompty Binance Skills, vygenerované výzkumné požadavky a volitelné soubory s AI kontextem.",
    },
    "reset_group_ai_chat": {"en": "AI chat history", "cs": "Historie AI chatu"},
    "reset_group_ai_chat_detail": {
        "en": "Locally stored AI Assistant conversations and screenshots pasted from the clipboard. The newest 20 chats and up to 40 pasted images are retained until this data group is removed.",
        "cs": "Lokálně uložené konverzace s AI Assistant a snímky obrazovky vložené ze schránky. Do odstranění této skupiny se uchovává 20 nejnovějších chatů a až 40 vložených obrázků.",
    },
    "reset_group_env": {"en": "API keys and local environment", "cs": "API klíče a lokální prostředí"},
    "reset_group_env_detail": {
        "en": ".env file with Binance keys and optional AI provider settings. Only delete this when you want a completely clean app setup.",
        "cs": "Soubor .env s klíči k Binance a volitelným nastavením poskytovatele AI. Mažte jej jen tehdy, když chcete úplně čisté nastavení aplikace.",
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
