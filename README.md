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
python -m trading_agent last-report --config config.example.toml
python -m trading_agent research-request --config config.example.toml --real-data
```

The first run uses mock market/account data and writes:

- SQLite journal to `work/trading_agent.sqlite3`
- Markdown report to `outputs/reports/`

Each report includes:

- portfolio summary
- portfolio valuation in USDT
- rebalance gap against configured target allocation
- Spot vs Flexible vs Locked balance view
- manual execution checklist
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

## Active Strategy Tracking

If you manually create a Binance Spot Grid bot, copy the example state file:

```powershell
Copy-Item state/active_strategies.example.toml state/active_strategies.toml
```

Then edit `state/active_strategies.toml` with the real grid range, symbol, and
investment. The assistant will track whether current price is inside the configured
range and add review actions when price approaches or leaves the range.

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

Use `doctor` to validate local setup and config consistency:

```powershell
python -m trading_agent doctor --config config.example.toml --real-data --ai-commentary
```

## Safety Defaults

Real trading and real redeem are disabled by default. Before enabling anything live:

- use a Binance sub-account
- disable withdrawals on API keys
- restrict API key by IP
- start with tiny amounts
- keep `allow_locked_redeem = false`
