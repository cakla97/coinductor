"""Localizable text the engine produces for the desktop to display.

The engine used to compose every user-facing sentence as an f-string, which
left nothing to translate at the display boundary: a finished sentence with
numbers baked in can only be re-localized by parsing English prose back apart.
Each localization round therefore fixed one screen and revealed the next.

So the producers emit ``Message`` (a key plus its parameters) and the text is
composed once per reader: English for the Markdown report, the user's language
for the desktop app. Started with the manual setup steps; the advisors, the
risk engine, the next-run recommender and the recommended-action builder use
the same registry.

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
class Message:
    """One instruction, still unrendered.

    ``key`` selects the sentence from ``MESSAGE_TEXT``; ``params`` fills its
    placeholders. Both survive a round trip through JSON so the desktop app can
    render a step recorded by an earlier run.
    """

    key: str
    params: dict[str, str] = field(default_factory=dict)


# Every sentence the advisors can emit. English is the fallback: an unknown key
# or a missing translation renders in English rather than showing the reader a
# raw identifier.
MESSAGE_TEXT: dict[str, dict[str, str]] = {
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
    # No config file, no setting names. The app should not send a desktop user
    # into a text editor to change how much of their own money it may commit;
    # saying the grid is out of reach at the current budget is the honest end of
    # the sentence until there is a control for it in the app.
    "grid_blocked_raise_capital": {
        "en": (
            "This grid needs more capital than your current budget allows for it, so there is "
            "nothing to set up yet."
        ),
        "cs": (
            "Tento grid potřebuje víc kapitálu, než mu váš současný rozpočet dovoluje, takže "
            "zatím není co nastavovat."
        ),
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
    # --- Grid scoring, the sentence under the card ---
    "grid_reason_score": {
        "en": "{symbol} scored {score}/100 as a range candidate: {reasons}.",
        "cs": "{symbol} získal {score}/100 jako kandidát na range strategii: {reasons}.",
    },
    "grid_reason_neutral_trend": {"en": "neutral trend", "cs": "neutrální trend"},
    "grid_reason_risk_on_trend": {"en": "controlled risk-on trend", "cs": "mírně růstový trend"},
    "grid_reason_risk_off_trend": {"en": "risk-off trend", "cs": "klesající trend"},
    "grid_reason_rsi": {"en": "RSI14 {value}", "cs": "RSI14 {value}"},
    "grid_reason_atr": {"en": "ATR {value}%", "cs": "ATR {value} %"},
    "grid_reason_atr_outside": {
        "en": "ATR {value}% (outside preferred range)",
        "cs": "ATR {value} % (mimo preferované pásmo)",
    },
    "grid_reason_ema_distance": {
        "en": "{value}% from EMA200",
        "cs": "{value} % od EMA200",
    },
    "grid_reason_7d": {"en": "7d move {value}%", "cs": "pohyb za 7 d {value} %"},
    "grid_reason_7d_directional": {
        "en": "7d move {value}% (strongly directional)",
        "cs": "pohyb za 7 d {value} % (výrazně jednosměrný)",
    },
    "grid_reason_no_research": {
        "en": "multi-timeframe research unavailable",
        "cs": "průzkum přes více časových rámců není k dispozici",
    },
    # --- Grid deployment blockers ---
    "grid_block_market_status": {
        "en": "market status is {status}, not SUITABLE",
        "cs": "stav trhu je {status}, ne SUITABLE",
    },
    "grid_block_max_bots": {
        "en": "maximum active grid bot count is already reached",
        "cs": "maximální počet aktivních grid botů je už vyčerpán",
    },
    "grid_block_kill_switch": {
        "en": "live risk kill switch is active",
        "cs": "je aktivní bezpečnostní kill switch",
    },
    "grid_block_cooldown": {
        "en": "loss cooldown is active",
        "cs": "probíhá pauza po ztrátě",
    },
    "grid_block_capital": {
        "en": "not enough grid capital: {grids} grids need {needed} USDC, only {allocated} is allocated",
        "cs": "málo kapitálu pro grid: {grids} gridů potřebuje {needed} USDC, vyhrazeno je jen {allocated}",
    },
    # --- Rebalancing summary and blockers ---
    "rebalance_summary": {
        "en": "Proposed {mode} Rebalancing Bot basket: {basket}; guarded investment {investment} USDC.",
        "cs": "Navržený košík Rebalancing Bota v režimu {mode}: {basket}; zabezpečená investice {investment} USDC.",
    },
    "rebalance_block_too_few_assets": {
        "en": "only {found} eligible assets meet the minimum value; at least {required} are required",
        "cs": "minimální hodnotu splňuje jen {found} vhodných aktiv; potřeba je alespoň {required}",
    },
    "rebalance_block_below_minimum": {
        "en": "guarded investment {investment} is below configured minimum {minimum}",
        "cs": "zabezpečená investice {investment} je pod nastaveným minimem {minimum}",
    },
    "rebalance_block_uncovered": {
        "en": "safe funding plan leaves {uncovered} USDC uncovered without using protected assets",
        "cs": "bezpečný plán financování nechává {uncovered} USDC nepokrytých bez sáhnutí na chráněná aktiva",
    },
    # --- Next-run recommendation ---
    "next_run_reason_grid": {
        "en": "A manual Spot Grid setup was recommended. Run again after setup to record the active strategy baseline.",
        "cs": "Bylo doporučeno ruční nastavení Spot Gridu. Po nastavení spusťte znovu, aby se zaznamenal výchozí stav strategie.",
    },
    "next_run_trigger_grid_created": {
        "en": "Run immediately after creating or skipping the recommended grid bot.",
        "cs": "Spusťte hned po založení doporučeného grid bota, nebo když ho vynecháte.",
    },
    "next_run_trigger_grid_range": {
        "en": "Run sooner if price moves outside the proposed grid range.",
        "cs": "Spusťte dřív, pokud cena vyjde mimo navržený rozsah gridu.",
    },
    "next_run_reason_spot_trade": {
        "en": "A spot trade recommendation was produced. Recheck after the next daily market update.",
        "cs": "Vzniklo doporučení ke spotovému obchodu. Zkontrolujte po další denní aktualizaci trhu.",
    },
    "next_run_trigger_after_execution": {
        "en": "Run sooner after manual execution.",
        "cs": "Spusťte dřív po ručním provedení obchodu.",
    },
    "next_run_trigger_tp_sl": {
        "en": "Run sooner if stop loss or take profit is hit.",
        "cs": "Spusťte dřív, pokud se trefí stop loss nebo take profit.",
    },
    "next_run_reason_no_action": {
        "en": "No action was recommended. Daily review is enough unless the market changes sharply.",
        "cs": "Nebyla doporučena žádná akce. Denní kontrola stačí, pokud se trh prudce nezmění.",
    },
    "next_run_trigger_large_move": {
        "en": "Run sooner after a large BTC or ETH move.",
        "cs": "Spusťte dřív po výrazném pohybu BTC nebo ETH.",
    },
    "next_run_trigger_manual_change": {
        "en": "Run sooner before making manual portfolio changes.",
        "cs": "Spusťte dřív, než budete ručně měnit portfolio.",
    },
    # --- Recommended actions, the headline of each item ---
    "action_review_rebalance_funding": {
        "en": "Review the Rebalancing Bot USDC funding plan.",
        "cs": "Zkontrolujte plán financování Rebalancing Bota v USDC.",
    },
    "action_review_rebalance_setup": {
        "en": "Review manual Binance Rebalancing Bot setup.",
        "cs": "Zkontrolujte ruční nastavení Rebalancing Bota na Binance.",
    },
    "action_review_active_grid": {
        "en": "Review active grid bot {name}.",
        "cs": "Zkontrolujte aktivního grid bota {name}.",
    },
    "action_review_grid_setup": {
        "en": "Review manual Spot Grid setup for {symbol}.",
        "cs": "Zkontrolujte ruční nastavení Spot Gridu pro {symbol}.",
    },
    "action_monitor_grid": {
        "en": "Monitor grid conditions for {symbol}; do not create it yet.",
        "cs": "Sledujte podmínky pro grid u {symbol}; zatím ho nezakládejte.",
    },
    "action_review_spot_trade": {
        "en": "Review spot trade proposal for {symbol}.",
        "cs": "Zkontrolujte návrh spotového obchodu pro {symbol}.",
    },
    "action_no_new_trade": {
        "en": "Do not open a new trade from this run.",
        "cs": "Z tohoto běhu neotvírejte nový obchod.",
    },
    # One key per label rather than a label parameter: a parameter is a plain
    # string, so a nested key would reach the reader unrendered.
    "action_source_capital_spot_trade": {
        "en": "For the spot trade, consider sourcing {amount} {quote} manually; first candidate is {asset}.",
        "cs": "Pro spotový obchod zvažte ruční obstarání {amount} {quote}; první kandidát je {asset}.",
    },
    "action_source_capital_grid_setup": {
        "en": "For the grid setup, consider sourcing {amount} {quote} manually; first candidate is {asset}.",
        "cs": "Pro nastavení gridu zvažte ruční obstarání {amount} {quote}; první kandidát je {asset}.",
    },
    "action_funding_gap_spot_trade": {
        "en": "Do not execute the spot trade until the {amount} {quote} funding gap is resolved.",
        "cs": "Neprovádějte spotový obchod, dokud není vyřešena chybějící částka {amount} {quote}.",
    },
    "action_funding_gap_grid_setup": {
        "en": "Do not execute the grid setup until the {amount} {quote} funding gap is resolved.",
        "cs": "Neprovádějte nastavení gridu, dokud není vyřešena chybějící částka {amount} {quote}.",
    },
    "action_run_again": {
        "en": "Run the assistant again in {hours} hours.",
        "cs": "Spusťte asistenta znovu za {hours} h.",
    },
    # Reasons written inline by the action builder rather than borrowed.
    "action_reason_rebalance_allowed": {
        "en": "Deterministic advisor allows a {mode} setup with {basket}, threshold {threshold}%, and maximum investment {investment} USDC-equivalent.",
        "cs": "Deterministický poradce povoluje nastavení {mode} s {basket}, prahem {threshold} % a maximální investicí {investment} v ekvivalentu USDC.",
    },
    "action_reason_grid_recommend_only": {
        "en": "Current market profile looks suitable for a range strategy, but bot creation is recommend-only.",
        "cs": "Současný profil trhu vypadá vhodně pro range strategii, ale bota lze jen doporučit, ne založit.",
    },
    "action_reason_trade_passed_checks": {
        "en": "The proposal passed deterministic MVP risk checks, but execution is still manual/recommend-only.",
        "cs": "Návrh prošel deterministickými rizikovými kontrolami, ale provedení zůstává ruční, jen jako doporučení.",
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


def render_message(step: Message, language: str = DEFAULT_LANGUAGE) -> str:
    """Compose one step's sentence, falling back to English then to the key.

    A key with no entry at all renders as the key itself: visible enough in a
    report to be reported as a bug, but never a crash in front of a user who
    only wanted to read their next move.
    """
    translations = MESSAGE_TEXT.get(step.key)
    if translations is None:
        return step.key
    template = translations.get(language) or translations[DEFAULT_LANGUAGE]
    try:
        return template.format(**step.params)
    except KeyError:
        # A template that outgrew its call site is a bug, but showing the
        # unfilled sentence beats showing nothing where an instruction belongs.
        return template


def render_messages(
    steps: Iterable[Message], language: str = DEFAULT_LANGUAGE
) -> tuple[str, ...]:
    return tuple(render_message(step, language) for step in steps)


def messages_to_json(steps: Iterable[Message]) -> str:
    return json.dumps(
        [{"key": step.key, "params": step.params} for step in steps],
        ensure_ascii=False,
    )


def messages_from_json(payload: str) -> tuple[Message, ...]:
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
        return tuple(Message(line) for line in text.splitlines() if line.strip())
    if not isinstance(decoded, list):
        return ()
    steps: list[Message] = []
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
        steps.append(Message(key, params))
    return tuple(steps)


# The names the manual-step call sites and the stored JSON already use. The
# shape is identical - a key and its parameters - so the storage format did not
# change when the concept was widened beyond setup steps.
ManualStep = Message
MANUAL_STEP_TEXT = MESSAGE_TEXT
render_manual_step = render_message
render_manual_steps = render_messages
manual_steps_to_json = messages_to_json
manual_steps_from_json = messages_from_json
