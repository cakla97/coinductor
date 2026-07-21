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


class UiStringsService:
    def wizard_text(self, language: str) -> dict[str, str]:
        normalized = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        return {
            key: variants.get(normalized, variants[DEFAULT_LANGUAGE])
            for key, variants in WIZARD_STRINGS.items()
        }
