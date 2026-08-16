from __future__ import annotations

from dataclasses import dataclass
import unicodedata


@dataclass(frozen=True)
class UiKnowledgeEntry:
    name: str
    page: str
    aliases: tuple[str, ...]
    english: str
    czech: str
    guide_id: str = ""


# Maps a knowledge entry's page to the guide that documents it. Ordered so a
# specific page wins over "Settings" in compound page strings such as
# "Live Actions and Settings".
_PAGE_GUIDE_MAP: tuple[tuple[str, str], ...] = (
    ("Overview", "page-overview"),
    ("Portfolio", "page-portfolio"),
    ("Live Actions", "page-live-actions"),
    ("Action Plan", "page-action-plan"),
    ("Active Strategies", "page-active-strategies"),
    ("Run History", "page-run-history"),
    ("AI Assistant", "page-ai-assistant"),
    ("Help & Guides", "page-help-guides"),
    ("Settings", "page-settings"),
)


class UiKnowledgeService:
    def answer(self, question: str) -> str | None:
        entries = self.matches(question)
        if not entries:
            return None
        czech = is_czech(question)
        if len(entries) == 1:
            return entries[0].czech if czech else entries[0].english
        heading = "Relevantní zdokumentované prvky:" if czech else "Relevant documented components:"
        details = "\n\n".join(
            f"{entry.name}: {entry.czech if czech else entry.english}"
            for entry in entries
        )
        return f"{heading}\n\n{details}"

    def match(self, question: str) -> UiKnowledgeEntry | None:
        matches = self.matches(question)
        return matches[0] if len(matches) == 1 else None

    def matched_guide_id(self, question: str) -> str:
        entry = self.match(question)
        if entry is None:
            return ""
        if entry.guide_id:
            return entry.guide_id
        for keyword, guide_id in _PAGE_GUIDE_MAP:
            if keyword in entry.page:
                return guide_id
        return ""

    def matches(self, question: str) -> tuple[UiKnowledgeEntry, ...]:
        query = _normalize(question)
        if not _looks_like_explanation_request(query):
            return ()
        exact = tuple(item for item in UI_KNOWLEDGE if any(alias in query for alias in item.aliases))
        if exact:
            return exact
        query_tokens = _meaningful_tokens(query)
        ranked = sorted(
            (
                (_semantic_score(query_tokens, _entry_identity_tokens(item)), item)
                for item in UI_KNOWLEDGE
            ),
            key=lambda candidate: candidate[0],
            reverse=True,
        )
        if not ranked or ranked[0][0] < 2:
            return ()
        if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
            return ()
        return (ranked[0][1],)

    def relevant_context(self, question: str, limit: int = 6) -> tuple[dict[str, str], ...]:
        query_tokens = _meaningful_tokens(_normalize(question))
        ranked = sorted(
            (
                (_semantic_score(query_tokens, _entry_context_tokens(item)), index, item)
                for index, item in enumerate(UI_KNOWLEDGE)
            ),
            key=lambda candidate: (-candidate[0], candidate[1]),
        )
        selected = [item for score, _index, item in ranked if score > 0][:limit]
        return tuple(self._context_item(item) for item in selected)

    def context(self) -> tuple[dict[str, str], ...]:
        return tuple(self._context_item(item) for item in UI_KNOWLEDGE)

    def page_summary(self, page_name: str, *, czech: bool) -> str | None:
        entry = next((item for item in UI_KNOWLEDGE if item.name == page_name), None)
        if entry is None:
            return None
        return entry.czech if czech else entry.english

    def _context_item(self, item: UiKnowledgeEntry) -> dict[str, str]:
        return {
            "component": item.name,
            "page": item.page,
            "documented_behavior": item.english,
        }


