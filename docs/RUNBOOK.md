# Binance Trading Agent Runbook

This runbook is the operational checklist for local, periodic use. It assumes the project is opened
in `<repo>` and that `.env` already contains the configured Binance keys.

## Default Safe Run

Use this for normal monitoring. It reads mainnet data, syncs existing OCO protection status, writes
a report, and does not submit orders or redeem Earn products.

```powershell
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview
```

Check these report sections:

- `Mainnet Live Positions`: open or closed live cycles and unrealized/realized PnL.
- `Mainnet OCO Status Sync`: whether Binance-side protection is still `EXECUTING` or has filled.
- `Mainnet OCO Protection Preview`: whether a position is already `PROTECTED`, `READY`, or `BLOCKED`.
- `Mainnet LIVE_CONFIRM Preview`: should normally be blocked while a live position is open.
- `Execution Checklist`: human-readable next steps and blockers.

Expected current state after the first live test:

- one open `BTCUSDC` live position,
- OCO order list tracked as protected,
- no new BUY while the live position remains open.

## Readiness Check

Run before any guarded mainnet action.

```powershell
python -m trading_agent readiness --config config.example.toml
```

Continue only if `Mainnet readiness: PASS`. A PASS does not mean an action should be submitted; it
only means the configured guards are not obviously broken.

## Local LLM Commentary

Use this when Qwen/OpenAI-compatible local endpoint is running and you want commentary in the report.
This does not give the model execution authority.

```powershell
$env:LLM_BASE_URL="http://127.0.0.1:11434/v1"
$env:LLM_MODEL="qwen3:14b"
$env:LLM_VISION_MODEL="qwen3-vl:8b"  # optional; image messages only
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview --ai-commentary
```

Treat LLM output as context only. Deterministic guards still control trading universe, bankroll,
position guard, OCO state, and submit eligibility.

## Local LLM Proposal Preview

To let Qwen rank the allowed BTC/ETH market snapshots and choose `BUY` or `HOLD` without submitting:

```powershell
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview --ai-proposals
```

The report shows the proposal, deterministic risk decision, and the bounded `AI Decision Memory`
used as context. The memory is built from closed live cycles in SQLite, survives report rotation,
and is limited by `[ai_memory].max_closed_cycles`. Do not combine this evaluation command with a
submit flag. Review the preview first, then use a separate guarded action run only if appropriate.
Pattern language is disabled until `[ai_memory].min_cycles_for_pattern_inference` cycles exist.

## Automatic Local Market Research

No separate command is required. When `[market_research].enabled = true`, every normal run queries
Binance public market endpoints before Qwen ranking and writes `Local Binance Market Research` into
the report. This layer is free and local except for the direct HTTPS calls to Binance.

Expected status:

- `OK`: breadth and all allowed-symbol multi-timeframe data were collected
- `PARTIAL`: one or more public requests or fields failed; the main run still continues
- `DISABLED`: the feature was disabled in config
- `MOCK`: deterministic mock data was used

Treat top gainers, losers, and volume leaders as market context only. They do not expand
`strategy.allowed_symbols` and cannot bypass deterministic risk or submission guards.

## Qwen Shadow Evaluation

Shadow tracking is automatic on runs using `--ai-proposals`. The current report should show a new
`PENDING` signal. On the first run after its 24-hour horizon, the report adds a verdict:

- `BUY_GAIN`, `BUY_LOSS`, or `BUY_FLAT`
- `HOLD_AVOIDED_LOSS`, `HOLD_MISSED_GAIN`, or `HOLD_NEUTRAL`

The `Price Source` column should normally be `BINANCE_1M_AT_HORIZON`, even when the application was
not running at the evaluation time. A fallback source means the historical candle request failed
and should be treated as lower-quality evidence. Shadow evaluation never submits an order.

Only one new shadow signal is recorded per `[shadow_evaluation].min_signal_interval_hours`, currently
20 hours. A repeated run during this window should show `Recording status: SKIPPED_COOLDOWN`; this is
expected and prevents multiple samples from the same market episode.

## Live Risk State

Every safe run contains `Live Risk State`. Before any future mainnet BUY, verify:

- `Kill switch active` is `False`
- `Cooldown active` is `False`
- daily and weekly limits are not reached
- the number of trades today is below `[risk].max_trades_per_day`
- the final `Risk Decision` also passed the deterministic consensus gate

Loss percentages are measured against `[trading_bankroll].initial_seed_usdc`. Closed OCO cycles are
dated by the SELL reconciliation run, so a loss blocks the day it was realized. The configured
24-hour loss cooldown can continue blocking BUY after the UTC daily limit resets.

The default consensus requires `RISK_ON`, price above EMA200, and RSI14 from 45 to 68. A Qwen BUY
outside these conditions must remain rejected even at high model confidence.

## Spot Grid Advisor V2

