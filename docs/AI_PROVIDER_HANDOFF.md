# Coinductor AI Provider Handoff

Last updated: 2026-07-15  
Known-good baseline commit: `a1c5204 Add dedicated vision model routing`

This document is the starting context for another AI coding agent taking over
Coinductor development. The user communicates in Czech. Keep user-facing discussion
in Czech unless they request another language; code, identifiers, and repository
documentation are primarily English.

## First Session Checklist

1. Work in `D:\CodexWork\binance-trading-agent`.
2. Read this file, `README.md`, `docs/ROADMAP.md`, and `docs/RUNBOOK.md`.
3. Run `git status --short` and `git log -5 --oneline` before editing.
4. Never print, quote, commit, overwrite, or upload `.env`.
5. Run `python -m pytest -q` before and after non-trivial changes. The baseline is
   `161 passed` (parameterization means a textual count of test functions is lower).
6. Run `python -m compileall -q coinductor` and `git diff --check` before committing.
7. Inspect the existing implementation before proposing abstractions. Preserve local
   conventions and keep changes scoped.
8. Tell the user what will be edited before editing, provide short progress updates,
   and commit coherent verified changes to the local Git repository.

There is currently no Git remote configured. Git is local and used as an audit trail.
Do not create or push to a remote unless the user explicitly chooses one.

## Non-Negotiable Safety Contract

Coinductor is a conservative local portfolio assistant, not an unconstrained trading
agent. Deterministic Python code owns permissions, sizing, asset eligibility, loss
limits, bankroll rules, OCO requirements, idempotency, and live confirmation gates.
AI may explain, summarize, rank an already bounded candidate set, and prepare safe
structured intents. It must never bypass deterministic controls.

- No futures, margin, leverage, or withdrawals.
- Never expose Binance or AI API credentials.
- Treat the saved Safety stage as potentially `LIVE_ENABLED`; do not assume the app
  is locked merely because a fresh process was started.
- Never run a mainnet submit, Earn redeem submit, OCO submit, destructive local-data
  action, or state-changing Binance call without an explicit request and confirmation
  from the user in the current conversation.
- Mainnet preview is not the same as submission.
- Grid and Rebalancing bot creation remains manual on Binance. Coinductor recommends
  parameters and stores a verified local registration after the user creates a bot.
- Do not loosen risk limits merely to make an action become eligible.
- Existing user files may be dirty or contain live state. Work with them; do not reset
  or revert changes that were not made by the current agent.

A tiny real mainnet trade and exchange-side protection lifecycle were exercised during
development. Do not repeat live testing casually. Testnet and previews are preferred.

## Product Intent

The product name is **Coinductor**. It began as a personal Binance automation prototype
and is intended to become a trustworthy local-first open-source desktop application for
non-technical users.

Core product principles:

- periodic or irregular user-initiated runs instead of requiring a 24/7 desktop PC;
- useful portfolio management for both existing holders and first-time portfolio users;
- USDC as the internal operating/trading budget, with Flexible Earn liquidity handling;
- profit-first trading bankroll, bounded seed use, and tightly limited fallback funding;
- complete portfolio visibility while only approved universes may trade or fund actions;
- exchange-side OCO protection so stop-loss/take-profit can work while Coinductor is off;
- clear manual instructions where Binance does not expose a suitable public API;
- local AI by default, optional cloud API, transparent privacy boundaries;
- explanations and recommendations, never promises of profit.

The current development machine has an NVIDIA RTX 4080 (16 GB VRAM), Ryzen 7 7800X3D,
32 GB RAM, and Python 3.14. The package declares Python `>=3.11`.

## Repository Map

### Deterministic engine: `trading_agent/`

- `runner.py`: orchestration of one complete analytical run.
- `binance_client.py`: Binance REST access and signed endpoints.
- `risk_engine.py`, `strategy_decision.py`, `strategy_state.py`: deterministic decision
  and risk gates.
- `trading_bankroll.py`, `earn_manager.py`, `capital_sourcing.py`, `dust_sourcing.py`:
  liquidity and funding policy.
