from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_LOCALES = ("en-US", "es-ES", "cs-CZ", "pt-BR")
REQUIRED_TRANSLATION_KEYS = (
    "planner.unavailable",
    "planner.summary",
    "funding.deposit.detail",
    "funding.reserve.detail",
    "funding.deployment.detail",
    "steps.fund.detail",
    "steps.buy.detail",
    "notes.execution.detail",
)


@dataclass(frozen=True)
class LocaleProfile:
    locale: str
    language_name: str
    region_name: str
    fiat_currency: str
    funding_currency: str
    default_starting_budget: float
    fiat_to_funding_hint: str
    translations: dict[str, str]


LOCALE_PROFILES: dict[str, LocaleProfile] = {
    "en-US": LocaleProfile(
        locale="en-US",
        language_name="English",
        region_name="United States",
        fiat_currency="USD",
        funding_currency="USDC",
        default_starting_budget=500.0,
        fiat_to_funding_hint="Use USD as the funding reference and keep the operating budget in USDC.",
        translations={
            "planner.unavailable": "First portfolio planning is available after selecting Build my first portfolio.",
            "planner.summary": "Start with {investment:.0f} {fiat}: keep {reserve:.0f} {fiat} as reserve and convert about {deployable:.0f} {fiat} to {funding} for the first basket.",
            "funding.deposit.detail": "Suggested first funding amount before any automation.",
            "funding.reserve.detail": "Keep this liquid; do not allocate it to bots or trades.",
            "funding.deployment.detail": "Convert this operating budget to {funding}, then split it into the proposed basket.",
            "steps.fund.detail": "Deposit {fiat}, then convert the operating budget to {funding}.",
            "steps.buy.detail": "Buy the suggested assets manually first; Coinductor can analyze after read-only API is connected.",
            "notes.execution.detail": "This planner never places orders; it prepares a human-readable starting plan.",
        },
    ),
    "es-ES": LocaleProfile(
        locale="es-ES",
        language_name="Español",
        region_name="Spain",
        fiat_currency="EUR",
        funding_currency="USDC",
        default_starting_budget=500.0,
        fiat_to_funding_hint="Deposita EUR y convierte el capital operativo a USDC.",
        translations={
            "planner.unavailable": "La planificación de la primera cartera está disponible tras seleccionar Build my first portfolio.",
            "planner.summary": "Empieza con {investment:.0f} {fiat}: conserva {reserve:.0f} {fiat} como reserva y convierte unos {deployable:.0f} {fiat} a {funding} para la primera cesta.",
            "funding.deposit.detail": "Importe inicial sugerido antes de activar cualquier automatización.",
            "funding.reserve.detail": "Mantén esta parte líquida; no la asignes a bots ni operaciones.",
            "funding.deployment.detail": "Convierte este capital operativo a {funding} y divídelo en la cesta propuesta.",
            "steps.fund.detail": "Deposita {fiat} y convierte el capital operativo a {funding}.",
            "steps.buy.detail": "Compra primero los activos sugeridos manualmente; Coinductor podrá analizarlos tras conectar la API de solo lectura.",
            "notes.execution.detail": "Este planificador nunca crea órdenes; prepara un plan inicial legible.",
        },
    ),
    "cs-CZ": LocaleProfile(
        locale="cs-CZ",
        language_name="Čeština",
        region_name="Česko",
        fiat_currency="CZK",
        funding_currency="USDC",
        default_starting_budget=10_000.0,
        fiat_to_funding_hint="Vlož CZK a provozní kapitál převeď do USDC.",
        # Formal address throughout, and the wizard choice named as it appears
        # on screen. These sat beside labels that address the reader as "vy",
        # and referred to an English button that the Czech wizard does not have.
        translations={
            "planner.unavailable": "Plán prvního portfolia se zobrazí po výběru možnosti Vybudovat první portfolio.",
            "planner.summary": "Začněte s {investment:.0f} {fiat}: nechte si {reserve:.0f} {fiat} jako rezervu a přibližně {deployable:.0f} {fiat} převeďte do {funding} na první koš.",
            "funding.deposit.detail": "Doporučená první částka před jakoukoliv automatizací.",
            "funding.reserve.detail": "Tuhle část nechte likvidní; nepoužívejte ji pro boty ani obchody.",
            "funding.deployment.detail": "Tento provozní kapitál převeďte do {funding} a potom ho rozdělte podle navrženého koše.",
            "steps.fund.detail": "Vložte {fiat} a provozní kapitál převeďte do {funding}.",
            "steps.buy.detail": "Navržená aktiva nejdřív nakupte ručně; Coinductor je zanalyzuje po připojení read-only API.",
            "notes.execution.detail": "Tento plánovač nikdy nezadává příkazy; připravuje jen čitelný startovní plán.",
        },
    ),
    "pt-BR": LocaleProfile(
        locale="pt-BR",
        language_name="Português do Brasil",
        region_name="Brazil",
        fiat_currency="BRL",
        funding_currency="USDC",
        default_starting_budget=2_500.0,
        fiat_to_funding_hint="Deposite BRL e converta o capital operacional para USDC.",
        translations={
            "planner.unavailable": "O planejamento da primeira carteira fica disponível depois de selecionar Build my first portfolio.",
            "planner.summary": "Comece com {investment:.0f} {fiat}: mantenha {reserve:.0f} {fiat} como reserva e converta cerca de {deployable:.0f} {fiat} para {funding} para a primeira cesta.",
            "funding.deposit.detail": "Valor inicial sugerido antes de qualquer automação.",
            "funding.reserve.detail": "Mantenha esta parte líquida; não aloque em bots ou trades.",
            "funding.deployment.detail": "Converta este capital operacional para {funding} e divida-o na cesta proposta.",
            "steps.fund.detail": "Deposite {fiat} e converta o capital operacional para {funding}.",
            "steps.buy.detail": "Compre primeiro os ativos sugeridos manualmente; o Coinductor poderá analisá-los depois que a API somente leitura for conectada.",
            "notes.execution.detail": "Este planejador nunca envia ordens; ele prepara um plano inicial legível.",
        },
    ),
}


def locale_profile(locale: str | None) -> LocaleProfile:
    return LOCALE_PROFILES.get(normalize_locale(locale), LOCALE_PROFILES["en-US"])


def normalize_locale(locale: str | None) -> str:
    raw = str(locale or "").strip()
    if not raw:
        return "en-US"
    lowered = raw.lower().replace("_", "-")
    for supported in SUPPORTED_LOCALES:
        if lowered == supported.lower():
            return supported
    return "en-US"


def translated(profile: LocaleProfile, key: str, **values: object) -> str:
    template = profile.translations[key]
    return template.format(**values)