UI_KNOWLEDGE = (
    UiKnowledgeEntry(
        "BINANCE connection status box",
        "Sidebar",
        ("binance not checked", "box binance", "binance status", "stav binance"),
        "The sidebar BINANCE box shows whether the read-only Binance API connection was checked in the current app session. Not checked does not prove that the key is missing or invalid; run the dedicated read-only check in Settings. This is separate from live trading-key verification.",
        "Box BINANCE v postranním panelu ukazuje, zda bylo read-only Binance API připojení ověřeno v aktuální session aplikace. Not checked neznamená, že klíč chybí nebo je neplatný; samostatnou read-only kontrolu spustíte v Settings. Jde o jiný stav než ověření live trading klíče.",
    ),
    UiKnowledgeEntry(
        "Refresh checks",
        "Live Actions and Settings",
        ("refresh checks", "obnovit kontroly", "aktualizovat kontroly"),
        "Refresh checks reloads Coinductor's local setup status: configuration, saved credentials presence, AI provider settings, user profile, Safety stage, readiness, and the first-portfolio plan. It does not run a Binance network permission check and does not place orders. Use the dedicated connection or permission check for live verification.",
        "Tlačítko Refresh checks znovu načte lokální stav nastavení Coinductoru: konfiguraci, přítomnost uložených přístupových údajů, nastavení AI, uživatelský profil, Safety stage, readiness a plán prvního portfolia. Neprovádí síťovou kontrolu oprávnění na Binance ani žádný příkaz. Pro živé ověření slouží samostatná kontrola připojení nebo oprávnění.",
    ),
    UiKnowledgeEntry(
        "Apply / Use safe defaults",
        "Setup wizard and Settings",
        ("use safe defaults", "apply safe defaults", "safe defaults", "bezpecne vychozi"),
        "Safe defaults immediately save a conservative local profile: beginner mode, recommendations only, weekly review, USDC funding, 20% reserve, 10% drawdown comfort, Earn and Rebalancing recommendations enabled, Grid disabled, and spot trading disabled. It does not place an order or change Binance settings.",
        "Safe defaults ihned uloží konzervativní lokální profil: režim pro začátečníka, pouze doporučení, týdenní kontrolu, funding v USDC, 20% rezervu, 10% toleranci drawdownu, zapnutá doporučení pro Earn a Rebalancing, vypnutý Grid a vypnuté spotové obchodování. Neprovede žádný příkaz ani nezmění nastavení Binance.",
    ),
    UiKnowledgeEntry(
        "Run analysis",
        "Overview",
        ("run analysis", "spustit analyzu", "spust analyzu"),
        "Run analysis opens the configurable analysis dialog. The run reads current data according to the selected mode and prepares a report. Opening the dialog or running a normal read-only analysis does not submit an order.",
        "Run analysis otevře dialog s parametry analýzy. Běh načte aktuální data podle zvoleného režimu a připraví report. Samotné otevření dialogu ani běžná read-only analýza neodesílá příkaz.",
    ),
    UiKnowledgeEntry(
        "Prepare trade preview",
        "Live Actions",
        ("prepare trade preview", "trade preview"),
        "Prepare trade preview runs a real-data analysis with AI commentary and bounded proposals, then opens Action Plan. A Binance order preview is included only when the current Safety stage permits it; submission remains a separate confirmed action.",
        "Prepare trade preview spustí analýzu reálných dat s AI komentářem a omezenými návrhy a poté otevře Action Plan. Náhled Binance příkazu se vytvoří jen tehdy, když ho dovoluje aktuální Safety stage; odeslání zůstává samostatnou potvrzovanou akcí.",
    ),
    UiKnowledgeEntry(
        "Prepare bot plan",
        "Live Actions",
        ("prepare bot plan", "bot plan"),
        "Prepare bot plan refreshes Spot Grid and Rebalancing recommendations from real data and opens Action Plan with the proposed parameters and blockers. It does not create a Binance bot.",
        "Prepare bot plan obnoví doporučení pro Spot Grid a Rebalancing z reálných dat a otevře Action Plan s navrženými parametry a blokery. Binance bota samo nezaloží.",
    ),
    UiKnowledgeEntry(
        "Open run dialog",
        "Live Actions",
        ("open run dialog", "run dialog"),
        "Open run dialog opens the same configurable analysis dialog used on Overview. It does not start anything until you confirm the run options.",
        "Open run dialog otevře stejný konfigurovatelný dialog analýzy jako na Overview. Nic nespustí, dokud nepotvrdíte parametry běhu.",
    ),
    UiKnowledgeEntry(
        "Open detailed report",
        "Overview and Action Plan",
        ("open detailed report", "detailni report", "podrobny report"),
        "Open detailed report opens the local Markdown report from the latest completed real-data run. It does not refresh data or run analysis.",
        "Open detailed report otevře lokální Markdown report z posledního dokončeného běhu nad reálnými daty. Neobnovuje data ani nespouští analýzu.",
    ),
    UiKnowledgeEntry(
        "Manage live API",
        "Live Actions",
        ("manage live api", "live api"),
        "Manage live API opens local credential and permission verification for the separate Binance Spot trading key. Saving or checking the key does not change the Safety stage and does not submit an order.",
        "Manage live API otevře správu lokálních přístupových údajů a ověření oprávnění samostatného Binance Spot trading klíče. Uložení ani kontrola klíče nezmění Safety stage a neodešle příkaz.",
    ),
    UiKnowledgeEntry(
        "Safety stage",
        "Live Actions",
        ("safety stage", "enable preview", "arm guarded actions", "enable live submit", "live enabled", "lock live submit"),
        "Safety stage is a local execution gate. Preview enables mainnet validation without submission, Armed verifies guarded prerequisites while submission stays locked, and Live enabled permits a separately confirmed guarded submit. Lock live submit returns execution to a locked state. Stage changes never place an order by themselves.",
        "Safety stage je lokální brána exekuce. Preview povolí mainnet validaci bez odeslání, Armed ověří podmínky zabezpečených akcí při stále zamčeném odesílání a Live enabled dovolí samostatně potvrzené zabezpečené odeslání. Lock live submit exekuci znovu zamkne. Samotná změna stage nikdy neprovede příkaz.",
    ),
    UiKnowledgeEntry(
        "Portfolio policy selector",
        "Portfolio",
        ("portfolio policy", "asset role", "policy selector", "role tokenu", "role assetu"),
        "The Policy selector saves a local override for an asset's role. The role controls which deterministic trading, Grid, Rebalancing, protection, or funding universes may consider that asset. Changing it does not trade the asset immediately.",
        "Výběr Policy uloží lokální přepsání role daného assetu. Role určuje, zda ho smějí zvažovat deterministická pravidla pro trading, Grid, Rebalancing, ochranu nebo funding. Samotná změna role asset ihned neobchoduje.",
    ),
    UiKnowledgeEntry(
        "Register active bot",
        "Active Strategies",
        ("register active bot", "registrovat bota", "active bot"),
        "Register active bot records a Grid or Rebalancing bot that already exists on Binance so Coinductor can monitor it. The form does not create, stop, or modify the Binance bot.",
        "Register active bot lokálně zaznamená Grid nebo Rebalancing bota, který už existuje na Binance, aby ho Coinductor mohl monitorovat. Formulář bota na Binance nevytváří, nezastavuje ani neupravuje.",
    ),
    UiKnowledgeEntry(
        "Import latest recommendation",
        "Active Strategies",
        ("import latest recommendation", "importovat doporuceni"),
        "Import latest recommendation fills the registration form with parameters from the latest Coinductor recommendation. You must still compare them with the bot actually created on Binance and save the registration.",
        "Import latest recommendation předvyplní registrační formulář parametry z posledního doporučení Coinductoru. Stále je musíte porovnat s botem skutečně založeným na Binance a registraci uložit.",
    ),
    UiKnowledgeEntry(
        "Check AI provider",
        "Setup wizard and Settings",
        ("check ai provider", "kontrola ai providera", "overit ai"),
        "Check AI provider contacts the configured model endpoint and verifies that it responds. It does not send portfolio analysis or change the selected model.",
        "Check AI provider kontaktuje nastavený endpoint modelu a ověří, že odpovídá. Neodesílá portfolio analýzu ani nemění vybraný model.",
    ),
    UiKnowledgeEntry(
        "AI image input and vision model",
        "AI Assistant and Settings",
        (
            "vision model", "llm_vision_enabled", "endpoint supports images", "image input",
            "attach image", "vlozit obrazek", "vložit obrázek", "vkladat obrazky",
            "vkládat obrázky", "nemohu vlozit", "nemohu vložit", "image attachment",
        ),
        "Coinductor blocks image sending until a vision-capable model is available. To enable it with Ollama: 1. Open https://ollama.com/library/qwen3-vl and install a model that fits your hardware; qwen3-vl:8b is a practical candidate for a 16 GB VRAM GPU. 2. Keep Ollama running. 3. In Coinductor open Settings > Configure AI models (or Setup wizard > AI). Keep http://127.0.0.1:11434/v1, leave the normal model in Text model, and enter the exact installed tag such as qwen3-vl:8b in optional Vision model. Select Save local AI and Check AI provider. 4. Return to AI Assistant; normal messages continue using the text model and image messages are routed automatically to the vision model. LLM_VISION_ENABLED=true only overrides detection and never adds vision to qwen3:14b.",
        "Coinductor blokuje odeslání obrázku, dokud není dostupný vision model. Zprovoznění přes Ollamu: 1. Otevřete https://ollama.com/library/qwen3-vl a nainstalujte model odpovídající vašemu HW; pro GPU s 16 GB VRAM je praktickým kandidátem qwen3-vl:8b. 2. Nechte Ollamu spuštěnou. 3. V Coinductoru otevřete Settings > Configure AI models (nebo Setup wizard > AI). Ponechte http://127.0.0.1:11434/v1, běžný model nechte v poli Text model a přesný tag jako qwen3-vl:8b vložte do volitelného pole Vision model. Klikněte na Save local AI a Check AI provider. 4. Vraťte se do AI Assistant; běžné zprávy nadále používají textový model a pouze zprávy s obrázkem se automaticky přesměrují na vision model. LLM_VISION_ENABLED=true pouze přepíše detekci a qwen3:14b vision schopnosti nepřidá.",
    ),
    UiKnowledgeEntry(
        "Setup wizard",
        "Settings",
        ("setup wizard", "open wizard", "pruvodce nastavenim"),
        "Setup wizard reopens the guided local setup for exchange, portfolio path, decision profile, AI, and read-only Binance API. Revisiting it does not place orders.",
        "Setup wizard znovu otevře průvodce lokálním nastavením burzy, typu portfolia, rozhodovacího profilu, AI a read-only Binance API. Opětovné projití neprovádí příkazy.",
    ),
    UiKnowledgeEntry(
        "Wizard: creating Binance API keys",
        "Setup wizard",
        (
            "create binance api key", "generate api key", "how do i get an api key",
            "jak vytvorit api klic", "jak vytvořit api klíč", "jak ziskat api klic",
        ),
        "In Binance, open API Management under your account, create a new key, and label it. For the read-only key used in early setup, leave Enable Spot & Margin Trading off; Coinductor only needs read permissions to analyze your portfolio. A separate live-trading key with trading enabled is only needed later, once you deliberately choose to allow guarded live actions. Never enable withdrawals on any key used with Coinductor. Restrict the key to your IP address if your connection allows it, then paste the key/secret into the matching wizard field; Coinductor saves them to your local .env file only.",
        "V Binance otevřete API Management ve svém účtu, vytvořte nový klíč a pojmenujte jej. Pro read-only klíč použitý v úvodním nastavení nechte Enable Spot & Margin Trading vypnuté; Coinductor pro analýzu portfolia potřebuje jen oprávnění ke čtení. Samostatný live-trading klíč s povoleným obchodováním je potřeba až později, pokud se vědomě rozhodnete povolit zabezpečené live akce. U žádného klíče používaného s Coinductorem nikdy nepovolujte výběry (withdrawals). Pokud to vaše připojení umožňuje, omezte klíč na vaši IP adresu a poté klíč/secret vložte do odpovídajícího pole ve wizardu; Coinductor je ukládá pouze do lokálního souboru .env.",
        guide_id="binance-api",
    ),
    UiKnowledgeEntry(
        "Wizard: automation level meaning",
        "Setup wizard",
        (
            "automation level", "recommend only", "guided automation", "uroven automatizace",
            "úroveň automatizace", "co znamena automation level", "co znamená automation level",
        ),
        "Automation level controls how much Coinductor is allowed to prepare without a fresh manual review. Recommend-only means every run produces analysis and suggestions that you review and confirm manually; nothing guarded is pre-armed. Guided automation still requires your explicit typed confirmation for every money-moving action and the same Safety-stage gating, but assumes you plan to review results on a regular cadence rather than deciding fresh each time. Neither level lets AI place an order, redeem funds, or bypass the deterministic risk engine on its own.",
        "Automation level určuje, kolik toho smí Coinductor připravit bez čerstvé ruční kontroly. Recommend-only znamená, že každý běh vytvoří analýzu a doporučení, která ručně zkontrolujete a potvrdíte; nic zabezpečeného není předem odjištěné. Guided automation stále vyžaduje váš explicitní psaný souhlas u každé peněžní akce a stejné hlídání Safety stage, ale počítá s tím, že výsledky budete kontrolovat v pravidelném rytmu místo rozhodování pokaždé od nuly. Ani jedna úroveň nedovolí AI samostatně zadat příkaz, vybrat prostředky z Earn ani obejít deterministický risk engine.",
    ),
    UiKnowledgeEntry(
        "Wizard: Decision profile field guide",
        "Setup wizard",
        (
            "decision profile fields", "what do the profile fields mean", "which profile options should i choose",
            "jednotliva pole v decision profile", "co znamenaji pole v decision profile",
            "jak vybrat profil", "jake pole zvolit v profilu",
        ),
        "Management style: Conservative keeps more reserve and fewer active suggestions; Balanced (default) is a useful middle ground; Active can surface more frequent opportunities. Every deterministic risk limit, protected-asset rule, and confirmation applies regardless of style. Automation: Recommendations only means Coinductor explains and suggests but you decide everything manually (the safest starting mode); Guarded automation lets Coinductor prepare guarded workflows after checks pass, but still cannot bypass limits, confirmations, stop-loss rules, or the Safety stage. Review rhythm is how often you plan to open Coinductor: Daily suits closer monitoring, Weekly suits passive management with fewer interventions, Twice weekly is a middle ground, Manual/irregular assumes no fixed schedule. Drawdown comfort is how much portfolio decline you can tolerate before wanting more conservative suggestions: Low (10%) stays conservative, Medium (15%, default) is risk-aware without being fully passive, High (20%) allows more growth-oriented suggestions but is not a guarantee or a hard stop-loss. Operating currency is fixed to USDC for now. Starting/Reference budget only drives planning on the first-portfolio path; for an existing portfolio it is optional context, since your real Binance balances are what Coinductor actually manages. The two checkboxes control whether Coinductor prepares Binance bot (Grid/Rebalancing) parameter recommendations and whether guarded spot trades may ever be prepared; both still require every other deterministic check and an explicit later confirmation. None of these choices place an order by themselves, and you can change them anytime by reopening the setup wizard.",
        "Management style: Conservative udržuje více rezervy a méně aktivních doporučení; Balanced (výchozí) je praktický střed; Active může nabízet příležitosti častěji. Bez ohledu na styl platí všechny deterministické limity rizika, pravidla pro chráněná aktiva i potvrzení. Automation: Recommendations only znamená, že Coinductor vysvětluje a navrhuje, ale o všem rozhodujete ručně vy (nejbezpečnější výchozí režim); Guarded automation umožňuje Coinductoru po splnění kontrol připravit zabezpečené postupy, ale stále nemůže obejít limity, potvrzení, pravidla stop-loss ani Safety stage. Review rhythm je, jak často plánujete Coinductor otevírat: Daily se hodí pro častější sledování, Weekly pro pasivnější správu s méně zásahy, Twice weekly je střed, Manual/irregular počítá s nepravidelným rytmem bez pevného plánu. Drawdown comfort je, jak velký propad portfolia jste ochotni tolerovat, než budete chtít konzervativnější doporučení: Low (10 %) zůstává konzervativní, Medium (15 %, výchozí) je citlivé na riziko, ale ne zcela pasivní, High (20 %) umožňuje růstově orientovanější doporučení, ale není to záruka ani tvrdý stop-loss. Provozní měna je zatím pevně USDC. Starting/Reference budget ovlivňuje plánování jen na cestě prvního portfolia; u existujícího portfolia jde jen o volitelný kontext, protože Coinductor reálně spravuje vaše skutečné zůstatky na Binance. Obě zaškrtávací pole určují, zda má Coinductor připravovat doporučené parametry pro boty Binance (Grid/Rebalancing) a zda smí vůbec někdy připravit zabezpečené spotové obchody; v obou případech stále platí všechny ostatní deterministické kontroly a pozdější explicitní potvrzení. Žádná z těchto voleb sama o sobě nezadává příkaz a kdykoli je můžete změnit opětovným otevřením setup wizardu.",
    ),
    UiKnowledgeEntry(
        "Wizard: existing portfolio vs first portfolio",
        "Setup wizard",
        (
            "difference between existing portfolio and first portfolio",
            "rozdil mezi existing portfolio a first portfolio",
            "rozdil mezi existing a first portfolio",
        ),
        "Choose Existing portfolio if you already hold crypto on Binance and want Coinductor to analyze and manage what is already there. Choose Build my first portfolio if you are starting from little or no crypto; that path plans a staged, guarded initial basket purchase (see the Action Plan 'First portfolio deployment' panel) instead of assuming existing holdings. You can change this later by resetting onboarding in Settings; it does not affect exchange credentials or trading history.",
        "Zvolte Existing portfolio, pokud už na Binance držíte kryptoměny a chcete, aby je Coinductor analyzoval a spravoval. Zvolte Build my first portfolio, pokud začínáte s malým množstvím nebo bez kryptoměn; tato cesta naplánuje postupný, zabezpečený nákup počátečního košíku (viz panel 'First portfolio deployment' na Action Plan) místo předpokladu existujících pozic. Volbu lze později změnit resetem onboardingu v Settings; nemá vliv na přístupové údaje k burze ani historii obchodování.",
    ),
    UiKnowledgeEntry(
        "Wizard: what to download for local AI",
        "Setup wizard",
        (
            "what should i download", "what do i install for local ai", "co si mam stahnout",
            "co si mám stáhnout", "co nainstalovat pro lokalni ai", "co nainstalovat pro lokální ai",
        ),
        "For local AI, install Ollama from ollama.com, then pull a text model with 'ollama pull <model>' in a terminal, e.g. qwen3:14b for GPUs with about 16 GB VRAM, or a smaller tag such as qwen3:4b on more limited hardware. A vision model such as qwen3-vl:8b is optional and only needed if you want to attach screenshots to AI Assistant questions. Use Scan hardware in this step for a hardware-based suggestion, or Detect installed models once Ollama is running to see exactly which tags it already reports, then Save local AI and Check AI provider to verify the endpoint.",
        "Pro lokální AI nainstalujte Ollamu z ollama.com a poté v terminálu stáhněte textový model příkazem 'ollama pull <model>', např. qwen3:14b pro GPU s cca 16 GB VRAM, nebo menší variantu jako qwen3:4b na slabším hardwaru. Vision model jako qwen3-vl:8b je volitelný a potřebný jen pokud chcete k dotazům do AI Assistant přikládat screenshoty. V tomto kroku použijte Scan hardware pro doporučení podle hardwaru, nebo po spuštění Ollamy Detect installed models pro zjištění, jaké tagy skutečně hlásí, a poté Save local AI a Check AI provider pro ověření endpointu.",
        guide_id="local-ai",
    ),
    UiKnowledgeEntry(
        "Wizard: what is Spot Testnet for",
        "Setup wizard",
        (
            "what is testnet for", "why use testnet", "k cemu je testnet", "k čemu je testnet",
            "je testnet povinny", "je testnet povinný",
        ),
        "Binance Spot Testnet lets you rehearse guarded actions, including first-portfolio tranches, with virtual funds on Binance's own test exchange before ever touching real money. It is optional but recommended: a Testnet credential pair is separate from your real Binance account and never places a real order regardless of the app's Safety stage. Skipping it does not block setup; it only means your first guarded rehearsal happens on mainnet preview instead.",
        "Binance Spot Testnet umožňuje si nanečisto vyzkoušet zabezpečené akce, včetně tranší prvního portfolia, s virtuálními prostředky na testovací burze Binance dřív, než sáhnete na skutečné peníze. Je volitelný, ale doporučený: pár přístupových údajů pro Testnet je oddělený od skutečného účtu Binance a nikdy nezadá skutečný příkaz bez ohledu na Safety stage aplikace. Přeskočení tohoto kroku nastavení nijak neblokuje; znamená jen, že první zabezpečenou zkoušku uděláte rovnou přes mainnet preview.",
        guide_id="binance-testnet",
    ),
    UiKnowledgeEntry(
        "Replay app tour",
        "Settings",
        ("replay app tour", "zopakovat tutorial", "zopakovat prohlidku"),
        "Replay app tour starts the short overlay tour of the main application pages again. It changes no portfolio or exchange settings.",
        "Replay app tour znovu spustí krátkého překryvného průvodce hlavními sekcemi aplikace. Nemění portfolio ani nastavení burzy.",
    ),
    UiKnowledgeEntry(
        "Reset onboarding",
        "Settings",
        ("reset onboarding", "resetovat onboarding"),
        "Reset onboarding removes the local preference profile and returns to the setup wizard. Exchange credentials, reports, and trading history remain untouched.",
        "Reset onboarding odstraní lokální preferenční profil a vrátí aplikaci do setup wizardu. Přístupové údaje k burze, reporty a historie tradingu zůstanou zachované.",
    ),
    UiKnowledgeEntry(
        "Delete local data",
        "Settings",
        ("delete local data", "smazat lokalni data"),
        "Delete local data opens a preview where you choose which local profile data, credentials, reports, research, database, and strategy state to remove. Nothing is deleted until the destructive action is explicitly confirmed.",
        "Delete local data otevře náhled, ve kterém zvolíte, zda odstranit lokální profil, přístupové údaje, reporty, research, databázi nebo stav strategií. Nic se nesmaže bez výslovného potvrzení destruktivní akce.",
    ),
    UiKnowledgeEntry(
        "Overview",
        "Overview",
        ("overview", "portfolio overview", "prehled portfolia"),
        "Overview is the dashboard for the latest portfolio totals, readiness and Safety stage, latest deterministic decision, recommended actions, AI summary, and the entry point for a new analysis. It summarizes the latest stored real-data run; it is not a live price screen.",
        "Overview je hlavní přehled poslední hodnoty portfolia, readiness a Safety stage, posledního deterministického rozhodnutí, doporučených kroků, AI shrnutí a vstupu pro novou analýzu. Shrnuje poslední uložený běh nad reálnými daty; nejde o obrazovku živých cen.",
    ),
    UiKnowledgeEntry(
        "Live Actions",
        "Live Actions",
        ("live actions", "live akce"),
        "Live Actions contains guarded workflows: preparing a trade preview, preparing Grid and Rebalancing plans, managing the separate live API key, and moving through Safety stages. Every actual live submission remains separately validated and confirmed.",
        "Live Actions obsahuje zabezpečené workflow: přípravu trade preview, plánů pro Grid a Rebalancing, správu samostatného live API klíče a přechody mezi Safety stages. Každé skutečné live odeslání zůstává samostatně validované a potvrzované.",
    ),
    UiKnowledgeEntry(
        "Portfolio",
        "Portfolio",
        ("portfolio section", "sekce portfolio", "portfolio page"),
        "Portfolio lists assets from the latest real-data run with their local policy role, estimated value, share, Spot/Flexible/Locked liquidity, and data source. Sorting changes only the display; changing Policy saves a local role override.",
        "Sekce Portfolio zobrazuje assety z posledního běhu nad reálnými daty, jejich lokální policy roli, odhadovanou hodnotu, podíl, likviditu ve Spot/Flexible/Locked a zdroj dat. Řazení mění jen zobrazení; změna Policy uloží lokální přepsání role.",
    ),
    UiKnowledgeEntry(
        "Action Plan",
        "Action Plan",
        ("action plan", "akcni plan"),
        "Action Plan is the consolidated result of the latest run. Separate cards show the current Trade, Spot Grid, and Rebalancing decision, exact parameters when available, blockers, and guarded confirmation controls only when deterministic prerequisites allow an action.",
        "Action Plan je konsolidovaný výsledek posledního běhu. Samostatné karty ukazují aktuální rozhodnutí pro Trade, Spot Grid a Rebalancing, dostupné přesné parametry, blokery a potvrzovací prvky pouze tehdy, když deterministické podmínky danou akci dovolí.",
    ),
    UiKnowledgeEntry(
        "Active Strategies",
        "Active Strategies",
        ("active strategies", "aktivni strategie"),
        "Active Strategies monitors Grid and Rebalancing bots that the user has already created on Binance and registered locally. It shows lifecycle status, next review timing, earlier-run triggers, and manual blockers. Coinductor does not create or edit those Binance bots through this page.",
        "Active Strategies monitoruje Grid a Rebalancing boty, které uživatel už založil na Binance a lokálně zaregistroval. Zobrazuje stav lifecycle, termín další kontroly, podmínky pro dřívější běh a manuální blokery. Coinductor na této stránce Binance boty nevytváří ani neupravuje.",
    ),
    UiKnowledgeEntry(
        "Run History",
        "Run History",
        ("run history", "historie behu"),
        "Run History shows the latest 30 analytical runs with their start time, status, decision, and short summary. It is historical local data and does not rerun an analysis when opened.",
        "Run History zobrazuje posledních 30 analytických běhů, jejich čas zahájení, stav, rozhodnutí a krátké shrnutí. Jde o lokální historii; otevření sekce analýzu znovu nespustí.",
    ),
    UiKnowledgeEntry(
        "AI Assistant",
        "AI Assistant",
        ("ai assistant", "ai asistent"),
        "AI Assistant explains documented app behavior, the latest stored run, portfolio roles, risk controls, and reports. Supported local app changes are shown as deterministic proposals that require confirmation. Chat cannot directly submit trades, OCO protection, Earn redemptions, or Binance bot changes.",
        "AI Assistant vysvětluje zdokumentované chování aplikace, poslední uložený běh, portfolio role, risk management a reporty. Podporované lokální změny zobrazí jako deterministický návrh vyžadující potvrzení. Chat nemůže přímo odesílat trades, OCO ochranu, Earn redeem ani změny Binance botů.",
    ),
    UiKnowledgeEntry(
        "Help & Guides",
        "Help & Guides",
        ("help and guides", "help & guides", "navody", "napoveda"),
        "Help & Guides contains local step-by-step instructions for setup, local and cloud AI, Binance read-only and live API keys, safety, and portfolio roles. Opening a guide performs no configuration change.",
        "Help & Guides obsahuje lokální návody krok za krokem pro instalaci, lokální a cloudovou AI, Binance read-only a live API klíče, bezpečnost a portfolio role. Otevření návodu nic v konfiguraci nezmění.",
    ),
    UiKnowledgeEntry(
        "Settings",
        "Settings",
        ("settings section", "sekce settings", "nastaveni aplikace"),
        "Settings manages local configuration, provider and connection checks, onboarding profile, privacy and data controls, readiness, and safety information. It does not contain direct order submission controls; guarded execution is kept in Live Actions and Action Plan.",
        "Settings spravuje lokální konfiguraci, kontroly AI providera a připojení, onboarding profil, Privacy & Data, readiness a bezpečnostní informace. Neobsahuje přímé odesílání příkazů; zabezpečená exekuce zůstává v Live Actions a Action Plan.",
    ),
    UiKnowledgeEntry(
        "Next review",
        "Active Strategies",
        ("next review", "dalsi kontrola", "run earlier if", "resolve before rerunning"),
        "Next review separates timing from prerequisites. Suggested timing says when the next normal analysis is useful. Run earlier if lists market or portfolio events that justify an earlier refresh. Resolve before rerunning lists manual or funding blockers that another unchanged run cannot fix.",
        "Next review odděluje načasování od podmínek. Suggested timing říká, kdy dává smysl další běžná analýza. Run earlier if uvádí tržní nebo portfolio události, kvůli kterým má smysl spustit ji dříve. Resolve before rerunning vypisuje manuální nebo funding blokery, které další nezměněný běh sám nevyřeší.",
    ),
    UiKnowledgeEntry(
        "Order sizing panel",
        "Live Actions",
        ("order sizing", "how large an order", "velikost prikaz", "jak velky prikaz",
         "trade size", "max trade pct", "order size"),
        "The order sizing panel decides what size the analysis considers appropriate, one layer before the cap that guards what may reach the exchange. The approved amount is the smallest of: what the analyst proposed, your order-size percentage of the portfolio, the flat never-more-than amount, the per-asset and trading-capital percentages, the risk-per-trade percentage measured against the stop loss, and what your account can actually pay. Every value is a ceiling, so raising one alone cannot enlarge an order - another ceiling then binds. The percentages bound a single order, not the position it builds towards: what you already hold is not counted, so repeated buys can accumulate past them.",
        "Panel velikosti příkazu rozhoduje, jakou velikost analýza považuje za přiměřenou - o úroveň dřív než strop, který hlídá, co smí odejít na burzu. Schválená částka je minimum z: návrhu analytika, vašeho procenta portfolia na příkaz, ploché meze „nikdy víc než“, procent na aktivum a na obchodní kapitál, procenta rizika na obchod měřeného proti stop lossu, a toho, co účet reálně zaplatí. Každá hodnota je strop, takže zvýšení jediné z nich příkaz zvětšit nemůže - pak váže jiná. Procenta omezují jeden příkaz, ne výslednou pozici: to, co už držíte, se nezapočítává, takže opakované nákupy se přes ně můžou nasčítat.",
    ),
    UiKnowledgeEntry(
        "Earn funding panel",
        "Live Actions",
        ("earn funding", "earn to spot", "presun z earnu", "financovani z earnu",
         "redeem limit", "auto funding", "automaticky presun", "z earnu na spot",
         "meze financovani", "funding limit"),
        "The Earn funding panel decides how much may move from Simple Earn Flexible to Spot so an approved action can be paid for. This is a transfer inside your own account, not a withdrawal: Coinductor cannot withdraw and refuses an API key that could. Each limit is a flat amount and a percentage of portfolio value, and the smaller wins; there is a per-run limit, a per-day limit counted across every run, and a reserve that is never touched. Only redemptions that actually went through count against the day. Automatic funding is off by default and is ignored below the LIVE_ENABLED safety stage.",
        "Panel financování z Earnu rozhoduje, kolik se smí přesunout ze Simple Earn Flexible na Spot, aby šla zaplatit schválená akce. Jde o přesun uvnitř vašeho účtu, ne o výběr: Coinductor vybírat neumí a API klíč, který by to uměl, odmítne. Každá mez je plochá částka i procento portfolia a platí menší; je tam mez na běh, mez na den počítaná napříč všemi běhy, a rezerva, na kterou se nesahá. Do denního součtu se počítají jen výběry, které skutečně proběhly. Automatický přesun je ve výchozím stavu vypnutý a pod stupněm LIVE_ENABLED se ignoruje.",
    ),
    UiKnowledgeEntry(
        "Automatic Earn funding",
        "Live Actions",
        ("auto funding enabled", "automatic funding", "automaticke financovani",
         "move earn automatically", "presune si to samo", "unattended transfer"),
        "Automatic Earn funding lets a run move money from Flexible Earn to Spot without you present, but only when an action the risk engine already approved is waiting on that money. It requires the switch turned on and the LIVE_ENABLED safety stage; an unreadable stage is not permission. It is a separate authority from a manual redeem, which still needs CONFIRM_EARN_REDEEM typed for the exact amount. It does not fund a Grid or Rebalancing bot: those are recommend-only, because Binance has no public API to create them, so the money would move and the bot would still have to be created by hand.",
        "Automatické financování z Earnu umožní běhu přesunout peníze z Flexible Earnu na Spot bez vaší přítomnosti, ale jen když na ty peníze čeká akce, kterou risk engine už schválil. Vyžaduje zapnutý přepínač a bezpečnostní stupeň LIVE_ENABLED; nečitelný stupeň není povolení. Je to jiná autorita než ruční výběr, který dál potřebuje napsané CONFIRM_EARN_REDEEM pro přesnou částku. Nefinancuje Grid ani Rebalancing bota: ti jsou pouze doporučující, protože Binance nemá veřejné API na jejich vytvoření, takže by se peníze přesunuly a bota byste stejně musel založit ručně.",
    ),
    UiKnowledgeEntry(
        "Use suggested limits",
        "Live Actions",
        ("use suggested", "pouzit doporucen", "suggested limits", "doporucen hodnot",
         "recommended settings", "co mam nastavit", "doporucen"),
        "Use suggested fills the sizing or funding limits with a starting point derived from your portfolio and saves it. Percentages are suggested as constants, because a percentage already scales with what you hold; the flat backstops scale, and are placed well above where the percentage binds so the percentage is what normally decides. It is disabled until an analysis has valued your portfolio. Everything it writes is reversible from the same screen, and each percentage field also shows what it is worth in money right now.",
        "Tlačítko Použít doporučené vyplní meze velikosti nebo financování výchozím bodem odvozeným z vašeho portfolia a uloží ho. Procenta se navrhují jako konstanty, protože procento už samo škáluje podle toho, co držíte; ploché pojistky škálují a jsou umístěné výrazně nad tím, kde by procento vázalo, takže normálně rozhoduje procento. Do první analýzy, která portfolio ocení, je tlačítko nedostupné. Vše, co zapíše, jde ze stejné obrazovky vrátit, a u každého procentního pole navíc vidíte, kolik to je právě teď v penězích.",
    ),
    UiKnowledgeEntry(
        "Why an order was this size",
        "Live Actions",
        ("binding limit", "why this size", "proc je prikaz", "co omezilo prikaz",
         "limited by", "omezil", "jak velky byl prikaz"),
        "The sizing panel reports which ceiling produced the last analysed order - for example available funding, the per-asset share, or the risk allowed per trade. It is recorded in the journal per run, so the reason survives a later config change. It stays empty for a rejected proposal, because no size was approved, and for runs recorded before this was added.",
        "Panel velikosti hlásí, který strop určil poslední analyzovaný příkaz - například dostupné financování, podíl na aktivum nebo riziko povolené na obchod. Ukládá se do journalu ke každému běhu, takže důvod přežije pozdější změnu konfigurace. U zamítnutého návrhu zůstává prázdný, protože žádná velikost schválená nebyla, stejně jako u běhů zaznamenaných dřív, než tohle přibylo.",
    ),
    UiKnowledgeEntry(
        "Updating Coinductor",
        "Settings",
        ("update", "upgrade", "aktualizac", "nova verz", "install new version",
         "quit before installing"),
        "Quit a running Coinductor from the tray icon before installing a new version. The single-instance guard only recognises instances that have it, so upgrading while an older one runs can leave two instances with two schedules writing one journal. From one guarded version to the next, launching again simply returns to the window that is already open.",
        "Před instalací nové verze ukončete běžící Coinductor přes ikonu v oznamovací oblasti (Quit). Ochrana proti druhé instanci pozná jen instance, které ji samy mají, takže upgrade při běžící starší verzi může nechat dvě instance se dvěma rozvrhy zapisující do jednoho journalu. Mezi verzemi, které ochranu mají, další spuštění jen vrátí okno, které už je otevřené.",
    ),
    UiKnowledgeEntry(
        "Start with Windows",
        "Automation",
        ("start with windows", "start on logon", "spoustet s windows", "po prihlaseni",
         "autostart", "spustit po startu", "start automatically", "spusteni po prihlaseni",
         "spoustet po", "sam spustit"),
        "Start with Windows brings Coinductor back after a restart, so a schedule does not depend on somebody remembering to launch it. Off unless you turn it on, and unavailable until a scheduled analysis exists - a background app with nothing to do is one people hunt down in Task Manager. It starts into the notification area rather than opening a window, because the reason to start is that the schedule runs, which needs a process rather than a screen; open it from the tray icon whenever you want to look. It is an ordinary Windows startup entry, so Task Manager's Startup apps tab lists it and can disable it too.",
        "Spouštět s Windows vrátí Coinductor po restartu, aby rozvrh nezávisel na tom, jestli si někdo vzpomene aplikaci spustit. Ve výchozím stavu vypnuté a nedostupné, dokud neexistuje naplánovaná analýza - aplikace běžící na pozadí bez práce je ta, kterou lidi hledají ve Správci úloh. Spustí se do oznamovací oblasti místo otevření okna, protože důvodem ke spuštění je běžící rozvrh, a k tomu je potřeba proces, ne obrazovka; kdykoli se chcete podívat, otevřete ho přes ikonu v traye. Je to běžná položka po spuštění Windows, takže ji vypisuje i záložka Aplikace po spuštění ve Správci úloh a jde vypnout i tam.",
    ),
)