- `live_preview.py`, `live_exit_preview.py`, `oco_protection_preview.py`,
  `oco_status_sync.py`: guarded mainnet and position protection lifecycle.
- `grid_advisor.py`, `rebalancing_bot_advisor.py`: recommend-only Binance bot plans.
- `grid_registry.py`, `rebalancing_registry.py`, `active_strategies.py`: local manual-bot
  registration and monitoring.
- `market_research.py`, `ai_analyst.py`, `shadow_evaluator.py`: local Binance research,
  bounded AI ranking, and outcome evaluation.
- `storage.py`, `reporting.py`: SQLite persistence and Markdown reports.
- `cli.py`: CLI surface and exact guarded confirmation flags.

### Desktop app: `coinductor/`

- `qml/Main.qml`: the current PySide6/QML UI. It is large; inspect surrounding layout
  before editing and test default/minimum window sizes.
- `controller.py`: QML properties, slots, background workers, navigation, and action
  plan composition.
- `application.py`: translates desktop run options into engine runtime configuration.
- `desktop_store.py`: reads the latest SQLite state for the UI.
- `safety_service.py`, `readiness_service.py`, `connection_check.py`: safety and setup
  state.
- `assistant.py`, `ui_knowledge.py`, `assistant_history.py`: AI Assistant routing,
  deterministic help/intents, provider fallback, and local chat history.
- `ai_provider.py`, `local_ai_recommender.py`: provider checks, separate text/vision
  model routing, and hardware recommendations.
- `user_profile_service.py`, `first_portfolio_planner.py`, `app_tour_service.py`:
  onboarding, profile planning, and first-use tour.
- `guide_service.py`: local Help & Guides content.
- `local_data_reset.py`: deletion preview only; execution is intentionally unfinished.

### Local state and generated data

- `.env`: real secrets and provider configuration; ignored by Git.
- `config.example.toml`: current policy/config baseline. Despite the name, it contains
  the active prototype policy and user-specific asset universe assumptions.
- `work/trading_agent.sqlite3`: structured run, order, strategy, and evaluation history.
- `outputs/reports/`: rotated human-readable reports.
- `state/`: onboarding, Safety stage, policy overrides, manual strategy registrations,
  chat history, and UI state. Most mutable files are ignored by Git.
- `research/notes/`: optional manually supplied Binance Skills research.
- `research/requests/`: generated semi-automatic research prompts, rotated by policy.

Do not infer live account state from committed example files. Use explicit read-only
checks and current generated state when the user asks for an actual portfolio decision.

## Current Feature Status

### Implemented and exercised

- Binance mainnet read-only inventory including Spot, Flexible Earn, and Locked balances.
- Binance Spot Testnet account checks and BUY/SELL lifecycle tests.
- Guarded mainnet BUY preview/submit with separate live API key and confirmations.
- Open-position guard, exchange-side OCO preview/submit, status sync, closed-cycle PnL,
  live risk state, cooldowns, and kill-switch inputs.
- Profit-first USDC bankroll accounting, Flexible Earn planning, bounded capital sources,
  dust/airdrop funding recommendations, and protected assets.
- Market research, BTC/ETH bounded AI ranking, AI memory from closed cycles, and shadow
  evaluation without execution authority.
- Spot Grid and Rebalancing recommendations, exact manual parameters, local registration,
  lifecycle status, and periodic monitoring.
- Desktop Flexible Earn redeem: preview, guarded confirmation (`CONFIRM_EARN_REDEEM`), and
  result, surfaced as an Action Plan item alongside the trade and OCO protection cards.
- PySide6/QML desktop shell with Overview, Live Actions, Portfolio, Action Plan, Active
  Strategies, Run History, AI Assistant, Help & Guides, and Settings.
- First-run step-by-step wizard, existing/first-portfolio paths, decision profile, API
  setup, privacy disclosure, readiness state, and first-use product tour.
