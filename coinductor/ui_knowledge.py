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


class UiKnowledgeService:
    def answer(self, question: str) -> str | None:
        query = _normalize(question)
        if not _looks_like_explanation_request(query):
            return None
        entry = next(
            (
                item
                for item in UI_KNOWLEDGE
                if any(alias in query for alias in item.aliases)
            ),
            None,
        )
        if entry is None:
            return None
        return entry.czech if is_czech(question) else entry.english

    def context(self) -> tuple[dict[str, str], ...]:
        return tuple(
            {
                "component": item.name,
                "page": item.page,
                "documented_behavior": item.english,
            }
            for item in UI_KNOWLEDGE
        )

    def page_summary(self, page_name: str, *, czech: bool) -> str | None:
        entry = next((item for item in UI_KNOWLEDGE if item.name == page_name), None)
        if entry is None:
            return None
        return entry.czech if czech else entry.english


UI_KNOWLEDGE = (
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
        ("safety stage", "enable preview", "arm guarded actions", "enable live submit", "lock live submit"),
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
        "Setup wizard",
        "Settings",
        ("setup wizard", "open wizard", "pruvodce nastavenim"),
        "Setup wizard reopens the guided local setup for exchange, portfolio path, decision profile, AI, and read-only Binance API. Revisiting it does not place orders.",
        "Setup wizard znovu otevře průvodce lokálním nastavením burzy, typu portfolia, rozhodovacího profilu, AI a read-only Binance API. Opětovné projití neprovádí příkazy.",
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
)


def is_czech(value: str) -> bool:
    normalized = _normalize(value)
    tokens = set(normalized.replace("?", "").replace(".", "").split())
    czech_words = {
        "co", "jak", "kde", "kdy", "proc", "udela", "dela", "znamena", "tlacitko",
        "sekce", "aplikace", "muzu", "otevre", "spusti", "nastaveni", "prosim", "chci", "shrn",
    }
    return bool(tokens & czech_words) or any(character in value.lower() for character in "áčďéěíňóřšťúůýž")


def _looks_like_explanation_request(query: str) -> bool:
    return any(
        phrase in query
        for phrase in (
            "what does", "what is", "explain", "how does", "what happens", "co dela", "co udela",
            "co znamena", "k cemu", "jak funguje", "vysvetli", "co se stane", "summarize", "tell me about", "shrn",
        )
    )


def _normalize(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.strip().lower())
        if not unicodedata.combining(character)
    )