def is_czech(value: str) -> bool:
    normalized = _normalize(value)
    tokens = set(normalized.replace("?", "").replace(".", "").split())
    czech_words = {
        "co", "jak", "kde", "kdy", "proc", "udela", "dela", "znamena", "tlacitko",
        "sekce", "aplikace", "muzu", "otevre", "spusti", "nastaveni", "prosim", "chci", "shrn",
        "cemu", "kolik", "ktery", "ktera", "ktere", "mam", "musim", "kdyz", "nebo",
        "penize", "presun", "castka", "vypnuty", "zapnuty", "prikaz",
    }
    return bool(tokens & czech_words) or any(character in value.lower() for character in "áčďéěíňóřšťúůýž")


def _looks_like_explanation_request(query: str) -> bool:
    return any(
        phrase in query
        for phrase in (
            "what does", "what is", "explain", "how does", "what happens", "co dela", "co udela",
            "co znamena", "k cemu", "jak funguje", "jak spolu", "souvisi", "vysvetli", "co se stane",
            "summarize", "tell me about", "shrn", "relationship between", "how are",
            "why cant", "why can t", "cannot", "how can i", "how do i", "what should i do",
            "why is", "why was", "why did", "why does", "proc je", "proc byl", "proc se",
            "proc ma", "proc mi", "how much", "how many", "kolik", "kdy se", "when does",
            "jak zaridit", "jak nastavit", "how do i set", "how to set",
            "not working", "proc nemohu", "proc nemuzu", "co mam udelat", "jak mohu", "jak muzu",
            "jak mam", "jak zprovoznit", "nejde mi", "nefunguje", "co si mam",
        )
    )


