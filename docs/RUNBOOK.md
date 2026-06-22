# Binance Trading Agent Runbook

This runbook is the operational checklist for local, periodic use. It assumes the project is opened
in `D:\CodexWork\binance-trading-agent` and that `.env` already contains the configured Binance keys.

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
python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview --ai-commentary
```

Treat LLM output as context only. Deterministic guards still control trading universe, bankroll,
position guard, OCO state, and submit eligibility.

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
