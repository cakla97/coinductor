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

## 2. First-Run Wizard

- With no onboarding profile, the app opens into the setup wizard instead of the
  main dashboard.
- Confirm the wizard is step-by-step: Exchange, Portfolio, Profile, AI, Binance API,
  Review.
- Confirm `Next` is disabled when the current required step is incomplete.
- Confirm the wizard says it does not place orders or change exchange settings.
- Confirm the exchange step starts with Binance and clearly marks other exchanges as
  planned.
- Select `I already have a portfolio`.
- Change management style, automation, review rhythm, language/region, drawdown,
  bot preference, spot-trade preference, and starting budget.
- Confirm the profile step explains the currently selected option before saving.
- Confirm `Apply safe defaults` immediately saves a conservative local profile and
  shows a confirmation toast.
- Confirm `Save profile` shows a confirmation toast and enables the next step.
- Confirm labels are human readable, not internal constants such as
  `GUARDED_AUTOMATION`.
- In AI setup, save a local AI endpoint/model or skip it. If you save one, run
  `Check AI provider`.
- In Binance API setup, follow the shown Binance API steps and paste the read-only
  key/secret into the wizard fields. Do not edit `.env` manually during this test.
- Confirm `Save key` shows a confirmation toast and clears the secret field.
- Run `Check read-only access`.
- Confirm the wizard allows entering Coinductor.

## 3. Main App Smoke Test

- App opens as `Coinductor`.
- Sidebar pages switch without freezing: Overview, Portfolio, Strategies, Run History,
  AI Assistant, Settings.
- Overview loads the latest stored state or a clear empty/default state.
- `Run analysis` dialog opens and does not offer live submit.
- Open `Settings`.
- Confirm `Setup wizard` opens the wizard again.

## 4. Existing Portfolio Flow

- Open `Settings`.
- Confirm `Onboarding profile` updates.
- Confirm readiness/system checks remain visible in Settings.
- Use `Reset onboarding` and confirm the profile returns to not configured.
- Confirm the wizard appears again after reset.

## 5. First Portfolio Flow

- Reopen `Setup wizard`.
- Select `Build my first portfolio`.
- Save the profile or use safe defaults.
- Confirm `First portfolio plan` appears in the wizard.
- Confirm it shows:
  - funding amount,
  - reserve,
  - initial deployment,
  - suggested basket,
  - manual setup steps.
- Choose `cs-CZ`, save, and confirm the planner uses localized funding wording
  where currently supported.
- Confirm planner uses `CZK -> USDC` wording.

## 6. Privacy And Local Data

- Read `Privacy & Data`.
- Confirm wording is transparent but not alarmist.
- Confirm `Reset onboarding` says it leaves API keys, reports, database history,
  role overrides, and safety state untouched.
- Open `Delete local data`.
- Toggle `Delete everything`.
- Confirm all groups are selected.
- Type `DELETE`.
- Confirm destructive deletion remains disabled in this build.

## 7. Binance Read-Only Check

- Confirm the wizard or Settings API form saved read-only Binance keys locally.
- In Settings, run the Binance read-only check.
- Expected result:
  - `Connected` if the key has safe read-only permissions.
  - `Blocked` if permissions or IP restrictions are wrong.
- Confirm no write/trade action is performed by this check.

## 8. Analysis Run

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

## 9. AI Assistant

- Open `AI Assistant`.
- Ask: `What can this app do?`
- Ask: `Explain the latest report.`
- If no external AI provider is configured, confirm the offline fallback still answers
  using local project context.

## 10. Planned Product Tour

- Product tour is not implemented yet.
- Expected later behavior:
  - first entry into the main app starts a short guided walkthrough,
  - Overview, Portfolio, Strategies, Run History, AI Assistant, Settings/State,
    and safety panel are highlighted one at a time,
  - Settings includes `Run app tour again`.

## 11. Safety Expectations

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
