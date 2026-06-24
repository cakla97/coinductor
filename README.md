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

For day-to-day operation, use [docs/RUNBOOK.md](docs/RUNBOOK.md). It lists the safe monitoring
command, guarded submit commands, and the report sections to check before taking action.

Each report includes:

- portfolio summary
- portfolio valuation in USD-like stable value, with USDC preferred for mainnet trading funds
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

AI trade proposals can also use the same OpenAI-compatible endpoint when `[ai].enabled = true`.
The model is only an analysis/ranking layer over `[strategy].allowed_symbols`; it cannot expand
the trading universe or bypass deterministic guards. With the current config it may only choose
between `BTCUSDC`, `ETHUSDC`, or `HOLD`.

When `[ai].enabled = false`, the fallback analyst is conservative: it returns `BUY` only when an
allowed symbol has a `RISK_ON` snapshot, price above EMA200, and RSI in the configured safe band.
Otherwise it returns `HOLD`.

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
- `[capital_sourcing].allowed_source_assets` lists assets that can be recommended as manual sources of stablecoin trading capital.
- `[capital_sourcing].protected_assets` lists assets that should not be recommended as capital sources.
- `[portfolio.asset_roles]` classifies assets as `CORE`, `PROTECTED`,
  `PROTECTED_UTILITY`, `CAPITAL_SOURCE`, `SPECULATIVE_SOURCE`, `STABLE`, or another
  explicit role used for audit/reporting.

Backup capital sourcing is deliberately conservative. It caps total suggested sourcing per run,
caps each asset by percentage, and keeps both an absolute and percentage reserve in every source
asset. Current defaults are 20 USD-like value per run, 15% max from one source asset, 10% max of
the whole source basket per run, and at least 70% / 50 USD-like value left in each source asset.
Current source assets are `SOL` and `WLD`. `BNB` is treated as protected utility capital because
holding it can be useful for Binance campaigns, Launchpool-style rewards, and small airdrops.
`BTC`, `ETH`, and `WBETH` remain protected core positions.

Small legacy holdings such as `PEPE`, `DOGE`, `ADA`, and `DOT` are tracked explicitly rather than
treated as random dust. Unclassified assets outside the keep-list can be reported as airdrop/dust
funding candidates for conversion to USDC, currently recommendation-only.

Assets that cannot be priced are shown as unpriced instead of silently disappearing from totals.
Binance internal voucher-like assets with configured prefixes, such as `LD`, are reported separately
and excluded from valuation to avoid double counting.

## Rebalancing Preview

The assistant translates allocation gaps into preview-only rebalance steps. It does not execute
these steps. The default `[rebalancing].target_mode = "baseline_current"` treats the current
portfolio allocation as the baseline, so the assistant preserves the existing portfolio shape
instead of forcing a static model allocation. `[rebalancing.target_allocation]` is kept for an
optional future/static mode and is used only when `target_mode = "static"`.

The planner:

- caps each suggested step with `[rebalancing].max_trade_value_usdt_per_step`
- ignores tiny gaps below `[rebalancing].min_trade_value_usdt`
- blocks sells for protected assets
- blocks symbols outside `[strategy].allowed_symbols`
- marks USDC increases as `KEEP_CASH` instead of creating a trade

## Spot Grid Policy

Spot Grid remains a manual Binance UI workflow because the public Spot API does not expose a
project-supported create-grid-bot endpoint. The assistant only recommends parameters and setup
steps. Current defaults are intentionally small:

- eligible symbols: `BTCUSDC`, then `ETHUSDC`
- max active grid bots: `1`
- default investment: `25 USDC`
- max grid capital: `50 USDC`
- only range-friendly conditions are accepted: `NEUTRAL`/`RISK_ON` trend and RSI 45-65
- no grid recommendations for BNB, SOL, WLD, PEPE, DOGE, ADA, or DOT

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

`LIVE_CONFIRM` defaults to a mainnet preview layer. It can validate an approved spot
proposal against a separate live trading API key, mainnet symbol filters, live spot
quote balance, and bankroll policy before any guarded submit is allowed.

Mainnet funding uses `[live_confirm].quote_asset`, currently `USDC` in `config.example.toml`.
This keeps the assistant aligned with Binance stablecoin compliance prompts while leaving
Spot Testnet examples on `BTCUSDT`.

```powershell
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview
```

