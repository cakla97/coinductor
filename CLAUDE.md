# Coinductor

Local Binance Spot assistant. Two packages, one direction of dependency:

- **`trading_agent/`** — headless engine and CLI. Knows nothing about the UI.
- **`coinductor/`** — PySide6/QML desktop app. Imports the engine; never the reverse.

## Commands

```bash
python -m pytest -q                                   # 467 tests, ~10s, fully offline
python -m ruff check trading_agent coinductor tests   # must be clean
python -m trading_agent run --config config.example.toml
coinductor                                            # desktop app (needs the desktop extra)
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
