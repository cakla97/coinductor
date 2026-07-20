# Coinductor Stage A Manual Testing

This checklist is for a local desktop-app test pass. It covers UI flow, read-only
Binance access, local data transparency, safety-stage progression, and (only when you
intentionally choose to) guarded live actions. Guarded mainnet BUY and OCO protection
submission ARE exposed from the desktop UI once the safety stage reaches
`LIVE_ENABLED` and you type the exact confirmation phrase — do not exercise those
steps casually; prefer Testnet and previews.

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
- Confirm setup steps in the left rail are clickable when previous required steps
  are complete, and disabled/faded when they are not.
- Confirm `Next` is disabled when the current required step is incomplete.
- Confirm the wizard says it does not place orders or change exchange settings.
- Confirm the exchange step starts with Binance and clearly marks other exchanges as
  planned.
- Select `I already have a portfolio`.
- Confirm the selected starting path shows a clear explanation of what changes next.
- Change management style, automation, review rhythm, language/region, drawdown,
  bot preference, spot-trade preference, and starting budget. Confirm the starting
  budget field/label change to "Reference budget (optional)" for the existing-portfolio
  path instead of talking about first-portfolio funding.
- Confirm `Operating currency` is shown as a fixed USDC operating budget note, not
  as a misleading one-item dropdown.
- Confirm the profile step explains the currently selected option before saving.
- Confirm `Apply safe defaults` immediately saves a conservative local profile and
  shows a confirmation toast.
- Confirm `Save profile` shows a confirmation toast and enables the next step.
- Confirm labels are human readable, not internal constants such as
  `GUARDED_AUTOMATION`.
- In AI setup, save a local AI endpoint/model or skip it. If you save one, run
  `Check AI provider`.
- In AI setup, click `Scan hardware` and confirm Coinductor shows a local hardware
  summary and ranked Ollama model suggestions.
- Open `Local AI guide` and `Cloud AI guide` from the wizard. Confirm the guides
  open in a modal, links are clickable, and closing returns to the same wizard step.
- In Binance API setup, follow the shown Binance API steps and paste the read-only
  key/secret into the wizard fields. Do not edit `.env` manually during this test.
- Open the Binance API guide from this step.
- Confirm `Save key` shows a confirmation toast and clears the secret field.
- Run `Check read-only access`.
- Confirm the optional "Spot Testnet" panel is present: save a Testnet key and run
  `Check Testnet access` if you have one, or confirm it is clearly marked optional if
  you skip it. Confirm the panel links to a dedicated Testnet guide.
- Confirm the live-trading key panel/guide link ("Open live-trade guide") is present
  and clearly marked as a later, optional step.
- In Review, open the safety and portfolio roles guides.
- Confirm the "Next steps outside Coinductor" checklist appears and matches the
  chosen path (existing vs. first portfolio).
- For the first-portfolio path, confirm the "Suggested first basket" panel appears
  with per-asset weights and manual funding steps, not just the summary sentence.
- Confirm the wizard allows entering Coinductor.

## 3. Main App Smoke Test

- App opens as `Coinductor`.
- Sidebar pages switch without freezing, in this order: Overview, Portfolio,
  Live Actions, Action Plan, Active Strategies, Run History, AI Assistant,
  Help & Guides, Settings. (Portfolio intentionally comes before Live Actions so a
  new user reviews their holdings before seeing safety-stage/live-execution controls.)
- Overview loads the latest stored state or a clear empty/default state.
- Overview shows a "Finish setup" banner when Binance read-only isn't connected or
  AI isn't configured, and its buttons reopen the wizard at the right step.
- Hover the Portfolio/Liquid/Locked/Risk gate cards and the decision badge on
  Overview; confirm each shows an explanatory tooltip.
