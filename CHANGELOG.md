# Changelog

Notable changes per release. This project follows [Semantic Versioning](https://semver.org),
and is pre-1.0: minor versions may still change behaviour.

## [0.1.1] — 2026-07-27

Fixes found by installing 0.1.0 and using it as a new user would. 0.1.0 was
never published; do not use it.

### Fixed

- **Connection checks could never pass on a fresh install.** Read-only, Testnet
  and live checks all refused to run unless a `.env` file existed, then reported
  "keys are not configured" - for keys sitting in Windows Credential Manager.
  A packaged install has no `.env` at all. They now resolve credentials first
  and report on what they actually found.
- **An installed build analysed the example portfolio and presented it as a
  result.** No `config.toml` was created, so the app fell back to the bundled
  template, which ships `mock_data = true` so the repository runs offline. The
  Action Plan therefore showed figures from a fixed sample portfolio while
  Binance was not even connected. A real `config.toml` is now written on first
  start, with `mock_data = false`, and the template is left untouched.
- **Saving the decision profile edited the bundled template**, for the same
  reason.
- The test suite could reach the live Binance API: a throwaway `.env` written by
  one test leaked into `os.environ` for every test after it. Credentials are now
  cleared per test.
- Two Qt test modules and one keychain test assumed a Windows machine, so the
  suite could not run on Linux without the desktop extra.

## [0.1.0] — 2026-07-26

First public release. Windows desktop app plus the headless engine and CLI.

### Added

- **Desktop app** (PySide6/QML): portfolio overview, live actions, action plan, active
  strategies, run history, AI assistant, in-app guides and settings, in English and Czech.
- **Setup wizard** that never touches the exchange — it writes a local profile and shows
  what still needs verifying.
- **Safety stages** (`SETUP` → `PREVIEW_ONLY` → `ARMED` → `LIVE_ENABLED`), each raised by
  hand with a typed confirmation, plus a one-click **Lock live submit**.
- **Decision profile** that materialises into `config.toml`: management style moves the
  consensus trend gates, drawdown comfort moves the daily/weekly loss caps, automation level
  and the spot-trade switch veto live submission.
- **Credential storage** in the OS credential store (Windows Credential Manager), with a
  plaintext `.env` fallback only when no store is available.
- **AI provider support**, local (Ollama and similar) or cloud, always advisory: the model
  proposes, `RiskEngine.evaluate()` decides.
- **Delete local data** in Settings, covering state, database, reports, research, chat
  history and the stored API keys.
- **Windows installer** (per-user, no admin) and a **portable ZIP**, with `SHA256SUMS.txt`.
  The uninstaller offers to remove your data and keys, defaulting to keeping them.
- Binance Spot Testnet execution path, mainnet preview, guarded live submit with OCO
  protection, rebalancing preview, Spot Grid and capital-sourcing advisors.

### Known limitations

- **Builds are unsigned.** Windows SmartScreen warns on first run; verify the SHA-256 from
  `SHA256SUMS.txt`. See [SECURITY.md](SECURITY.md).
- **Windows only** for the packaged builds. The engine and CLI run anywhere Python does.
- **One AI provider at a time.** Local and cloud share the same settings; saving one replaces
  the other.
- Spot Grid bot creation stays recommend-only — Binance has no public API for it.
- Guarded desktop submit supports BUY previews only.