Review `Spot Grid Recommendation` even when the overall strategy decision is `HOLD`. Its fields
have separate meanings:

- `Market status: SUITABLE` means the range model likes current conditions
- `Deployment allowed: True` means no risk/cooldown/active-bot/capital blocker remains
- `Recommended: True` requires both of the above

Never create a grid from `WATCH`, `REJECTED`, or `Deployment allowed: False`. Before manual setup,
also verify Binance's displayed minimum investment and estimated profit/grid because exchange-side
limits may change.

After manually creating a grid, copy `state/active_strategies.example.toml` to
`state/active_strategies.toml` only for manual recovery. The preferred path is the guarded registry:

```powershell
python -m trading_agent grid-register --config config.example.toml `
  --name <local-name> --binance-bot-id <id-from-binance> `
  --symbol <BTCUSDC-or-ETHUSDC> `
  --range-low <exact-low> --range-high <exact-high> `
  --grid-count <exact-count> --grid-type ARITHMETIC `
  --investment <exact-usdc> --entry-price <creation-price> `
  --stop-loss <exact-stop> --take-profit <exact-take>
```

Run this first without confirmation. It must show a clean preview. Then rerun with
`--confirm CONFIRM_GRID_REGISTER`. Registration is local only and never creates a Binance bot.

Active-grid report states include:

- `IN_RANGE`, `NEAR_LOWER`, `NEAR_UPPER`
- `BELOW_RANGE`, `ABOVE_RANGE`
- `STOP_LOSS_BREACH`, `TAKE_PROFIT_REACHED`
- `RUNTIME_EXPIRED`, `UNKNOWN_PRICE`

After changing the real bot in Binance, keep local state synchronized:

```powershell
python -m trading_agent grid-set-status --config config.example.toml `
  --name <local-name> --status CLOSED --confirm CONFIRM_GRID_STATUS
```

## Guarded USDC Flexible Earn Redeem

Use only when the report shows `Flexible Earn Redeem` status `PREVIEW_READY` and the `Execution
Checklist` says a USDC draw is needed.

```powershell
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview --earn-redeem-submit --confirm-earn-redeem CONFIRM_EARN_REDEEM
```

After redeem submit, immediately run the default safe run again and verify that Spot USDC changed
as expected. Do not submit a BUY just because a redeem succeeded.

## Guarded Mainnet BUY

Use only when all of these are true:

- `Mainnet LIVE_CONFIRM Preview` shows status `PREVIEW_READY`.
- `Execution Checklist` has no relevant `BLOCKER` for the live action.
- `Mainnet Live Positions` has no open live position, unless the strategy was deliberately changed.
- The proposed symbol is in `[strategy].allowed_symbols`.
- The quote amount is still within `[live_confirm].max_quote_amount_usdt`.

Submit command:

```powershell
python -m trading_agent run --config config.example.toml --real-data --live-confirm-submit --confirm-mainnet-order CONFIRM_MAINNET_ORDER
```

After submit, immediately run the default safe run again. Verify:

- order status is `FILLED` or clearly reported otherwise,
- `Mainnet Live Positions` contains the new position,
- no duplicate order is proposed on the next run.

## Guarded OCO Protection Submit

Use after a filled live BUY when the report shows `Mainnet OCO Protection Preview` status `READY`.
This places Binance-side protection so stop/take-profit can work even when the local bot is not
running.

```powershell
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview --oco-protection-submit --confirm-mainnet-oco CONFIRM_MAINNET_OCO
```

After submit, immediately run the default safe run again. Verify:

- `Mainnet OCO Status Sync` shows the order list as active, usually `EXECUTING`.
- `Mainnet OCO Protection Preview` shows the position as `PROTECTED`.
- Available base may drop because Binance locks the OCO quantity.

## When OCO Fills

On a later safe run, `Mainnet OCO Status Sync` should detect a filled SELL leg and record it into
`live_orders`. Then the report should move the position from open to closed and show realized PnL.

Before allowing a new BUY cycle, verify:

- `Mainnet Live Positions` has no open cycle for the previous intent.
- `Mainnet OCO Status Sync` is not reporting query errors.
- Trading bankroll and Spot/Flexible USDC state make sense.
- The new proposal is not just a duplicate of the previous cycle.

## What Not To Run Casually

Avoid submit flags unless the report explicitly says the matching preview is ready:

- `--live-confirm-submit`
- `--earn-redeem-submit`
- `--oco-protection-submit`

Never combine submit flags just to save time. Use one guarded action per run, then run the default
safe monitoring command again.

## If Something Looks Wrong

Use these checks before taking action:

```powershell
python -m trading_agent doctor --config config.example.toml
python -m trading_agent readiness --config config.example.toml
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview
git status --short
```

If Binance UI and the report disagree, trust neither blindly. Use Binance UI as the source of truth
for funds/orders, then investigate the local report and SQLite state before submitting another action.