The report includes `Mainnet LIVE_CONFIRM Preview`. Missing
`BINANCE_LIVE_TRADE_API_KEY` / `BINANCE_LIVE_TRADE_API_SECRET` is reported as a blocker.
If Spot quote balance is too low, the report adds a Flexible Earn redeem plan. USDC may remain
in Auto-Subscribe; the assistant can prepare a bounded USDC redeem back to Spot when bankroll
policy allows it.

Before any first real submit, review the `Execution Checklist` section. It includes a
`First LIVE action gate` item with required USDC, spot-free USDC, preferred bankroll source,
Flexible Earn draw needed, Earn redeem status, and the current LIVE_CONFIRM order status. A real
order should be considered only when the gate shows no `BLOCKER` items and the order status is
`PREVIEW_READY`.

Guarded submit requires a separate explicit command:

```powershell
python -m trading_agent run --config config.example.toml --real-data --live-confirm-submit --confirm-mainnet-order CONFIRM_MAINNET_ORDER
```

Submit still passes through symbol filters, balance checks, risk checks, and the trading
bankroll policy. Without the exact confirmation string, the run records `SUBMIT_SKIPPED`.
Submitted live intents are stored in SQLite so rerunning the same daily signal does not submit
the same mainnet order twice.

## Mainnet Live Positions

Filled LIVE_CONFIRM mainnet BUY orders are stored in `live_orders` with executed quantity and
cumulative quote amount. Each run builds a `Mainnet Live Positions` report from that history:

- open positions show entry price, current price, unrealized PnL, stop-loss, and take-profit
- closed cycles show realized PnL when a matching filled SELL exists
- exit preview is report-only for now: `HOLD`, `STOP_LOSS_REVIEW`, `TAKE_PROFIT_REVIEW`, or `UNKNOWN_PRICE`

Guarded SELL submission is intentionally not automatic yet. The assistant first needs to observe
and report open live positions before it is allowed to close them.

`[live_position_guard].block_new_buy_when_open = true` prevents new BUY proposals while an open
mainnet live position exists. The assistant should monitor stop-loss/take-profit state first,
then a future guarded SELL flow can be added separately.

Stop-loss and take-profit are currently soft thresholds inside the assistant. They are not live
exchange stop/OCO orders, so a position will not close automatically while the assistant is not
running. Each run creates a `Mainnet LIVE_EXIT Preview` section. It remains `MONITORING` while
price is between thresholds, and becomes `READY` only when a stop-loss or take-profit review is
triggered and Binance symbol/quantity/notional checks pass. A future guarded SELL submit should
use a separate confirmation such as `CONFIRM_MAINNET_SELL`.

For irregular/manual runs, the assistant also creates `Mainnet OCO Protection Preview`. This is a
report-only plan for a Binance-side SELL OCO protection order using the position's take-profit
price and stop-loss stop price. The preview validates available base balance, step size, minQty,
minNotional, and the required price relationship. It does not place the OCO order yet; a future
guarded submit should use a separate confirmation such as `CONFIRM_MAINNET_OCO`.

Guarded OCO protection submit is intentionally separate from normal live order submit:

```powershell
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview --oco-protection-submit --confirm-mainnet-oco CONFIRM_MAINNET_OCO
```

Only `READY` OCO protection previews are eligible. Submitted OCO intents are stored so reruns do
not submit the same protection order list again.

Each later run also performs `Mainnet OCO Status Sync`: it queries submitted Binance order lists,
reports whether protection is still `EXECUTING`, and records a filled OCO SELL leg into
`live_orders` so the live position becomes a closed cycle with realized PnL.

## Trading Bankroll

`[trading_bankroll]` separates the bot's working capital from the rest of the portfolio.
The initial manual allocation is tracked as seed capital, while any quote balance above that
seed is treated as estimated realized profit. Reports show whether a trade would use:

- `PROFIT_SPOT`: realized profit already available in Spot
- `SEEDED_SPOT`: bootstrap seed capital, not profit yet
- `FLEXIBLE_EARN_REDEEM_REQUIRED`: quote asset must be manually redeemed from Flexible Earn
- `INSUFFICIENT`: not enough tracked bankroll is available

This is intentionally audit-first. Flexible Earn redemption and mainnet order submission are
guarded. The compromise policy prefers profit first, allows limited bootstrap seed while the
strategy is new, and can prepare a bounded USDC Flexible Earn draw when Spot capital is insufficient.
Redeem submit requires an explicit flag and confirmation string:

```powershell
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview --earn-redeem-submit --confirm-earn-redeem CONFIRM_EARN_REDEEM
```

After a submitted redeem, rerun the assistant so it can verify Spot USDC before any mainnet order.

## Local LLM Trade Ranking

Use `--ai-proposals` to let the local Qwen endpoint rank `strategy.allowed_symbols` and choose
between `BUY` and `HOLD` for one run:

```powershell
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview --ai-proposals
```

This command is preview-safe unless a separate guarded submit flag and its exact confirmation are
also supplied. Qwen cannot choose position size, stop-loss, or take-profit; those values come from
the deterministic config and still pass through the risk, bankroll, open-position, and idempotency
guards. It also cannot propose `SELL`; exits remain owned by the OCO/position workflow.

`[ai_memory]` supplies a bounded history of recent closed mainnet cycles from SQLite to Qwen. The
memory contains entry conditions and realized results, not raw report files and not model training.
This keeps the input small, structured, auditable, and independent of report rotation. Historical
outcomes are explicitly treated as context rather than proof that a setup will repeat.
The model may describe recurring patterns only after
`[ai_memory].min_cycles_for_pattern_inference` closed cycles are available.
Until that threshold is reached, individual outcomes remain visible in reports and commentary but
are withheld from the trade-ranking prompt.

## Local Binance Market Research

`[market_research]` is the default standalone research layer. It uses Binance public endpoints
directly from Python, requires no web-search subscription, and does not require Binance Skills.
Each run collects:

- 24-hour price change, range, quote volume, and trade count
- 7-day and approximately 30-day returns from 4-hour K-lines
- ATR percentage, distance from EMA200, and relative strength versus BTC
- liquidity-filtered USDC market breadth, gainers, losers, and volume leaders

The result is included in the Markdown report, stored in SQLite under the normal run retention,
and supplied to Qwen as structured context. Rankings are not standalone BUY signals. If a public
endpoint fails or returns malformed data, the research section becomes `PARTIAL` and the portfolio,
OCO, and reporting workflow continues.

Binance AI Agent Skills remain optional supplemental research. Their notes can still be placed in
`research/notes/`, but normal local runs no longer depend on that manual step for broader market
context.

## Qwen Shadow Evaluation

`[shadow_evaluation]` measures local Qwen proposals without placing orders. It is active only on
runs where AI proposals are enabled. Each proposal stores the allowed-universe entry prices in
SQLite and remains `PENDING` until the configured horizon, currently 24 hours.

At the first later run, the evaluator requests Binance 1-minute candles at the exact horizon:

- `BUY` is correct when the selected symbol gains at least the configured threshold
- `BUY` is wrong when it loses at least that threshold
- `HOLD` is wrong when any allowed symbol offered a threshold-sized gain
- `HOLD` is correct when even the best allowed symbol fell by at least that threshold
- smaller changes are neutral

The default threshold is 0.5% and results are measured before fees. If historical candles cannot
be loaded, the report clearly marks use of the current-price fallback. Shadow records live in
SQLite and follow the normal database-run retention.

`min_signal_interval_hours` defaults to 20 hours. Additional Qwen runs inside that cooldown still
perform portfolio analysis and evaluate due older signals, but do not add another highly correlated
shadow sample. The report identifies the blocking run and remaining cooldown time.

## Live Risk State And Consensus

Every run now rebuilds live risk state from closed mainnet cycles in SQLite. Realized PnL is
assigned to the SELL/OCO close time and partial exits use proportional BUY cost basis. Daily and
weekly loss percentages use `[trading_bankroll].initial_seed_usdc` as the conservative loss basis.

The risk state enforces:

- mainnet BUY count for the current UTC day
- daily and weekly realized-loss limits
- consecutive losing cycles
- cooldown after the most recent realized loss
- derived kill switch when a configured loss boundary is reached

`[consensus]` is a second deterministic gate for BUY proposals. By default, the selected symbol
must be `RISK_ON`, above EMA200, and have RSI14 between 45 and 68. Qwen can rank BTC/ETH and explain
its choice, but cannot bypass these market conditions, bankroll rules, OCO workflow, or the live
risk state.

## Spot Grid Advisor V2

