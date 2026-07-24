"""Czech translations for the in-app guides.

Merged over the English guides by ``GuideService.list_guides("cs")``. Binance,
Ollama, and OpenAI screen labels, shell commands, URLs, environment variable
names, and file paths stay in English because the user has to match them
literally; Coinductor's own button and page names use the app's Czech labels.
"""

from __future__ import annotations


GUIDE_SECTIONS_CS: dict[str, str] = {
    "AI setup": "Nastavení AI",
    "Binance": "Binance",
    "Safety": "Bezpečnost",
    "Portfolio": "Portfolio",
    "Using Coinductor": "Používání Coinductoru",
}


GUIDES_CS: dict[str, dict[str, object]] = {
    "local-ai": {
        "title": "Lokální AI s Ollamou",
        "summary": "Soukromý lokální asistent pro nápovědu k aplikaci, shrnutí reportů a pomoc při nastavení.",
        "body": "<br>".join(
            [
                "Tuto cestu zvolte, když chcete, aby Coinductor zůstal plně lokální.",
                "",
                '1. Otevřete <a href="https://ollama.com/">https://ollama.com/</a> a tlačítkem Download nainstalujte Ollamu pro váš operační systém.',
                "2. Vyberte model, který se vejde do vašeho hardwaru. V kroku nastavení AI použijte tlačítko Scan hardware pro lokální doporučení. Sken je lokální: přečte RAM a GPU/VRAM z nástrojů operačního systému a žádné údaje o hardwaru neodesílá.",
                '3. Na <a href="https://ollama.com/search">https://ollama.com/search</a> vyhledejte textový model doporučený v kroku 2 a stáhněte přesně ten tag. Na slabších systémech otevřete terminál a spusťte: ollama pull qwen3:8b. Na silnějších GPU spusťte: ollama pull qwen3:14b.',
                "4. Nechte Ollamu běžet, dokud Coinductor používá AI funkce. Na Windows to obvykle znamená, že ikona Ollamy zůstává v systémové liště.",
                "5. V Coinductoru nastavte lokální endpoint na http://127.0.0.1:11434/v1 a zadejte tag modelu do pole Text model.",
                '6. Volitelná podpora obrázků: otevřete <a href="https://ollama.com/library/qwen3-vl">https://ollama.com/library/qwen3-vl</a>, stáhněte vhodný Qwen3-VL tag (například: ollama pull qwen3-vl:8b) a zadejte jej do pole Vision model. Coinductor ponechá textový model pro běžné zprávy a do tohoto modelu směruje pouze zprávy s obrázkem.',
                "7. Uložte nastavení a spusťte Zkontrolovat poskytovatele AI. Musí ohlásit textový model jako připravený a, pokud je nastaven, i vision model.",
                "",
                "Poznámka ke kvalitě modelu: pro komentáře k portfoliu a úvahy o trhu jsou modely třídy 14B preferované minimum, pokud to hardware zvládne. Menší modely zvládnou základní dotazy na aplikaci, ale častěji minou kontext nebo vytvoří slabá doporučení.",
                "Nezapínejte LLM_VISION_ENABLED jen proto, abyste vynutili textový model. Tento pokročilý přepínač mění pouze detekci a podporu obrázků přidat nedokáže.",
                "",
                "Lokální AI umí vysvětlit Coinductor, shrnout reporty a pomoci s prvotním nastavením. Nedokáže obejít deterministické bezpečnostní brány ani sama zadat obchod.",
                "",
                'V aplikaci: poskytovatele nastavíte a otestujete na <a href="guide:page-settings">stránce Nastavení</a> a používáte jej na <a href="guide:page-ai-assistant">stránce AI Assistant</a>.',
            ]
        ),
        "images": [
            "Domovská stránka Ollamy se zvýrazněným tlačítkem Download a vyhledáváním modelů.",
            "Ollama běžící v systémové liště Windows.",
        ],
    },
    "cloud-ai": {
        "title": "Cloudové AI API",
        "summary": "Volitelná kvalitnější AI cesta se samostatným účtováním API a zpracováním dat mimo váš počítač.",
        "body": "<br>".join(
            [
                "Cloudová AI je volitelná a je třeba ji brát jako pokročilou alternativu.",
                "",
                "Upozornění na ceny: předplatné chatu a používání API jsou obvykle samostatné produkty se samostatnými cenami. ChatGPT Plus/Pro, plány Claude ani předplatné Gemini automaticky neznamenají, že jsou volání API z Coinductoru zahrnuta.",
                "",
                "Příklad OpenAI:",
                '1. Otevřete <a href="https://platform.openai.com/">https://platform.openai.com/</a> a přejděte do API Keys.',
                "2. Pokud je to vyžadováno, doplňte v dashboardu poskytovatele platební údaje a limity.",
                "3. V Coinductoru použijte jako endpoint https://api.openai.com/v1.",
                "4. Zadejte název modelu, který chcete používat.",
                "5. Vložte API klíč a spusťte Zkontrolovat poskytovatele AI.",
                "",
                "Poznámka k soukromí: vybraný report, profil a kontext dotazu mohou být odeslány nastavenému poskytovateli. Nepoužívejte cloudovou AI, pokud chcete, aby veškerý kontext portfolia zůstal na vašem počítači.",
                "",
                'V aplikaci: endpoint, model a klíč nastavíte na <a href="guide:page-settings">stránce Nastavení</a> (Nastavit modely AI) a používáte je na <a href="guide:page-ai-assistant">stránce AI Assistant</a>.',
            ]
        ),
        "warning": "Volání cloudového AI API mohou stát peníze odděleně od běžného předplatného chatu. Než je začnete používat, nastavte limity na straně poskytovatele.",
        "images": [
            "Stránka API Keys na OpenAI Platform se zvýrazněnou akcí pro vytvoření klíče.",
        ],
    },
    "binance-api": {
        "title": "Binance read-only API",
        "summary": "Vytvořte bezpečný read-only API klíč Binance pro inventuru a analýzu portfolia.",
        "body": "<br>".join(
            [
                "Coinductor začíná s přístupem pouze pro čtení. Díky tomu může zjišťovat zůstatky a stav portfolia, aniž by na burze cokoliv měnil.",
                "",
                "1. V Binance otevřete User profile > Account > API Management.",
                "2. Zvolte Create API > System generated.",
                "3. Použijte srozumitelný název, například coinductor-readonly.",
                "4. Dokončete dvoufaktorové ověření.",
                "5. Okamžitě si zkopírujte API Key i Secret Key.",
                "6. V omezeních ponechte u read-only klíče povolené pouze čtení.",
                "7. Nepovolujte výběry (withdrawals), futures, margin transfer ani universal transfer.",
                "8. Vložte klíč a secret do Coinductoru a spusťte Zkontrolovat read-only přístup.",
                "",
                "Obchodní/zápisový přístup by měl používat samostatný pozdější klíč až po testnetu a preview kontrolách. Výběry musí zůstat vypnuté.",
                "",
                'V aplikaci: Zkontrolovat read-only přístup spustíte na <a href="guide:page-settings">stránce Nastavení</a>. Inventura, kterou tím odemknete, se zobrazí na <a href="guide:page-portfolio">stránce Portfolio</a>.',
            ]
        ),
        "images": [
            "Očištěný snímek dashboardu Binance se zvýrazněnou položkou API Management.",
            "Očištěná obrazovka omezení API v Binance pro read-only klíč.",
        ],
    },
    "binance-live-api": {
        "title": "Binance API pro živé obchodování",
        "summary": "Vytvořte samostatný API klíč Binance pro zabezpečené Spot obchodování, až budete read-only nastavení důvěřovat.",
        "body": "<br>".join(
            [
                "Tohle dělejte až ve chvíli, kdy vám read-only přístup, reporty a preview postupy dávají smysl. Tento klíč slouží pro zabezpečené Spot obchodování a nikdy nesmí umožňovat výběry.",
                "",
                "1. V Binance otevřete User profile > Account > API Management.",
                "2. Zvolte Create API > System generated.",
                "3. Použijte srozumitelný název, například coinductor-live-trading.",
                "4. Dokončete dvoufaktorové ověření a okamžitě si zkopírujte API Key i Secret Key.",
                "5. U nového klíče otevřete Edit restrictions.",
                "6. V IP access restrictions nejprve zvolte Restrict access to trusted IPs only. Binance může nechat obchodní oprávnění nedostupná, dokud není omezení na důvěryhodné IP nastaveno.",
                '7. Přidejte veřejnou IP adresu počítače nebo serveru, kde poběží Coinductor. Zjistíte ji například na <a href="https://ifconfig.me/">https://ifconfig.me/</a> nebo <a href="https://whatismyipaddress.com/">https://whatismyipaddress.com/</a>.',
                "8. Pokud se vaše IP mění po restartu routeru nebo ze dne na den, berte ji jako dynamickou. Uživatelé s dynamickou IP by měli nechat živé provádění zamčené, whitelist podle potřeby ručně aktualizovat, nebo později použít důvěryhodný stále běžící stroj/VPS se stabilní veřejnou IP.",
                "9. Až je omezení na důvěryhodné IP nastavené, povolte Reading a Enable Spot & Margin & Stock Trading. Nepovolujte Futures, Margin Loan/Repay/Transfer, Universal Transfer, Prediction Trading ani Withdrawals.",
                "10. Vložte klíč pro živé obchodování do Coinductoru v sekci Live Actions. Živé odeslání zůstává zamčené, dokud jej nepovolí samostatná bezpečnostní fáze.",
                "",
                "Důležité: použijte jiný klíč než read-only. Výběry nechte navždy vypnuté. Coinductor umí tento klíč uložit lokálně, ale živé odeslání nezpřístupní, dokud nejsou zapnuté deterministické bezpečnostní brány a výslovná potvrzení.",
                "",
                'V aplikaci: tento klíč vkládáte a spravujete na <a href="guide:page-live-actions">stránce Live Actions</a> a živé odeslání zůstává zamčené, dokud neposunete fáze podle <a href="guide:safety-model">Bezpečnostního modelu</a>.',
            ]
        ),
        "warning": "Klíč pro živé obchodování může zadávat a rušit Spot příkazy, pokud to oprávnění v Binance dovolí. Nechte výběry vypnuté a klíč omezte pouze na důvěryhodné IP.",
        "images": [
            "Očištěná stránka API Management v Binance.",
            "Očištěná obrazovka omezení pro živé obchodování: nejdřív omezit na důvěryhodnou IP, pak povolit Reading a Spot trading; výběry zůstávají vypnuté.",
        ],
    },
    "binance-testnet": {
        "title": "Binance Spot Testnet (nácvik s virtuálními prostředky)",
        "summary": "Vytvořte samostatný Testnet klíč, abyste si logiku obchodů vyzkoušeli s virtuálními prostředky dřív, než půjde o skutečné peníze.",
        "body": "<br>".join(
            [
                "Spot Testnet je samostatné prostředí Binance s virtuálními prostředky. Má vlastní účet a vlastní API klíče; s vaším skutečným zůstatkem na Binance nijak nesouvisí.",
                "Použijte jej, abyste viděli, jak Coinductor připravuje náhled a (po výslovném potvrzení) odesílá příkazy, ještě než sáhnete na skutečný klíč.",
                "",
                '1. Otevřete <a href="https://testnet.binance.vision/">https://testnet.binance.vision/</a> a přihlaste se účtem GitHub (Testnet používá pro přihlášení GitHub, ne váš běžný účet Binance).',
                "2. Na této stránce vygenerujte Testnet API Key a Secret Key.",
                "3. Obě hodnoty vložte do panelu Spot Testnet níže (nebo v Nastavení) a stiskněte Uložit Testnet klíč. Ukládají se do lokálního souboru .env, odděleně od read-only a live-trading klíčů.",
                "4. Stiskněte Zkontrolovat přístup k Testnetu a ověřte, že se klíč dostane k Testnet účtu.",
                "5. Testnet příkazy lze pro větší kontrolu spouštět i z terminálu, například: python -m trading_agent testnet-market-buy --symbol BTCUSDT --quote-amount 10. Úplný seznam Testnet CLI příkazů najdete v README.md.",
                "",
                "Testnet je volitelný, ale doporučený před jakýmkoliv skutečným mainnet příkazem: nic nestojí, nic neriskuje a procvičí stejnou logiku validace příkazů a potvrzovacích řetězců jako skutečné obchodování.",
                "",
                'V aplikaci: Testnet provádění se spouští ze <a href="guide:page-action-plan">stránky Action Plan</a> (včetně nasazení prvního portfolia), jakmile bezpečnostní fáze dosáhne stavu Testnet ready.',
            ]
        ),
    },
    "safety-model": {
        "title": "Bezpečnostní model",
        "summary": "Jak Coinductor odděluje doporučení, náhledy, zabezpečené akce a živé provádění.",
        "body": "<br>".join(
            [
                "Coinductor je navržen tak, aby AI pomáhala vysvětlovat a řadit ohraničené možnosti, zatímco limity a brány provádění vlastní deterministický kód.",
                "",
                "Bezpečnostní fáze:",
                "1. Setup: pouze lokální profil a konfigurace.",
                "2. Read-only connected: portfolio lze analyzovat, ale akce měnící stav na burze zůstávají nedostupné.",
                "3. Testnet ready: logiku obchodů lze tam, kde je to podporováno, testovat bez skutečných prostředků.",
                "4. Preview only: mainnet akce lze připravit k posouzení, ale ne odeslat.",
                "5. Guarded live: výslovně povolené postupy mohou akce odeslat až po deterministických kontrolách a potvrzeních.",
                "",
                "Coinductor nikdy nepovoluje výběry. Limity ztrát, chráněná aktiva, stropy kapitálu a potvrzovací brány zůstávají deterministické i tehdy, když je připojená AI.",
                "",
                'V aplikaci: tyto fáze posouváte na <a href="guide:page-live-actions">stránce Live Actions</a> a zabezpečené akce se připravují a potvrzují na <a href="guide:page-action-plan">stránce Action Plan</a>.',
            ]
        ),
    },
    "portfolio-roles": {
        "title": "Role v portfoliu",
        "summary": "Pochopte chráněná aktiva, obchodovaná aktiva, zdroje kapitálu a ruční přepsání rolí.",
        "body": "<br>".join(
            [
                "Role v portfoliu určují, co Coinductor smí s daným aktivem dělat.",
                "",
                "System default: zruší ruční přepsání a nechá rozhodnout poslední klasifikaci portfolia / konfiguraci.",
                "Protected core: dlouhodobá jádrová pozice. Coinductor by ji neměl používat k běžnému financování ani obchodování.",
                "Protected utility: aktivum držené k jinému účelu, například kvůli slevám na poplatcích nebo výhodám na burze. Je chráněné stejně jako jádrové pozice.",
                "Trading allowed: aktivum může být zvažováno pro zabezpečená doporučení spotových obchodů.",
                "Grid candidate: aktivum může být zvažováno pro doporučení parametrů Binance Spot Grid.",
                "Rebalancing candidate: aktivum může být zahrnuto do doporučení rebalancovacího koše.",
                "Funding source: aktivum může poskytovat kapitál v rámci nastavených limitů financování.",
                "Dust/airdrop funding: malá nebo nechtěná aktiva lze podle pravidel převést na provozní kapitál.",
                "Active strategy: aktivum může být způsobilé pro obchodování, Grid i rebalancování.",
                "Stable: stablecoinová pozice, obvykle provozní kapitál nebo rezerva; nepovažuje se za chráněné volatilní aktivum.",
                "Unclassified: ponechat viditelné, ale zatím mu záměrně nepřiřazovat aktivní roli.",
                "",
                "Ruční přepsání je k dispozici proto, že každému uživateli záleží na jiných aktivech. Přepsání může změnit způsobilost, ale nesmí vypnout globální limity rizika, stop-loss ani potvrzovací brány.",
                "",
                'V aplikaci: tato přepsání nastavujete na <a href="guide:page-portfolio">stránce Portfolio</a>.',
            ]
        ),
    },
    "page-overview": {
        "title": "Stránka Přehled",
        "summary": "Váš přehled: aktuální stav portfolia, bezpečnostní připravenost, poslední rozhodnutí a doporučené další kroky.",
        "body": "<br>".join(
            [
                "Přehled je první stránka a shrnuje vše na jednom místě. Nic zde nezadává příkaz.",
                "",
                "Co uvidíte:",
                "- Karty s metrikami: celková hodnota portfolia, likvidní vs. zamčený zůstatek a aktuální riziková brána (například zda je návrh AI HOLD).",
                '- Bezpečnost &amp; připravenost: aktuální bezpečnostní fáze a zda jsou dostupné zabezpečené živé akce. Viz návod <a href="guide:safety-model">Bezpečnostní model</a>.',
                "- Poslední rozhodnutí: nejnovější výsledek analýzy a proč byla či nebyla akce doporučena.",
                "- Doporučené akce: prioritizované další kroky z posledního běhu.",
                "- Shrnutí AI: volitelný komentář běžným jazykem, když je připojený poskytovatel AI.",
                "- Banner dokončení nastavení: objeví se, když ještě není připojený read-only přístup k Binance, včetně tlačítka zpět do nastavení.",
                "",
                "Co můžete dělat:",
                "- Spustit analýzu a vše výše aktualizovat z aktuálních dat.",
                '- Otevřít podrobný report pro úplný rozpis, nebo přejít na <a href="guide:page-action-plan">Action Plan</a> a podle doporučení jednat.',
                "",
                'Běh pouze čte data a vytváří doporučení. Jakákoliv živá akce se děje až později, na <a href="guide:page-live-actions">Live Actions</a> nebo <a href="guide:page-action-plan">Action Plan</a>, za výslovného potvrzení.',
            ]
        ),
    },
    "page-portfolio": {
        "title": "Stránka Portfolio",
        "summary": "Úplná inventura aktiv s rolemi, oceněním a ručním přepsáním role u jednotlivých aktiv.",
        "body": "<br>".join(
            [
                "Portfolio vypisuje každé sledované aktivum s jeho zůstatkem, hodnotou a rolí. Role rozhodují, co s ním Coinductor smí dělat.",
                "",
                "Co můžete dělat:",
                "- Projít zůstatky a způsob ocenění jednotlivých aktiv (aktiva, která nelze ocenit, se zobrazí jako neoceněná, místo aby zmizela).",
                "- Nastavit ruční přepsání role, když chcete změnit způsobilost aktiva pro obchodování, Grid, rebalancování, financování nebo převod dustu.",
                "",
                'Význam jednotlivých rolí a pravidla bezpečného přepsání najdete v návodu <a href="guide:portfolio-roles">Role v portfoliu</a>. Přepsání může změnit způsobilost, ale nikdy nevypne globální limity rizika, kontroly chráněných aktiv ani potvrzovací brány.',
            ]
        ),
    },
    "page-live-actions": {
        "title": "Stránka Live Actions",
        "summary": "Ovládání bezpečnostních fází a klíč pro živé obchodování: jak Coinductor přechází z read-only k zabezpečenému živému odeslání.",
        "body": "<br>".join(
            [
                "Live Actions je místo, kde probíhá záměrný, postupný přechod od read-only k zabezpečenému živému provádění. Každý krok je výslovný a vratný.",
                "",
                "Co uvidíte:",
                "- Aktuální bezpečnostní fázi a ovládání pro její posun (Setup, Read-only connected, Testnet ready, Preview only, Armed, Live enabled).",
                '- Správu samostatného klíče pro živé obchodování (viz návod <a href="guide:binance-live-api">Binance API pro živé obchodování</a>).',
                "- Stavové odznaky jako VERIFIED, CONFIGURED a LOCKED, které ukazují, co je připravené a co je stále zamčené.",
                "",
                "Co můžete dělat:",
                "- Posunout bezpečnostní fázi napsáním přesné potvrzovací fráze zobrazené u daného kroku. Posun je podložený deterministickými kontrolami, ne jen tlačítkem.",
                "- Kdykoliv znovu zamknout živé odesílání.",
                "",
                'Nic není živé, dokud vědomě nedosáhnete fáze zabezpečeného živého provozu a každou akci nepotvrdíte. Úplný seznam fází najdete v návodu <a href="guide:safety-model">Bezpečnostní model</a>.',
            ]
        ),
    },
    "page-action-plan": {
        "title": "Stránka Action Plan",
        "summary": "Převeďte doporučení na náhledy a jednotlivě potvrzené akce: obchody, OCO ochranu, výběr z Earn a nasazení prvního portfolia.",
        "body": "<br>".join(
            [
                "Action Plan vypisuje konkrétní další kroky z posledního běhu a ke každému otevře detail. Každá akce s penězi má nejdřív náhled a vyžaduje vlastní napsané potvrzení.",
                "",
                "Co můžete dělat (každé je samostatně hlídané):",
                "- Zobrazit náhled a, pokud to bezpečnostní fáze dovolí, odeslat zabezpečený Spot obchod.",
                "- Přidat OCO ochranu (spojený take-profit / stop-loss) k otevřené pozici.",
                "- Vybrat prostředky z Flexible Earn jako krok k zajištění likvidity.",
                "- Challenge HOLD: požádat rizikový engine o nové vyhodnocení jednoho povoleného symbolu pro nákup. Stále projde všemi deterministickými kontrolami a stále může být zamítnut.",
                "- Nasazení prvního portfolia: spouštět po jednom aktivu/tranši koše při budování portfolia od nuly, na Testnetu nebo na mainnetu.",
                "",
                'Každé odeslání vyžaduje přesnou potvrzovací frázi dané akce a projde kontrolami rozpočtu, expozice, stop-lossu, kill-switche a bezpečnostní fáze. Viz <a href="guide:page-live-actions">Live Actions</a> a návod <a href="guide:safety-model">Bezpečnostní model</a>.',
            ]
        ),
    },
    "page-active-strategies": {
        "title": "Stránka Aktivní strategie",
        "summary": "Sledujte Grid a rebalancovací boty, které jste zaregistrovali lokálně, včetně zdraví a termínu další kontroly.",
        "body": "<br>".join(
            [
                "Coinductor doporučuje parametry Grid a rebalancovacích botů, ale samotné boty nevytváří; vytvoříte je v aplikaci Binance a zde je zaregistrujete pro lokální sledování.",
                "",
                "Co můžete dělat:",
                "- Vidět každého zaregistrovaného bota s jeho zdravím, termínem další kontroly a tím, zda je cena blízko nastaveného rozpětí.",
                "- Změnit stav bota na Paused, Stopped nebo Closed podle toho, jak jej spravujete v Binance.",
                "",
                "Sledování vychází z lokální registrace a tržních cen, ne z vlastní telemetrie provádění botů na Binance, takže jej berte spíš jako pomůcku ke kontrole než jako živý přehled zisků a ztrát.",
            ]
        ),
    },
    "page-run-history": {
        "title": "Stránka Historie běhů",
        "summary": "Procházejte minulé analytické běhy a otevírejte jejich reporty.",
        "body": "<br>".join(
            [
                "Historie běhů je záznam předchozích analytických běhů pouze pro čtení.",
                "",
                "Co můžete dělat:",
                "- Vidět, kdy každý běh proběhl, v jakém režimu a s jakým výsledkem.",
                "- Otevřít report běhu a projít stav portfolia, rozhodnutí a doporučení zachycená v daném okamžiku.",
                "",
                "Historie je užitečná pro porovnání, jak se doporučení a stav portfolia mezi běhy mění.",
            ]
        ),
    },
    "page-ai-assistant": {
        "title": "Stránka AI Assistant",
        "summary": "Ptejte se na aplikaci, své reporty a stav portfolia; můžete přiložit snímky obrazovky. Živé akce nikdy neprovádí.",
        "body": "<br>".join(
            [
                "AI Assistant odpovídá na dotazy a umí vás nasměrovat na správnou obrazovku nebo návod. Má pouze poradní roli: nikdy nemůže zadat obchod, vybrat z Earn ani změnit bezpečnostní bránu.",
                "",
                "Co můžete dělat:",
                "- Zeptat se, jak funguje určitá funkce, co znamená část reportu nebo jaký je váš aktuální stav.",
                "- Přiložit obrázek (ze souboru nebo schránky) a zeptat se na snímek obrazovky.",
                "- Znovu použít a kopírovat starší zprávy z historie.",
                "",
                'Deterministické odpovědi o zdokumentovaných funkcích mají přednost a fungují i bez nastaveného poskytovatele AI. Připojení poskytovatele přidá širší volné odpovědi; viz návody <a href="guide:local-ai">Lokální AI s Ollamou</a> a <a href="guide:cloud-ai">Cloudové AI API</a>. Jakoukoliv akci, kterou asistent navrhne, stále musíte potvrdit v běžném zabezpečeném postupu.',
            ]
        ),
    },
    "page-settings": {
        "title": "Stránka Nastavení",
        "summary": "Kontroly připojení, nastavení poskytovatele AI, jazyk, onboarding profil, soukromí & data a diagnostika.",
        "body": "<br>".join(
            [
                "V Nastavení připojujete služby a spravujete lokální data. Kontroly připojení se spouští jen tehdy, když na ně kliknete.",
                "",
                "Co můžete dělat:",
                '- Spustit kontrolu read-only připojení k Binance (viz návod <a href="guide:binance-api">Binance read-only API</a>) a kontrolu poskytovatele AI, případně Nastavit modely AI.',
                "- Přepnout jazyk aplikace mezi angličtinou a češtinou.",
                "- Projít nebo znovu otevřít onboarding profil, případně zopakovat prohlídku aplikace.",
                "- Soukromí &amp; data: Exportovat diagnostiku (očištěný report bez klíčů a zůstatků, bezpečný ke sdílení při hlášení problému), Resetovat onboarding nebo Smazat lokální data.",
                "",
                "Vše zde zůstává lokálně na tomto počítači. Smazání lokálních dat odstraní pouze vybrané soubory a nikdy nesáhne na nic mimo vlastní složku aplikace.",
            ]
        ),
    },
    "page-help-guides": {
        "title": "Stránka Nápověda a návody",
        "summary": "Procházejte všechny vestavěné návody včetně průvodců nastavením a těchto vysvětlení jednotlivých stránek.",
        "body": "<br>".join(
            [
                "Nápověda a návody shromažďuje všechny vestavěné návody na jednom místě: průvodce nastavením AI a Binance, bezpečnostní model, role v portfoliu a návod ke každé stránce aplikace.",
                "",
                "Stejné návody jsou dostupné i během prvotního nastavení, takže kvůli nápovědě nikdy nemusíte vstupovat do hlavní aplikace. Odkazy uvnitř návodu otevřou buď externí stránku (v prohlížeči), nebo jiný návod.",
            ]
        ),
    },
}
