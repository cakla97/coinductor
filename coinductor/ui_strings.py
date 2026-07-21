from __future__ import annotations

SUPPORTED_LANGUAGES = ("en", "cs")
DEFAULT_LANGUAGE = "en"

WIZARD_STRINGS: dict[str, dict[str, str]] = {
    "welcome_title": {
        "en": "Welcome to Coinductor",
        "cs": "Vítejte v Coinductoru",
    },
    "welcome_subtitle": {
        "en": "A short setup wizard prepares your local profile before the main portfolio manager opens.",
        "cs": "Krátký průvodce nastavením připraví váš lokální profil, než se otevře hlavní správce portfolia.",
    },
    "enter_app_button": {
        "en": "Enter app",
        "cs": "Vstoupit do aplikace",
    },
    "local_first_banner": {
        "en": "Nothing in this wizard places orders or changes exchange settings. It only creates a local preference profile and shows what still needs to be verified.",
        "cs": "Nic v tomto průvodci nezadává příkazy ani nemění nastavení burzy. Vytváří pouze lokální profil preferencí a ukazuje, co ještě zbývá ověřit.",
    },
    "local_first_badge": {
        "en": "Local-first",
        "cs": "Lokální data",
    },
    "setup_steps_title": {
        "en": "Setup steps",
        "cs": "Kroky nastavení",
    },
    "setup_steps_hint": {
        "en": "The wizard changes only local Coinductor settings until you explicitly run checks or analysis.",
        "cs": "Průvodce mění pouze lokální nastavení Coinductoru, dokud sami nespustíte kontrolu nebo analýzu.",
    },
    "step_name_exchange": {"en": "Exchange", "cs": "Burza"},
    "step_name_portfolio": {"en": "Portfolio", "cs": "Portfolio"},
    "step_name_profile": {"en": "Profile", "cs": "Profil"},
    "step_name_ai": {"en": "AI", "cs": "AI"},
    "step_name_binance_api": {"en": "Binance API", "cs": "Binance API"},
    "step_name_review": {"en": "Review", "cs": "Shrnutí"},
    "step1_title": {
        "en": "1. Choose exchange",
        "cs": "1. Vyberte burzu",
    },
    "step1_description": {
        "en": "Coinductor needs to know where the portfolio lives before it can explain API permissions, funding, and safety checks.",
        "cs": "Coinductor potřebuje vědět, kde se portfolio nachází, než dokáže vysvětlit oprávnění API, financování a bezpečnostní kontroly.",
    },
    "step1_binance_supported": {
        "en": "Binance is supported in this build",
        "cs": "Binance je v této verzi podporována",
    },
    "step1_coinbase_planned": {
        "en": "Coinbase is planned, not available yet",
        "cs": "Coinbase je plánována, zatím není dostupná",
    },
    "step1_binance_detail": {
        "en": "The wizard will guide you through Binance read-only API setup, optional AI configuration, and a safe local profile. Guarded live trading uses a separate key and separate confirmations, and stays locked until you explicitly progress the safety stage later in the app.",
        "cs": "Průvodce vás provede nastavením read-only API pro Binance, volitelnou konfigurací AI a bezpečným lokálním profilem. Zabezpečený live obchod používá samostatný klíč a samostatná potvrzení a zůstává uzamčený, dokud sami později v aplikaci neposunete bezpečnostní stupeň.",
    },
    "step1_coinbase_detail": {
        "en": "The app is being designed so future exchanges can be added behind the same safety contract. Continue with Binance for now.",
        "cs": "Aplikace je navržena tak, aby bylo možné v budoucnu přidat další burzy za stejných bezpečnostních podmínek. Prozatím pokračujte s Binance.",
    },
    "step1_manual_setup_note": {
        "en": "Manual setup covered later: account access, API key permissions, IP restrictions, read-only checks, and local privacy boundaries.",
        "cs": "Ruční nastavení bude vysvětleno později: přístup k účtu, oprávnění API klíče, omezení IP adresy, read-only kontroly a hranice lokálního soukromí.",
    },
    "step1_first_portfolio_selected": {
        "en": "First portfolio path selected",
        "cs": "Zvolena cesta prvního portfolia",
    },
    "step1_existing_selected": {
        "en": "Existing portfolio path selected",
        "cs": "Zvolena cesta existujícího portfolia",
    },
    "step1_first_portfolio_focus": {
        "en": "The rest of the wizard will focus on a starting budget, reserve, initial basket, deposit guidance, and safe manual setup before any automation.",
        "cs": "Zbytek průvodce se zaměří na počáteční rozpočet, rezervu, počáteční košík, pokyny k vkladu a bezpečné ruční nastavení před jakoukoli automatizací.",
    },
    "step1_existing_focus": {
        "en": "The rest of the wizard will focus on read-only Binance access, portfolio inventory, asset classification, and guarded recommendations for assets you already hold.",
        "cs": "Zbytek průvodce se zaměří na read-only přístup k Binance, přehled portfolia, klasifikaci aktiv a zabezpečená doporučení pro aktiva, která už držíte.",
    },
    "step2_title": {
        "en": "2. Starting point",
        "cs": "2. Výchozí bod",
    },
    "step2_description": {
        "en": "This choice changes what Coinductor explains next: existing portfolio classification, or a first funding and basket plan.",
        "cs": "Tato volba určuje, co vám Coinductor vysvětlí dál: klasifikaci existujícího portfolia, nebo plán prvního financování a košíku.",
    },
    "step2_existing_card_title": {
        "en": "I already have a portfolio",
        "cs": "Už mám portfolio",
    },
    "step2_existing_card_detail": {
        "en": "Best if you already hold assets on Binance. Coinductor will inventory balances, classify assets, and explain which ones can or cannot be used.",
        "cs": "Nejlepší volba, pokud už na Binance držíte aktiva. Coinductor zjistí zůstatky, klasifikuje aktiva a vysvětlí, která lze a která nelze použít.",
    },
    "step2_existing_card_next": {
        "en": "Next: profile and read-only API",
        "cs": "Dále: profil a read-only API",
    },
    "step2_first_card_title": {
        "en": "Build my first portfolio",
        "cs": "Vybudovat první portfolio",
    },
    "step2_first_card_detail": {
        "en": "Best if you start from fiat or USDC. Coinductor will suggest a reserve, initial deployment, and manual setup steps before automation.",
        "cs": "Nejlepší volba, pokud začínáte s fiatem nebo USDC. Coinductor navrhne rezervu, počáteční nasazení a kroky ručního nastavení před automatizací.",
    },
    "step2_first_card_next": {
        "en": "Next: profile and first plan",
        "cs": "Dále: profil a první plán",
    },
    "step3_title": {
        "en": "3. Decision profile",
        "cs": "3. Rozhodovací profil",
    },
    "step3_description": {
        "en": "This short profile tells Coinductor how cautious, active, and hands-on recommendations should be. It does not place orders.",
        "cs": "Tento krátký profil řekne Coinductoru, jak opatrná, aktivní a osobní mají být doporučení. Nezadává žádné příkazy.",
    },
    "field_management_style": {
        "en": "Management style",
        "cs": "Styl správy",
    },
    "field_automation": {
        "en": "Automation",
        "cs": "Automatizace",
    },
    "field_review_rhythm": {
        "en": "Review rhythm",
        "cs": "Rytmus kontrol",
    },
    "field_language_region": {
        "en": "Language / region",
        "cs": "Jazyk / region",
    },
    "field_operating_currency": {
        "en": "Operating currency",
        "cs": "Provozní měna",
    },
    "operating_currency_note": {
        "en": "Coinductor currently plans bot funding and trading budgets around USDC. Regional fiat funding comes later.",
        "cs": "Coinductor v současnosti plánuje financování botů a obchodní rozpočty v USDC. Regionální fiat financování přijde později.",
    },
    "field_starting_budget": {
        "en": "Starting budget",
        "cs": "Počáteční rozpočet",
    },
    "field_reference_budget": {
        "en": "Reference budget (optional)",
        "cs": "Referenční rozpočet (volitelné)",
    },
    "field_drawdown_comfort": {
        "en": "Drawdown comfort",
        "cs": "Tolerance k propadu",
    },
    "checkbox_use_bots": {
        "en": "Use Binance bot recommendations",
        "cs": "Používat doporučení botů Binance",
    },
    "checkbox_allow_spot": {
        "en": "Allow guarded spot trades",
        "cs": "Povolit zabezpečené spotové obchody",
    },
    "current_selection_title": {
        "en": "Current selection",
        "cs": "Aktuální výběr",
    },
    "current_selection_placeholder": {
        "en": "Choose a profile option above to see what it changes. Nothing is saved until you press Save profile or Apply safe defaults.",
        "cs": "Vyberte výše některou volbu profilu a uvidíte, co změní. Nic se neuloží, dokud nestisknete Save profile nebo Apply safe defaults.",
    },
    "apply_safe_defaults_button": {
        "en": "Apply safe defaults",
        "cs": "Použít bezpečné výchozí hodnoty",
    },
    "apply_safe_defaults_tooltip": {
        "en": "Immediately saves a conservative local profile: recommendations only, no guarded spot trades, and beginner-friendly risk settings.",
        "cs": "Okamžitě uloží konzervativní lokální profil: pouze doporučení, žádné zabezpečené spotové obchody a nastavení rizika vhodné pro začátečníky.",
    },
    "save_profile_button": {
        "en": "Save profile",
        "cs": "Uložit profil",
    },
    "save_profile_tooltip": {
        "en": "Saves these profile choices locally. It does not connect to Binance or place orders.",
        "cs": "Uloží tyto volby profilu lokálně. Nepřipojuje se k Binance ani nezadává příkazy.",
    },
    "profile_saved_status": {
        "en": "Profile is saved. Continue to AI setup.",
        "cs": "Profil je uložen. Pokračujte na nastavení AI.",
    },
    "profile_not_saved_status": {
        "en": "Save a profile or use safe defaults before continuing.",
        "cs": "Před pokračováním uložte profil nebo použijte bezpečné výchozí hodnoty.",
    },
    "step4_title": {
        "en": "4. AI assistant setup",
        "cs": "4. Nastavení AI asistenta",
    },
    "step4_description": {
        "en": "AI is optional. After a provider is connected, Coinductor can offer step-by-step wizard help, report summaries, and app Q&A without giving AI direct execution control.",
        "cs": "AI je volitelná. Po připojení poskytovatele může Coinductor nabízet nápovědu krok za krokem, shrnutí reportů a odpovědi na dotazy o aplikaci, aniž by AI dostala přímou kontrolu nad prováděním akcí.",
    },
    "open_local_ai_guide_button": {
        "en": "Open local AI guide",
        "cs": "Otevřít návod na lokální AI",
    },
    "open_cloud_ai_guide_button": {
        "en": "Open cloud AI guide",
        "cs": "Otevřít návod na cloudové AI",
    },
    "current_ai_provider_title": {
        "en": "Current AI provider",
        "cs": "Aktuální poskytovatel AI",
    },
    "ai_skip_hint": {
        "en": "You can skip AI setup and add it later. \"Ask about this step\" below works with or without a configured provider.",
        "cs": "Nastavení AI můžete přeskočit a doplnit později. \"Ask about this step\" níže funguje s nastaveným poskytovatelem i bez něj.",
    },
    "check_ai_provider_button": {
        "en": "Check AI provider",
        "cs": "Zkontrolovat poskytovatele AI",
    },
    "checking_status": {
        "en": "Checking...",
        "cs": "Kontroluji...",
    },
    "step5_title": {
        "en": "5. Binance API and safety checks",
        "cs": "5. Binance API a bezpečnostní kontroly",
    },
    "step5_description": {
        "en": "Coinductor needs read-only Binance API access for portfolio analysis. Trading permissions are separate and should only be added later when guarded workflows are ready.",
        "cs": "Coinductor potřebuje pro analýzu portfolia read-only přístup k API Binance. Obchodní oprávnění jsou samostatná a měla by se přidat až později, jakmile budou připraveny zabezpečené postupy.",
    },
    "open_binance_guide_button": {
        "en": "Open Binance API guide",
        "cs": "Otevřít návod na Binance API",
    },
    "connect_readonly_title": {
        "en": "Connect read-only key to Coinductor",
        "cs": "Připojit read-only klíč k Coinductoru",
    },
    "save_key_button": {
        "en": "Save key",
        "cs": "Uložit klíč",
    },
    "key_storage_note": {
        "en": "The key is stored in the local .env file in this project folder. It is not sent anywhere by the wizard.",
        "cs": "Klíč se ukládá do lokálního souboru .env ve složce projektu. Průvodce jej nikam neodesílá.",
    },
    "check_readonly_button": {
        "en": "Check read-only access",
        "cs": "Zkontrolovat read-only přístup",
    },
    "testnet_practice_title": {
        "en": "Optional: practice on Spot Testnet",
        "cs": "Volitelné: vyzkoušet na Spot Testnet",
    },
    "open_testnet_guide_button": {
        "en": "Open Testnet guide",
        "cs": "Otevřít návod na Testnet",
    },
    "testnet_description": {
        "en": "Spot Testnet uses virtual funds and a separate key from your real Binance account. Recommended before any real mainnet order, but not required to continue this wizard.",
        "cs": "Spot Testnet používá virtuální prostředky a klíč oddělený od vašeho skutečného účtu Binance. Doporučuje se před jakýmkoli skutečným mainnet příkazem, ale pro pokračování v tomto průvodci není povinný.",
    },
    "save_testnet_key_button": {
        "en": "Save Testnet key",
        "cs": "Uložit Testnet klíč",
    },
    "check_testnet_button": {
        "en": "Check Testnet access",
        "cs": "Zkontrolovat přístup k Testnet",
    },
    "live_trade_note": {
        "en": "A separate live-trading key with IP restriction is used later, only when you are ready for guarded real orders.",
        "cs": "Samostatný live-trading klíč s omezením IP adresy se použije až později, jakmile budete připraveni na zabezpečené skutečné příkazy.",
    },
    "open_live_trade_guide_button": {
        "en": "Open live-trade guide",
        "cs": "Otevřít návod na live obchodování",
    },
    "step6_title": {
        "en": "6. Review and enter Coinductor",
        "cs": "6. Shrnutí a vstup do Coinductoru",
    },
    "step6_description": {
        "en": "The setup profile is saved locally. The main app will show your dashboard, portfolio roles, strategy recommendations, assistant, settings, and safety state.",
        "cs": "Profil nastavení je uložen lokálně. Hlavní aplikace zobrazí váš přehled, role portfolia, doporučení strategií, asistenta, nastavení a stav zabezpečení.",
    },
    "open_safety_guide_button": {
        "en": "Open safety guide",
        "cs": "Otevřít návod na zabezpečení",
    },
    "open_portfolio_roles_guide_button": {
        "en": "Open portfolio roles guide",
        "cs": "Otevřít návod na role portfolia",
    },
    "ask_ai_title": {
        "en": "Ask about this step",
        "cs": "Zeptejte se na tento krok",
    },
    "ask_ai_description": {
        "en": "Uses your configured AI provider when available, with a deterministic offline fallback. This is read-only, never places orders or changes settings, and never blocks Back/Next.",
        "cs": "Používá vašeho nastaveného poskytovatele AI, pokud je dostupný, jinak deterministickou offline odpověď. Je pouze pro čtení, nikdy nezadává příkazy ani nemění nastavení a nikdy neblokuje Back/Next.",
    },
    "ask_ai_provider_status_configured": {
        "en": "AI provider configured:",
        "cs": "Nastavený AI provider:",
    },
    "ask_ai_provider_status_missing": {
        "en": "No AI provider configured yet — deterministic answers still work here; connect one in step 4 for broader help.",
        "cs": "Zatím není nastavený žádný AI provider — deterministická nápověda funguje i tak; pro širší pomoc jej připojte v kroku 4.",
    },
    "ask_ai_placeholder": {
        "en": "e.g. How do I create a Binance API key?",
        "cs": "např. Jak vytvořím API klíč na Binance?",
    },
    "ask_ai_button": {
        "en": "Ask",
        "cs": "Zeptat se",
    },
    "ask_ai_asking_status": {
        "en": "Asking...",
        "cs": "Ptám se...",
    },
    "back_button": {
        "en": "Back",
        "cs": "Zpět",
    },
    "next_button": {
        "en": "Next",
        "cs": "Další",
    },
    "enter_coinductor_button": {
        "en": "Enter Coinductor",
        "cs": "Vstoupit do Coinductoru",
    },
    "warn_choose_binance": {
        "en": "Choose Binance to continue.",
        "cs": "Pro pokračování vyberte Binance.",
    },
    "warn_choose_starting": {
        "en": "Choose how you are starting.",
        "cs": "Vyberte, jak začínáte.",
    },
    "warn_save_profile": {
        "en": "Save a profile before continuing.",
        "cs": "Před pokračováním uložte profil.",
    },
}

