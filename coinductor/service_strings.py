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
    "hardware_scanning": {
        "en": "Reading RAM and GPU from OS tools...",
        "cs": "Zjišťuji RAM a GPU ze systémových nástrojů...",
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
    # --- safety stage labels (display only; the stage identifier is separate) ---
    "safety_stage_label_SETUP": {"en": "Setup", "cs": "Nastavení"},
    "safety_stage_label_READ_ONLY_CONNECTED": {"en": "Read Only Connected", "cs": "Připojeno read-only"},
    "safety_stage_label_TESTNET_READY": {"en": "Testnet Ready", "cs": "Testnet připraven"},
    "safety_stage_label_PREVIEW_ONLY": {"en": "Preview Only", "cs": "Pouze náhled"},
    "safety_stage_label_ARMED": {"en": "Armed", "cs": "Připraveno"},
    "safety_stage_label_LIVE_ENABLED": {"en": "Live Enabled", "cs": "Živě povoleno"},
    # --- safety service checks ---
    "safety_check_orders": {"en": "Orders", "cs": "Příkazy"},
    "safety_check_orders_locked": {
        "en": "Live order submit is disabled",
        "cs": "Odesílání živých příkazů je vypnuté",
    },
    "safety_check_orders_recommend_only": {
        "en": "Locked by your profile: automation level is Recommendations only",
        "cs": "Uzamčeno vaším profilem: úroveň automatizace je Pouze doporučení",
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
    "safety_stage_detail_recommend_only": {
        "en": "The stage would allow guarded live submissions, but your profile keeps Coinductor on recommendations only, so nothing can be submitted.",
        "cs": "Stupeň by zabezpečená živá odeslání dovolil, ale váš profil drží Coinductor na pouhých doporučeních, takže nelze nic odeslat.",
    },
    # --- connection checks ---
    "conn_missing_config": {"en": "Missing config: {path}", "cs": "Chybí konfigurace: {path}"},
    "conn_missing_env_readonly": {
        "en": "Binance read-only keys are not configured",
        "cs": "Read-only klíče pro Binance nejsou nastaveny",
    },
    "conn_missing_env_live": {
        "en": "Binance live trading keys are not configured",
        "cs": "Klíče pro živé obchodování na Binance nejsou nastaveny",
    },
    "conn_missing_env_testnet": {
        "en": "Binance Spot Testnet keys are not configured",
        "cs": "Klíče pro Binance Spot Testnet nejsou nastaveny",
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
    "reset_group_config": {"en": "Configuration", "cs": "Konfigurace"},
    "reset_group_config_detail": {
        "en": "Your config.toml - risk limits, allowed symbols, strategy settings. Deleting it means the next start writes fresh defaults.",
        "cs": "Váš config.toml - limity rizika, povolené symboly, nastavení strategií. Po smazání se při dalším startu zapíšou výchozí hodnoty.",
    },
    "reset_group_credentials": {"en": "API keys", "cs": "API klíče"},
    "reset_group_credentials_detail": {
        "en": "Your Binance and AI keys, removed from the operating system's credential store and from any local .env file. Choose this when you are removing Coinductor for good - the uninstaller does not touch your keys.",
        "cs": "Vaše klíče k Binance a AI se odstraní ze systémového úložiště pověření i z případného lokálního souboru .env. Zvolte, když Coinductor odstraňujete natrvalo - odinstalátor se vašich klíčů nedotkne.",
    },
    "reset_keychain_entry": {
        "en": "{count} key(s) from the OS credential store",
        "cs": "{count} klíč(ů) ze systémového úložiště pověření",
    },
    # --- readiness steps (step codes and action codes stay identifiers) ---
    "readiness_summary": {
        "en": "{ready}/{total} readiness step(s) ready",
        "cs": "připraveno kroků: {ready}/{total}",
    },
    "readiness_all_satisfied": {
        "en": "All personal-stage readiness gates are satisfied.",
        "cs": "Všechny brány připravenosti osobní fáze jsou splněné.",
    },
    "readiness_step_profile": {"en": "Profile", "cs": "Profil"},
    "readiness_profile_ready_detail": {
        "en": "Onboarding profile is configured.",
        "cs": "Onboarding profil je nastavený.",
    },
    "readiness_profile_ready_action": {
        "en": "Review when your risk preference changes.",
        "cs": "Zkontrolujte při změně tolerance rizika.",
    },
    "readiness_profile_next_detail": {
        "en": "Choose safe defaults or Guide me before relying on recommendations.",
        "cs": "Než se spolehnete na doporučení, zvolte bezpečné výchozí hodnoty nebo Provést průvodcem.",
    },
    "readiness_profile_next_action": {
        "en": "Use Settings > Guide me.",
        "cs": "Použijte Nastavení > Provést průvodcem.",
    },
    "readiness_step_binance": {"en": "Binance read-only", "cs": "Binance read-only"},
    "readiness_binance_ready_detail": {
        "en": "Read-only API connection has been verified.",
        "cs": "Read-only API připojení bylo ověřeno.",
    },
    "readiness_binance_ready_action": {
        "en": "Recheck only after changing API keys.",
        "cs": "Kontrolujte znovu až po změně API klíčů.",
    },
    "readiness_binance_next_detail": {
        "en": "Read-only keys exist but the connection check has not passed in this session.",
        "cs": "Read-only klíče existují, ale kontrola připojení v této relaci neproběhla úspěšně.",
    },
    "readiness_binance_next_action": {
        "en": "Run the Binance read-only check.",
        "cs": "Spusťte read-only kontrolu Binance.",
    },
    "readiness_binance_blocked_detail": {
        "en": "Read-only API keys are required for real portfolio analysis.",
        "cs": "Pro skutečnou analýzu portfolia jsou nutné read-only API klíče.",
    },
    "readiness_binance_blocked_action": {
        "en": "Create read-only Binance keys and save them in the setup wizard.",
        "cs": "Vytvořte read-only klíče Binance a uložte je v průvodci nastavením.",
    },
    "readiness_step_classification": {"en": "Portfolio classification", "cs": "Klasifikace portfolia"},
    "readiness_classification_ready_detail": {
        "en": "{count} tracked asset(s) loaded from the latest real run.",
        "cs": "Načtených sledovaných aktiv z posledního skutečného běhu: {count}.",
    },
    "readiness_classification_ready_action": {
        "en": "Review manual role overrides if needed.",
        "cs": "V případě potřeby zkontrolujte ruční přepsání rolí.",
    },
    "readiness_classification_next_detail": {
        "en": "No real portfolio classification has been loaded yet.",
        "cs": "Zatím nebyla načtena žádná skutečná klasifikace portfolia.",
    },
    "readiness_classification_next_action": {
        "en": "Run initial classification after read-only access is ready.",
        "cs": "Po zprovoznění read-only přístupu spusťte úvodní klasifikaci.",
    },
    "readiness_step_preview": {"en": "Mainnet preview", "cs": "Náhled na mainnetu"},
    "readiness_preview_ready_detail": {
        "en": "Mainnet execution previews may be shown, but orders remain blocked.",
        "cs": "Náhledy provádění na mainnetu se mohou zobrazit, ale příkazy zůstávají blokované.",
    },
    "readiness_preview_ready_action": {
        "en": "Use preview runs before any live action.",
        "cs": "Před jakoukoliv živou akcí použijte náhledové běhy.",
    },
    "readiness_preview_locked_detail": {
        "en": "Safety stage must reach PREVIEW_ONLY before mainnet previews are shown.",
        "cs": "Než se zobrazí náhledy na mainnetu, musí bezpečnostní fáze dosáhnout PREVIEW_ONLY.",
    },
    "readiness_preview_locked_action": {
        "en": "Complete setup and testnet checks first.",
        "cs": "Nejdřív dokončete nastavení a kontroly na testnetu.",
    },
    "readiness_step_live": {"en": "Guarded live execution", "cs": "Zabezpečené živé provádění"},
    "readiness_live_ready_detail": {
        "en": "Guarded live submit workflows may be exposed.",
        "cs": "Zabezpečené postupy živého odeslání mohou být dostupné.",
    },
    "readiness_live_ready_action": {
        "en": "Keep limits and confirmations enabled.",
        "cs": "Ponechte limity a potvrzení zapnuté.",
    },
    "readiness_live_locked_detail": {
        "en": "Live submit stays locked until explicit safety stage promotion.",
        "cs": "Živé odeslání zůstává zamčené až do výslovného posunu bezpečnostní fáze.",
    },
    "readiness_live_locked_action": {
        "en": "Do not unlock before repeated preview/testnet confidence.",
        "cs": "Neodemykejte dřív, než budete opakovaně jistí náhledy a testnetem.",
    },
    "readiness_action_guide_me": {"en": "Guide me", "cs": "Provést průvodcem"},
    "readiness_action_check_binance": {"en": "Run read-only check", "cs": "Spustit read-only kontrolu"},
    "readiness_action_add_keys": {"en": "Add API keys first", "cs": "Nejdřív přidejte API klíče"},
    "readiness_action_run_classification": {"en": "Run classification", "cs": "Spustit klasifikaci"},
    "readiness_action_review_portfolio": {"en": "Review portfolio roles", "cs": "Zkontrolovat role v portfoliu"},
    "readiness_action_none": {"en": "No action needed", "cs": "Není potřeba žádná akce"},
    # --- onboarding exchange steps (wizard summary) ---
    "exch_unsupported_name": {"en": "Exchange", "cs": "Burza"},
    "exch_unsupported_detail": {
        "en": "This exchange is planned but not supported yet.",
        "cs": "Tato burza je plánovaná, ale zatím není podporovaná.",
    },
    "exch_value_manual": {"en": "Manual", "cs": "Ručně"},
    "exch_value_required_later": {"en": "Required later", "cs": "Bude potřeba později"},
    "exch_value_recommended": {"en": "Recommended", "cs": "Doporučeno"},
    "exch_value_assumed": {"en": "Assumed", "cs": "Předpokládá se"},
    "exch_value_next": {"en": "Next", "cs": "Další krok"},
    "exch_create_account": {"en": "Create account", "cs": "Založit účet"},
    "exch_create_account_detail": {
        "en": "Open a Binance account and complete identity verification.",
        "cs": "Založte si účet na Binance a dokončete ověření totožnosti.",
    },
    "exch_deposit": {"en": "Deposit funds", "cs": "Vložit prostředky"},
    "exch_deposit_detail": {
        "en": "Deposit EUR or stablecoins; Coinductor can later recommend a USDC starting plan.",
        "cs": "Vložte EUR nebo stablecoiny; Coinductor může později doporučit počáteční plán v USDC.",
    },
    "exch_api_access": {"en": "API access", "cs": "Přístup k API"},
    "exch_api_access_detail": {
        "en": "Create read-only API keys before portfolio analysis.",
        "cs": "Před analýzou portfolia vytvořte read-only API klíče.",
    },
    "exch_test_first": {"en": "Test first", "cs": "Nejdřív otestovat"},
    "exch_test_first_detail": {
        "en": "Use Testnet or preview-only flows before guarded mainnet actions.",
        "cs": "Před zabezpečenými akcemi na mainnetu použijte Testnet nebo postupy pouze s náhledem.",
    },
    "exch_existing_account": {"en": "Existing account", "cs": "Existující účet"},
    "exch_existing_account_detail": {
        "en": "Account creation is skipped for existing Binance users.",
        "cs": "U stávajících uživatelů Binance se zakládání účtu přeskakuje.",
    },
    "exch_readonly_api": {"en": "Read-only API", "cs": "Read-only API"},
    "exch_readonly_api_detail": {
        "en": "Connect read-only keys so Coinductor can inventory the portfolio.",
        "cs": "Připojte read-only klíče, aby Coinductor mohl provést inventuru portfolia.",
    },
    "exch_classify": {"en": "Classify assets", "cs": "Klasifikovat aktiva"},
    "exch_classify_detail": {
        "en": "Review protected, funding, trading, Grid, and Rebalancing universes.",
        "cs": "Projděte chráněná aktiva, zdroje financování, obchodování, Grid a rebalancování.",
    },
    # --- action plan card buttons (display labels; actionCode is the identifier) ---
    "card_review_trade": {"en": "Review trade", "cs": "Zkontrolovat obchod"},
    "card_why_hold": {"en": "Why HOLD?", "cs": "Proč HOLD?"},
    "card_why_watched": {"en": "Why watched?", "cs": "Proč jen sledovat?"},
    "card_show_blockers": {"en": "Show blockers", "cs": "Zobrazit blokátory"},
    "card_show_manual_setup": {"en": "Show manual setup", "cs": "Zobrazit ruční nastavení"},
    # --- manual HOLD challenge outcome ---
    "challenge_rejected": {
        "en": "Challenge for {symbol} was rejected: the risk engine still returns HOLD. No order was placed.",
        "cs": "Výzva pro {symbol} byla zamítnuta: rizikový engine stále vrací HOLD. Žádný příkaz nebyl zadán.",
    },
    "challenge_accepted": {
        "en": "Challenge for {symbol} passed the checks: the decision is now {decision}. Nothing was submitted - review it and confirm explicitly.",
        "cs": "Výzva pro {symbol} prošla kontrolami: rozhodnutí je nyní {decision}. Nic nebylo odesláno – zkontrolujte a výslovně potvrďte.",
    },
    "assistant_cancelled": {
        "en": "Question stopped. The answer will be discarded when it arrives.",
        "cs": "Dotaz zastaven. Odpověď bude po dokončení zahozena.",
    },
    "style_gates_updated": {
        "en": "{style} style applied to the trend filter: {changes}. Loss limits, stop-loss and confirmations are unchanged.",
        "cs": "Styl {style} promítnut do trendového filtru: {changes}. Limity ztrát, stop-loss a potvrzení zůstávají beze změny.",
    },
    # Filled with the real numbers from risk_profile.STYLE_GATES so the wizard
    # cannot drift from the gates it actually writes into config.toml.
    "style_hint_risk_on": {
        "en": "Considers a buy only while the market regime is RISK_ON and RSI 14 sits between {min} and {max}. Price must still be above the EMA200.",
        "cs": "Nákup zvažuje jen v režimu RISK_ON a při RSI 14 mezi {min} a {max}. Cena musí být stále nad EMA200.",
    },
    "style_hint_any_regime": {
        "en": "Considers a buy in any regime while RSI 14 sits between {min} and {max}. Price must still be above the EMA200.",
        "cs": "Nákup zvažuje v jakémkoli režimu při RSI 14 mezi {min} a {max}. Cena musí být stále nad EMA200.",
    },
    "submit_locked_by_stage": {
        "en": "{action} is locked by the Safety stage. Keep reviewing previews until LIVE_ENABLED is explicit.",
        "cs": "{action} je uzamčeno bezpečnostním stupněm. Zůstaňte u náhledů, dokud výslovně nenastavíte LIVE_ENABLED.",
    },
    "submit_locked_by_profile": {
        "en": "{action} is locked by your profile: automation level is Recommendations only. Switch it to Guarded automation in the setup wizard first.",
        "cs": "{action} je uzamčeno vaším profilem: úroveň automatizace je Pouze doporučení. Nejprve ji v průvodci nastavením přepněte na Zabezpečená automatizace.",
    },
    "diagnostics_saved": {
        "en": "Diagnostics bundle saved and opened: {path}",
        "cs": "Diagnostika uložena a otevřena: {path}",
    },
    "bot_setup_is_manual": {
        "en": "Binance has no public API for creating trading bots, so Coinductor works out the parameters and you enter them on Binance yourself. The full step-by-step is in the detailed report.",
        "cs": "Binance nemá veřejné API pro zakládání obchodních botů, takže Coinductor spočítá parametry a vy je na Binance zadáte sami. Podrobný postup krok za krokem najdete v detailním reportu.",
    },
    # --- Action Plan trade card ---
    "trade_param_action": {"en": "Action", "cs": "Akce"},
    "trade_param_symbol": {"en": "Symbol", "cs": "Symbol"},
    "trade_param_confidence": {"en": "Confidence", "cs": "Jistota"},
    "trade_param_quote": {"en": "Quote amount", "cs": "Objem v kotaci"},
    "trade_param_run_decision": {"en": "Run decision", "cs": "Rozhodnutí běhu"},
    # --- Privacy & data (Settings) ---
    "privacy_binance_name": {"en": "Binance account data", "cs": "Data účtu Binance"},
    "privacy_binance_value": {"en": "Read when you run checks", "cs": "Čtena při spuštění kontrol"},
    "privacy_binance_detail": {
        "en": "Balances, Earn/Spot positions, order history and strategy status are read to build local reports. Coinductor never requests withdrawal permission.",
        "cs": "Zůstatky, pozice Earn/Spot, historie příkazů a stav strategií se čtou pro sestavení lokálních reportů. Coinductor nikdy nežádá oprávnění k výběru.",
    },
    "privacy_credentials_name": {"en": "API keys", "cs": "API klíče"},
    "privacy_credentials_keychain": {"en": "Windows Credential Manager", "cs": "Správce pověření Windows"},
    "privacy_credentials_keychain_detail": {
        "en": "Your Binance and AI keys are held by the operating system's credential store, not in a plaintext file. Coinductor reads them at startup and never writes them into reports, logs or the database.",
        "cs": "Klíče k Binance a AI drží úložiště pověření operačního systému, ne soubor v čitelné podobě. Coinductor je načte při startu a nikdy je nezapisuje do reportů, logů ani databáze.",
    },
    "privacy_credentials_envfile": {"en": "Local .env file", "cs": "Lokální soubor .env"},
    "privacy_credentials_envfile_detail": {
        "en": "No OS credential store is available on this system, so keys fall back to a plaintext .env file in {folder}. Protect that folder accordingly.",
        "cs": "Na tomto systému není dostupné úložiště pověření, klíče proto končí v čitelném souboru .env ve složce {folder}. Podle toho tuto složku chraňte.",
    },
    "privacy_local_files_name": {"en": "Local files", "cs": "Lokální soubory"},
    "privacy_local_files_value": {"en": "Stored on this PC", "cs": "Uloženy na tomto počítači"},
    "privacy_local_files_detail": {
        "en": "SQLite state, reports, research notes, safety stage and your onboarding profile stay in {folder} and are never uploaded.",
        "cs": "Stav v SQLite, reporty, výzkumné poznámky, bezpečnostní stupeň a váš profil zůstávají ve složce {folder} a nikam se neodesílají.",
    },
    "privacy_cloud_ai_name": {"en": "Cloud AI", "cs": "Cloudová AI"},
    "privacy_cloud_ai_value": {"en": "Optional", "cs": "Volitelná"},
    "privacy_cloud_ai_detail": {
        "en": "Everything stays local unless you configure a cloud AI provider. If you do, the selected prompt and report context is sent to that provider - nothing else, and never your API keys.",
        "cs": "Bez nastaveného cloudového poskytovatele AI zůstává vše lokální. Pokud jej nastavíte, odešle se mu vybraný dotaz a kontext reportu - nic dalšího, a nikdy vaše API klíče.",
    },
    "privacy_execution_name": {"en": "Execution", "cs": "Provádění"},
    "privacy_execution_value": {"en": "Guarded", "cs": "Zabezpečené"},
    "privacy_execution_detail": {
        "en": "Coinductor cannot withdraw funds, and never submits a live order without the safety stage, your profile and an explicit typed confirmation all allowing it.",
        "cs": "Coinductor neumí vybírat prostředky a nikdy neodešle živý příkaz, dokud to nedovolí bezpečnostní stupeň, váš profil i výslovné napsané potvrzení zároveň.",
    },
    # --- AI provider health check and model discovery ---
    "aiph_missing_config": {"en": "Missing config: {path}", "cs": "Chybí konfigurace: {path}"},
    "aiph_no_base_url": {"en": "{key} is not set.", "cs": "{key} není nastaveno."},
    "aiph_no_model": {"en": "{key} is not set.", "cs": "{key} není nastaveno."},
    "aiph_vision_not_capable": {
        "en": "Configured vision model {model} is not recognized as vision-capable.",
        "cs": "Nastavený vision model {model} není rozpoznán jako model s podporou obrázků.",
    },
    "aiph_endpoint_failed": {
        "en": "AI endpoint check failed: {reason}",
        "cs": "Kontrola AI endpointu selhala: {reason}",
    },
    "aiph_text_model_missing": {
        "en": "Endpoint reachable, but text model {model} was not reported by /models.",
        "cs": "Endpoint je dostupný, ale textový model {model} nebyl v /models nahlášen.",
    },
    "aiph_vision_model_missing": {
        "en": "Text model ready, but vision model {model} was not reported by /models.",
        "cs": "Textový model je připraven, ale vision model {model} nebyl v /models nahlášen.",
    },
    "aiph_vision_ready": {"en": " Vision model ready: {model}.", "cs": " Vision model připraven: {model}."},
    "aiph_vision_absent": {
        "en": " Vision model is optional and not configured.",
        "cs": " Vision model je volitelný a není nastaven.",
    },
    "aiph_ok": {
        "en": "Endpoint reachable; {count} model(s) reported. Text model ready: {model}.{vision}",
        "cs": "Endpoint je dostupný; nahlášeno {count} model(ů). Textový model připraven: {model}.{vision}",
    },
    "aidisc_no_url": {
        "en": "Enter the endpoint URL before detecting models.",
        "cs": "Před detekcí modelů zadejte URL endpointu.",
    },
    "aidisc_unreachable": {
        "en": "Could not reach {url}: {reason}",
        "cs": "Nepodařilo se kontaktovat {url}: {reason}",
    },
    "aidisc_no_models": {
        "en": "{url} responded, but reported no installed models.",
        "cs": "{url} odpovědělo, ale nenahlásilo žádné nainstalované modely.",
    },
    "aidisc_ok": {
        "en": "{count} model(s) reported by {url}.",
        "cs": "{url} nahlásilo {count} model(ů).",
    },
    "spot_trades_locked_by_profile": {
        "en": "Guarded spot trades are switched off in your profile, so Coinductor will not submit this buy. Enable them in the setup wizard if you want it to.",
        "cs": "Zabezpečené spotové obchody máte v profilu vypnuté, takže Coinductor tento nákup neodešle. Pokud chcete, zapněte je v průvodci nastavením.",
    },
    "drawdown_hint": {
        "en": "Pauses trading after a {daily}% loss in a day or {weekly}% in a week. The kill switch, stop-loss and position caps do not move.",
        "cs": "Pozastaví obchodování po ztrátě {daily} % za den nebo {weekly} % za týden. Kill switch, stop-loss a limity pozic se nemění.",
    },
    "drawdown_hint_off": {
        "en": "Off: the wizard leaves the loss limits in config.toml exactly as you set them.",
        "cs": "Vypnuto: průvodce nechá limity ztrát v config.toml přesně tak, jak jste je nastavili.",
    },
    "drawdown_limits_updated": {
        "en": "Drawdown comfort applied to the loss limits: {changes}.",
        "cs": "Tolerance k propadu promítnuta do limitů ztrát: {changes}.",
    },
    "bots_state_enabled": {"en": "enabled", "cs": "zapnuta"},
    "bots_state_disabled": {"en": "disabled", "cs": "vypnuta"},
    "bots_config_updated": {
        "en": "Grid bot recommendations {state}: {changes}.",
        "cs": "Doporučení grid botů {state}: {changes}.",
    },
    "style_hint_shared": {
        "en": "Loss limits, stop-loss, kill switch and confirmations are identical at every level.",
        "cs": "Limity ztrát, stop-loss, kill switch a potvrzení jsou na všech úrovních stejné.",
    },
    # --- credential storage ---
    "creds_stored_keychain": {
        "en": "Stored in the OS keychain, not in a plaintext file.",
        "cs": "Uloženo do systémového úložiště přihlašovacích údajů, ne do souboru v čitelné podobě.",
    },
    "creds_stored_env": {
        "en": "No OS keychain is available, so this was stored in the local .env file.",
        "cs": "Systémové úložiště přihlašovacích údajů není dostupné, uloženo do lokálního souboru .env.",
    },
    "creds_readonly_saved": {
        "en": "Run the read-only check to verify the credentials.",
        "cs": "Spusťte read-only kontrolu pro ověření přihlašovacích údajů.",
    },
    "creds_live_saved": {
        "en": "Credentials changed. Verify live-key permissions again.",
        "cs": "Přihlašovací údaje se změnily. Znovu ověřte oprávnění živého klíče.",
    },
    "creds_testnet_saved": {
        "en": "Run the Testnet check to verify the credentials.",
        "cs": "Spusťte kontrolu Testnetu pro ověření přihlašovacích údajů.",
    },
    "creds_ai_local_saved": {
        "en": "Run the AI provider check to verify the endpoint.",
        "cs": "Spusťte kontrolu poskytovatele AI pro ověření endpointu.",
    },
    "creds_ai_cloud_saved": {
        "en": "Run the AI provider check before using it.",
        "cs": "Před použitím spusťte kontrolu poskytovatele AI.",
    },
    # --- setup service check names ---
    "setup_check_python": {"en": "Python", "cs": "Python"},
    "setup_check_configuration": {"en": "Configuration", "cs": "Konfigurace"},
    "setup_check_credential_store": {"en": "Credential storage", "cs": "Úložiště přihlašovacích údajů"},
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
    "setup_creds_keychain": {
        "en": "OS credential store (keys are not kept in a plaintext file)",
        "cs": "Systémové úložiště pověření (klíče nejsou v čitelném souboru)",
    },
    "setup_creds_envfile": {
        "en": "Local .env file - no OS credential store is available here",
        "cs": "Lokální soubor .env - systémové úložiště pověření zde není dostupné",
    },
    "setup_creds_none": {
        "en": "Not configured yet. Add your keys in the setup wizard.",
        "cs": "Zatím nenastaveno. Klíče přidejte v průvodci nastavením.",
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
