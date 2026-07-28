"""Localizable manual-setup steps for the bot advisors.

Binance has no public API for creating trading bots, so the procedure the user
has to carry out by hand is the one place the assistant cannot act for them -
and it was the one place still stuck in English inside a translated UI.

The advisors used to compose these as f-strings, which left nothing to
translate at the display boundary: a finished sentence with numbers baked in
can only be re-localized by parsing English prose back apart. So they emit
``ManualStep`` (a key plus its parameters) instead, and the text is composed
once per reader: English for the Markdown report, the user's language for the
desktop app.

Parameter values are deliberately *not* translated. They are either numbers or
labels the user must find verbatim in Binance's own interface ("By Ratio",
"OFF", "Equal"), and translating those would send someone hunting for a control
that does not exist.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field

DEFAULT_LANGUAGE = "en"


@dataclass(frozen=True)
class ManualStep:
    """One instruction, still unrendered.

    ``key`` selects the sentence from ``MANUAL_STEP_TEXT``; ``params`` fills its
    placeholders. Both survive a round trip through JSON so the desktop app can
    render a step recorded by an earlier run.
    """

    key: str
    params: dict[str, str] = field(default_factory=dict)


# Every sentence the advisors can emit. English is the fallback: an unknown key
# or a missing translation renders in English rather than showing the reader a
# raw identifier.
MANUAL_STEP_TEXT: dict[str, dict[str, str]] = {
    "bots_manual_because_no_api": {
        "en": (
            "Binance has no public API for creating trading bots, so Coinductor works out the "
            "parameters and you enter them yourself - it is not an unfinished feature."
        ),
        "cs": (
            "Binance nemá veřejné API pro zakládání obchodních botů, takže Coinductor spočítá "
            "parametry a vy je zadáte sami - není to nedodělaná funkce."
        ),
    },
    # --- Spot Grid -------------------------------------------------------
    "grid_blocked_do_not_create": {
        "en": "Do not create the grid while any deployment blocker remains.",
        "cs": "Nezakládejte grid, dokud trvá jakýkoli blokátor nasazení.",
    },
    "grid_blocked_rerun": {
        "en": "Run the assistant again after the risk cooldown/kill switch and market-status blockers clear.",
        "cs": "Spusťte asistenta znovu, až pominou blokátory rizikové pauzy, kill switche a stavu trhu.",
    },
    "grid_open_menu": {
        "en": "Open Binance Home > Trading Bots > Spot Grid.",
        "cs": "Otevřete Binance Home > Trading Bots > Spot Grid.",
    },
    "grid_select_symbol": {
        # Written as a pair, the way Binance's own picker shows it.
        "en": "Select {symbol} and choose Manual parameters.",
        "cs": "Vyberte {symbol} a zvolte Manual parameters.",
    },
    "grid_set_range": {
        "en": "Set lower price {low} and upper price {high}.",
        "cs": "Nastavte spodní cenu {low} a horní cenu {high}.",
    },
    "grid_set_count": {
        "en": "Choose Arithmetic and set {count} grids.",
        "cs": "Zvolte Arithmetic a nastavte {count} gridů.",
    },
    "grid_set_investment": {
        "en": "In the Investment currency dropdown select {quote}, then enter no more than {investment} {quote}.",
        "cs": "V rozbalovacím seznamu Investment currency vyberte {quote} a zadejte nejvýše {investment} {quote}.",
    },
    "grid_binance_minimum_wins": {
        "en": (
            "Binance will show its own minimum investment for the range you entered, and it is "
            "usually higher than this figure - ours is a risk cap, theirs is an exchange floor. "
            "If theirs is higher, do not raise yours to match: close the form and decide "
            "deliberately whether that much capital belongs in this bot."
        ),
        "cs": (
            "Binance u zadaného rozsahu ukáže vlastní minimální investici a bývá vyšší než tato "
            "částka - naše je strop rizika, jejich je limit burzy. Pokud je jejich vyšší, "
            "nezvyšujte tu naši, abyste se trefil: zavřete formulář a rozmyslete si, jestli do "
            "tohoto bota tolik kapitálu opravdu patří."
        ),
    },
    "grid_trading_up_off": {
        "en": "Keep Trading Up OFF and Grid Trigger OFF for the initial deployment.",
        "cs": "Při prvním nasazení nechte Trading Up na OFF a Grid Trigger na OFF.",
    },
    "grid_set_tpsl": {
        "en": "Enable TP/SL; set stop loss near {stop_loss} and take profit near {take_profit}.",
        "cs": "Zapněte TP/SL; nastavte stop loss kolem {stop_loss} a take profit kolem {take_profit}.",
    },
    "grid_sell_all_base": {
        "en": (
            "Enable Sell All Base Coin on Stop only for this isolated grid allocation so stopping "
            "the bot closes its residual base exposure."
        ),
        "cs": (
            "Zapněte Sell All Base Coin on Stop pouze pro tuto oddělenou alokaci gridu, aby "
            "zastavení bota uzavřelo i zbytkovou pozici v základní měně."
        ),
    },
    "grid_review_before_confirm": {
        "en": "Review Binance's estimated profit/grid and minimum investment before confirming.",
        "cs": "Před potvrzením zkontrolujte odhad zisku na grid a minimální investici podle Binance.",
    },
    # This used to tell a desktop user to copy a TOML file by hand and fill in
    # values. The app has had a dialog for it since active-strategy monitoring
    # was added; the step was simply never updated to point at it.
    "grid_register_locally": {
        "en": (
            "After creation, register it in Coinductor: Active Strategies > Register active bot > "
            "Import latest recommendation, then add the bot ID Binance gave you and save."
        ),
        "cs": (
            "Po vytvoření ho zaregistrujte v Coinductoru: Aktivní strategie > Registrovat aktivního "
            "bota > Importovat poslední doporučení, pak doplňte ID bota z Binance a uložte."
        ),
    },
    "grid_rerun_to_monitor": {
        "en": "Rerun the assistant to begin active range monitoring.",
        "cs": "Spusťte asistenta znovu, aby začal aktivně sledovat rozsah.",
    },
    # --- Rebalancing Bot -------------------------------------------------
    "rebalance_blocked_do_not_create": {
        "en": "Do not create a Rebalancing Bot while any deployment blocker remains.",
        "cs": "Nezakládejte Rebalancing Bot, dokud trvá jakýkoli blokátor nasazení.",
    },
    "rebalance_blocked_divider": {
        "en": (
            "Everything below is the configuration to use once every blocker above is resolved. "
            "Rerun the assistant then, and only create the bot if it is no longer blocked."
        ),
        "cs": (
            "Vše níže je nastavení, které použijete až po vyřešení všech blokátorů výše. "
            "Potom spusťte asistenta znovu a bota založte, jen pokud už blokovaný není."
        ),
    },
    "rebalance_open_menu": {
        "en": "Open Binance Home > Trading Bots > Rebalancing Bot.",
        "cs": "Otevřete Binance Home > Trading Bots > Rebalancing Bot.",
    },
    "rebalance_allocation_custom": {
        "en": (
            "After funding is complete: Select Equal as the starting layout, then manually edit "
            "the percentages; use {allocation}."
        ),
        "cs": (
            "Po dokončení financování: jako výchozí rozvržení zvolte Equal a poté ručně upravte "
            "procenta; použijte {allocation}."
        ),
    },
    "rebalance_allocation_preset": {
        "en": "After funding is complete: Select {method}; use {allocation}.",
        "cs": "Po dokončení financování: zvolte {method}; použijte {allocation}.",
    },
    "rebalance_auto_rebalance": {
        "en": "Enable Auto Rebalance, choose {mode}, and set {threshold}%.",
        "cs": "Zapněte Auto Rebalance, zvolte {mode} a nastavte {threshold} %.",
    },
    "rebalance_trigger_price": {
        "en": "Trigger Price: {state} for the initial deployment.",
        "cs": "Trigger Price: {state} pro první nasazení.",
    },
    "rebalance_stop_trigger": {
        "en": "Stop Trigger: {state} for the initial deployment.",
        "cs": "Stop Trigger: {state} pro první nasazení.",
    },
    "rebalance_sell_all_on_stop": {
        "en": "Sell All Coins on Stop: {state} to avoid unintended liquidation on a manual stop.",
        "cs": "Sell All Coins on Stop: {state}, aby ruční zastavení nezpůsobilo nechtěný výprodej.",
    },
    "rebalance_invest_cap": {
        "en": "Invest no more than {investment} USDC-equivalent.",
        "cs": "Investujte nejvýše {investment} v ekvivalentu USDC.",
    },
    "rebalance_fund_separately": {
        "en": (
            "Fund the bot from its separate USDC allocation; let Binance acquire the configured "
            "ETH share inside the bot."
        ),
        "cs": (
            "Financujte bota z jeho oddělené alokace v USDC; nastavený podíl ETH ať nakoupí "
            "Binance uvnitř bota."
        ),
    },
    "rebalance_keep_wbeth": {
        "en": "Keep existing WBETH outside the bot and do not convert or sell it automatically.",
        "cs": "Stávající WBETH nechte mimo bota a automaticky ho nekonvertujte ani neprodávejte.",
    },
    "rebalance_do_not_sell_protected": {
        "en": "Do not fund it by automatically selling protected assets ({protected}).",
        "cs": "Nefinancujte ho automatickým prodejem chráněných aktiv ({protected}).",
    },
    "rebalance_review_minimums": {
        "en": "Review Binance minimum allocation and investment requirements before confirming.",
        "cs": "Před potvrzením zkontrolujte minimální alokaci a investiční požadavky Binance.",
    },
    "rebalance_record_locally": {
        "en": "Record the created bot parameters in the local strategy registry before the next run.",
        "cs": "Před dalším během zapište parametry vytvořeného bota do lokálního registru strategií.",
    },
    # --- Funding the Rebalancing Bot -------------------------------------
    "funding_convert": {
        "en": "Convert approximately {value} USDC-equivalent of {asset} to {quote}.",
        "cs": "Zkonvertujte přibližně {value} v ekvivalentu USDC z {asset} na {quote}.",
    },
    "funding_summary_balance_covers": {
        "en": "Existing {quote} balance fully covers the {investment} setup.",
        "cs": "Stávající zůstatek {quote} plně pokrývá nastavení za {investment}.",
    },
    "funding_summary_conversions_cover": {
        "en": (
            "Existing {available} {quote} plus proposed conversions cover the {investment} investment."
        ),
        "cs": (
            "Stávajících {available} {quote} plus navržené konverze pokryjí investici {investment}."
        ),
    },
    "funding_summary_gap": {
        "en": (
            "Use existing {available} {quote} and convert about {covered} from allowed sources. "
            "Remaining gap: {uncovered} {quote}; do not fill it from protected BTC, ETH, WBETH, "
            "or BNB without a separate policy decision."
        ),
        "cs": (
            "Použijte stávajících {available} {quote} a zkonvertujte přibližně {covered} z povolených "
            "zdrojů. Zbývající mezera: {uncovered} {quote}; nedoplňujte ji z chráněných BTC, ETH, "
            "WBETH ani BNB bez samostatného rozhodnutí o pravidlech."
        ),
    },
}


def render_manual_step(step: ManualStep, language: str = DEFAULT_LANGUAGE) -> str:
    """Compose one step's sentence, falling back to English then to the key.

    A key with no entry at all renders as the key itself: visible enough in a
    report to be reported as a bug, but never a crash in front of a user who
    only wanted to read their next move.
    """
    translations = MANUAL_STEP_TEXT.get(step.key)
    if translations is None:
        return step.key
    template = translations.get(language) or translations[DEFAULT_LANGUAGE]
    try:
        return template.format(**step.params)
    except KeyError:
        # A template that outgrew its call site is a bug, but showing the
        # unfilled sentence beats showing nothing where an instruction belongs.
        return template


def render_manual_steps(
    steps: Iterable[ManualStep], language: str = DEFAULT_LANGUAGE
) -> tuple[str, ...]:
    return tuple(render_manual_step(step, language) for step in steps)


def manual_steps_to_json(steps: Iterable[ManualStep]) -> str:
    return json.dumps(
        [{"key": step.key, "params": step.params} for step in steps],
        ensure_ascii=False,
    )


def manual_steps_from_json(payload: str) -> tuple[ManualStep, ...]:
    """Parse stored steps, tolerating rows written before this format existed.

    Runs recorded by 0.1.3 stored newline-separated English prose. Those rows
    carry no key to translate, so they are returned verbatim under a sentinel
    key that renders as itself - an old run keeps showing what it always showed
    instead of vanishing from the dialog.
    """
    text = (payload or "").strip()
    if not text:
        return ()
    try:
        decoded = json.loads(text)
    except (ValueError, TypeError):
        return tuple(ManualStep(line) for line in text.splitlines() if line.strip())
    if not isinstance(decoded, list):
        return ()
    steps: list[ManualStep] = []
    for item in decoded:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key", "")).strip()
        if not key:
            continue
        raw_params = item.get("params")
        params = (
            {str(name): str(value) for name, value in raw_params.items()}
            if isinstance(raw_params, dict)
            else {}
        )
        steps.append(ManualStep(key, params))
    return tuple(steps)
