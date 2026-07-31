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
    # Completion toasts. Keyed rather than passed as sentences so they are not
    # the last English text left on a translated screen.
    # --- new listings ---
    "listing_new_title": {
        "en": "New on Binance",
        "cs": "Nové na Binance",
    },
    "listing_new_body": {
        "en": "Newly listed: {symbols}. Coinductor has not bought anything - open New listings to look.",
        "cs": "Nově zalistováno: {symbols}. Coinductor nic nekoupil - otevřete Nové listingy a podívejte se.",
    },
    "listing_scan_ok": {
        "en": "Watching {count} pairs.",
        "cs": "Sledováno {count} párů.",
    },
    "listing_scan_failed": {
        "en": "Could not reach Binance: {reason}. The next check will try again.",
        "cs": "Nepodařilo se spojit s Binance: {reason}. Další kontrola to zkusí znovu.",
    },
    "listing_watch_on": {
        "en": "Watching for new listings every {minutes} min while Coinductor is open. It only ever notifies.",
        "cs": "Nové listingy se sledují každých {minutes} min, dokud je Coinductor otevřený. Vždy jen upozorní.",
    },
    "listing_watch_off": {
        "en": "New listing watch is off.",
        "cs": "Sledování nových listingů je vypnuté.",
    },
    "allowed_symbol_added": {
        "en": "{symbol} can now be analysed. Nothing was bought - run an analysis, then confirm as usual if you want to act.",
        "cs": "{symbol} se teď smí analyzovat. Nic se nekoupilo - spusťte analýzu a pokud budete chtít jednat, potvrďte ji jako obvykle.",
    },
    "allowed_symbol_already_there": {
        "en": "{symbol} is already on the list.",
        "cs": "{symbol} už na seznamu je.",
    },
    "allowed_symbol_invalid": {
        "en": "{symbol} does not look like a Binance pair.",
        "cs": "{symbol} nevypadá jako pár na Binance.",
    },
    "allowed_symbol_list_full": {
        "en": "The allowed list is full. Remove a pair you no longer follow first.",
        "cs": "Seznam povolených párů je plný. Nejdřív odeberte pár, který už nesledujete.",
    },
    "allowed_symbol_no_config": {
        "en": "No configuration file was found, so nothing was changed.",
        "cs": "Konfigurační soubor se nenašel, takže se nic nezměnilo.",
    },
    "allowed_symbol_not_written": {
        "en": "The allowed symbol list could not be found in the configuration.",
        "cs": "Seznam povolených symbolů se v konfiguraci nenašel.",
    },
    # --- scheduled task and catch-up ---
    "catch_up_runs": {
        "en": "{count} analysis(es) ran while Coinductor was closed. The latest ended with {decision} - see Run History.",
        "cs": "Zatímco byl Coinductor zavřený, proběhly analýzy: {count}. Poslední skončila s výsledkem {decision} - viz Historie běhů.",
    },
    "task_registered": {
        "en": "Windows will run one analysis a day at {time}, whether or not Coinductor is open. Your PC has to be on.",
        "cs": "Windows spustí jednu analýzu denně v {time}, ať je Coinductor otevřený nebo ne. Počítač musí být zapnutý.",
    },
    "task_removed": {
        "en": "The scheduled task was removed. Nothing runs while Coinductor is closed.",
        "cs": "Naplánovaná úloha byla odstraněna. Se zavřeným Coinductorem už neběží nic.",
    },
    "task_not_registered": {
        "en": "There was no scheduled task to remove.",
        "cs": "Žádná naplánovaná úloha k odstranění nebyla.",
    },
    "task_bad_time": {
        "en": "The time has to look like 07:30. Nothing was scheduled.",
        "cs": "Čas musí vypadat jako 07:30. Nic se nenaplánovalo.",
    },
    "task_failed": {
        "en": "Windows refused to create the task. Nothing was scheduled.",
        "cs": "Windows odmítly úlohu vytvořit. Nic se nenaplánovalo.",
    },
    "task_not_windows": {
        "en": "Scheduled tasks are a Windows feature. The in-app schedule works everywhere.",
        "cs": "Naplánované úlohy jsou funkce Windows. Rozvrh uvnitř aplikace funguje všude.",
    },
    # --- automation ---
    "tray_open": {"en": "Open Coinductor", "cs": "Otevřít Coinductor"},
    "tray_run_now": {"en": "Run analysis now", "cs": "Spustit analýzu teď"},
    "tray_quit": {"en": "Quit", "cs": "Ukončit"},
    "toast_automatic_analysis_done": {
        "en": "Scheduled analysis complete. Review the Action Plan.",
        "cs": "Naplánovaná analýza dokončena. Zkontrolujte Plán akcí.",
    },
    "tray_run_finished": {
        "en": "Coinductor: {decision}",
        "cs": "Coinductor: {decision}",
    },
    "tray_no_action": {
        "en": "Nothing to do right now.",
        "cs": "Teď není co dělat.",
    },
    "automation_saved_on": {
        "en": "Scheduled analysis is on, every {hours} h while Coinductor is open.",
        "cs": "Naplánovaná analýza je zapnutá, každých {hours} h, dokud je Coinductor spuštěný.",
    },
    "automation_saved_off": {
        "en": "Scheduled analysis is off. Run analysis works as before.",
        "cs": "Naplánovaná analýza je vypnutá. Spustit analýzu funguje jako dřív.",
    },
    "automation_unchanged": {
        "en": "Nothing changed - that is already the schedule in force.",
        "cs": "Nic se nezměnilo - tenhle rozvrh už platí.",
    },
    "toast_analysis_done": {
        "en": "Analysis complete. Review the Action Plan.",
        "cs": "Analýza dokončena. Zkontrolujte Action Plan.",
    },
    "toast_readonly_analysis_done": {
        "en": "Read-only analysis complete. Review the Action Plan.",
        "cs": "Read-only analýza dokončena. Zkontrolujte Action Plan.",
    },
    "toast_trade_preview_ready": {
        "en": "Trade preview ready. Review the Action Plan.",
        "cs": "Náhled obchodu je připraven. Zkontrolujte Action Plan.",
    },
    "toast_bot_plan_ready": {
        "en": "Bot plan ready. Review the Action Plan.",
        "cs": "Plán bota je připraven. Zkontrolujte Action Plan.",
    },
    "toast_guarded_trade_done": {
        "en": "Guarded trade submit run complete. Review the Action Plan.",
        "cs": "Zabezpečené odeslání obchodu dokončeno. Zkontrolujte Action Plan.",
    },
    "toast_monitoring_refreshed": {
        "en": "Active strategy monitoring refreshed.",
        "cs": "Sledování aktivních strategií bylo obnoveno.",
    },
    "toast_guarded_oco_done": {
        "en": "Guarded OCO protection run complete. Review the Action Plan.",
        "cs": "Zabezpečená OCO ochrana dokončena. Zkontrolujte Action Plan.",
    },
    "toast_guarded_earn_done": {
        "en": "Guarded Earn redeem run complete. Review the Action Plan.",
        "cs": "Zabezpečený výběr z Earn dokončen. Zkontrolujte Action Plan.",
    },
    "active_strategies_none": {
        "en": "No registered active Grid or Rebalancing bots were evaluated in the latest run.",
        "cs": "V posledním běhu nebyli vyhodnoceni žádní registrovaní aktivní Grid ani Rebalancing boti.",
    },
    "active_strategies_counts": {
        "en": "{total} active strategy(s): {healthy} healthy, {review} to review, {action} requiring action.",
        "cs": "Aktivních strategií: {total} - {healthy} v pořádku, {review} ke kontrole, {action} vyžaduje zásah.",
    },
    "active_strategies_pending": {
        "en": "{pending} registered strategy(s) awaiting a fresh evaluation.",
        "cs": "Registrovaných strategií čekajících na nové vyhodnocení: {pending}.",
    },
    "decision_grid_recommended": {
        "en": "A Spot Grid was recommended",
        "cs": "Doporučen Spot Grid",
    },
    "decision_rebalancing_recommended": {
        "en": "A Rebalancing Bot was recommended",
        "cs": "Doporučen Rebalancing Bot",
    },
    "decision_spot_trade": {
        "en": "A spot trade was proposed",
        "cs": "Navržen spotový obchod",
    },
    "decision_hold": {
        "en": "No action",
        "cs": "Žádná akce",
    },
    "decision_no_action": {
        "en": "No action",
        "cs": "Žádná akce",
    },
    "next_review_status_manual_step": {
        "en": "Manual step before rerun",
        "cs": "Ruční krok před dalším během",
    },
    "next_review_headline_manual_step": {
        "en": "A fresh run can update market data, but it cannot remove the listed funding or configuration blocker.",
        "cs": "Nový běh aktualizuje tržní data, ale uvedený blokátor financování ani konfigurace neodstraní.",
    },
    "next_review_timing_manual_step": {
        "en": "After the manual step",
        "cs": "Po ručním kroku",
    },
    "next_review_status_review_now": {
        "en": "Review now",
        "cs": "Zkontrolovat nyní",
    },
    "next_review_headline_review_now": {
        "en": "The latest run produced an action that should be reviewed before waiting for another scheduled check.",
        "cs": "Poslední běh vytvořil akci, kterou je vhodné zkontrolovat dřív, než přijde další naplánovaná kontrola.",
    },
    "next_review_timing_review_now": {
        "en": "Now",
        "cs": "Nyní",
    },
    "next_review_status_due_now": {
        "en": "Review due now",
        "cs": "Kontrola je na řadě",
    },
    "next_review_headline_due_now": {
        "en": "The recommended review interval has elapsed. Run a fresh analysis when convenient.",
        "cs": "Doporučený interval kontroly uplynul. Spusťte novou analýzu, až se vám to bude hodit.",
    },
    "next_review_timing_due_now": {
        "en": "Now",
        "cs": "Nyní",
    },
    "next_review_status_scheduled": {
        "en": "Check again in {hours} hours",
        "cs": "Další kontrola za {hours} h",
    },
    "next_review_headline_scheduled": {
        "en": "No immediate action is required. Wait for the suggested interval unless an earlier trigger occurs.",
        "cs": "Není potřeba nic dělat hned. Vyčkejte doporučený interval, pokud nenastane dřívější podnět.",
    },
    "next_review_timing_scheduled": {
        "en": "In {hours} hours",
        "cs": "Za {hours} h",
    },
    "cadence_daily": {"en": "Daily", "cs": "Denně"},
    "cadence_twice_weekly": {"en": "Twice weekly", "cs": "Dvakrát týdně"},
    "cadence_weekly": {"en": "Weekly", "cs": "Týdně"},
    "cadence_manual": {"en": "Manual / irregular", "cs": "Ručně / nepravidelně"},
    "urgency_normal": {"en": "Normal", "cs": "Běžná"},
    "urgency_action_required": {"en": "Action required", "cs": "Vyžaduje zásah"},
    "urgency_elevated": {"en": "Elevated", "cs": "Zvýšená"},
    "submit_blocked_not_buy": {
        "en": "Live submit appears only for BUY previews that pass the deterministic checks.",
        "cs": "Zabezpečené odeslání se objeví jen u nákupních náhledů, které projdou deterministickými kontrolami.",
    },
    "submit_blocked_stage": {
        "en": "Live submit is locked until you raise the safety stage to LIVE_ENABLED.",
        "cs": "Zabezpečené odeslání je zamčené, dokud nezvýšíte bezpečnostní stupeň na LIVE_ENABLED.",
    },
    "submit_blocked_no_key": {
        "en": "The live trading key is not configured, or has not passed the setup checks.",
        "cs": "Živý obchodní klíč není nastavený, nebo neprošel kontrolami nastavení.",
    },
    "submit_blocked_unverified": {
        "en": "Verify the live key's permissions in Live Actions for this app session.",
        "cs": "Ověřte oprávnění živého klíče v Živých akcích pro tuto session aplikace.",
    },
    "submit_confirm_label": {
        "en": "Confirm live {action}",
        "cs": "Potvrdit živý {action}",
    },
    "submit_locked_label": {
        "en": "Live submit locked",
        "cs": "Odeslání zamčeno",
    },
    "manual_steps_copied": {
        "en": "{count} setup steps copied. Paste them next to Binance and work down the list.",
        "cs": "Zkopírováno {count} kroků nastavení. Vložte si je vedle Binance a projděte je shora dolů.",
    },
    "value_copied": {
        "en": "Copied: {value}",
        "cs": "Zkopírováno: {value}",
    },
    "clipboard_unavailable": {
        "en": "The clipboard is not available.",
        "cs": "Schránka není k dispozici.",
    },
    "run_report_missing": {
        "en": "That run's report file is no longer on disk.",
        "cs": "Soubor s reportem tohoto běhu už na disku není.",
    },
    "ai_summary_not_requested": {
        "en": (
            "This analysis ran without AI commentary, so there is nothing here. Nothing is missing "
            "from the result: every decision above comes from the deterministic analysis, which "
            "never uses a model. Tick \"Generate AI summary\" when starting a run to get one."
        ),
        "cs": (
            "Tato analýza běžela bez hodnocení od AI, takže tu nic není. Ve výsledku nic nechybí - "
            "všechna rozhodnutí výše pocházejí z deterministické analýzy, která model nikdy "
            "nepoužívá. Hodnocení dostanete, když při spuštění zaškrtnete \"Vygenerovat shrnutí od AI\"."
        ),
    },
    # --- built-in offline help ---
    # Answers the assistant gives when no model is connected. The language
    # follows the question, not the app: someone asking in Czech gets Czech.
    "help_no_question": {
        "en": "Ask about the latest run, portfolio roles, risk controls, Grid, Rebalancing, or where your data is kept.",
        "cs": "Zeptejte se na poslední běh, role v portfoliu, bezpečnostní pojistky, Grid, Rebalancing nebo kde jsou uložená data.",
    },
    "help_not_understood": {
        "en": "I did not understand that one. Without a connected model I answer from a short list of topics: the latest run, your portfolio, risk controls, Grid, Rebalancing, and where your data is kept. Connect an AI model in Settings for anything broader.",
        "cs": "Téhle otázce jsem nerozuměl. Bez připojeného modelu odpovídám z krátkého seznamu témat: poslední běh, portfolio, bezpečnostní pojistky, Grid, Rebalancing a kde jsou uložená data. Na cokoli dalšího připojte AI model v Nastavení.",
    },
    "help_no_run": {
        "en": "No completed run on real data yet.",
        "cs": "Zatím neproběhl žádný běh nad skutečnými daty.",
    },
    "help_no_follow_up": {
        "en": "no follow-up action was recorded",
        "cs": "žádná navazující akce nebyla zaznamenána",
    },
    "help_last_run": {
        "en": "Run {run_id} ended with {decision}. {summary} Highest-priority follow-up: {action}",
        "cs": "Běh {run_id} skončil s výsledkem {decision}. {summary} Nejdůležitější navazující krok: {action}",
    },
    "help_risk": {
        "en": "Execution stays deterministic: the AI cannot get past the symbol allowlist, protected assets, position limits, daily and weekly loss limits, cooldowns, liquidity checks, or the confirmation you type yourself.",
        "cs": "Provádění zůstává deterministické: AI se nedostane přes seznam povolených symbolů, chráněná aktiva, limity pozic, denní a týdenní ztrátové limity, cooldowny, kontrolu likvidity ani přes potvrzení, které vypisujete vy.",
    },
    "help_no_grid": {
        "en": "No Grid recommendation is stored for the latest run on real data.",
        "cs": "Pro poslední běh nad skutečnými daty není uložené žádné doporučení pro Grid.",
    },
    "help_no_rebalancing": {
        "en": "No Rebalancing recommendation is stored for the latest run on real data.",
        "cs": "Pro poslední běh nad skutečnými daty není uložené žádné doporučení pro Rebalancing.",
    },
    "help_no_portfolio": {
        "en": "Portfolio data is not loaded yet.",
        "cs": "Data portfolia zatím nejsou načtená.",
    },
    "help_portfolio": {
        "en": "Largest holdings in the latest run: {assets}. Open Portfolio for roles and liquidity.",
        "cs": "Největší pozice v posledním běhu: {assets}. Role a likviditu najdete v Portfoliu.",
    },
    "help_data": {
        "en": "Reports are in outputs/reports and the run history is in work/trading_agent.sqlite3. Open detailed report on Overview opens the latest one.",
        "cs": "Reporty jsou v outputs/reports a historie běhů v work/trading_agent.sqlite3. Tlačítko Otevřít podrobný report na Přehledu otevře ten poslední.",
    },
    "reset_group_ai_provider": {
        "en": "AI model connection",
        "cs": "Připojení AI modelu",
    },
    "reset_group_ai_provider_detail": {
        "en": "Disconnects the local or cloud model: its endpoint, model names and API key. Binance access, your portfolio and every run are untouched, and the analysis keeps working - it never asks a model.",
        "cs": "Odpojí místní nebo cloudový model: endpoint, názvy modelů a API klíč. Přístup k Binance, portfolio ani žádný běh se nemění a analýza funguje dál - modelu se nikdy neptá.",
    },
    "no_ai_provider_toast": {
        "en": "No AI provider is set up, so there is nothing to ask. Settings has the setup - it is optional.",
        "cs": "Není nastavený žádný AI model, takže není koho se zeptat. Nastavení najdete v Nastavení - je to volitelné.",
    },
    # --- per-order size cap ---
    "order_caps_saved": {
        "en": "Order size caps saved.",
        "cs": "Stropy na velikost příkazu uloženy.",
    },
    "order_caps_saved_above_suggestion": {
        "en": "Saved. The live cap is above the {suggested} suggested for a portfolio this size - deliberate is fine, accidental is not.",
        "cs": "Uloženo. Živý strop je nad hodnotou {suggested} doporučenou pro portfolio této velikosti - pokud je to záměr, v pořádku.",
    },
    "order_caps_unchanged": {
        "en": "Nothing changed - those are the caps already in force.",
        "cs": "Nic se nezměnilo - tyhle stropy už platí.",
    },
    "order_caps_invalid": {
        "en": "A cap must be a number greater than zero. Nothing was saved.",
        "cs": "Strop musí být číslo větší než nula. Nic se neuložilo.",
    },
    # --- first portfolio tranches ---
    "tranche_busy": {
        "en": "Wait for the current analysis to finish first.",
        "cs": "Nejdřív počkejte, až doběhne probíhající analýza.",
    },
    "tranche_bad_mode": {
        "en": "Mode must be Testnet or Mainnet.",
        "cs": "Režim musí být Testnet nebo Mainnet.",
    },
    "tranche_no_budget": {
        "en": "Enter the actual budget for this basket before continuing.",
        "cs": "Než budete pokračovat, zadejte skutečný rozpočet pro tenhle koš.",
    },
    "tranche_bad_count": {
        "en": "The number of tranches must be at least 1.",
        "cs": "Počet tranší musí být aspoň 1.",
    },
    "tranche_stage_locked": {
        "en": "Mainnet submit is locked until the Safety stage is raised to LIVE_ENABLED.",
        "cs": "Odeslání na Mainnet je zamčené, dokud nezvýšíte bezpečnostní stupeň na LIVE_ENABLED.",
    },
    "tranche_failed": {
        "en": "The tranche could not be run: {reason}",
        "cs": "Tranši se nepodařilo spustit: {reason}",
    },
    "tranche_on_testnet": {"en": "on Testnet", "cs": "na Testnetu"},
    "tranche_on_mainnet": {"en": "on Mainnet", "cs": "na Mainnetu"},
    "tranche_subject": {
        "en": "Tranche {index}/{total} for {asset} {where}",
        "cs": "Tranše {index}/{total} pro {asset} {where}",
    },
    "tranche_validated": {
        "en": "{subject} passed every check. Nothing was sent - type the confirmation phrase and press Submit to place it.",
        "cs": "{subject} prošla všemi kontrolami. Nic se neodeslalo - pro zadání vypište potvrzovací frázi a stiskněte Odeslat.",
    },
    "tranche_submitted": {
        "en": "{subject} was submitted for {amount}.",
        "cs": "{subject} byla odeslána za {amount}.",
    },
    "tranche_submitted_capped": {
        "en": "{subject} was submitted for {amount}, not the planned {planned} - a per-order cap applied. Raise live_confirm.max_quote_amount_usdt if that was not what you wanted.",
        "cs": "{subject} byla odeslána za {amount}, ne za plánovaných {planned} - zasáhl strop na jeden příkaz. Pokud jste to tak nechtěl, zvyšte live_confirm.max_quote_amount_usdt.",
    },
    "tranche_already_done": {
        "en": "{subject} is already done. Nothing was sent twice.",
        "cs": "{subject} už proběhla. Nic se neodeslalo podruhé.",
    },
    "tranche_not_sent": {
        "en": "{subject} was not sent: {reason}",
        "cs": "{subject} se neodeslala: {reason}",
    },
    # --- first portfolio plan ---
    # The planner's prose comes from the locale profile; these are the labels
    # and short values that used to be English literals beside it.
    "first_plan_role_core": {"en": "Core", "cs": "Základ"},
    "first_plan_role_utility": {"en": "Utility", "cs": "Užitkové"},
    "first_plan_role_growth": {"en": "Growth", "cs": "Růstové"},
    "first_plan_share_of_converted": {
        "en": "{pct}% of converted {funding}",
        "cs": "{pct} % z převedených {funding}",
    },
    "first_plan_funding_deposit": {"en": "Deposit", "cs": "Vklad"},
    "first_plan_funding_reserve": {"en": "Reserve", "cs": "Rezerva"},
    "first_plan_funding_deployment": {"en": "Initial deployment", "cs": "První nasazení"},
    "first_plan_step_fund": {"en": "Fund Binance", "cs": "Poslat peníze na Binance"},
    "first_plan_step_buy": {"en": "Buy basket", "cs": "Nakoupit koš"},
    "first_plan_step_earn": {"en": "Enable Earn", "cs": "Zapnout Earn"},
    "first_plan_step_rhythm": {"en": "Review rhythm", "cs": "Rytmus kontrol"},
    "first_plan_value_manual": {"en": "Manual", "cs": "Ručně"},
    "first_plan_value_optional": {"en": "Optional", "cs": "Volitelné"},
    "first_plan_value_later": {"en": "Later", "cs": "Později"},
    "first_plan_value_manual_first": {"en": "Manual first", "cs": "Nejdřív ručně"},
    "first_plan_step_earn_detail": {
        "en": "Flexible Earn is fine for idle reserve, but keep enough liquid for planned actions.",
        "cs": "Flexible Earn je pro nečinnou rezervu v pořádku, ale nechte si dost likvidních prostředků na plánované akce.",
    },
    "first_plan_step_rhythm_detail": {
        "en": "Run Coinductor on this rhythm before enabling more active automation.",
        "cs": "Než zapnete aktivnější automatizaci, spouštějte Coinductor v tomto rytmu.",
    },
    "first_plan_note_rebalancing": {"en": "Rebalancing", "cs": "Rebalancování"},
    "first_plan_note_grid": {"en": "Grid", "cs": "Grid"},
    "first_plan_note_execution": {"en": "Execution", "cs": "Provedení"},
    "first_plan_note_rebalancing_ready": {
        "en": "Rebalancing bot can be considered after at least 200 USDC is available for its basket.",
        "cs": "Rebalancing bota zvažte, až bude pro jeho koš k dispozici alespoň 200 USDC.",
    },
    "first_plan_note_rebalancing_below_minimum": {
        "en": "Rebalancing bot is below the usual 200 USDC minimum; start with manual basket review.",
        "cs": "Na Rebalancing bota je to pod obvyklým minimem 200 USDC. Začněte ruční kontrolou koše.",
    },
    "first_plan_note_grid_disabled": {
        "en": "Grid bot stays disabled for the first portfolio plan.",
        "cs": "Grid bot zůstává pro plán prvního portfolia vypnutý.",
    },
    "first_plan_note_grid_later": {
        "en": "Grid bot can be reviewed later, after the first portfolio has a stable tracked baseline.",
        "cs": "Grid bota můžete zvážit později, až bude mít první portfolio stabilní sledovaný základ.",
    },
    "ai_summary_other_language": {
        "en": "— These are the model's own words, written during that run in the language set at the time. Run the analysis again to get them in this one.",
        "cs": "— Tohle jsou vlastní slova modelu, napsaná při onom běhu v tehdy nastaveném jazyce. Spusťte analýzu znovu, ať je dostanete v tomto.",
    },
    "ai_summary_empty": {
        "en": "The model was asked but returned nothing usable. The deterministic decisions above are unaffected.",
        "cs": "Model byl dotázán, ale nevrátil nic použitelného. Deterministických rozhodnutí výše se to nijak netýká.",
    },
    "ai_summary_no_provider": {
        "en": (
            "No AI provider is configured, so there is no commentary to show. This is optional - "
            "every decision above comes from the deterministic analysis, which never uses a model. "
            "Settings has the setup if you want it."
        ),
        "cs": (
            "Není nastavený žádný AI provider, takže není co zobrazit. Je to volitelné - všechna "
            "rozhodnutí výše pocházejí z deterministické analýzy, která model nikdy nepoužívá. "
            "Nastavení najdete v Nastavení."
        ),
    },
    "connection_confirmed_by_run": {
        "en": "Confirmed by run {run_id}: the analysis read your Binance account successfully.",
        "cs": "Potvrzeno během běhu {run_id}: analýza úspěšně načetla váš účet Binance.",
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
    "ai_check_vision_model": {"en": "Vision model", "cs": "Vision model (obrazový)"},
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
    "readiness_step_binance": {"en": "Binance read-only", "cs": "Binance jen pro čtení"},
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
    "exch_readonly_api": {"en": "Read-only API", "cs": "API jen pro čtení"},
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
    # Detection only fills the dropdowns - it stores nothing. Without saying so,
    # models appearing looked like the provider was configured, and the setting
    # was silently absent until an analysis reported having no AI at all.
    "aidisc_ok": {
        "en": (
            "{count} model(s) reported by {url}. Nothing is stored yet: pick the models you want, "
            "then press Save local AI."
        ),
        "cs": (
            "{url} nahlásilo {count} model(ů). Zatím se nic neuložilo: vyberte modely, které chcete, "
            "a stiskněte Save local AI."
        ),
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
    "setup_check_binance_readonly": {"en": "Binance read-only", "cs": "Binance jen pro čtení"},
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

# Parameter labels composed in DesktopStore, which has no language of its
# own. Stored English is the identifier; this is the display mapping, so a
# label with no entry (or one added later) simply passes through.
PARAMETER_LABELS: dict[str, str] = {
    'Age': 'Stáří',
    'Amount': 'Množství',
    'Asset': 'Aktivum',
    'Assets': 'Aktiva',
    'BUY order ID': 'ID nákupní objednávky',
    'Basket': 'Košík',
    'Blockers': 'Blokátory',
    'Current / exit price': 'Aktuální / výstupní cena',
    'Current estimate': 'Aktuální odhad',
    'Current price': 'Aktuální cena',
    'Distance to range': 'Vzdálenost od rozsahu',
    'Entry': 'Vstup',
    'Entry price': 'Vstupní cena',
    'Grid setup': 'Nastavení gridu',
    'Grids': 'Počet gridů',
    'Investment': 'Investice',
    'Last synchronized': 'Naposledy synchronizováno',
    'Maximum drift': 'Maximální odchylka',
    'Mode': 'Režim',
    'OCO exchange status': 'Stav OCO na burze',
    'OCO list ID': 'ID OCO seznamu',
    'PnL (fees excluded)': 'Zisk/ztráta (bez poplatků)',
    'Product': 'Produkt',
    'Quantity': 'Množství',
    'Range': 'Rozsah',
    'Rebalance threshold': 'Práh rebalancování',
    'Redeem type': 'Typ výběru',
    'SL estimate': 'Odhad při stop lossu',
    'Spacing': 'Rozestup',
    'Stop loss': 'Stop loss',
    'Symbol': 'Symbol',
    'TP / SL': 'TP / SL',
    'TP estimate': 'Odhad při take profitu',
    'Take profit': 'Take profit',
    'Target basket': 'Cílový košík',
    'Trigger': 'Spouštěč',
}