The grid advisor evaluates every symbol in `[grid_bot].allowed_symbols` and separates:

- `market_status`: `SUITABLE`, `WATCH`, or `REJECTED`
- `deployment_allowed`: whether risk, cooldown, active-bot count, and capital-per-grid checks allow setup
- `recommended`: true only when both market suitability and deployment eligibility pass

Candidate scoring uses trend regime, RSI, ATR percentage, distance from EMA200, and 7-day
directionality. Grid boundaries combine ATR with EMA20/EMA50 and 30-day support/resistance from
the local Binance research layer. The range is still capped by configured percentage limits.

Grid count is constrained by `min_quote_per_grid_usdt`. With the default 25 USDC allocation and
2.5 USDC minimum, the advisor proposes at most 10 grids rather than mechanically using 20.
Reports include estimated quote/grid, spacing, blockers, stop-loss, take-profit, and exact manual
Binance setup steps. The project never creates the Binance bot automatically.

## Register And Monitor A Manual Grid

After the Spot Grid is actually created in Binance, preview local registration using the exact
values displayed by Binance:

```powershell
python -m trading_agent grid-register --config config.example.toml `
  --name eth-grid-1 `
  --binance-bot-id 123456789 `
  --symbol ETHUSDC `
  --range-low 1505.34 `
  --range-high 1869.39 `
  --grid-count 10 `
  --grid-type ARITHMETIC `
  --investment 25 `
  --entry-price 1660 `
  --stop-loss 1460.18 `
  --take-profit 1925.47
```

Preview never writes the state file. After matching every value against Binance, append:

```powershell
--confirm CONFIRM_GRID_REGISTER
```

The local registry enforces symbol/range/stop/take-profit validity, unique names/Binance IDs, and
`max_active_grid_bots`. Later runs monitor current price, range boundaries, registered stop-loss
and take-profit, and `[grid_bot].max_runtime_days`.

When the Binance bot is paused, stopped, or closed, update the local lifecycle state:

```powershell
python -m trading_agent grid-set-status --config config.example.toml `
  --name eth-grid-1 --status CLOSED
```

## Binance Rebalancing Bot Advisor

Each normal run also creates a recommend-only Binance Rebalancing Bot proposal. It:

- preserves relative weights inside the configured eligible basket,
- defaults to threshold rebalancing to avoid unnecessary periodic turnover,
- caps proposed investment by an absolute and portfolio-percentage limit,
- keeps BNB and other excluded portfolio roles outside the bot,
- treats WBETH-to-ETH as a separate manual decision and blocks deployment until resolved,
- stores each recommendation and target basket in SQLite for later comparison.

The advisor never creates the Binance bot or converts protected assets. Use a real-data
preview to generate parameters from the current portfolio:

```powershell
python -m trading_agent run --config config.example.toml --real-data
```

After manually creating the bot in Binance, preview its local registration:

```powershell
python -m trading_agent rebalancing-register --config config.example.toml `
  --name core-rebalance-1 `
  --binance-bot-id 123456789 `
  --assets BTC,ETH,SOL `
  --target-weights 52.9,23.4,23.7 `
  --entry-prices 61116.76,1781.44,67.89 `
  --investment 100 `
  --threshold 5
```

The command writes nothing until the exact confirmation is added:

```powershell
  --confirm CONFIRM_REBALANCING_REGISTER
```

Each later real-data run reports theoretical current basket weights and maximum drift.
This is a local price-based monitor, not a claim about Binance's internal bot PnL or
executed rebalance history. Update lifecycle state when the bot is paused or closed:

```powershell
python -m trading_agent rebalancing-set-status --config config.example.toml `
  --name core-rebalance-1 --status CLOSED `
  --confirm CONFIRM_REBALANCING_STATUS
```

When local AI commentary is enabled, Qwen receives a separate focused copy of the
deterministic Rebalancing Bot proposal. Its assessment is advisory only. A validator
rejects the text if it introduces Grid conditions, market-status blockers, or other
facts absent from the deterministic proposal; the report then shows a guarded fallback.

Append `--confirm CONFIRM_GRID_STATUS` only after the Binance-side status really changed.

## Safety Defaults

Real trading and real redeem are disabled by default. Before enabling anything live:

- use a Binance sub-account
- disable withdrawals on API keys
- restrict API key by IP
- start with tiny amounts
- keep `allow_locked_redeem = false`