- Manual portfolio-role overrides with deterministic risk controls preserved.
- AI Assistant history, selectable/copyable messages, file/clipboard image attachment,
  deterministic app knowledge, and safe structured actions.
- Separate `LLM_MODEL` and optional `LLM_VISION_MODEL`. Text messages stay on the text
  model; image messages route to the vision model. Provider health checks validate both.
- Report/research/order-related retention and rotation where applicable.

### Implemented but still needs real/manual validation

- The latest vision-model routing code is tested but no vision model was installed or
  configured during the handoff. The current local text model is Qwen3 14B. A practical
  next manual test is Ollama `qwen3-vl:8b`, then Settings > Configure AI models, provider
  check, image paste, response, history reload, and model-routing verification.
- Current responsive UI has been iteratively tested by the user, but a fresh complete
  Stage A walkthrough is still needed after recent AI Assistant and vision changes.
- Cloud AI remains a generic OpenAI-compatible path. Provider-specific presets, exact
  onboarding, billing guidance, and end-to-end tests are incomplete.
- Active Grid/Rebalancing monitoring is based on local registration and market prices,
  not full Binance bot PnL/execution telemetry.

### Known incomplete Stage A work

1. **Synchronize documentation.** `docs/ROADMAP.md` and
   `docs/COINDUCTOR_STAGE_A_TESTING.md` contain stale claims (for example, product tour
   and desktop guarded submits are now implemented). Update them from code and tests.
2. **AI Assistant reliability.** The structured UI catalog is safer than free-form Qwen,
   but coverage is still finite and paraphrases can fall through to the model. Build a
   maintainable project knowledge/retrieval layer, add broad paraphrase tests for every
   visible control, and keep deterministic answers ahead of model guesses.
3. **Inline wizard AI.** The wizard still says inline Q&A is planned. Add contextual
   ask-AI help that works with an offline deterministic fallback and never blocks setup.
4. **Standalone market questions.** The Assistant currently refuses to invent live
   prices and has no dedicated tool flow for “current BTC price” or a lightweight market
   analysis independent of a full run. Add a deterministic Binance public-data intent.
5. **First portfolio execution path.** The planner exists, but deterministic allocation
   simulation, Testnet validation, staged mainnet previews, and confirmed initial basket
   deployment remain incomplete.
6. ~~**Earn redeem desktop workflow.**~~ Implemented: the Action Plan item detail
   dialog now has a guarded Earn redeem card (preview, `CONFIRM_EARN_REDEEM`
   confirmation, result), mirroring the trade/OCO pattern.
7. ~~**Manual trade override workflow.**~~ Implemented: "Challenge HOLD" on the Action
   Plan trade card lets the user request a BUY evaluation of one `strategy.allowed_symbols`
   entry (`AiAnalyst.propose_manual_override`, `_runtime.manual_override_symbol`). It still
   flows through the exact same `RiskEngine.evaluate()` as any AI proposal — consensus/RSI/
   trend/EMA200, bankroll, kill switch/cooldown, stop-loss, idempotency, and the existing
   `CONFIRM_MAINNET_ORDER` live-submit confirmation all still apply and can still reject it.
8. ~~**Hard local-data deletion.**~~ Implemented: `LocalDataResetService.execute()`
   deletes only the selected groups, resolves every path and refuses anything that
   does not stay under the resolved project root (or resolves to the root itself),
   and wraps each removal in try/except so a locked file is reported rather than
   crashing the app. `executeLocalDataReset(codes, confirmation)` in the desktop
   controller requires typed `DELETE` and is blocked while an analysis is running.
9. **Full UI localization.** `en-US`, `es-ES`, `cs-CZ`, and `pt-BR` locale profiles exist
   for first-portfolio funding text, but most QML UI strings remain English.
10. **Installed-model discovery.** Hardware recommendations and `/models` validation
    exist, but the wizard does not yet offer a polished “detect installed Ollama models
    and select one” flow.
11. **Profiles/accounts.** Multiple Coinductor profiles/Binance accounts are a planned
    nice-to-have, not implemented. Current state and `.env` are single-profile.
