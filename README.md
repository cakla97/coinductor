# Binance Periodic Trading Agent MVP

Experimental local portfolio assistant for Binance Spot, Simple Earn Flexible, rebalancing,
and Spot Grid bot recommendations.

This project is intentionally conservative:

- periodic runs instead of a 24/7 bot
- `DRY_RUN` by default
- no futures, no margin, no leverage
- AI is an analyst only; deterministic code enforces risk and liquidity rules
- Flexible Earn redeem is modeled as a liquidity-management step
- Locked Earn is read-only
- Spot Grid bot creation is recommend-only unless an official execution path is added later

## Prerequisites

- Python 3.11 or newer
- Optional: local OpenAI-compatible LLM endpoint, for example Ollama/Open WebUI/LM Studio
- Binance API keys only when moving beyond mock/dry-run

## Quick Start

```powershell
Copy-Item .env.example .env
python -m trading_agent --config config.example.toml
```

Preferred CLI form:

```powershell
python -m trading_agent run --config config.example.toml
python -m trading_agent run --config config.example.toml --real-data --ai-commentary
python -m trading_agent doctor --config config.example.toml --real-data --ai-commentary
python -m trading_agent readiness --config config.example.toml
python -m trading_agent last-report --config config.example.toml
python -m trading_agent research-request --config config.example.toml --real-data
python -m trading_agent testnet-account --config config.example.toml
python -m trading_agent testnet-symbol --config config.example.toml --symbol BTCUSDT --quote-amount 10
python -m trading_agent testnet-market-buy --config config.example.toml --symbol BTCUSDT --quote-amount 10
python -m trading_agent testnet-market-sell --config config.example.toml --symbol BTCUSDT --from-last-buy
python -m trading_agent testnet-order-status --config config.example.toml --symbol BTCUSDT --order-id 123456
python -m trading_agent run --config config.example.toml --real-data --testnet-execution
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview
```

The first run uses mock market/account data and writes:

- SQLite journal to `work/trading_agent.sqlite3`
- Markdown report to `outputs/reports/`

Each report includes:

- portfolio summary
- portfolio valuation in USDT
- rebalance gap against configured target allocation
- rebalancing preview steps with protected-asset and trading-universe guards
- Spot vs Flexible vs Locked balance view
- manual execution checklist
- paper execution simulation
- daily paper order idempotency
- Spot Testnet position summary
- market snapshot
- AI trade proposal
- risk decision
- Flexible Earn liquidity recommendation
- Spot Grid bot recommendation and manual setup steps
- recommendation for when to run the assistant again

You can also run the helper script:

```powershell
.\scripts\run.ps1
```

If Windows blocks local PowerShell scripts, run:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

To use real Binance read-only data, create `.env` from `.env.example`, add a
read-only Binance API key, then run:

```powershell
python -m trading_agent --config config.example.toml --real-data
```

The application checks Binance API permissions before reading account data and
stops if trading, withdrawal, transfer, margin, or futures permissions are enabled.

To enable local LLM commentary, expose an OpenAI-compatible endpoint and set:

```env
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen3:14b
```

Then set `commentary_enabled = true` under `[ai]` in your local config. AI commentary
is explanatory only; deterministic risk, liquidity, grid, and capital sourcing rules
remain authoritative.

For a one-off run without editing config:

```powershell
$env:LLM_BASE_URL="http://127.0.0.1:11434/v1"
python -m trading_agent --config config.example.toml --real-data --ai-commentary
```

## Research Layer

Optional research notes can be stored in `research/notes` as `.md`, `.txt`, or `.json`.
This is the preferred integration point for outputs from Binance AI Agent Skills.

Example workflow:

1. Run the assistant. If research is missing or stale, it creates a prompt in `research/requests`.
2. Use Binance Skills in your agent/runtime to run that request.
3. Save the result into `research/notes/YYYY-MM-DD_topic.md`.
4. Run the assistant again with `--ai-commentary`.

The assistant includes recent research notes in the report and passes them to the local LLM
as context. Research notes never override deterministic risk, whitelist, liquidity, or
capital sourcing rules.

## Retention

Incremental artifacts are capped by configuration:

- `[reports].keep_last` keeps the latest Markdown reports.
- `[retention].keep_research_requests` keeps the latest generated research request prompts.
- `[retention].keep_database_runs` keeps the latest SQLite run records and deletes older
  associated snapshots, recommendations, paper orders, and testnet orders.

Research notes are not auto-deleted because they are manually curated inputs.

## Active Strategy Tracking

If you manually create a Binance Spot Grid bot, copy the example state file:

```powershell
Copy-Item state/active_strategies.example.toml state/active_strategies.toml
```

Then edit `state/active_strategies.toml` with the real grid range, symbol, and
investment. The assistant will track whether current price is inside the configured
range and add review actions when price approaches or leaves the range.

## Binance Spot Testnet

Spot Testnet support is separate from mainnet read-only portfolio analysis.
Create testnet API keys at `https://testnet.binance.vision`, then add them to `.env`:

```env
BINANCE_TESTNET_API_KEY=...
BINANCE_TESTNET_API_SECRET=...
```

Check access:

```powershell
python -m trading_agent testnet-account --config config.example.toml
```

Inspect symbol filters before placing anything:

```powershell
python -m trading_agent testnet-symbol --config config.example.toml --symbol BTCUSDT --quote-amount 10
```

