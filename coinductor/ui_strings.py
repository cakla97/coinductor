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
    # --- decision profile options ---
    # Labels are display text; the values they carry (CONSERVATIVE, WEEKLY, ...)
    # stay English identifiers in profile_choices and are never translated.
    "opt_style_conservative": {"en": "Conservative", "cs": "Konzervativní"},
    "opt_style_balanced": {"en": "Balanced", "cs": "Vyvážený"},
    "opt_style_active": {"en": "Active", "cs": "Aktivní"},
    "opt_automation_recommend": {"en": "Recommendations only", "cs": "Pouze doporučení"},
    "opt_automation_guarded": {"en": "Guarded automation", "cs": "Zabezpečená automatizace"},
    "opt_cadence_weekly": {"en": "Weekly", "cs": "Týdně"},
    "opt_cadence_twice_weekly": {"en": "Twice weekly", "cs": "Dvakrát týdně"},
    "opt_cadence_daily": {"en": "Daily", "cs": "Denně"},
    "opt_cadence_manual": {"en": "Manual / irregular", "cs": "Ručně / nepravidelně"},
    "opt_drawdown_off": {"en": "Off - do not change limits", "cs": "Vypnuto - neměnit limity"},
    "opt_drawdown_low": {"en": "Low - 10%", "cs": "Nízká - 10 %"},
    "opt_drawdown_medium": {"en": "Medium - 15%", "cs": "Střední - 15 %"},
    "opt_drawdown_high": {"en": "High - 20%", "cs": "Vysoká - 20 %"},
    "opt_budget_auto": {"en": "Auto", "cs": "Automaticky"},
    # Help text says what the choice changes, not what the word means.
    "help_automation_recommend": {
        "en": "Coinductor never submits anything. It analyses, explains and recommends; every order stays in your hands. This is the safest mode and the right one until you trust the recommendations.",
        "cs": "Coinductor nikdy nic neodešle. Analyzuje, vysvětluje a doporučuje; každý příkaz zůstává ve vašich rukou. Nejbezpečnější režim a správná volba, dokud doporučením nedůvěřujete.",
    },
    "help_automation_guarded": {
        "en": "Unlocks the guarded submit buttons, so Coinductor can place an order after you confirm it. It still cannot bypass the safety stage, loss limits, stop-loss or the per-action confirmation phrase. Pick this only once live keys are verified.",
        "cs": "Odemkne tlačítka zabezpečeného odeslání, takže Coinductor může po vašem potvrzení zadat příkaz. Stále nemůže obejít bezpečnostní stupeň, limity ztrát, stop-loss ani potvrzovací frázi u každé akce. Volte až po ověření živých klíčů.",
    },
    "help_cadence_weekly": {
        "en": "Written into the Action Plan as your intended review rhythm; it is a reminder, not a scheduler. Coinductor never runs on its own - you always start each analysis.",
        "cs": "Zapíše se do Action Planu jako váš zamýšlený rytmus kontrol; je to připomínka, ne plánovač. Coinductor se nikdy nespustí sám - každou analýzu spouštíte vy.",
    },
    "help_cadence_twice_weekly": {
        "en": "Written into the Action Plan as your intended review rhythm; it is a reminder, not a scheduler. Coinductor never runs on its own - you always start each analysis.",
        "cs": "Zapíše se do Action Planu jako váš zamýšlený rytmus kontrol; je to připomínka, ne plánovač. Coinductor se nikdy nespustí sám - každou analýzu spouštíte vy.",
    },
    "help_cadence_daily": {
        "en": "Written into the Action Plan as your intended review rhythm; it is a reminder, not a scheduler. Coinductor never runs on its own - you always start each analysis.",
        "cs": "Zapíše se do Action Planu jako váš zamýšlený rytmus kontrol; je to připomínka, ne plánovač. Coinductor se nikdy nespustí sám - každou analýzu spouštíte vy.",
    },
    "help_cadence_manual": {
        "en": "Written into the Action Plan as your intended review rhythm; it is a reminder, not a scheduler. Coinductor never runs on its own - you always start each analysis.",
        "cs": "Zapíše se do Action Planu jako váš zamýšlený rytmus kontrol; je to připomínka, ne plánovač. Coinductor se nikdy nespustí sám - každou analýzu spouštíte vy.",
    },
    "help_locale": {
        "en": "Sets your fiat currency and regional funding route for deposit guidance. It does not change the app language - use the English / Cestina switch at the top for that.",
        "cs": "Nastavuje vaši fiat měnu a regionální cestu financování pro pokyny k vkladům. Nemění jazyk aplikace - k tomu slouží přepínač English / Čeština nahoře.",
    },
    "value_on": {"en": "On", "cs": "Zapnuto"},
    "value_off": {"en": "Off", "cs": "Vypnuto"},
    # One set of LLM_* variables means one provider at a time; two side-by-side
    # panels would otherwise read as two independent, coexisting settings.
    "ai_one_provider_notice": {
        "en": "Only one AI provider is active at a time. Saving either panel replaces the other - the text and vision models move together.",
        "cs": "Aktivní může být vždy jen jeden poskytovatel AI. Uložením kterékoli karty nahradíte tu druhou - textový i vision model se mění společně.",
    },
    "ai_active_local": {
        "en": "Active now: local AI. Your prompts stay on this computer.",
        "cs": "Nyní aktivní: lokální AI. Vaše dotazy zůstávají na tomto počítači.",
    },
    "ai_active_cloud": {
        "en": "Active now: cloud AI. Selected report and portfolio context leaves this computer.",
        "cs": "Nyní aktivní: cloudová AI. Vybraný report a kontext portfolia opouští tento počítač.",
    },
    "ai_active_none": {
        "en": "No AI provider is configured yet. Coinductor works without one.",
        "cs": "Zatím není nastaven žádný poskytovatel AI. Coinductor funguje i bez něj.",
    },
    "ai_switch_to_local_clears_key": {
        "en": "Saving the local panel also deletes the stored cloud API key, so it can never be sent to a local endpoint.",
        "cs": "Uložením lokální karty se zároveň smaže uložený cloudový API klíč, aby se nikdy nemohl odeslat na lokální endpoint.",
    },
    "help_budget_existing": {
        "en": "Optional context only: your existing Binance holdings define what Coinductor manages, not this number. Leave it on Auto unless you plan to add fresh capital.",
        "cs": "Pouze doplňující kontext: co Coinductor spravuje, určuje váš skutečný zůstatek na Binance, ne toto číslo. Nechte Automaticky, pokud neplánujete přidat nový kapitál.",
    },
    "help_budget_auto": {
        "en": "Auto means Coinductor will not assume fresh capital. It will use discovered balances and conservative defaults until real funding is known.",
        "cs": "Automaticky znamená, že Coinductor nepředpokládá žádný nový kapitál. Použije zjištěné zůstatky a konzervativní výchozí hodnoty, dokud nezná skutečné financování.",
    },
    "help_budget_amount": {
        "en": "Starting budget is the approximate operating capital Coinductor uses for first-portfolio planning and funding recommendations.",
        "cs": "Počáteční rozpočet je přibližný provozní kapitál, se kterým Coinductor plánuje první portfolio a doporučení k financování.",
    },
    "help_bots_on": {
        "en": "Turns on grid_bot in config.toml, so Coinductor works out Grid and Rebalancing parameters for you to enter on Binance by hand. Binance has no public API for creating bots, so nothing is created automatically.",
        "cs": "Zapne grid_bot v config.toml, takže vám Coinductor spočítá parametry pro Grid a Rebalancing, které pak na Binance zadáte ručně. Binance nemá veřejné API pro zakládání botů, takže se nic nevytvoří automaticky.",
    },
    "help_bots_off": {
        "en": "Turns off grid_bot in config.toml. Coinductor stops working out bot parameters; existing bots on Binance are untouched.",
        "cs": "Vypne grid_bot v config.toml. Coinductor přestane počítat parametry botů; už založených botů na Binance se to nedotkne.",
    },
    "help_spot_on": {
        "en": "Lets the guarded submit actually place a spot buy, once the safety stage is LIVE_ENABLED and you type the confirmation phrase. Leave it off to keep Coinductor out of opening positions while still using bots and rebalancing.",
        "cs": "Umožní zabezpečenému odeslání skutečně zadat spotový nákup, jakmile je bezpečnostní stupeň LIVE_ENABLED a napíšete potvrzovací frázi. Nechte vypnuté, pokud nechcete, aby Coinductor otevíral pozice, a přesto chcete používat boty a rebalancing.",
    },
    "help_spot_off": {
        "en": "Coinductor will refuse to submit a spot buy even at LIVE_ENABLED. Bots, rebalancing and protective OCO orders still work.",
        "cs": "Coinductor odmítne odeslat spotový nákup i na stupni LIVE_ENABLED. Boti, rebalancing a ochranné OCO příkazy fungují dál.",
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
    # Named for what it does. It was "Language / region", which contradicted the
    # hint right under it and had people expecting a Spanish UI from es-ES; the
    # interface language is a separate switch at the top of the window.
    "field_language_region": {
        "en": "Region and fiat currency",
        "cs": "Region a fiat měna",
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
        "en": "The key goes to your operating system's credential store, not a plaintext file. If no credential store is available it falls back to a local .env. Either way the wizard sends it nowhere.",
        "cs": "Klíč se uloží do systémového úložiště pověření, ne do čitelného souboru. Pokud úložiště není dostupné, použije se lokální .env. V obou případech jej průvodce nikam neodesílá.",
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
    "next_steps_outside_title": {
        "en": "Next steps outside Coinductor",
        "cs": "Další kroky mimo Coinductor",
    },
    "first_portfolio_plan_title": {
        "en": "First portfolio plan",
        "cs": "Plán prvního portfolia",
    },
    "existing_portfolio_next_step_title": {
        "en": "Existing portfolio next step",
        "cs": "Další krok pro existující portfolio",
    },
    "suggested_first_basket_title": {
        "en": "Suggested first basket (manual purchase)",
        "cs": "Navrhovaný první košík (ruční nákup)",
    },
    "suggested_first_basket_description": {
        "en": "Weights match your chosen management style. Buying is always manual on Binance; Coinductor never places this order for you.",
        "cs": "Váhy odpovídají vámi zvolenému stylu správy. Nákup je vždy ruční na Binance; Coinductor tento příkaz za vás nikdy nezadává.",
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
    "portfolio_empty_title": {
        "en": "No portfolio loaded yet",
        "cs": "Portfolio zatím není načtené",
    },
    "portfolio_empty_detail": {
        "en": "Connecting a Binance key proves the app can read your account; it does not fetch anything by itself. This table shows the latest real analysis, so run one to populate it.",
        "cs": "Připojením klíče k Binance se jen ověří, že aplikace umí číst váš účet; sama o sobě nic nestahuje. Tato tabulka ukazuje poslední skutečnou analýzu, takže ji naplníte jejím spuštěním.",
    },
    "portfolio_empty_action": {"en": "Run analysis", "cs": "Spustit analýzu"},
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
        "cs": "Flexibilní",
    },
    "portfolio_locked_label": {
        "en": "Locked",
        "cs": "Zamčeno",
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
        "cs": "Živé akce",
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
        "en": "All three run the same full analysis and fill the whole Action Plan - trade, Grid and Rebalancing. They differ only in whether a mainnet preview is prepared as well.",
        "cs": "Všechny tři spustí tu samou úplnou analýzu a naplní celý Action Plan - obchod, Grid i Rebalancing. Liší se jen tím, zda se navíc připraví mainnet náhled.",
    },
    "trade_preview_title": {
        "en": "Trade preview",
        "cs": "Náhled obchodu",
    },
    "trade_preview_description": {
        "en": "Full analysis plus a mainnet preview: the trade is validated against Binance without submitting anything.",
        "cs": "Úplná analýza plus mainnet náhled: obchod se ověří proti Binance, aniž by se cokoli odeslalo.",
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
        "en": "Full analysis without the mainnet preview. Use this when you only want refreshed recommendations.",
        "cs": "Úplná analýza bez mainnet náhledu. Použijte, když chcete jen aktualizovaná doporučení.",
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
        "en": "The same analysis with the run dialog, so you can set the data mode, AI options and preview yourself.",
        "cs": "Tatáž analýza s dialogem spuštění, kde si sami zvolíte režim dat, možnosti AI a náhled.",
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
    "automation_locks_submit": {
        "en": "Your profile is set to Recommendations only, so Coinductor never submits orders - it only explains and recommends. Switch Automation to Guarded automation in the setup wizard to unlock guarded live submit.",
        "cs": "Váš profil je nastaven na Pouze doporučení, takže Coinductor nikdy neodesílá příkazy - pouze vysvětluje a doporučuje. Pro odemčení zabezpečeného živého odesílání přepněte Automatizaci na Zabezpečená automatizace v průvodci nastavením.",
    },
    "live_api_title": {
        "en": "Live API",
        "cs": "Živé API",
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
    "prerequisite_live_key": {
        "en": "Next prerequisite: add a live trading key and verify its permissions.",
        "cs": "Další předpoklad: přidejte klíč pro živé obchodování a ověřte jeho oprávnění.",
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
    "safety_next_action_add_live_key": {
        "en": "Add live trading key",
        "cs": "Přidat klíč pro živé obchodování",
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
        "cs": "Plán akcí",
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
    "manual_steps_title": {
        "en": "Manual setup on Binance",
        "cs": "Ruční nastavení na Binance",
    },
    "last_live_trade_label": {
        "en": "Last live trade",
        "cs": "Poslední live obchod",
    },
    "review_button": {
        "en": "Review",
        "cs": "Zkontrolovat",
    },
    "active_strategies_title": {
        "en": "Active Strategies",
        "cs": "Aktivní strategie",
    },
    "refreshing_status": {
        "en": "Refreshing...",
        "cs": "Obnovuji...",
    },
    "refresh_monitoring_button": {
        "en": "Refresh monitoring",
        "cs": "Obnovit sledování",
    },
    "click_to_copy_tooltip": {
        "en": "Click to copy",
        "cs": "Kliknutím zkopírujete",
    },
    "blockers_label": {
        "en": "Blockers",
        "cs": "Blokátory",
    },
    "copy_manual_steps_button": {
        "en": "Copy steps",
        "cs": "Kopírovat kroky",
    },
    "open_run_report_button": {
        "en": "Open report",
        "cs": "Otevřít report",
    },
    "refresh_monitoring_tooltip": {
        "en": (
            "Runs a fresh read-only analysis and re-evaluates every registered bot against it. "
            "No AI, no trade preview, and nothing is sent to Binance."
        ),
        "cs": (
            "Spustí novou read-only analýzu a znovu proti ní vyhodnotí všechny registrované boty. "
            "Bez AI, bez náhledu obchodu a na Binance se nic neodesílá."
        ),
    },
    "register_active_bot_button": {
        "en": "Register active bot",
        "cs": "Registrovat aktivního bota",
    },
    "monitoring_evaluation_pending_title": {
        "en": "Monitoring evaluation pending",
        "cs": "Vyhodnocení sledování čeká",
    },
    "no_active_bots_title": {
        "en": "No active bots registered",
        "cs": "Nejsou registrováni žádní aktivní boti",
    },
    "monitoring_evaluation_pending_detail": {
        "en": "The bot is stored locally, but no fresh evaluation is available yet. Refresh monitoring after checking your Binance connection.",
        "cs": "Bot je uložen lokálně, ale zatím není k dispozici čerstvé vyhodnocení. Obnovte sledování po kontrole připojení k Binance.",
    },
    "no_active_bots_detail": {
        "en": "Create a Grid or Rebalancing Bot in Binance from a READY Action Plan recommendation, then register its real parameters in Coinductor for periodic monitoring.",
        "cs": "Vytvořte Grid nebo Rebalancing Bota na Binance podle doporučení se stavem READY z Action Plan a poté zaregistrujte jeho skutečné parametry v Coinductoru pro pravidelné sledování.",
    },
    "open_action_plan_button": {
        "en": "Open Action Plan",
        "cs": "Otevřít Action Plan",
    },
    "next_review_title": {
        "en": "Next review",
        "cs": "Další kontrola",
    },
    "next_review_not_scheduled": {
        "en": "Not scheduled",
        "cs": "Není naplánováno",
    },
    "next_review_suggested_timing": {
        "en": "Suggested timing",
        "cs": "Doporučené načasování",
    },
    "next_review_not_available": {
        "en": "Not available",
        "cs": "Není k dispozici",
    },
    "next_review_scheduled_from_run": {
        "en": "Scheduled from latest run",
        "cs": "Naplánováno podle posledního běhu",
    },
    "next_review_profile_cadence": {
        "en": "Profile review rhythm",
        "cs": "Rytmus kontrol z profilu",
    },
    "next_review_not_configured": {
        "en": "Not configured",
        "cs": "Není nastaveno",
    },
    "next_review_run_earlier_if_title": {
        "en": "Run earlier if",
        "cs": "Spusťte dříve, pokud",
    },
    "next_review_run_earlier_if_description": {
        "en": "These are optional triggers for refreshing the analysis before the scheduled review. You do not need to make them happen.",
        "cs": "Toto jsou volitelné podněty pro obnovení analýzy před naplánovanou kontrolou. Není třeba je záměrně vyvolávat.",
    },
    "next_review_resolve_before_rerun_title": {
        "en": "Resolve before rerunning",
        "cs": "Vyřešte před opětovným spuštěním",
    },
    "next_review_resolve_before_rerun_description": {
        "en": "These blockers need a manual or funding change. Repeating the same analysis alone will not remove them.",
        "cs": "Tyto blokátory vyžadují ruční zásah nebo změnu financování. Samotné opakování stejné analýzy je neodstraní.",
    },
    "next_review_no_manual_prerequisite": {
        "en": "No manual prerequisite. A fresh run can reassess current market conditions.",
        "cs": "Žádný ruční předpoklad. Nový běh může znovu vyhodnotit aktuální tržní podmínky.",
    },
    "next_review_ai_disclaimer_prefix": {
        "en": "Based on deterministic output from run",
        "cs": "Na základě deterministického výstupu z běhu",
    },
    "next_review_ai_disclaimer_suffix": {
        "en": "AI commentary does not control this timing.",
        "cs": "Komentář AI toto načasování neřídí.",
    },
    "run_analysis_now_button": {
        "en": "Run analysis now",
        "cs": "Spustit analýzu nyní",
    },
    "binance_id_label": {
        "en": "Binance ID",
        "cs": "Binance ID",
    },
    "view_details_button": {
        "en": "View details",
        "cs": "Zobrazit detail",
    },
    "run_history_title": {
        "en": "Run History",
        "cs": "Historie běhů",
    },
    "run_history_subtitle": {
        "en": "The latest 30 analytical runs",
        "cs": "Posledních 30 analytických běhů",
    },
    "run_history_description": {
        "en": "REAL runs read your live Binance account and are the ones behind Action Plan and Active Strategies. MOCK runs use example data for trying the app and never touch your real portfolio. This is a read-only log; to act on a decision, use Action Plan.",
        "cs": "REAL běhy čtou váš skutečný účet Binance a jsou to ty, ze kterých vychází Action Plan a Active Strategies. MOCK běhy používají ukázková data pro vyzkoušení aplikace a nikdy se nedotknou vašeho skutečného portfolia. Toto je pouze log ke čtení; pro reakci na rozhodnutí použijte Action Plan.",
    },
    "run_history_run_label": {
        "en": "RUN",
        "cs": "BĚH",
    },
    "assistant_title": {
        "en": "AI Assistant",
        "cs": "AI asistent",
    },
    "assistant_context_prefix": {
        "en": "Read-only help | Context:",
        "cs": "Nápověda pouze pro čtení | Kontext:",
    },
    "assistant_active_ai_prefix": {
        "en": "Active AI:",
        "cs": "Aktivní AI:",
    },
    "assistant_history_button": {
        "en": "History",
        "cs": "Historie",
    },
    "assistant_new_chat_button": {
        "en": "New chat",
        "cs": "Nový chat",
    },
    "assistant_proposed_action_title": {
        "en": "Proposed app action",
        "cs": "Navrhovaná akce v aplikaci",
    },
    "assistant_dismiss_button": {
        "en": "Dismiss",
        "cs": "Zamítnout",
    },
    "assistant_confirm_button": {
        "en": "Confirm",
        "cs": "Potvrdit",
    },
    "assistant_attached_image_fallback": {
        "en": "Attached image",
        "cs": "Připojený obrázek",
    },
    "assistant_vision_available_note": {
        "en": "The active AI supports image input. The screenshot will be sent with this message. You can paste another screenshot with Ctrl+V.",
        "cs": "Aktivní AI podporuje vstup obrázků. Screenshot bude odeslán s touto zprávou. Další screenshot můžete vložit pomocí Ctrl+V.",
    },
    "assistant_remove_button": {
        "en": "Remove",
        "cs": "Odebrat",
    },
    "assistant_attach_image_button": {
        "en": "Attach image",
        "cs": "Připojit obrázek",
    },
    "assistant_input_placeholder": {
        "en": "Ask about the latest run, portfolio, risk, Grid...",
        "cs": "Zeptejte se na poslední běh, portfolio, riziko, Grid...",
    },
    "assistant_send_button": {
        "en": "Send",
        "cs": "Odeslat",
    },
    "assistant_stop_button": {
        "en": "Stop",
        "cs": "Zastavit",
    },
    "help_guides_title": {
        "en": "Help & Guides",
        "cs": "Nápověda a návody",
    },
    "help_guides_subtitle": {
        "en": "Step-by-step local guides for setup, safety, AI providers, Binance API access, and portfolio roles.",
        "cs": "Lokální návody krok za krokem pro nastavení, zabezpečení, poskytovatele AI, přístup k Binance API a role portfolia.",
    },
    "open_guide_button": {
        "en": "Open guide",
        "cs": "Otevřít návod",
    },
    "settings_title": {
        "en": "Settings",
        "cs": "Nastavení",
    },
    "settings_subtitle": {
        "en": "Manage local configuration, privacy controls, and readiness checks.",
        "cs": "Spravujte lokální konfiguraci, ovládání soukromí a kontroly připravenosti.",
    },
    "setup_wizard_button": {
        "en": "Setup wizard",
        "cs": "Průvodce nastavením",
    },
    # --- no AI provider configured ---
    "no_ai_provider_title": {
        "en": "No AI model is connected",
        "cs": "Není připojený žádný AI model",
    },
    "no_ai_provider_assistant_detail": {
        "en": "The assistant needs a local or cloud model to answer. Everything else in Coinductor works without one - the analysis is deterministic and never asks a model.",
        "cs": "Asistent potřebuje místní nebo cloudový model, aby mohl odpovídat. Všechno ostatní v Coinductoru funguje i bez něj - analýza je deterministická a model se jí nikdy neptá.",
    },
    "no_ai_provider_input_placeholder": {
        "en": "Connect a model in Settings to ask questions",
        "cs": "Pro dotazy připojte model v Nastavení",
    },
    "no_ai_provider_setup_button": {
        "en": "Open Settings",
        "cs": "Otevřít Nastavení",
    },
    "no_ai_provider_run_detail": {
        "en": "No AI model is connected, so these two are unavailable. The analysis itself runs exactly the same without them.",
        "cs": "Není připojený žádný AI model, takže tyhle dvě volby nejsou dostupné. Samotná analýza proběhne úplně stejně i bez nich.",
    },
    # --- scheduled analysis ---
    "automation_title": {
        "en": "Run the analysis on a schedule",
        "cs": "Spouštět analýzu podle rozvrhu",
    },
    "automation_description": {
        "en": "An extra way to start the same analysis the button starts — the Run analysis dialog keeps working exactly as it does now. A scheduled run only ever reads: it cannot place an order, because the confirmation you type is what authorises one and no timer can type.",
        "cs": "Další způsob, jak spustit tutéž analýzu jako tlačítko — dialog Spustit analýzu funguje přesně jako dosud. Naplánovaný běh jen čte: příkaz zadat nemůže, protože ho povoluje potvrzení, které vypisujete vy, a to žádný časovač nenapíše.",
    },
    "automation_enable_checkbox": {
        "en": "Run automatically while Coinductor is open",
        "cs": "Spouštět automaticky, dokud je Coinductor otevřený",
    },
    "automation_interval_label": {
        "en": "Every (hours)",
        "cs": "Každých (hodin)",
    },
    "automation_ai_checkbox": {
        "en": "Include the AI summary",
        "cs": "Zahrnout shrnutí od AI",
    },
    "automation_preview_checkbox": {
        "en": "Include the mainnet execution preview",
        "cs": "Zahrnout mainnet náhled provedení",
    },
    "automation_save_button": {
        "en": "Save schedule",
        "cs": "Uložit rozvrh",
    },
    "automation_tray_note": {
        "en": "With a schedule on, closing the window hides Coinductor to the notification area instead of quitting, so the schedule can keep running. The tray icon has Open, Run analysis now and Quit. Your PC has to be on — there is no server doing this for you.",
        "cs": "Se zapnutým rozvrhem se Coinductor při zavření okna schová do oznamovací oblasti místo ukončení, aby rozvrh mohl běžet dál. V ikoně je Otevřít, Spustit analýzu teď a Ukončit. Počítač musí být zapnutý — žádný server to za vás nedělá.",
    },
    # --- scheduled task ---
    "task_title": {
        "en": "Also run when Coinductor is closed",
        "cs": "Spouštět i se zavřeným Coinductorem",
    },
    "task_description": {
        "en": "Registers a Windows scheduled task that runs one analysis a day using this same program, with no window. It reads only — it cannot place an order, for the same reason the in-app schedule cannot. Your PC still has to be on; nothing runs it for you while the machine is off. You can inspect or delete it yourself with: schtasks /query /tn \"Coinductor scheduled analysis\"",
        "cs": "Zaregistruje ve Windows naplánovanou úlohu, která jednou denně spustí analýzu tímhle stejným programem, bez okna. Jen čte — příkaz zadat nemůže, ze stejného důvodu jako rozvrh uvnitř aplikace. Počítač pořád musí být zapnutý; s vypnutým strojem to za vás nikdo nespustí. Sám si ji můžete prohlédnout nebo smazat příkazem: schtasks /query /tn \"Coinductor scheduled analysis\"",
    },
    "task_time_label": {
        "en": "Every day at",
        "cs": "Každý den v",
    },
    "task_register_button": {
        "en": "Schedule it",
        "cs": "Naplánovat",
    },
    "task_remove_button": {
        "en": "Remove the task",
        "cs": "Odstranit úlohu",
    },
    "task_state_registered": {
        "en": "A scheduled task is registered.",
        "cs": "Naplánovaná úloha je zaregistrovaná.",
    },
    "task_next_run_label": {"en": "Next run", "cs": "Příští spuštění"},
    "task_status_label": {"en": "Status", "cs": "Stav"},
    "task_catch_up_note": {
        "en": "A run missed because the PC was off happens as soon as it is next on, not silently skipped.",
        "cs": "Běh zmeškaný kvůli vypnutému počítači proběhne, jakmile ho příště zapnete — nepřeskočí se potichu.",
    },
    "task_state_absent": {
        "en": "No scheduled task. Nothing runs while Coinductor is closed.",
        "cs": "Žádná naplánovaná úloha. Se zavřeným Coinductorem neběží nic.",
    },
    "order_caps_title": {
        "en": "Maximum size of a single order",
        "cs": "Maximální velikost jednoho příkazu",
    },
    "order_caps_description": {
        "en": "The last limit before an order reaches the exchange. Everything else decides whether an order goes; this decides how big. It applies to every order Coinductor can place - the guarded trade and each first-portfolio tranche alike - and it truncates silently rather than refusing, so a tranche planned above it submits this amount instead.",
        "cs": "Poslední mez, než příkaz odejde na burzu. Všechno ostatní rozhoduje, jestli příkaz vůbec odejde; tohle rozhoduje, jak velký bude. Platí na každý příkaz, který Coinductor umí zadat - na zabezpečený obchod i na každou tranši prvního portfolia - a ořezává tiše, takže tranše plánovaná výš odešle jen tuhle částku.",
    },
    "order_caps_testnet_label": {
        "en": "Testnet (USDT)",
        "cs": "Testnet (USDT)",
    },
    "order_caps_mainnet_label": {
        "en": "Live (USDC)",
        "cs": "Živé (USDC)",
    },
    "order_caps_save_button": {
        "en": "Save caps",
        "cs": "Uložit stropy",
    },
    "order_caps_suggestion_template": {
        "en": "For a portfolio this size, {suggested} is a conservative live cap. Raise it deliberately, not to make one blocked order go through.",
        "cs": "Pro portfolio této velikosti je {suggested} konzervativní živý strop. Zvyšujte ho vědomě, ne kvůli jednomu zablokovanému příkazu.",
    },
    "earn_funding_title": {
        "en": "How much may move from Earn to Spot",
        "cs": "Kolik se smí přesunout z Earnu na Spot",
    },
    "earn_funding_description": {
        "en": "This is a transfer inside your own Binance account, not a withdrawal - Coinductor cannot withdraw and refuses an API key that could. It exists so an approved action can be paid for when the money is sitting in Simple Earn Flexible. What it costs is forgone yield, and subscribing again reverses it. Each limit below is a flat amount and a percentage of your portfolio, and the smaller one wins.",
        "cs": "Jde o přesun uvnitř vašeho Binance účtu, ne o výběr - Coinductor vybírat neumí a API klíč, který by to uměl, odmítne. Slouží k tomu, aby šla zaplatit schválená akce, když peníze leží v Simple Earn Flexible. Stojí to jen ušlý výnos a opětovným vložením se to vrátí. Každá mez níže je plochá částka a zároveň procento portfolia; platí ta menší.",
    },
    "earn_funding_run_pct_label": {
        "en": "One run may release (% of portfolio)",
        "cs": "Jeden běh smí uvolnit (% portfolia)",
    },
    "earn_funding_run_pct_help": {
        "en": "Raising it lets a single run reach further into Earn, so a larger order can be funded. This is what makes the limit scale with your portfolio instead of staying a fixed number of USDC.",
        "cs": "Zvýšení pustí jeden běh hlouběji do Earnu, takže lze zafinancovat větší příkaz. Právě tohle dělá z meze číslo, které roste s portfoliem, místo pevné částky v USDC.",
    },
    "earn_funding_run_amount_label": {
        "en": "But never more per run (USDC)",
        "cs": "Ale nikdy víc na běh (USDC)",
    },
    "earn_funding_run_amount_help": {
        "en": "A flat backstop on a single run. Set it low enough to bind on every portfolio and the percentage above stops having any effect.",
        "cs": "Plochá pojistka na jeden běh. Když ji nastavíte tak nízko, že váže na každém portfoliu, procento výše přestane mít jakýkoli vliv.",
    },
    "earn_funding_day_pct_label": {
        "en": "One day may release (% of portfolio)",
        "cs": "Jeden den smí uvolnit (% portfolia)",
    },
    "earn_funding_day_pct_help": {
        "en": "The whole day's allowance, counted across every run. Lowering it slows how fast savings can be drawn down when the schedule runs often; a two-hourly schedule reaches the per-run limit twelve times a day.",
        "cs": "Denní příděl napříč všemi běhy. Snížení zpomalí, jak rychle se spoření rozpouští při častém rozvrhu; dvouhodinový rozvrh sáhne na strop běhu dvanáctkrát denně.",
    },
    "earn_funding_day_amount_label": {
        "en": "But never more per day (USDC)",
        "cs": "Ale nikdy víc za den (USDC)",
    },
    "earn_funding_day_amount_help": {
        "en": "A flat backstop on the day. Only redemptions that actually went through count against it; a plan that was prepared and never confirmed moved no money.",
        "cs": "Plochá pojistka na den. Počítají se jen výběry, které skutečně proběhly; připravený a nepotvrzený plán žádné peníze nepřesunul.",
    },
    "earn_funding_reserve_label": {
        "en": "Always leave in Earn (USDC)",
        "cs": "Vždy nechat v Earnu (USDC)",
    },
    "earn_funding_reserve_help": {
        "en": "Untouchable, whatever the limits above allow. Zero is a real answer and means the balance may be drawn to nothing.",
        "cs": "Nedotknutelné bez ohledu na meze výše. Nula je platná odpověď a znamená, že zůstatek smí být vyčerpán do nuly.",
    },
    "earn_funding_save_button": {
        "en": "Save funding limits",
        "cs": "Uložit meze financování",
    },
    "limits_suggested_button": {
        "en": "Use suggested",
        "cs": "Použít doporučené",
    },
    "trade_sizing_title": {
        "en": "How large an order the analysis proposes",
        "cs": "Jak velký příkaz analýza navrhne",
    },
    "trade_sizing_description": {
        "en": "One layer before the cap above. These decide what size the analysis considers appropriate; the cap decides what may reach the exchange whatever the analysis concluded. Every value here is a ceiling and the order becomes the smallest of them, together with what your account can actually pay - so raising any one of them on its own cannot enlarge an order, because another ceiling then binds instead.",
        "cs": "O úroveň dřív než strop výše. Tohle rozhoduje, jakou velikost analýza považuje za přiměřenou; strop rozhoduje, co smí odejít na burzu bez ohledu na to, k čemu analýza došla. Každá hodnota je strop a příkaz je jejich minimem spolu s tím, co účet reálně zaplatí - zvýšení jediné z nich proto příkaz zvětšit nemůže, protože pak váže jiný strop.",
    },
    "trade_sizing_trade_pct_label": {
        "en": "Order size (% of portfolio)",
        "cs": "Velikost příkazu (% portfolia)",
    },
    "trade_sizing_trade_pct_help": {
        "en": "Raising it allows larger orders on every portfolio. This is the setting that makes the same configuration behave sensibly whether you hold 500 or 50,000.",
        "cs": "Zvýšení dovolí větší příkazy na každém portfoliu. Právě tohle nastavení zajišťuje, že se stejná konfigurace chová rozumně, ať držíte 500 nebo 50 000.",
    },
    "trade_sizing_trade_amount_label": {
        "en": "Never more than (USDC)",
        "cs": "Nikdy víc než (USDC)",
    },
    "trade_sizing_trade_amount_help": {
        "en": "A flat backstop for the far end. Lowering it tightens every order; set low enough it binds on every portfolio and the percentage above stops having any effect.",
        "cs": "Plochá pojistka pro krajní případ. Snížení stáhne každý příkaz; když ji nastavíte tak nízko, že váže na každém portfoliu, procento výše přestane mít jakýkoli vliv.",
    },
    "trade_sizing_position_pct_label": {
        "en": "One order into one asset (% of portfolio)",
        "cs": "Jeden příkaz do jednoho aktiva (% portfolia)",
    },
    "trade_sizing_position_pct_help": {
        "en": "Lowering it tightens how much of the portfolio a single buy may put into one asset. It bounds the order, not what you end up holding - repeated buys can still accumulate past it, and what you already own is not counted.",
        "cs": "Snížení stáhne, kolik z portfolia smí jeden nákup vložit do jednoho aktiva. Omezuje příkaz, ne výsledný stav - opakované nákupy se přes něj pořád můžou nasčítat a to, co už držíte, se nezapočítává.",
    },
    "trade_sizing_capital_pct_label": {
        "en": "One order from trading capital (% of portfolio)",
        "cs": "Jeden příkaz z obchodního kapitálu (% portfolia)",
    },
    "trade_sizing_capital_pct_help": {
        "en": "The share of the portfolio a single tactical order may draw on. Like the one above it bounds each order rather than the running total, so lowering it slows how fast trading can build a position rather than capping the position itself.",
        "cs": "Podíl portfolia, ze kterého smí čerpat jeden taktický příkaz. Stejně jako výše omezuje jednotlivý příkaz, ne průběžný součet - snížení tedy zpomalí, jak rychle obchodování pozici vybuduje, spíš než že by pozici zastropovalo.",
    },
    "trade_sizing_risk_pct_label": {
        "en": "Risked per trade (% of portfolio)",
        "cs": "Riskováno na obchod (% portfolia)",
    },
    "trade_sizing_risk_pct_help": {
        "en": "How much of the portfolio is lost if the stop loss is hit. Sized against the stop, so a tighter stop allows a larger position for the same risk. Ignored when an order has no stop loss, because there is then no defined loss to size against.",
        "cs": "Kolik z portfolia se ztratí, když se dosáhne stop lossu. Počítá se proti stopu, takže těsnější stop dovolí větší pozici při stejném riziku. Bez stop lossu se ignoruje, protože pak není definovaná ztráta, proti které měřit.",
    },
    "trade_sizing_save_button": {
        "en": "Save sizing",
        "cs": "Uložit velikosti",
    },
    "replay_app_tour_button": {
        "en": "Replay app tour",
        "cs": "Zopakovat prohlídku aplikace",
    },
    "settings_checking_status": {
        "en": "Checking...",
        "cs": "Kontroluji...",
    },
    "binance_readonly_connection_title": {
        "en": "Binance read-only connection",
        "cs": "Read-only připojení k Binance",
    },
    "check_readonly_access_button": {
        "en": "Check read-only access",
        "cs": "Zkontrolovat read-only přístup",
    },
    "settings_ai_provider_title": {
        "en": "AI provider",
        "cs": "Poskytovatel AI",
    },
    "settings_check_ai_provider_button": {
        "en": "Check AI provider",
        "cs": "Zkontrolovat poskytovatele AI",
    },
    "configure_ai_models_button": {
        "en": "Configure AI models",
        "cs": "Nastavit modely AI",
    },
    "onboarding_profile_title": {
        "en": "Onboarding profile",
        "cs": "Onboarding profil",
    },
    "open_wizard_button": {
        "en": "Open wizard",
        "cs": "Otevřít průvodce",
    },
    "use_safe_defaults_button": {
        "en": "Use safe defaults",
        "cs": "Použít bezpečné výchozí hodnoty",
    },
    "privacy_data_title": {
        "en": "Privacy & Data",
        "cs": "Soukromí a data",
    },
    "privacy_data_description": {
        "en": "Coinductor is local-first: it reads only what is needed for portfolio management and keeps project data on this computer unless you opt into an external AI provider.",
        "cs": "Coinductor je navržen lokálně: čte pouze to, co je potřeba pro správu portfolia, a data projektu ponechává na tomto počítači, dokud se sami nerozhodnete pro externího poskytovatele AI.",
    },
    "reset_onboarding_button": {
        "en": "Reset onboarding",
        "cs": "Resetovat onboarding",
    },
    "delete_local_data_button": {
        "en": "Delete local data",
        "cs": "Smazat lokální data",
    },
    "export_diagnostics_button": {
        "en": "Export diagnostics",
        "cs": "Exportovat diagnostiku",
    },
    "privacy_data_note": {
        "en": "Reset onboarding only changes preferences. Delete local data permanently removes the local files you select; it never touches anything outside this project folder.",
        "cs": "Reset onboardingu mění pouze preference. Delete local data trvale odstraní vybrané lokální soubory; nikdy se nedotkne ničeho mimo tuto složku projektu.",
    },
    "system_readiness_title": {
        "en": "System readiness",
        "cs": "Připravenost systému",
    },
    "safety_baseline_title": {
        "en": "Safety baseline",
        "cs": "Základní zabezpečení",
    },
    "safety_baseline_secrets_note": {
        "en": "Checks only report whether secrets exist; they never display or transmit them.",
        "cs": "Kontroly pouze ohlásí, zda přístupové údaje existují; nikdy je nezobrazí ani neodešlou.",
    },
    "safety_baseline_path_note": {
        "en": "Selecting an onboarding path does not place orders or change configuration.",
        "cs": "Výběr cesty onboardingu nezadává příkazy ani nemění konfiguraci.",
    },
    "safety_baseline_live_note": {
        "en": "Live execution retains separate preview, limits, and explicit confirmation gates.",
        "cs": "Live provádění si zachovává samostatný náhled, limity a explicitní potvrzovací brány.",
    },
    "safety_stage_prefix": {
        "en": "Stage:",
        "cs": "Stupeň:",
    },
    "register_bot_dialog_title": {
        "en": "Register an active Binance bot",
        "cs": "Registrovat aktivního bota Binance",
    },
    "register_bot_warning": {
        "en": "This records a bot that you already created in Binance. Coinductor does not create, stop, or modify the Binance bot from this form.",
        "cs": "Tento formulář pouze zaznamenává bota, kterého jste již vytvořili na Binance. Coinductor z tohoto formuláře bota na Binance nevytváří, nezastavuje ani neupravuje.",
    },
    "tab_spot_grid": {
        "en": "Spot Grid",
        "cs": "Spot Grid",
    },
    "tab_rebalancing": {
        "en": "Rebalancing",
        "cs": "Rebalancing",
    },
    "grid_tab_description": {
        "en": "Copy the exact active Grid parameters from Binance. Price range, entry, TP/SL, and creation time are used to identify review conditions.",
        "cs": "Zkopírujte přesné aktivní parametry Gridu z Binance. Cenové rozpětí, vstup, TP/SL a čas vytvoření se používají k určení podmínek pro kontrolu.",
    },
    "import_latest_recommendation_button": {
        "en": "Import latest recommendation",
        "cs": "Importovat poslední doporučení",
    },
    "grid_import_notice_template": {
        "en": "Imported proposed values from run {run}. Compare every field with the bot you actually created in Binance; missing values remain blank.",
        "cs": "Importovány navrhované hodnoty z běhu {run}. Porovnejte každé pole s botem, kterého jste skutečně vytvořili na Binance; chybějící hodnoty zůstanou prázdné.",
    },
    "field_local_name": {
        "en": "Local name *",
        "cs": "Lokální název *",
    },
    "field_binance_bot_id": {
        "en": "Binance bot ID",
        "cs": "Binance bot ID",
    },
    "field_symbol": {
        "en": "Symbol *",
        "cs": "Symbol *",
    },
    "field_grid_spacing": {
        "en": "Grid spacing *",
        "cs": "Rozestup Gridu *",
    },
    "field_lower_price": {
        "en": "Lower price *",
        "cs": "Spodní cena *",
    },
    "field_upper_price": {
        "en": "Upper price *",
        "cs": "Horní cena *",
    },
    "field_number_of_grids": {
        "en": "Number of grids *",
        "cs": "Počet Gridů *",
    },
    "field_investment_usdc": {
        "en": "Investment in USDC *",
        "cs": "Investice v USDC *",
    },
    "field_entry_price": {
        "en": "Entry price *",
        "cs": "Vstupní cena *",
    },
    "field_created_at": {
        "en": "Created at",
        "cs": "Vytvořeno",
    },
    "field_stop_loss": {
        "en": "Stop loss *",
        "cs": "Stop loss *",
    },
    "field_take_profit": {
        "en": "Take profit *",
        "cs": "Take profit *",
    },
    "field_local_notes": {
        "en": "Local notes",
        "cs": "Lokální poznámky",
    },
    "verified_matches_bot_checkbox": {
        "en": "I verified that these values match the currently active bot in Binance.",
        "cs": "Ověřil(a) jsem, že tyto hodnoty odpovídají aktuálně aktivnímu botovi na Binance.",
    },
    "working_status": {
        "en": "Working...",
        "cs": "Pracuji...",
    },
    "register_and_refresh_button": {
        "en": "Register and refresh monitoring",
        "cs": "Registrovat a obnovit sledování",
    },
    "rebalancing_tab_description": {
        "en": "Use comma-separated values in the same order for assets, target weights, and entry prices. Target weights must total exactly 100%.",
        "cs": "Použijte hodnoty oddělené čárkou ve stejném pořadí pro aktiva, cílové váhy a vstupní ceny. Cílové váhy musí dát dohromady přesně 100 %.",
    },
    "rebalancing_import_notice_template": {
        "en": "Imported proposed values from run {run}. Compare every field with Binance; entry prices stay blank if the latest run did not contain all required markets.",
        "cs": "Importovány navrhované hodnoty z běhu {run}. Porovnejte každé pole s Binance; vstupní ceny zůstanou prázdné, pokud poslední běh neobsahoval všechny potřebné trhy.",
    },
    "allowed_assets_prefix": {
        "en": "Allowed assets:",
        "cs": "Povolená aktiva:",
    },
    "field_assets": {
        "en": "Assets *",
        "cs": "Aktiva *",
    },
    "field_target_weights": {
        "en": "Target weights (%) *",
        "cs": "Cílové váhy (%) *",
    },
    "field_entry_prices_usdc": {
        "en": "Entry prices in USDC *",
        "cs": "Vstupní ceny v USDC *",
    },
    "field_rebalance_threshold": {
        "en": "Rebalance threshold (%) *",
        "cs": "Práh rebalancování (%) *",
    },
    "close_button": {
        "en": "Close",
        "cs": "Zavřít",
    },
    "app_tour_quick_tour_label": {
        "en": "QUICK TOUR",
        "cs": "RYCHLÁ PROHLÍDKA",
    },
    "app_tour_skip_button": {
        "en": "Skip tour",
        "cs": "Přeskočit prohlídku",
    },
    "app_tour_back_button": {
        "en": "Back",
        "cs": "Zpět",
    },
    "app_tour_next_button": {
        "en": "Next",
        "cs": "Další",
    },
    "app_tour_finish_button": {
        "en": "Finish",
        "cs": "Dokončit",
    },
    "active_strategy_fallback_title": {
        "en": "Active strategy",
        "cs": "Aktivní strategie",
    },
    "unknown_status_fallback": {
        "en": "Unknown",
        "cs": "Neznámý",
    },
    "strategy_monitor_note": {
        "en": "Monitoring compares registered parameters with locally collected market data. Verify profit, fills, and final bot status directly in Binance before changing or stopping a bot.",
        "cs": "Sledování porovnává registrované parametry s lokálně sesbíranými tržními daty. Před změnou nebo zastavením bota vždy ověřte zisk, výplně a konečný stav bota přímo na Binance.",
    },
    "update_local_monitoring_status_title": {
        "en": "Update local monitoring status",
        "cs": "Aktualizovat lokální stav sledování",
    },
    "update_local_status_warning": {
        "en": "First pause, stop, or close the bot in Binance. This control only updates Coinductor's local monitoring record and never sends a command to Binance.",
        "cs": "Nejprve bota pozastavte, zastavte nebo uzavřete na Binance. Tento ovládací prvek pouze aktualizuje lokální záznam sledování v Coinductoru a nikdy neodesílá příkaz na Binance.",
    },
    "new_local_status_label": {
        "en": "New local status",
        "cs": "Nový lokální stav",
    },
    "update_local_record_button": {
        "en": "Update local record",
        "cs": "Aktualizovat lokální záznam",
    },
    "already_applied_status_checkbox": {
        "en": "I already applied this status change to the bot in Binance.",
        "cs": "Tuto změnu stavu jsem již na botovi na Binance provedl(a).",
    },
    "status_records_note": {
        "en": "Paused, Stopped, and Closed records leave active monitoring but remain in the local registry and historical run data.",
        "cs": "Záznamy Paused, Stopped a Closed opustí aktivní sledování, ale zůstávají v lokálním registru a historických datech běhů.",
    },
    "manage_live_api_dialog_title": {
        "en": "Manage live trading API",
        "cs": "Spravovat live trading API",
    },
    "live_api_dialog_description": {
        "en": "Store and verify the separate Binance key used by guarded live actions. Managing credentials never changes the Safety stage or submits an order.",
        "cs": "Uložte a ověřte samostatný klíč Binance používaný pro zabezpečené live akce. Správa přístupových údajů nikdy nemění Safety stage ani nezadává příkaz.",
    },
    "live_api_dialog_warning": {
        "en": "Use a separate key with Reading + Spot trading only, trusted-IP restriction enabled, and withdrawals disabled. Dynamic-IP users should keep live execution locked unless they can maintain the whitelist.",
        "cs": "Používejte samostatný klíč pouze s Reading + Spot trading, zapnutým omezením na důvěryhodnou IP a vypnutými výběry. Uživatelé s dynamickou IP by měli live provádění nechat uzamčené, pokud nedokážou udržovat aktuální whitelist.",
    },
    "open_setup_guide_button": {
        "en": "Open setup guide",
        "cs": "Otevřít návod na nastavení",
    },
    "live_api_checkbox_separate_key": {
        "en": "This key is separate from the read-only key",
        "cs": "Tento klíč je oddělený od read-only klíče",
    },
    "live_api_checkbox_ip_restricted": {
        "en": "Trusted-IP restriction is enabled in Binance",
        "cs": "Na Binance je zapnuté omezení na důvěryhodnou IP",
    },
    "live_api_checkbox_no_withdrawals": {
        "en": "Withdrawals and transfer permissions remain disabled",
        "cs": "Oprávnění k výběrům a převodům zůstávají vypnutá",
    },
    "save_live_trading_key_button": {
        "en": "Save live trading key",
        "cs": "Uložit live trading klíč",
    },
    "live_trading_key_saved_toast": {
        "en": "Live trading key saved locally; submit remains locked",
        "cs": "Live trading klíč uložen lokálně; odeslání zůstává uzamčené",
    },
    "checking_permissions_status": {
        "en": "Checking permissions...",
        "cs": "Kontroluji oprávnění...",
    },
    "live_submit_control_note": {
        "en": "Live submit remains controlled by Safety stage, fresh validation, and a separate confirmation for every trade or OCO action.",
        "cs": "Live odeslání zůstává řízeno Safety stage, čerstvou validací a samostatným potvrzením pro každý obchod nebo OCO akci.",
    },
    "confirm_safety_stage_title": {
        "en": "Confirm Safety stage change",
        "cs": "Potvrdit změnu Safety stage",
    },
    "safety_confirm_live_enabled_note": {
        "en": "This enables guarded live submit controls. It does not place an order, but future READY actions can be submitted after their own confirmation.",
        "cs": "Tímto se zapnou ovládací prvky pro zabezpečené live odeslání. Nezadává se tím žádný příkaz, ale budoucí akce ve stavu READY lze po vlastním potvrzení odeslat.",
    },
    "safety_confirm_armed_note": {
        "en": "This records that the live API permissions were verified and arms guarded workflows. Live submit remains locked.",
        "cs": "Tímto se zaznamená, že oprávnění live API byla ověřena, a odjistí se zabezpečené postupy. Live odeslání zůstává uzamčené.",
    },
    "safety_confirm_preview_note": {
        "en": "This enables mainnet previews only. No order or exchange-changing action can be submitted.",
        "cs": "Tímto se povolí pouze mainnet náhledy. Nelze odeslat žádný příkaz ani akci měnící stav burzy.",
    },
    "confirmation_phrase_prefix": {
        "en": "Confirmation phrase:",
        "cs": "Potvrzovací fráze:",
    },
    "copy_phrase_button": {
        "en": "Copy phrase",
        "cs": "Kopírovat frázi",
    },
    "cancel_button": {
        "en": "Cancel",
        "cs": "Zrušit",
    },
    "change_safety_stage_button": {
        "en": "Change Safety stage",
        "cs": "Změnit Safety stage",
    },
    "action_detail_fallback_title": {
        "en": "Action detail",
        "cs": "Detail akce",
    },
    "action_note_trade_resync": {
        "en": "The current recommendation and the last live trade are separate. Run a fresh analysis to synchronize Binance order and OCO status again.",
        "cs": "Aktuální doporučení a poslední live obchod jsou oddělené. Spusťte novou analýzu pro opětovnou synchronizaci stavu příkazu a OCO na Binance.",
    },
    "action_note_trade_locked": {
        "en": "Live trade submission is separate from review. It stays locked unless the latest BUY preview, live key, safety stage, and confirmation text all pass.",
        "cs": "Odeslání live obchodu je oddělené od kontroly. Zůstává uzamčené, dokud neprojdou zároveň poslední BUY náhled, live klíč, safety stage i potvrzovací text.",
    },
    "action_note_oco": {
        "en": "OCO protection is a separate SELL order pair. Submission requires a READY preview and its own explicit confirmation.",
        "cs": "OCO ochrana je samostatný pár SELL příkazů. Odeslání vyžaduje náhled ve stavu READY a vlastní explicitní potvrzení.",
    },
    "action_note_earn_redeem": {
        "en": "Earn redeem moves funds from Flexible Earn back to Spot so a trade can be funded. Submission requires a READY preview and its own explicit confirmation.",
        "cs": "Earn redeem přesune prostředky z Flexible Earn zpět na Spot, aby bylo možné obchod financovat. Odeslání vyžaduje náhled ve stavu READY a vlastní explicitní potvrzení.",
    },
    "action_note_lifecycle": {
        "en": "Coinductor detected a lifecycle condition from locally registered parameters. Verify the real bot state in Binance before updating the local record.",
        "cs": "Coinductor zjistil stav životního cyklu z lokálně registrovaných parametrů. Před aktualizací lokálního záznamu ověřte skutečný stav bota na Binance.",
    },
    "action_note_review_only": {
        "en": "This dialog is review-only. Manual bot setup remains outside automatic desktop submission.",
        "cs": "Tento dialog je pouze ke kontrole. Ruční nastavení bota zůstává mimo automatické odesílání z desktopové aplikace.",
    },
    "guard_title_oco": {
        "en": "Guarded position protection",
        "cs": "Zabezpečená ochrana pozice",
    },
    "guard_title_earn_redeem": {
        "en": "Guarded Earn redeem",
        "cs": "Zabezpečený Earn redeem",
    },
    "guard_title_trade": {
        "en": "Guarded live trade",
        "cs": "Zabezpečený live obchod",
    },
    "guard_ready_oco": {
        "en": "This will run a fresh validation pass and submit the OCO pair only if the position protection preview is still ready.",
        "cs": "Toto spustí novou validaci a odešle pár OCO příkazů, pouze pokud je náhled ochrany pozice stále ready.",
    },
    "guard_ready_earn_redeem": {
        "en": "This will run a fresh validation pass and redeem from Flexible Earn only if the preview is still ready.",
        "cs": "Toto spustí novou validaci a provede redeem z Flexible Earn, pouze pokud je náhled stále ready.",
    },
    "guard_ready_trade": {
        "en": "This will run a fresh validation pass and submit only if the new mainnet preview is still ready.",
        "cs": "Toto spustí novou validaci a odešle příkaz, pouze pokud je nový mainnet náhled stále ready.",
    },
    "live_submit_locked_fallback": {
        "en": "Live submit is locked.",
        "cs": "Live odeslání je uzamčené.",
    },
    "locked_button_fallback": {
        "en": "Locked",
        "cs": "Uzamčeno",
    },
    "challenge_hold_title": {
        "en": "Challenge this HOLD",
        "cs": "Zpochybnit tento HOLD",
    },
    "challenge_hold_description": {
        "en": "Request a BUY evaluation for a specific allowed symbol instead of accepting HOLD. This does not bypass any check: bankroll, exposure, consensus/RSI/trend, stop-loss, and live-submit confirmation all still apply and can still reject it.",
        "cs": "Vyžádejte si vyhodnocení BUY pro konkrétní povolený symbol místo přijetí HOLD. Tímto se neobchází žádná kontrola: bankroll, expozice, consensus/RSI/trend, stop-loss i potvrzení live odeslání stále platí a mohou požadavek stále odmítnout.",
    },
    "challenge_hold_button": {
        "en": "Challenge HOLD",
        "cs": "Zpochybnit HOLD",
    },
    "open_active_strategies_button": {
        "en": "Open Active Strategies",
        "cs": "Otevřít Active Strategies",
    },
    "confirm_live_trade_title": {
        "en": "Confirm guarded live trade",
        "cs": "Potvrdit zabezpečený live obchod",
    },
    "confirm_live_trade_description": {
        "en": "Coinductor will run a fresh guarded analysis and may submit a mainnet MARKET BUY only if the preview remains ready. This is not a 24/7 process and it will not bypass deterministic limits.",
        "cs": "Coinductor spustí novou zabezpečenou analýzu a odešle mainnet MARKET BUY pouze pokud náhled zůstane ready. Nejde o nepřetržitý proces a neobejde deterministické limity.",
    },
    "confirm_live_trade_warning": {
        "en": "Type CONFIRM_MAINNET_ORDER exactly. Never use this if Binance trusted-IP restrictions, live key permissions, or funding look wrong.",
        "cs": "Napište přesně CONFIRM_MAINNET_ORDER. Nikdy toto nepoužívejte, pokud omezení na důvěryhodnou IP na Binance, oprávnění live klíče nebo financování vypadají špatně.",
    },
    "run_guarded_submit_button": {
        "en": "Run guarded submit",
        "cs": "Spustit zabezpečené odeslání",
    },
    "attach_screenshot_dialog_title": {
        "en": "Attach a screenshot or image",
        "cs": "Připojit screenshot nebo obrázek",
    },
    "ai_chat_history_title": {
        "en": "AI chat history",
        "cs": "Historie chatu s AI",
    },
    "ai_chat_history_storage_note": {
        "en": "Stored locally. The newest 20 conversations are kept.",
        "cs": "Ukládáno lokálně. Uchovává se posledních 20 konverzací.",
    },
    "ai_chat_history_empty": {
        "en": "No saved conversations yet. A chat appears here after its first completed answer.",
        "cs": "Zatím nejsou uložené žádné konverzace. Chat se zde objeví po první dokončené odpovědi.",
    },
    "ai_chat_history_messages_label": {
        "en": "messages",
        "cs": "zpráv",
    },
    "open_button": {
        "en": "Open",
        "cs": "Otevřít",
    },
    "confirm_oco_title": {
        "en": "Confirm OCO position protection",
        "cs": "Potvrdit OCO ochranu pozice",
    },
    "confirm_oco_description": {
        "en": "Coinductor will run a fresh mainnet validation and may submit a linked take-profit and stop-loss SELL pair for the open position. Binance keeps this protection active while Coinductor is closed.",
        "cs": "Coinductor spustí novou mainnet validaci a odešle propojený pár SELL příkazů take-profit a stop-loss pro otevřenou pozici. Binance udržuje tuto ochranu aktivní i po zavření Coinductoru.",
    },
    "confirm_oco_warning": {
        "en": "Type CONFIRM_MAINNET_OCO exactly. Recheck the quantity, take-profit, stop-loss, trusted IP, and live-key permissions before continuing.",
        "cs": "Napište přesně CONFIRM_MAINNET_OCO. Před pokračováním znovu zkontrolujte množství, take-profit, stop-loss, důvěryhodnou IP a oprávnění live klíče.",
    },
    "submit_oco_button": {
        "en": "Submit OCO protection",
        "cs": "Odeslat OCO ochranu",
    },
    "confirm_earn_redeem_title": {
        "en": "Confirm Earn redeem",
        "cs": "Potvrdit Earn redeem",
    },
    "confirm_earn_redeem_description": {
        "en": "Coinductor will run a fresh guarded analysis and may redeem the previewed amount from Flexible Earn back to Spot, only if the preview remains ready. This does not place a trade by itself.",
        "cs": "Coinductor spustí novou zabezpečenou analýzu a provede redeem náhledové částky z Flexible Earn zpět na Spot, pouze pokud náhled zůstane ready. Samo o sobě to nezadává obchod.",
    },
    "confirm_earn_redeem_warning": {
        "en": "Type CONFIRM_EARN_REDEEM exactly. Recheck the asset and amount before continuing.",
        "cs": "Napište přesně CONFIRM_EARN_REDEEM. Před pokračováním znovu zkontrolujte aktivum a částku.",
    },
    "submit_earn_redeem_button": {
        "en": "Submit Earn redeem",
        "cs": "Odeslat Earn redeem",
    },
    "deploy_tranche_dialog_title_template": {
        "en": "Deploy {asset} tranche",
        "cs": "Nasadit tranši {asset}",
    },
    "deploy_tranche_description_template": {
        "en": "This runs the next tranche for {asset} (target {pct}% of the basket) using the total USDC budget and tranche count set on the Action Plan page. Every existing safety gate applies except market-timing consensus, which is intentionally skipped for this initial deployment.",
        "cs": "Toto spustí další tranši pro {asset} (cíl {pct}% košíku) s použitím celkového rozpočtu v USDC a počtu tranší nastavených na stránce Action Plan. Platí všechny stávající bezpečnostní brány kromě consensus časování trhu, který je pro toto počáteční nasazení záměrně vynechán.",
    },
    "mode_label": {
        "en": "Mode:",
        "cs": "Režim:",
    },
    "mainnet_submit_warning": {
        "en": "Mainnet submit also requires the Safety stage to be LIVE_ENABLED and will place a real order.",
        "cs": "Mainnet odeslání navíc vyžaduje, aby byl Safety stage LIVE_ENABLED, a zadá skutečný příkaz.",
    },
    "validate_only_button": {
        "en": "Validate only",
        "cs": "Pouze validovat",
    },
    # The phrase is shown beside this line to be copied, rather than embedded
    # in it and retyped by hand - which is what the wording used to ask for.
    "submit_for_real_prefix": {
        "en": "To submit for real, copy this phrase into the field below:",
        "cs": "Pro skutečné odeslání zkopírujte tuhle frázi do pole níže:",
    },
    "copy_button": {
        "en": "Copy",
        "cs": "Kopírovat",
    },
    "submit_tranche_button": {
        "en": "Submit tranche",
        "cs": "Odeslat tranši",
    },
    "guide_section_fallback": {
        "en": "Guide",
        "cs": "Návod",
    },
    "guide_footer_note": {
        "en": "Screenshots and more detailed provider-specific steps can be added to this guide later.",
        "cs": "Screenshoty a podrobnější kroky specifické pro poskytovatele mohou být do tohoto návodu doplněny později.",
    },
    "reset_onboarding_profile_title": {
        "en": "Reset onboarding profile",
        "cs": "Resetovat onboarding profil",
    },
    "reset_onboarding_profile_note1": {
        "en": "This resets only your onboarding profile: region, risk preference, automation preference, budget, and planner settings.",
        "cs": "Toto resetuje pouze váš onboarding profil: region, preferenci rizika, preferenci automatizace, rozpočet a nastavení plánovače.",
    },
    "reset_onboarding_profile_note2": {
        "en": "API keys, reports, database history, role overrides, and safety state are not deleted.",
        "cs": "API klíče, reporty, historie v databázi, přepsané role a stav zabezpečení se nemažou.",
    },
    "delete_local_app_data_title": {
        "en": "Delete local app data",
        "cs": "Smazat lokální data aplikace",
    },
    "delete_everything_checkbox": {
        "en": "Delete everything",
        "cs": "Smazat vše",
    },
    "delete_local_data_warning": {
        "en": "This permanently deletes the selected local files. It cannot be undone. Type DELETE to confirm.",
        "cs": "Toto trvale smaže vybrané lokální soubory. Nelze vzít zpět. Pro potvrzení napište DELETE.",
    },
    "delete_selected_local_data_button": {
        "en": "Delete selected local data",
        "cs": "Smazat vybraná lokální data",
    },
    "type_delete_to_continue_button": {
        "en": "Type DELETE to continue",
        "cs": "Pro pokračování napište DELETE",
    },
    "data_source_label": {
        "en": "Data source",
        "cs": "Zdroj dat",
    },
    "generate_ai_summary_checkbox": {
        "en": "Generate AI summary",
        "cs": "Vygenerovat shrnutí od AI",
    },
    "allow_ai_market_ranking_checkbox": {
        "en": "Allow AI market ranking",
        "cs": "Povolit AI žebříček trhu",
    },
    "include_mainnet_preview_checkbox": {
        "en": "Include mainnet execution preview",
        "cs": "Zahrnout mainnet náhled provedení",
    },
    "mainnet_preview_locked_checkbox": {
        "en": "Mainnet preview locked by safety stage",
        "cs": "Mainnet náhled uzamčen podle safety stage",
    },
    "run_dialog_note": {
        "en": "This screen never submits orders. Confirmed execution remains a separate guarded workflow.",
        "cs": "Tato obrazovka nikdy nezadává příkazy. Potvrzené provedení zůstává samostatným zabezpečeným postupem.",
    },
    "start_analysis_button": {
        "en": "Start analysis",
        "cs": "Spustit analýzu",
    },
    "app_title": {
        "en": "Coinductor",
        "cs": "Coinductor",
    },
    "app_tagline": {
        "en": "Portfolio automation",
        "cs": "Automatizace portfolia",
    },
    "sidebar_safety_caption": {
        "en": "SAFETY",
        "cs": "BEZPEČNOST",
    },
    "sidebar_binance_caption": {
        "en": "BINANCE",
        "cs": "BINANCE",
    },
    "safety_summary_live_guarded": {
        "en": "Live guarded",
        "cs": "Live zabezpečeno",
    },
    "safety_summary_preview_only": {
        "en": "Preview only",
        "cs": "Pouze náhled",
    },
    "safety_summary_no_exchange_changes": {
        "en": "No exchange changes",
        "cs": "Žádné změny na burze",
    },
    "nav_overview": {"en": "Overview", "cs": "Přehled"},
    "nav_portfolio": {"en": "Portfolio", "cs": "Portfolio"},
    "nav_live_actions": {"en": "Live Actions", "cs": "Živé akce"},
    "nav_action_plan": {"en": "Action Plan", "cs": "Plán akcí"},
    "nav_active_strategies": {"en": "Active Strategies", "cs": "Aktivní strategie"},
    "nav_run_history": {"en": "Run History", "cs": "Historie běhů"},
    "nav_ai_assistant": {"en": "AI Assistant", "cs": "AI asistent"},
    "nav_help_guides": {"en": "Help & Guides", "cs": "Nápověda a návody"},
    "nav_settings": {"en": "Settings", "cs": "Nastavení"},
    "nav_new_listings": {"en": "New listings", "cs": "Nové listingy"},
    "nav_automation": {"en": "Automation", "cs": "Automatizace"},
    "automation_page_title": {"en": "Automation", "cs": "Automatizace"},
    "automation_page_subtitle": {
        "en": "Everything that starts on its own, and when it runs next. Nothing here can place an order — a scheduled run only ever reads.",
        "cs": "Všechno, co se spouští samo, a kdy poběží příště. Nic z toho nemůže zadat příkaz — naplánovaný běh jen čte.",
    },
    "automation_page_empty": {
        "en": "Nothing is scheduled. Coinductor runs only when you press Run analysis.",
        "cs": "Nic není naplánované. Coinductor běží jen tehdy, když stisknete Spustit analýzu.",
    },
    "automation_next_run": {"en": "Next", "cs": "Příště"},
    "automation_inactive": {"en": "Off", "cs": "Vypnuto"},
    "automation_configure": {"en": "Set up", "cs": "Nastavit"},
    # --- new listings page ---
    "listings_title": {
        "en": "New listings",
        "cs": "Nové listingy",
    },
    "listings_subtitle": {
        "en": "Pairs that appeared on Binance since Coinductor started watching.",
        "cs": "Páry, které se na Binance objevily od chvíle, kdy je Coinductor začal sledovat.",
    },
    "listings_not_a_signal": {
        "en": "This is a record, not a trade signal. Coinductor never buys a listing, and buying one at market in its first minutes is how the bots that got there first get paid — the book is thin and the price you see is not the price you fill at. Use this to watch what actually happens, and decide later.",
        "cs": "Tohle je záznam, ne obchodní signál. Coinductor listing nikdy nekoupí a nákup za tržní cenu v prvních minutách je přesně to, čím se platí botům, kteří tam byli dřív — kniha je tenká a cena, kterou vidíte, není cena, za kterou nakoupíte. Berte to jako pozorování a rozhodujte se až podle něj.",
    },
    "listings_watch_checkbox": {
        "en": "Watch for new listings",
        "cs": "Sledovat nové listingy",
    },
    "listings_interval_label": {
        "en": "Check every (minutes)",
        "cs": "Kontrolovat každých (minut)",
    },
    "listings_save_button": {
        "en": "Save",
        "cs": "Uložit",
    },
    "listings_check_now_button": {
        "en": "Check now",
        "cs": "Zkontrolovat teď",
    },
    "listings_empty": {
        "en": "Nothing yet. The first check records what is already listed as a starting point, so only pairs that appear after that show up here.",
        "cs": "Zatím nic. První kontrola si zapíše, co už je zalistované, jako výchozí stav — objeví se tu tedy jen páry, které přibydou potom.",
    },
    "listings_first_seen_template": {
        "en": "First seen {when}",
        "cs": "Poprvé zaznamenáno {when}",
    },
    "listings_allow_button": {
        "en": "Allow analysis",
        "cs": "Povolit analýzu",
    },
    "listings_allowed_button": {
        "en": "Analysis allowed",
        "cs": "Analýza povolena",
    },
    # --- app tour ---
    # One entry per step of the guided tour behind Settings > Replay app tour.
    # The nav label of each step is reused from the nav_* keys above.
    "app_tour_overview_title": {
        "en": "Your portfolio at a glance",
        "cs": "Portfolio na jednom místě",
    },
    "app_tour_overview_detail": {
        "en": "Overview shows the latest portfolio totals, readiness state, safety stage, and the clearest next action.",
        "cs": "Přehled ukazuje poslední součty portfolia, stav připravenosti, bezpečnostní stupeň a nejbližší jasnou akci.",
    },
    "app_tour_overview_tip": {
        "en": "Start a normal read-only analysis here. It never submits an order by itself.",
        "cs": "Tady spustíte běžnou analýzu, která jen čte. Sama nikdy nezadá příkaz.",
    },
    "app_tour_portfolio_title": {
        "en": "Review how every asset may be used",
        "cs": "Zkontrolujte, jak se smí s každým aktivem naložit",
    },
    "app_tour_portfolio_detail": {
        "en": "Portfolio lists all detected holdings and their roles, including protected assets, funding sources, trading assets, and dust.",
        "cs": "Portfolio vypisuje všechna nalezená aktiva a jejich role: chráněná aktiva, zdroje financování, obchodovaná aktiva a drobné zbytky.",
    },
    "app_tour_portfolio_tip": {
        "en": "You can override a role, but Coinductor keeps deterministic risk and funding limits in force.",
        "cs": "Roli můžete přepsat ručně, ale deterministické limity rizika a financování platí dál.",
    },
    "app_tour_live_actions_title": {
        "en": "Safety before execution",
        "cs": "Nejdřív zabezpečení, potom provedení",
    },
    "app_tour_live_actions_detail": {
        "en": "Live Actions holds the staged safety lock, the live API management workflow, and the cap on how large a single order may be.",
        "cs": "Živé akce obsahují stupňovaný bezpečnostní zámek, správu živého API klíče a strop na velikost jednoho příkazu.",
    },
    "app_tour_live_actions_tip": {
        "en": "Preview, Armed and Live Enabled decide whether an order may go; the size cap decides how big. Every real order still needs its own typed confirmation.",
        "cs": "Náhled, Připraveno a Živě povoleno rozhodují, jestli příkaz smí odejít; strop rozhoduje, jak velký. Každý skutečný příkaz stejně potřebuje vlastní vypsané potvrzení.",
    },
    "app_tour_action_plan_title": {
        "en": "One place for every run result",
        "cs": "Výsledek běhu na jednom místě",
    },
    "app_tour_action_plan_detail": {
        "en": "After an analysis, Action Plan consolidates the trade decision, Spot Grid plan, Rebalancing plan, blockers, and next-review timing.",
        "cs": "Po analýze sdruží Plán akcí rozhodnutí o obchodu, plán Spot Gridu, plán rebalancování, blokátory a termín další kontroly.",
    },
    "app_tour_action_plan_tip": {
        "en": "A READY action can expose a guarded confirmation. HOLD, Watched, and Blocked remain review-only.",
        "cs": "U akce ve stavu READY se může objevit zabezpečené potvrzení. HOLD, Sledováno a Blokováno zůstávají jen ke kontrole.",
    },
    "app_tour_active_strategies_title": {
        "en": "Monitor Binance bots you created",
        "cs": "Sledujte boty, které jste založili na Binance",
    },
    "app_tour_active_strategies_detail": {
        "en": "Register the real parameters of an active Grid or Rebalancing Bot so future runs can evaluate its lifecycle and health.",
        "cs": "Zaregistrujte skutečné parametry aktivního Grid nebo Rebalancing bota, aby další běhy mohly hodnotit jeho stav a průběh.",
    },
    "app_tour_active_strategies_tip": {
        "en": "Coinductor currently guides bot creation in Binance; registration here does not create or modify the bot.",
        "cs": "Coinductor vás zakládáním bota na Binance zatím jen provede. Registrace tady bota nevytvoří ani nezmění.",
    },
    "app_tour_run_history_title": {
        "en": "Every past run stays on record",
        "cs": "Každý proběhlý běh zůstává zaznamenaný",
    },
    "app_tour_run_history_detail": {
        "en": "Run History lists the latest analytical runs with their data mode, status, and decision, so you can trace what happened and when.",
        "cs": "Historie běhů vypisuje poslední analýzy s režimem dat, stavem a rozhodnutím, takže dohledáte co a kdy se stalo.",
    },
    "app_tour_run_history_tip": {
        "en": "REAL runs read your live Binance account. MOCK runs use example data and never touch it.",
        "cs": "Běhy REAL čtou váš skutečný účet na Binance. Běhy MOCK používají ukázková data a na účet vůbec nesáhnou.",
    },
    "app_tour_new_listings_title": {
        "en": "See what Binance just listed",
        "cs": "Uvidíte, co Binance právě zalistoval",
    },
    "app_tour_new_listings_detail": {
        "en": "Coinductor can watch for newly listed pairs and tell you when one appears. It records and notifies; it never buys.",
        "cs": "Coinductor umí sledovat nově zalistované páry a dát vědět, když nějaký přibude. Zaznamenává a upozorňuje; nikdy nenakupuje.",
    },
    "app_tour_new_listings_tip": {
        "en": "Buying a listing at market in its first minutes is how the bots that got there first get paid. Use this to watch, and decide later.",
        "cs": "Nákup listingu za tržní cenu v prvních minutách je to, čím se platí botům, kteří tam byli dřív. Berte to jako pozorování a rozhodujte se až podle něj.",
    },
    "app_tour_automation_title": {
        "en": "Everything that starts on its own",
        "cs": "Všechno, co se spouští samo",
    },
    "app_tour_automation_detail": {
        "en": "Set the analysis to run on a schedule while Coinductor is open, or register a Windows task so it also runs when it is closed. The list below shows what is active and when each one runs next.",
        "cs": "Nastavte, aby analýza běžela podle rozvrhu, dokud je Coinductor otevřený, nebo zaregistrujte úlohu ve Windows, ať běží i zavřený. Seznam pod tím ukazuje, co je aktivní a kdy co poběží příště.",
    },
    "app_tour_automation_tip": {
        "en": "A scheduled run only ever reads. It cannot place an order, because the confirmation you type is what authorises one and no timer can type.",
        "cs": "Naplánovaný běh jen čte. Příkaz zadat nemůže, protože ho povoluje potvrzení, které vypisujete vy, a to žádný časovač nenapíše.",
    },
    "app_tour_ai_assistant_title": {
        "en": "Ask for explanations, not permission bypasses",
        "cs": "Ptejte se na vysvětlení, ne na obejití pojistek",
    },
    "app_tour_ai_assistant_detail": {
        "en": "The assistant can explain reports, portfolio roles, settings, and market context using your configured local or cloud provider.",
        "cs": "Asistent umí vysvětlit reporty, role v portfoliu, nastavení a tržní souvislosti pomocí vašeho místního nebo cloudového modelu.",
    },
    "app_tour_ai_assistant_tip": {
        "en": "AI commentary supports decisions but cannot override deterministic safety gates or submit an action on its own.",
        "cs": "Hodnocení od AI je jen podpora rozhodování. Nemůže přebít deterministické pojistky ani samo něco odeslat.",
    },
    "app_tour_help_guides_title": {
        "en": "Detailed help stays available",
        "cs": "Podrobná nápověda je pořád po ruce",
    },
    "app_tour_help_guides_detail": {
        "en": "Open the built-in guides whenever you need step-by-step help with Ollama, Binance APIs, safety, or portfolio roles.",
        "cs": "Vestavěné návody otevřete, kdykoli potřebujete krok za krokem poradit s Ollamou, Binance API, zabezpečením nebo rolemi aktiv.",
    },
    "app_tour_help_guides_tip": {
        "en": "You can replay this tour later from Settings.",
        "cs": "Tuhle prohlídku si můžete kdykoli znovu pustit z Nastavení.",
    },
    "app_tour_settings_title": {
        "en": "Configuration and system status live here",
        "cs": "Nastavení a stav systému najdete tady",
    },
    "app_tour_settings_detail": {
        "en": "Settings holds your Binance and AI connections, the onboarding profile, and privacy controls - including disconnecting an AI model or deleting local data.",
        "cs": "V Nastavení je připojení k Binance a k AI, profil z průvodce a ovládání soukromí - včetně odpojení AI modelu nebo smazání lokálních dat.",
    },
    "app_tour_settings_tip": {
        "en": "Nothing here places an order. \"Delete local data\" does delete - it lists what it will remove and asks you to type DELETE first.",
        "cs": "Nic tady nezadá příkaz. \"Smazat lokální data\" opravdu maže - napřed vypíše, co odstraní, a chce po vás napsat DELETE.",
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