- `Run analysis` dialog opens; confirm `REAL` vs mock data and the AI options are
  clear.
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
- Confirm `First portfolio plan` appears in the wizard Review step.
- Confirm it shows:
  - funding amount, reserve, initial deployment (funding table),
  - suggested basket with per-asset target weights and roles,
  - manual setup steps ("Fund Binance", "Buy basket", "Enable Earn", "Review rhythm"),
  - the "Next steps outside Coinductor" checklist (account creation, deposit,
    API access, test first).
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
- Confirm the current behavior of the destructive button (preview-only vs. guarded
  execution — check the current `docs/AI_PROVIDER_HANDOFF.md` "Known incomplete
  Stage A work" list for whether this has shipped yet in your checkout).

## 7. Binance Read-Only, Testnet, and Live-Trading Checks

- Confirm the wizard or Settings API form saved read-only Binance keys locally.
- In Settings or Live Actions, run the Binance read-only check. Expected result:
  `Connected` if the key has safe read-only permissions, `Blocked` otherwise.
- If you saved a Spot Testnet key, run `Check Testnet access` and confirm it reports
  `Verified`/`Blocked` without placing any real or virtual order by itself.
- If you saved a live-trading key (optional, advanced), run `Verify permissions` on
  Live Actions and confirm it reports trusted-IP/Spot-trading/no-withdrawals status.
- Confirm none of these checks alone perform a write/trade action.

## 8. Analysis Run

- Open `Run analysis` (available from Overview, Live Actions, and Action Plan's
  "Run analysis now").
- Use `REAL` only when read-only check is ready.
- Keep `Generate AI summary` enabled if desired.
- Keep `Allow AI market ranking` disabled for the first UI test unless a local/cloud
  AI endpoint is running and you intentionally want to test it.
- Start analysis.
- Confirm progress updates and the UI does not freeze.
- After completion, confirm:
  - Overview metrics and "Latest decision" update,
  - Action Plan shows the trade/Grid/Rebalancing decision with a ready/watch/other
    legend above the list,
  - `Open report` works,
  - Portfolio page shows roles with hover tooltips explaining each role,
  - Active Strategies page reflects any registered bots,
  - Run History updates and shows REAL vs MOCK data mode with an explanation.

## 9. Live Actions and the Safety Stage

- Open `Live Actions`.
- Confirm the "Safety stage" card explains the current stage (`SETUP`,
  `PREVIEW_ONLY`, `ARMED`, `LIVE_ENABLED`) and the 3-step progress strip
  (Preview / Armed / Live enabled) has a one-line explanation per stage.
- Confirm the "Guarded Action Center" has three distinct actions: `Prepare trade
  preview`, `Prepare bot plan`, and `Open run dialog` (same custom dialog as
  Overview) — none of these place a real order by themselves.
- Do not progress the safety stage to `LIVE_ENABLED` or submit a guarded trade/OCO
  during a routine UI test. If you intentionally test guarded submission, use a
  small amount, a separate live-trade API key with withdrawals disabled, and the
  exact confirmation phrase (`CONFIRM_MAINNET_ORDER` / `CONFIRM_MAINNET_OCO`).
- Confirm `Lock live submit` returns the stage to `PREVIEW_ONLY` or `ARMED`.

## 10. Action Plan and Active Strategies

- Open `Action Plan` after a real run. Confirm the "Next review" panel shows
  suggested timing, triggers, and blockers, and that the ready/watch/other legend
  matches each item's status pill.
- Confirm `Open detailed report` opens the same Markdown report as Overview.
- Open `Active Strategies`. If no bot is registered, confirm the empty state links
  back to `Open Action Plan`. If a bot is registered, confirm its parameters and
  health status are shown, and that registration text is clear that Coinductor does
  not create or modify the Binance bot itself.

## 10a. Earn Redeem (Action Plan)

- After a real run where bankroll needs Flexible Earn funding, open the item
  detail dialog for the "Earn redeem" card on Action Plan.
- Confirm it shows asset, amount, product, and redeem type, and a status of
  `Ready`, `Blocked`, or `Submitted` matching the engine's plan.
- Do not submit during a routine UI test. If you intentionally test it, confirm
  the dialog requires typing `CONFIRM_EARN_REDEEM` exactly and that the button
  stays disabled until the safety stage is `LIVE_ENABLED`, the live-trading key
  check is `Verified`, and a `Ready` preview exists.

## 10b. Challenge HOLD (Action Plan)

- After a real run that returned `HOLD`, open the trade item's detail dialog on
  Action Plan and confirm a "Challenge this HOLD" panel appears with a symbol
  picker (from `strategy.allowed_symbols`) and a "Challenge HOLD" button.
- Pick a symbol and run it. Confirm this always runs a fresh REAL analysis and
  that the result can still be `HOLD`/blocked if the symbol fails consensus,
  bankroll, or any other deterministic check — it must never guarantee a BUY.
- Confirm the button/panel is hidden once the decision is no longer `HOLD`.

## 11. AI Assistant

- Open `AI Assistant`.
- Ask: `What can this app do?`
- Ask: `Explain the latest report.`
- If no external AI provider is configured, confirm the offline fallback still answers
  using local project context.
- Attach an image (file or clipboard paste) if a vision model is configured; confirm
  a clear message if no vision model is available instead of a silent failure.
- If the assistant proposes a structured action (e.g. navigation, opening the report,
  a role change), confirm it requires explicit Confirm before anything happens.

## 12. Help & Guides

- Open `Help & Guides`.
- Confirm the page lists Local AI, Cloud AI, Binance read-only API, Binance live
  trading API, Binance Spot Testnet, Safety model, and Portfolio roles.
- Open each guide and confirm the modal is readable, links are clickable
  (`Qt.openUrlExternally`), and it can be closed.
- Note where screenshots or more detailed instructions should be added.

## 13. Product Tour

- On first entry into the main app after onboarding, confirm the "Quick tour"
  overlay starts automatically and highlights the sidebar entry for each step.
- Confirm the tour order matches the sidebar order: Overview, Portfolio,
  Live Actions, Action Plan, Active Strategies, Run History, AI Assistant,
  Help & Guides, Settings (9 steps total).
- Confirm `Settings` includes `Replay app tour`.

## 14. Safety Expectations

- Guarded mainnet BUY, OCO protection, and Earn redeem submission from the desktop
  UI require `LIVE_ENABLED` safety stage AND their own exact confirmation phrase;
  none are reachable by accident through normal navigation.
- The desktop app must not withdraw funds; no UI path exists for this.
- Mainnet preview remains controlled by safety stage.
- Cloud AI is optional; if not configured, data should stay local.

## Notes To Capture

During testing, write down:

- confusing labels,
- text that feels too technical,
- layout issues (especially at the default 1240x860 window size — some panels are
  known to be tight there pending the planned QML redesign),
- any failed Binance check message,
- any command/output shown in the terminal,
- any report section that is too long or unclear.
