# Changelog

Notable changes per release. This project follows [Semantic Versioning](https://semver.org),
and is pre-1.0: minor versions may still change behaviour.

## [0.1.4] — 2026-07-28

Found by installing 0.1.3 and working through a real portfolio.

### Added

- **The Binance setup procedure is in your language.** Binance has no public API
  for creating trading bots, so those numbered steps are the one thing the app
  cannot do for you - and they were the last English text left in a translated
  UI. The advisors now emit each step as a key plus its parameters instead of a
  finished sentence, so the Markdown report stays English while the dialog
  speaks your language. Amounts, prices and Binance's own control labels
  ("Equal", "By Ratio", "OFF") are left verbatim, because you have to find them
  in Binance's interface exactly as written.

### Fixed

- **The Binance badge stayed on "Not checked" after a successful analysis.** A
  real run authenticates and reads your account, so it is better evidence than
  the check button - but only that button ever cleared the badge, which left
  another trip through the wizard as the only way to do it. This affects the
  readiness display only; permission to place orders still comes from the
  live-key check and the safety stage.
- **A blocked Rebalancing Bot read like an instruction to set it up now.** Its
  steps keep the parameters on purpose, because a funding shortfall is a
  blocker you can actually clear - unlike the grid, whose blocker is a market
  condition and whose price range would be stale by the time it lifts. But the
  numbered list ran straight from "do not create this yet" into the settings to
  enter, with nothing marking where one ended and the other began.
- **Switching language left the Action Plan in the previous one.** The cards are
  built once and cached, and nothing rebuilt them on a language change, so they
  kept the language of the last analysis until you ran another one.

### Upgrading

Runs recorded by 0.1.3 keep their setup steps and still display them in English:
they were stored as finished sentences, with no key left to translate. Run a
fresh analysis to get the procedure in your language.

## [0.1.3] — 2026-07-28

Found by installing 0.1.2 and using it as a new user would.

### Added

- **The manual bot setup steps are in the app.** The Action Plan dialog handed
  over parameters to retype on Binance with no procedure to retype them into -
  the numbered steps existed only in the Markdown report, because neither
  recommendation table had a column for them.
- **Bot cards say why setup is manual.** Binance has no public API for creating
  trading bots; without that, a list of steps to perform by hand reads as an
  unfinished feature. Shown in the app in your language, and in the report.
- `config.toml` is its own group under Delete local data, off by default: it
  holds hand-tuned risk limits, so it is the one thing worth keeping while
  clearing everything else.

### Fixed

- **Export diagnostics looked like it did nothing.** It wrote the file correctly
  but named a path relative to the working directory, which for an installed
  build is a folder nobody has reason to know. The path is now absolute and the
  file opens.
- **"Delete everything" left the diagnostics bundle behind**, on a screen that
  calls that selection a full local reset.
- The locale picker was labelled "Language / region" while only setting region
  and fiat currency, so es-ES read as a promise of a Spanish interface. It is now
  "Region and fiat currency"; the interface language stays its own switch.
- The uninstaller's first checkbox was clipped at the default window width -
  a checkbox caption does not wrap, so the detail is now a label beneath it.
- The antivirus guidance recommended excluding a versioned installer filename,
  which stops matching on the next release.

## [0.1.2] — 2026-07-27

Found by installing 0.1.1 and walking it as a new user would.

### Fixed

- **The safety stages could not be reached at all on a quiet market.** Arming required a
  past `PREVIEW_READY` live order, which only exists when the analysis returns something
  tradable - so on a HOLD day a user could never progress to live, no matter what they did.
  It guarded nothing: the engine submits only when the preview it computes in that same run
  comes back ready, validated against Binance. Every real gate is unchanged.
- **The guided next step had no way to add a live key.** It jumped straight to verifying
  one, which without a key answers "not configured" and leaves the user to find the dialog
  themselves. Key setup also no longer waits behind the market-dependent preview step.
- **The Action Plan trade card showed the run's decision as the trade's verdict** - reading
  `GRID_BOT_RECOMMENDATION` while Action said `HOLD`, colouring a plain HOLD as blocked, and
  hiding the submit button for an approved BUY whenever a grid was recommended too.
- **Scan hardware froze the window and flashed console windows.** It ran on the GUI thread
  and shelled out without `CREATE_NO_WINDOW`.
- **An empty Portfolio table looked like a failed load.** Connecting a key fetches nothing;
  the table shows the latest real run. It now says so and offers the run.
- The analysis button in Live Actions gave no sign it was working.
- The Guarded Action Center implied three different jobs; all three run the same analysis
  and differ only in whether a mainnet preview is prepared.
- Trade card labels were hardcoded English in the Czech UI.

### Changed

- **The uninstaller asks once, up front, with checkboxes** for local data and API keys,
  instead of a chain of Yes/No prompts where "No" read as if it might cancel the uninstall.
  Nothing ticked removes the program only.
- The README leads with what Coinductor is for, and documents third-party antivirus
  behaviour - Avast blocking the installer or sandboxing it is a reputation signal for an
  unsigned build, not a fault, and it does not explain itself.

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