12. **Credential storage.** Wizard-managed `.env` is easier than manual editing but is
    not OS keychain storage. Evaluate Windows Credential Manager/keyring before public
    distribution, without breaking portable/local-first usage.

### Stage B: open-source distribution - not started as a release product

- signed Windows installer and reproducible builds;
- dependency bootstrap without requiring users to understand Python;
- publisher identity, checksums, release signing, update/migration strategy;
- sanitized diagnostics bundle;
- polished provider presets and setup documentation;
- dynamic-IP guidance and an optional always-on host path;
- contributor docs, license/repository hygiene, and removal of personal defaults.

Before publishing, split user-specific policy from neutral defaults. In particular,
`config.example.toml` currently contains personal tracked assets, protected roles,
source-asset choices, and small-capital limits developed for the original portfolio.

### Stage C: extended automation - future

- scheduled local runs without keeping the full UI open;
- optional self-hosted always-on worker;
- notifications and review reminders;
- additional exchanges behind the same adapter and safety contract.

## Recommended Next Development Order

1. Perform the dedicated vision-model manual test and fix any UI/runtime defects.
2. Update stale roadmap and Stage A testing documentation.
3. Run a complete Stage A manual regression at default/minimum/large window sizes.
4. Strengthen Assistant knowledge coverage and add standalone read-only market intents.
5. Finish the remaining guarded Stage A workflow: first portfolio staged
   deployment. (Earn redeem, manual HOLD challenge, and hard local-data
   deletion are done as of 2026-07-20.)
6. Only then begin Stage B packaging and public-default cleanup.

Do not jump directly to installer work while core setup and guarded workflows still have
known gaps. The user prefers completing and testing the personal Stage A application
before broad open-source distribution.

## Useful Commands

```powershell
cd D:\CodexWork\binance-trading-agent

# Install desktop dependencies in the active Python environment
python -m pip install -e ".[desktop]"

# Run all tests
python -m pytest -q

# Static import/bytecode check
python -m compileall -q coinductor trading_agent

# Start desktop app
python -m coinductor.desktop

# Safe CLI diagnostics (still inspect flags before running)
python -m trading_agent doctor --config config.example.toml --real-data --ai-commentary
python -m trading_agent readiness --config config.example.toml
python -m trading_agent last-report --config config.example.toml
```

Do not copy guarded submit commands from `README.md` or `docs/RUNBOOK.md` into the
terminal without a fresh explicit user request.

## Git and Editing Conventions

- Branch: `master`.
- No remote is configured.
- Use `rg`/`rg --files` for search.
- Use patch-based edits; do not rewrite unrelated files.
- Preserve user-generated and ignored state.
- Never use destructive Git commands unless explicitly requested.
- Keep commits coherent and descriptive. Recent commits are useful context:
  - `a1c5204 Add dedicated vision model routing`
  - `71e9684 Improve vision setup help and chat text selection`
  - `334d1b5 Generalize assistant app knowledge and clipboard images`
  - `6aec653 Persist AI assistant chat history`
  - `533b9e3 Add guarded AI assistant actions`
- QML regressions frequently involve clipped bottoms, scroll bounds, fixed positions,
  and controls escaping cards. Test responsive behavior, not just QML parsing.

## Suggested Prompt for the New AI Provider

Use this as the first message after giving the provider access to the project folder:

> Continue development of the Coinductor project in
> `D:\CodexWork\binance-trading-agent`. First read
> `docs/AI_PROVIDER_HANDOFF.md`, then inspect `README.md`, `docs/ROADMAP.md`, the last
> five Git commits, and the working-tree status. Do not read aloud or expose `.env`, do
> not execute any live Binance action, and do not change the Safety stage. Run the test
> suite and summarize your understanding, current risks, and the next recommended task
> before editing. Communicate with me in Czech. Preserve deterministic safety gates and
> treat AI as advisory only.

After the new provider summarizes the project, ask it to start with one item from
"Recommended Next Development Order," not the entire backlog at once.