def _normalize(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.strip().lower())
        if not unicodedata.combining(character)
    )


_STOP_WORDS = {
    "a", "an", "the", "this", "that", "what", "does", "is", "how", "explain", "means", "mean",
    "co", "to", "znamena", "dela", "udela", "jak", "funguje", "vysvetli", "mi", "box", "nad", "tim",
    "v", "ve", "na", "u", "k", "se", "tady", "tahle", "tento", "tato", "prosim",
}


def _meaningful_tokens(value: str) -> set[str]:
    cleaned = "".join(character if character.isalnum() else " " for character in value)
    return {token for token in cleaned.split() if len(token) >= 3 and token not in _STOP_WORDS}


def _entry_identity_tokens(item: UiKnowledgeEntry) -> set[str]:
    return _meaningful_tokens(" ".join((item.name, item.page, *item.aliases)))


def _entry_context_tokens(item: UiKnowledgeEntry) -> set[str]:
    return _meaningful_tokens(" ".join((item.name, item.page, *item.aliases, item.english, item.czech)))


def _semantic_score(query_tokens: set[str], candidate_tokens: set[str]) -> int:
    score = 0
    for query_token in query_tokens:
        if any(
            query_token == candidate
            or (min(len(query_token), len(candidate)) >= 4 and (
                query_token.startswith(candidate) or candidate.startswith(query_token)
            ))
            for candidate in candidate_tokens
        ):
            score += 1
    return score