Preview a testnet market buy without submitting it:

```powershell
python -m trading_agent testnet-market-buy --config config.example.toml --symbol BTCUSDT --quote-amount 10
```

Submit only when you intentionally add the exact confirmation string:

```powershell
python -m trading_agent testnet-market-buy --config config.example.toml --symbol BTCUSDT --quote-amount 10 --confirm CONFIRM_TESTNET_ORDER
```

Preview closing the latest locally tracked filled testnet BUY:

```powershell
python -m trading_agent testnet-market-sell --config config.example.toml --symbol BTCUSDT --from-last-buy
```

Submit the testnet exit only with explicit confirmation:

```powershell
python -m trading_agent testnet-market-sell --config config.example.toml --symbol BTCUSDT --from-last-buy --confirm CONFIRM_TESTNET_ORDER
```

Query an existing Spot Testnet order:

```powershell
python -m trading_agent testnet-order-status --config config.example.toml --symbol BTCUSDT --order-id 123456
```

To connect Spot Testnet execution to the normal assistant run, first run a preview:

```powershell
python -m trading_agent run --config config.example.toml --real-data --testnet-execution
```

This writes a Spot Testnet Execution section to the report, but does not submit unless
the exact confirmation string is included:

```powershell
python -m trading_agent run --config config.example.toml --real-data --testnet-execution --confirm-testnet-order CONFIRM_TESTNET_ORDER
```

The assistant still follows the deterministic risk engine first. It submits only approved
spot `BUY` proposals, caps quote size with `[testnet_execution].max_quote_amount_usdt`,
validates Binance `exchangeInfo` symbol filters, queries order status after submit,
and skips duplicate intents inside the configured idempotency window.

Binance Spot Testnet uses virtual funds and supports `/api` endpoints only, so
Simple Earn `/sapi` operations and read-only permission checks are still mainnet-only.
Reports include a Spot Testnet Positions section built from local SQLite BUY/SELL cycles.

## VS Code

Open the project folder directly:

```powershell
code "D:\CodexWork\binance-trading-agent"
```

The repository includes a minimal `.vscode/launch.json` debug profile named
`Trading Agent: DRY_RUN`.

## Modes

- `DRY_RUN`: simulates decisions and orders
- `TESTNET`: reserved for Binance Spot Testnet execution
- `LIVE_CONFIRM`: reserved for future manual-confirm mainnet mode
- `LIVE_AUTO`: intentionally outside this MVP

## Strategy Decisions

The assistant can currently produce these decision types:

- `HOLD`
- `SPOT_TRADE_RECOMMENDATION`
- `REBALANCE_RECOMMENDATION`
- `GRID_BOT_RECOMMENDATION`

Grid bot recommendations are designed for manual setup in Binance Trade-X / Trading Bots.
The assistant generates parameters and checklist steps, but does not create the bot directly.

## Portfolio vs Trading Universe

Portfolio tracking is intentionally broader than trading permissions:

- `[portfolio].tracked_assets` lists assets the assistant should price and include in portfolio analysis.
- `[strategy].allowed_symbols` lists pairs that can be considered for spot trade recommendations.
- `[grid_bot].allowed_symbols` lists pairs that can be considered for Spot Grid recommendations.
- `[capital_sourcing].allowed_source_assets` lists assets that can be recommended as manual sources of USDT.
- `[capital_sourcing].protected_assets` lists assets that should not be recommended as capital sources.
- `[portfolio.asset_roles]` classifies assets as `CORE`, `PROTECTED`, `CAPITAL_SOURCE`,
  `SPECULATIVE_SOURCE`, `STABLE`, or another explicit role used for audit/reporting.

Assets that cannot be priced are shown as unpriced instead of silently disappearing from totals.
Binance internal voucher-like assets with configured prefixes, such as `LD`, are reported separately
and excluded from valuation to avoid double counting.

## Rebalancing Preview

The assistant translates target allocation gaps into preview-only rebalance steps. It does not
execute these steps. The planner:

- caps each suggested step with `[rebalancing].max_trade_value_usdt_per_step`
- ignores tiny gaps below `[rebalancing].min_trade_value_usdt`
- blocks sells for protected assets
- blocks symbols outside `[strategy].allowed_symbols`
- marks USDT increases as `KEEP_CASH` instead of creating a trade

Use `doctor` to validate local setup and config consistency:

```powershell
python -m trading_agent doctor --config config.example.toml --real-data --ai-commentary
```

Use `readiness` before any future mainnet `LIVE_CONFIRM` work:

```powershell
python -m trading_agent readiness --config config.example.toml
```

This command is expected to report `BLOCKED` until a separate live trading API key
and live confirmation implementation exist.

## LIVE_CONFIRM Preview

`LIVE_CONFIRM` starts as a mainnet preview-only layer. It can validate an approved spot
proposal against a separate live trading API key, mainnet symbol filters, and live spot
USDT balance, but it never submits an order in this implementation step.

```powershell
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview
```

The report includes `Mainnet LIVE_CONFIRM Preview`. Missing
`BINANCE_LIVE_TRADE_API_KEY` / `BINANCE_LIVE_TRADE_API_SECRET` is reported as a blocker.

## Safety Defaults

Real trading and real redeem are disabled by default. Before enabling anything live:

- use a Binance sub-account
- disable withdrawals on API keys
- restrict API key by IP
- start with tiny amounts
- keep `allow_locked_redeem = false`
