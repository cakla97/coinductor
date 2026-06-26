# Coinductor Roadmap

Coinductor is moving from a personal CLI prototype to a local-first desktop
application. Deterministic policy code remains responsible for permissions, limits,
and execution. AI may explain, summarize, and rank bounded options, but it cannot
bypass those controls.

## Stage A: Personal Desktop Application

### A1. Desktop foundation - complete

- PySide6/QML application shell
- background analysis without freezing the UI
- latest real-run dashboard and report access
- Portfolio, Strategies, Run History, and offline help views

### A2. Settings and onboarding - in progress

- local setup checks that never reveal API secrets
- separate paths for an existing portfolio and a first portfolio
- guided Binance read-only, Testnet, live-key, and AI-provider setup
- explicit network checks only after user action
- local configuration editor with validation and safe defaults

### A3. Existing portfolio onboarding

- connect read-only Binance access
- run the first complete portfolio inventory
- review and edit asset classification with manual per-asset policy overrides
- approve trading, Grid, funding, protected, legacy, and dust universes
- simulate policies on Testnet before enabling guarded mainnet actions

Manual asset overrides may change whether an asset is eligible for trading, Grid,
Rebalancing, funding, or dust conversion. They must not disable global risk
limits, protected-asset checks, OCO requirements, or loss kill switches.

### A4. Build my first portfolio

This path is for a user who starts with no crypto portfolio.

1. Choose a planned USDC budget, time horizon, and risk profile.
2. Keep a configurable USDC reserve outside the initial allocation.
3. Select an auditable portfolio template such as Conservative, Balanced, or Growth.
4. Simulate the allocation and staged entry plan without placing orders.
5. Validate the same plan on Binance Spot Testnet where supported.
6. Create mainnet buy previews split across multiple entries rather than one immediate purchase.
7. Require explicit confirmation for every initial live deployment step.
8. Enable Grid or Rebalancing only when their minimum capital and risk conditions are met.

Portfolio templates will be deterministic and versioned. AI can explain trade-offs
or help choose among eligible templates, but cannot invent unrestricted allocations.
The application must present this as an automation plan, not a promise of profit.

### A5. AI provider layer

- offline project-help assistant remains available without a model
- local OpenAI-compatible endpoint for private summaries
- optional user-supplied API keys for supported cloud providers
- clear disclosure of which data leaves the computer
- provider health checks, timeouts, and deterministic fallback

### A6. Desktop execution workflows

- preview-first trade, Earn redeem, and OCO protection screens
- human-readable guard failures
- explicit confirmation phrases for submissions
- manual Binance Grid/Rebalancing creation instructions and local registration
- guarded manual trade intent overrides that can challenge a HOLD signal but
  still must pass funding, exposure, stop-loss, and kill-switch checks

## Stage B: Open-source Distribution

- signed Windows installer and reproducible release process
- first-run dependency and hardware checks
- optional local-model recommendations based on available hardware
- guided updates and configuration migration
- documentation for dynamic IP, API restrictions, and remote operation
- sanitized diagnostics bundle for support

## Stage C: Extended Automation

- scheduled local runs without keeping the full UI open
- optional self-hosted always-on worker
- notifications and review reminders
- additional exchanges only behind the same deterministic safety contract
