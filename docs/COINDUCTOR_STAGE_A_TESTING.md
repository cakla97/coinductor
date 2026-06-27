# Coinductor Stage A Manual Testing

This checklist is for the first local desktop-app test pass. It focuses on UI flow,
read-only Binance access, local data transparency, and safety gates. Do not test live
order submission from the desktop UI; it is intentionally not exposed there.

## 1. Start The App

From the project folder:

```powershell
cd D:\CodexWork\binance-trading-agent
python -m pip install -e ".[desktop]"
python -m coinductor.desktop
```

If you prefer VS Code, open the folder and run the same commands in the integrated
terminal.

## 2. Smoke Test

- App opens as `Coinductor`.
- Sidebar pages switch without freezing: Overview, Portfolio, Strategies, Run History,
  AI Assistant, Settings.
- Overview loads the latest stored state or a clear empty/default state.
- `Run analysis` dialog opens and does not offer live submit.

## 3. Settings And Onboarding

- Open `Settings`.
- Select `I already have a portfolio`.
- Open `Guide me`.
- Change language/region, management style, automation, review rhythm, drawdown, and
  starting budget.
- Save the guided profile.
- Confirm `Onboarding profile` updates.
- Confirm `Personal readiness` action updates.
- Use `Reset onboarding` and confirm the profile returns to not configured.

## 4. First Portfolio Flow

- Select `Build my first portfolio`.
- Confirm `First portfolio planner` appears.
- Confirm it shows:
  - funding amount,
  - reserve,
  - initial deployment,
  - suggested basket,
  - manual setup steps.
- Reopen `Guide me`, choose `cs-CZ`, and save.
- Confirm planner uses `CZK -> USDC` wording.

## 5. Privacy And Local Data

- Read `Privacy & Data`.
- Confirm wording is transparent but not alarmist.
- Confirm `Reset onboarding` says it leaves API keys, reports, database history,
  role overrides, and safety state untouched.
- Open `Delete local data`.
- Toggle `Delete everything`.
- Confirm all groups are selected.
- Type `DELETE`.
- Confirm destructive deletion remains disabled in this build.

## 6. Binance Read-Only Check

- Confirm `.env` contains read-only Binance keys.
- In Settings, run the Binance read-only check.
- Expected result:
  - `Connected` if the key has safe read-only permissions.
  - `Blocked` if permissions or IP restrictions are wrong.
- Confirm no write/trade action is performed by this check.

## 7. Analysis Run

- Open `Run analysis`.
- Use `REAL` only when read-only check is ready.
- Keep `Generate AI summary` enabled if desired.
- Keep `Allow AI market ranking` disabled for the first UI test unless Qwen endpoint is
  running and you intentionally want to test it.
- Start analysis.
- Confirm progress updates and the UI does not freeze.
- After completion, confirm:
  - Overview metrics update,
  - recommended actions appear,
  - `Open report` works,
  - Portfolio page shows roles,
  - Strategies page shows Grid/Rebalancing recommendations,
  - Run History updates.

## 8. AI Assistant

- Open `AI Assistant`.
- Ask: `What can this app do?`
- Ask: `Explain the latest report.`
- If no external AI provider is configured, confirm the offline fallback still answers
  using local project context.

## 9. Safety Expectations

- The desktop app must not submit live orders.
- The desktop app must not redeem Earn.
- The desktop app must not withdraw funds.
- Mainnet preview remains controlled by safety stage.
- Cloud AI is optional; if not configured, data should stay local.

## Notes To Capture

During testing, write down:

- confusing labels,
- text that feels too technical,
- layout issues,
- any failed Binance check message,
- any command/output shown in the terminal,
- any report section that is too long or unclear.