APP_STRINGS: dict[str, dict[str, str]] = {
    "language_toggle_label": {
        "en": "App language:",
        "cs": "Jazyk aplikace:",
    },
    "open_detailed_report_button": {
        "en": "Open detailed report",
        "cs": "Otevřít podrobný report",
    },
    "running_status": {
        "en": "Running...",
        "cs": "Probíhá...",
    },
    "overview_finish_setup_title": {
        "en": "Finish setup",
        "cs": "Dokončit nastavení",
    },
    "overview_finish_setup_binance": {
        "en": "Binance read-only access is not connected yet. Portfolio analysis needs it to show real data instead of examples.",
        "cs": "Read-only přístup k Binance zatím není připojen. Analýza portfolia jej potřebuje k zobrazení skutečných dat místo ukázkových.",
    },
    "overview_complete_binance_setup_button": {
        "en": "Complete Binance setup",
        "cs": "Dokončit nastavení Binance",
    },
    "overview_finish_setup_ai": {
        "en": "AI assistant is not configured yet. This step is optional; Coinductor works without it.",
        "cs": "AI asistent zatím není nastaven. Tento krok je volitelný; Coinductor funguje i bez něj.",
    },
    "overview_setup_ai_button": {
        "en": "Set up AI (optional)",
        "cs": "Nastavit AI (volitelné)",
    },
    "overview_title": {
        "en": "Portfolio Overview",
        "cs": "Přehled portfolia",
    },
    "overview_subtitle": {
        "en": "Deterministic analysis with guarded execution",
        "cs": "Deterministická analýza se zabezpečeným prováděním",
    },
    "overview_run_analysis_button": {
        "en": "Run analysis",
        "cs": "Spustit analýzu",
    },
    "overview_safety_title": {
        "en": "Safety & readiness",
        "cs": "Bezpečnost a připravenost",
    },
    "overview_safety_setup_with_analysis": {
        "en": "Real analysis is available. Continue in Live Actions when you want to enable mainnet preview.",
        "cs": "Skutečná analýza je k dispozici. Až budete chtít povolit mainnet preview, pokračujte v Live Actions.",
    },
    "overview_safety_setup_no_analysis": {
        "en": "Setup is complete and exchange-changing actions are locked. Start with a real read-only analysis.",
        "cs": "Nastavení je dokončeno a akce měnící stav burzy jsou uzamčeny. Začněte skutečnou read-only analýzou.",
    },
    "overview_safety_preview_waiting": {
        "en": "Mainnet preview is enabled. Wait for a valid BUY setup and review its preview before arming guarded actions.",
        "cs": "Mainnet preview je povolený. Počkejte na platné BUY nastavení a před odjištěním zabezpečených akcí zkontrolujte jeho náhled.",
    },
    "overview_safety_never_places_order": {
        "en": "This stage never places an order by itself. See Live Actions for the full safety-stage controls and confirmation gates.",
        "cs": "Tento stupeň sám o sobě nikdy nezadá příkaz. Úplné ovládání bezpečnostního stupně a potvrzovací brány najdete v Live Actions.",
    },
    "overview_open_live_actions_button": {
        "en": "Open Live Actions",
        "cs": "Otevřít Live Actions",
    },
    "metric_portfolio_title": {
        "en": "Portfolio",
        "cs": "Portfolio",
    },
    "metric_portfolio_help": {
        "en": "Total value of everything Coinductor tracks, including Spot, Flexible Earn, and Locked balances.",
        "cs": "Celková hodnota všeho, co Coinductor sleduje, včetně zůstatků Spot, Flexible Earn a Locked.",
    },
    "metric_liquid_title": {
        "en": "Liquid",
        "cs": "Likvidní",
    },
    "metric_liquid_help": {
        "en": "Value in Spot or Flexible Earn that could be used without waiting.",
        "cs": "Hodnota ve Spot nebo Flexible Earn, kterou lze použít bez čekání.",
    },
    "metric_locked_title": {
        "en": "Locked",
        "cs": "Uzamčeno",
    },
    "metric_locked_help": {
        "en": "Value in Locked Earn or otherwise not immediately available.",
        "cs": "Hodnota v Locked Earn nebo jinak okamžitě nedostupná.",
    },
    "metric_risk_gate_title": {
        "en": "Risk gate",
        "cs": "Riziková brána",
    },
    "metric_risk_gate_help": {
        "en": "Whether the deterministic risk engine currently approves a new trade. When it does not, the reason is shown here instead of \"Approved\".",
        "cs": "Zda deterministický risk engine aktuálně schvaluje nový obchod. Pokud ne, zobrazí se zde místo \"Approved\" důvod.",
    },
    "overview_latest_decision_title": {
        "en": "Latest decision",
        "cs": "Poslední rozhodnutí",
    },
    "overview_decision_tooltip": {
        "en": "HOLD means no trade is currently recommended. Any other decision type is explained below and detailed further in Action Plan.",
        "cs": "HOLD znamená, že aktuálně není doporučen žádný obchod. Jakýkoli jiný typ rozhodnutí je vysvětlen níže a podrobněji v Action Plan.",
    },
    "overview_recommended_actions_title": {
        "en": "Recommended actions",
        "cs": "Doporučené akce",
    },
    "overview_ai_summary_title": {
        "en": "AI summary",
        "cs": "Shrnutí od AI",
    },
    "portfolio_title": {
        "en": "Portfolio",
        "cs": "Portfolio",
    },
    "portfolio_subtitle": {
        "en": "Latest real-run valuation, asset roles, and liquidity location",
        "cs": "Ocenění z posledního skutečného běhu, role aktiv a umístění likvidity",
    },
    "portfolio_sort_value_desc": {
        "en": "Value high to low",
        "cs": "Hodnota sestupně",
    },
    "portfolio_sort_value_asc": {
        "en": "Value low to high",
        "cs": "Hodnota vzestupně",
    },
    "portfolio_sort_asset_asc": {
        "en": "Asset A-Z",
        "cs": "Aktivum A-Z",
    },
    "portfolio_sort_role_asc": {
        "en": "Policy A-Z",
        "cs": "Politika A-Z",
    },
    "portfolio_col_asset": {
        "en": "ASSET",
        "cs": "AKTIVUM",
    },
    "portfolio_col_policy": {
        "en": "POLICY",
        "cs": "POLITIKA",
    },
    "portfolio_col_value": {
        "en": "VALUE",
        "cs": "HODNOTA",
    },
    "portfolio_col_share": {
        "en": "SHARE",
        "cs": "PODÍL",
    },
    "portfolio_col_liquidity": {
        "en": "LIQUIDITY",
        "cs": "LIKVIDITA",
    },
    "portfolio_col_source": {
        "en": "SOURCE",
        "cs": "ZDROJ",
    },
    "portfolio_spot_label": {
        "en": "Spot",
        "cs": "Spot",
    },
    "portfolio_flexible_label": {
        "en": "Flexible",
        "cs": "Flexible",
    },
    "portfolio_locked_label": {
        "en": "Locked",
        "cs": "Locked",
    },
    "portfolio_policy_changed_toast": {
        "en": "Policy for {asset} changed to {role}",
        "cs": "Politika pro {asset} změněna na {role}",
    },
    "refresh_checks_button": {
        "en": "Refresh checks",
        "cs": "Obnovit kontroly",
    },
    "live_actions_title": {
        "en": "Live Actions",
        "cs": "Live Actions",
    },
    "live_actions_subtitle": {
        "en": "Prepare guarded previews and manage live trading safety gates. Results open in Action Plan after each run.",
        "cs": "Připravte zabezpečené náhledy a spravujte bezpečnostní brány pro live obchodování. Výsledky se po každém běhu otevřou v Action Plan.",
    },
    "open_live_api_guide_button": {
        "en": "Open live API guide",
        "cs": "Otevřít návod na live API",
    },
    "guarded_action_center_title": {
        "en": "Guarded Action Center",
        "cs": "Centrum zabezpečených akcí",
    },
    "guarded_action_center_description": {
        "en": "Choose what kind of output you want. Coinductor runs the required analysis, then opens Action Plan with an updated summary.",
        "cs": "Vyberte, jaký výstup chcete. Coinductor spustí potřebnou analýzu a poté otevře Action Plan s aktualizovaným shrnutím.",
    },
    "trade_preview_title": {
        "en": "Trade preview",
        "cs": "Náhled obchodu",
    },
    "trade_preview_description": {
        "en": "Prepare a guarded trade recommendation and open Action Plan with the latest decision.",
        "cs": "Připravte zabezpečené obchodní doporučení a otevřete Action Plan s posledním rozhodnutím.",
    },
    "prepare_trade_preview_button": {
        "en": "Prepare trade preview",
        "cs": "Připravit náhled obchodu",
    },
    "bot_plan_title": {
        "en": "Bot plan",
        "cs": "Plán bota",
    },
    "bot_plan_description": {
        "en": "Refresh Grid and Rebalancing recommendations and open Action Plan with setup details.",
        "cs": "Aktualizujte doporučení pro Grid a Rebalancing a otevřete Action Plan s detaily nastavení.",
    },
    "prepare_bot_plan_button": {
        "en": "Prepare bot plan",
        "cs": "Připravit plán bota",
    },
    "custom_analysis_title": {
        "en": "Custom analysis",
        "cs": "Vlastní analýza",
    },
    "custom_analysis_description": {
        "en": "Open the same configurable run dialog used by Overview when you want custom parameters.",
        "cs": "Otevřete stejné konfigurovatelné dialogové okno pro spuštění jako na Overview, pokud chcete vlastní parametry.",
    },
    "open_run_dialog_button": {
        "en": "Open run dialog",
        "cs": "Otevřít dialog spuštění",
    },
    "guarded_submission_available_note": {
        "en": "Guarded submission is available only inside a READY Action Plan item and still requires a fresh validation plus per-action confirmation.",
        "cs": "Zabezpečené odeslání je dostupné pouze uvnitř položky Action Plan se stavem READY a stále vyžaduje čerstvou validaci a potvrzení pro danou akci.",
    },
    "guarded_submission_locked_note": {
        "en": "Analysis and recommendations do not submit orders. Live actions remain locked by the current Safety stage.",
        "cs": "Analýza a doporučení nezadávají příkazy. Live akce zůstávají uzamčené aktuálním Safety stage.",
    },
    "safety_stage_title": {
        "en": "Safety stage",
        "cs": "Bezpečnostní stupeň",
    },
    "live_api_title": {
        "en": "Live API",
        "cs": "Live API",
    },
    "live_api_credentials_configured": {
        "en": "Credentials configured",
        "cs": "Přístupové údaje nastaveny",
    },
    "live_api_credentials_not_configured": {
        "en": "Credentials not configured",
        "cs": "Přístupové údaje nejsou nastaveny",
    },
    "live_api_permissions_verified": {
        "en": "Permissions verified this session",
        "cs": "Oprávnění ověřena v této relaci",
    },
    "live_api_permissions_not_verified": {
        "en": "Permissions not verified this session",
        "cs": "Oprávnění v této relaci neověřena",
    },
    "manage_live_api_button": {
        "en": "Manage live API",
        "cs": "Spravovat live API",
    },
    "verify_permissions_button": {
        "en": "Verify permissions",
        "cs": "Ověřit oprávnění",
    },
    "verifying_status": {
        "en": "Verifying...",
        "cs": "Ověřuji...",
    },
    "prerequisite_analysis": {
        "en": "Next prerequisite: complete a real read-only analysis.",
        "cs": "Další předpoklad: dokončit skutečnou read-only analýzu.",
    },
    "prerequisite_preview": {
        "en": "Next prerequisite: prepare and review a ready trade preview. Hold and blocked results do not unlock arming.",
        "cs": "Další předpoklad: připravit a zkontrolovat připravený náhled obchodu. Výsledky HOLD a blocked odjištění neodemknou.",
    },
    "prerequisite_verify_api": {
        "en": "Next prerequisite: verify the live API permissions for this app session.",
        "cs": "Další předpoklad: ověřit oprávnění live API pro tuto relaci aplikace.",
    },
    "prerequisite_all_available": {
        "en": "All prerequisites for the next Safety stage are available.",
        "cs": "Všechny předpoklady pro další Safety stage jsou splněny.",
    },
    "recommended_next_step_label": {
        "en": "Recommended next step",
        "cs": "Doporučený další krok",
    },
    "safety_next_action_enable_preview": {
        "en": "Enable preview",
        "cs": "Povolit náhled",
    },
    "safety_next_action_run_analysis": {
        "en": "Run read-only analysis",
        "cs": "Spustit read-only analýzu",
    },
    "safety_next_action_prepare_preview": {
        "en": "Prepare trade preview",
        "cs": "Připravit náhled obchodu",
    },
    "safety_next_action_verify_api": {
        "en": "Verify live API permissions",
        "cs": "Ověřit oprávnění live API",
    },
    "safety_next_action_arm": {
        "en": "Arm guarded actions",
        "cs": "Odjistit zabezpečené akce",
    },
    "safety_next_action_enable_submit": {
        "en": "Enable live submit",
        "cs": "Povolit live odeslání",
    },
    "safety_next_action_open_action_plan": {
        "en": "Open Action Plan",
        "cs": "Otevřít Action Plan",
    },
    "safety_step1_title": {
        "en": "1. Preview",
        "cs": "1. Náhled",
    },
    "safety_step1_detail": {
        "en": "Mainnet validation without submit",
        "cs": "Validace na mainnetu bez odeslání",
    },
    "safety_step2_title": {
        "en": "2. Armed",
        "cs": "2. Odjištěno",
    },
    "safety_step2_detail": {
        "en": "Verified key, submit still locked",
        "cs": "Ověřený klíč, odeslání stále uzamčeno",
    },
    "safety_step3_title": {
        "en": "3. Live enabled",
        "cs": "3. Live povoleno",
    },
    "safety_step3_detail": {
        "en": "Guarded submit can be confirmed",
        "cs": "Zabezpečené odeslání lze potvrdit",
    },
    "safety_enable_preview_button": {
        "en": "Enable preview",
        "cs": "Povolit náhled",
    },
    "safety_arm_button": {
        "en": "Arm guarded actions",
        "cs": "Odjistit zabezpečené akce",
    },
    "safety_enable_submit_button": {
        "en": "Enable live submit",
        "cs": "Povolit live odeslání",
    },
    "safety_lock_button": {
        "en": "Lock live submit",
        "cs": "Uzamknout live odeslání",
    },
    "safety_stage_disclaimer": {
        "en": "Stage changes are local safety controls and never place an order. Every live trade or OCO protection still needs its own confirmation. If your public IP is dynamic, keep live execution locked unless the Binance whitelist is current.",
        "cs": "Změny stupně jsou lokální bezpečnostní ovládací prvky a nikdy nezadávají příkaz. Každý live obchod nebo OCO ochrana stále vyžaduje vlastní potvrzení. Pokud máte dynamickou veřejnou IP adresu, nechte live provádění uzamčené, dokud není whitelist na Binance aktuální.",
    },
    "action_plan_title": {
        "en": "Action Plan",
        "cs": "Action Plan",
    },
    "action_plan_subtitle": {
        "en": "Latest trade, Grid, and Rebalancing decisions in one review list.",
        "cs": "Poslední rozhodnutí o obchodu, Gridu a Rebalancingu v jednom přehledu ke kontrole.",
    },
    "first_portfolio_deployment_title": {
        "en": "First portfolio deployment",
        "cs": "Nasazení prvního portfolia",
    },
    "first_portfolio_deployment_description": {
        "en": "Staged, guarded purchase of your starting basket. Each tranche still passes bankroll, stop-loss, and confirmation checks; only market-timing (consensus/RSI) is intentionally skipped, since this executes a plan you already chose.",
        "cs": "Postupný, zabezpečený nákup vašeho počátečního košíku. Každá tranše stále prochází kontrolou bankroll, stop-loss a potvrzení; záměrně je vynechán jen časový odhad trhu (consensus/RSI), protože se provádí plán, který jste už zvolili.",
    },
    "first_portfolio_testnet_label": {
        "en": "Testnet",
        "cs": "Testnet",
    },
    "first_portfolio_mainnet_label": {
        "en": "Mainnet",
        "cs": "Mainnet",
    },
    "first_portfolio_deploy_button": {
        "en": "Deploy",
        "cs": "Nasadit",
    },
    "first_portfolio_budget_label": {
        "en": "Total USDC budget for the whole basket:",
        "cs": "Celkový rozpočet v USDC pro celý košík:",
    },
    "first_portfolio_tranches_label": {
        "en": "Tranches:",
        "cs": "Tranše:",
    },
    "first_portfolio_budget_warning": {
        "en": "Enter the real USDC amount you intend to deploy here — the wizard's planned budget may be in a different currency and is not auto-converted.",
        "cs": "Zadejte skutečnou částku v USDC, kterou zde chcete nasadit — plánovaný rozpočet z wizardu může být v jiné měně a není automaticky přepočítán.",
    },
    "legend_ready": {
        "en": "Ready - can be confirmed now",
        "cs": "Ready - lze nyní potvrdit",
    },
    "legend_watch": {
        "en": "Watch - conditions not met yet",
        "cs": "Watch - podmínky zatím nesplněny",
    },
    "legend_other": {
        "en": "Other - review-only, e.g. HOLD or blocked",
        "cs": "Other - jen ke kontrole, např. HOLD nebo blocked",
    },
    "last_live_trade_label": {
        "en": "Last live trade",
        "cs": "Poslední live obchod",
    },
    "review_button": {
        "en": "Review",
        "cs": "Zkontrolovat",
    },
}


class UiStringsService:
    def wizard_text(self, language: str) -> dict[str, str]:
        return self._resolve(WIZARD_STRINGS, language)

    def app_text(self, language: str) -> dict[str, str]:
        return self._resolve(APP_STRINGS, language)

    def _resolve(self, strings: dict[str, dict[str, str]], language: str) -> dict[str, str]:
        normalized = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        return {
            key: variants.get(normalized, variants[DEFAULT_LANGUAGE])
            for key, variants in strings.items()
        }
