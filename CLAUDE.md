# Coinductor

Local Binance Spot assistant. Two packages, one direction of dependency:

- **`trading_agent/`** — headless engine and CLI. Knows nothing about the UI.
- **`coinductor/`** — PySide6/QML desktop app. Imports the engine; never the reverse.

## Commands

```bash
python -m pytest -q                                   # 777 tests, ~35s, fully offline
python -m ruff check trading_agent coinductor tests   # must be clean
python -m trading_agent run --config config.example.toml
python -m coinductor.desktop                          # desktop app (needs the desktop extra)
```

Everything runs offline by default: `app.mock_data = true` serves a fixed portfolio
from `binance_clients.MockBinanceClient`, so a full run needs no keys and no network.

## The invariant that matters

**The LLM proposes; deterministic code decides.** `AiAnalyst` only ever returns a
candidate action. `RiskEngine.evaluate()` is what governs whether anything happens,
and every execution path is gated behind it. Do not let model output reach a
submit path without passing through the risk engine.

## Where things live

| Concern | Owner |
| --- | --- |
| SQLite schema, migrations, retention | `trading_agent/storage.py` — sole owner |
| Reading that schema back for the UI | `coinductor/desktop_store.py` |
| Per-run submit authority | `trading_agent/runtime_flags.py` |
| Run orchestration | `trading_agent/runner.py` + `run_phases.py` |
| Background jobs off the GUI thread | `coinductor/workers.py` |
| Schedules, tray, headless `--run-once` | `coinductor/automation.py`, `tray.py`, `scheduled_task.py`, `desktop.py` |
| One window per data directory | `coinductor/single_instance.py` |
| How large an approved order may be | `RiskEngine.sizing_caps` + `coinductor/trade_sizing.py` (its screen) |
| How much Earn may fund it | `EarnLiquidityManager` + `coinductor/earn_funding.py` (its screen) |
| Numeric settings on a screen | `coinductor/config_fields.py` — shared read/validate/write |
| Starting values derived from the portfolio | `coinductor/suggested_limits.py` |
| New-listing watch (records and notifies; never buys) | `coinductor/listing_watcher.py` |
| Permission to submit unattended | `coinductor/standing_authorisation.py` — built, tested, **wired to nothing** |
| User-facing text the engine produces | `trading_agent/messages.py` — key + params, never a finished sentence |

## Things that will bite you

- **Never retry a POST in `binance_client`.** A failed order submission may already
  have reached the matching engine. Only GET is replayed. Rate limits (429) escalate
  to a temporary IP ban (418), which is why the retry loop backs off and 418 fails fast.
- **`RuntimeFlags` fail closed.** A missing or misspelled flag parses to "do not
  submit". Keep it that way — never add a gate that defaults to permitting.
- **Three tables are exempt from run retention**
  (`first_portfolio_tranches`, `oco_protection_orders`, `oco_status_checks`).
  They hold the intent ids that stop an executed order being sent twice. See
  `_RETENTION_EXEMPT_TABLES` in `storage.py`.
- **A schedule must never reach an *order* submit path.** An automatic run passes no
  confirmation string, and the tests assert those arguments never reach it at all rather
  than arriving false. `standing_authorisation.py` is the only thing that could change
  that; it is deliberately unconnected, and connecting it is a decision, not a refactor.
- **One exception, and only one: `earn.auto_funding_enabled`.** A run may move Earn to
  Spot unattended, because that is a transfer inside one account — no exposure changes,
  nothing can be lost to the market, and subscribing again reverses it. It is a second
  authority in `EarnLiquidityManager.redeem_authority()`, not a weakening of the first:
  MANUAL still demands `CONFIRM_EARN_REDEEM` for the exact amount, AUTOMATIC demands the
  switch plus `LIVE_ENABLED`. Do not extend this shape to orders.
- **The per-day Earn limit is enforced by subtracting the journal's total from the per-run
  cap**, not by a check at submission, so a run cannot be sized against an allowance the
  day has spent. Only submitted plans count; counting previews would let an unconfirmed
  one exhaust the day.
- **The single-instance handshake carries no payload, on purpose.** A second instance
  connects and exits, and on Windows anything written into a `QLocalSocket` is discarded
  when it closes or the process leaves, before the server ever accepts. Measured, not
  assumed. The connection itself is the whole message; a message added here will vanish.
- **Every entry in `RiskEngine.sizing_caps` is a ceiling, and the order is their minimum.**
  That is what makes the list safe to extend: nothing added there can enlarge an order.
  A limit written as a floor breaks the property, and
  `test_no_limit_can_ever_enlarge_the_proposal` is what catches it.
- **Those ceilings bound one order, not the position it builds towards.** Current holdings
  are not in the arithmetic, so repeated buys can accumulate past
  `max_position_pct_per_asset`. The UI and the config template say so; do not reword them
  into a promise the code does not keep.
- **`evaluate()` takes `portfolio_value` and `spendable_quote` keyword-only with no
  default.** They shrink the order, so a caller that forgot them would silently get the
  most permissive sizing. `None` is allowed but has to be written at the call site.
- **Anything the schedule panel derives from a `QTimer` needs `automationChanged`.** The
  next-run time is computed from `remainingTime()` when QML reads it, so a timer that
  fires without emitting leaves a correct schedule looking stopped.
- **Two panels write into one `[automation]` section**, so an omitted value means "leave it"
  rather than "turn it off". `_apply` only edits keys that already exist, so a new key needs
  `ensure_section` or it is accepted and silently discarded.
- **`config.toml` and `state/` are gitignored.** `config.example.toml` is the tracked
  template and is what the tests load.
- **Version lives only in `trading_agent/__init__.py`.** pyproject reads it dynamically,
  `coinductor` re-exports it, and a test holds `packaging/coinductor.iss` to it.

## Testing notes

- Qt tests use `pytest.importorskip("PySide6")`, so the suite passes without the
  desktop extra installed. CI runs Windows with it and Linux without.
- `tests/test_runner_end_to_end.py` characterises a whole run; treat a change there
  as a behaviour change, not a test fix.
- `tests/test_desktop_store_reads_the_real_schema.py` points the UI reader at a
  journal from a genuine run. It is the only test that catches a renamed column —
  the other DesktopStore tests hand-build their own schema.

## Measured, so you don't have to

LLM prompts per run: ~900 tokens for the proposal, ~2500 for the commentary.
Already bounded by `ai_memory.max_closed_cycles` (10) and the 5-item caps in
`_string_list`. There is no easy win left there; don't trim payloads for cost.
