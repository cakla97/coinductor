# Binance Periodic Trading Agent MVP

Experimental local trading/rebalancing agent for Binance Spot + Simple Earn Flexible.

This project is intentionally conservative:

- periodic runs instead of a 24/7 bot
- `DRY_RUN` by default
- no futures, no margin, no leverage
- AI is an analyst only; deterministic code enforces risk and liquidity rules
- Flexible Earn redeem is modeled as a liquidity-management step
- Locked Earn is read-only

## Prerequisites

- Python 3.11 or newer
- Optional: local OpenAI-compatible LLM endpoint, for example Ollama/Open WebUI/LM Studio
- Binance API keys only when moving beyond mock/dry-run

The current Codex desktop environment has a bundled Python at:

```powershell
C:\Users\cakla\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

## Quick Start

```powershell
Copy-Item .env.example .env
& 'C:\Users\cakla\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m trading_agent --config config.example.toml
```

The first run uses mock market/account data and writes:

- SQLite journal to `work/trading_agent.sqlite3`
- Markdown report to `outputs/reports/`

## Modes

- `DRY_RUN`: simulates decisions and orders
- `TESTNET`: reserved for Binance Spot Testnet execution
- `LIVE_CONFIRM`: reserved for future manual-confirm mainnet mode
- `LIVE_AUTO`: intentionally outside this MVP

## Safety Defaults

Real trading and real redeem are disabled by default. Before enabling anything live:

- use a Binance sub-account
- disable withdrawals on API keys
- restrict API key by IP
- start with tiny amounts
- keep `allow_locked_redeem = false`

