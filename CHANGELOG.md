# Changelog

Notable changes per release. This project follows [Semantic Versioning](https://semver.org),
and is pre-1.0: minor versions may still change behaviour.

## [0.1.10] — 2026-07-29

First public release of the repository.

### Fixed

- **One unusable field no longer loses the whole AI proposal.** Models answer "high" or
  "0.72 (strong)" where a number was asked for; `Decimal(str(value))` raised on that and
  the Trade card reported the loss as `[<class 'decimal.ConversionSyntax'>]`. The value is
  salvaged when the text contains a number and otherwise takes the conservative end.
- **The funding plan asked for a zero conversion.** When no allowed source asset can
  contribute anything, "convert about 0.00 from allowed sources" was the instruction. That
  case now says the gap cannot be covered and names the two honest options.

### Added

- **What to expect from the AI**, in the README and the in-app guide. A local model may
  ignore the requested format and return no commentary, answer in the wrong language, or
  have its trade opinion discarded — none of which touches the analysis, and all of which
  reads like a broken app if nobody says so first.
- **A note on Binance account access.** Coinductor uses the API from your desktop and never
  the mobile app, so mobile availability is irrelevant to it; what matters is an account you
  can create an API key on, and that varies by country.

### Changed

- `outputs/diagnostics/` is git-ignored. A diagnostics bundle names your home directory and
  app state, and is written to be sent to a maintainer — it was the file most likely to
  carry personal detail and the one that could still be committed by accident.
- The two internal working documents are gone and the roadmap says where the project
  actually is. Neither had been updated as the code moved, and a stale internal doc is
  worse in a public repository than no doc.

## [0.1.9] — 2026-07-28

The Action Plan is in one language, and the reason it kept not being is fixed
rather than patched again.

### Changed

- **The engine no longer writes finished sentences.** Every localization round
  so far fixed one screen and revealed the next, because a sentence with its
  numbers already baked in can only be re-translated by parsing English prose
  back apart. The producers emit a key and its parameters instead, and the text
  is composed once per reader — English for the Markdown report, your language
  for the app. This now covers the grid's scoring line and both advisors'
  blockers, the next-review reason and its triggers, and every recommended
  action with the explanation under it.
- **The Overview action list is read from the journal**, not parsed back out of
  the report with a regex. By the time the report exists its sentences are
  already English, which is why nothing in that list could ever be translated.
- **Blockers are no longer squeezed into a parameter tile.** They are sentences,
  and beside "Grids: 8" a sentence can only be cut off — which is why shortening
  the text kept not being enough. They have their own full-width wrapping
  section.

### Fixed

- The navigation, the Live Actions and Action Plan titles, and the safety
  caption had Czech entries that were copies of their English. A copied string
  passes every automated check there is, so it took someone reading the screen;
  auditing all three tables at once found 34 such entries, about a dozen of them
  real.
- The recommended actions and the next-review panel were composed once when a
  run loaded and never recomposed, so switching language left them in the
  previous one. That makes four places with the same cause.

### Added

- Tests that read the producers rather than a list kept by hand: every message
  key the engine can emit must have text, every parameter label and decision
  type must be mapped, no table entry may be a silent copy of its English, and
  no new prose may be assigned to a user-facing field in a converted module.
  Each of these failure modes was invisible at runtime, because all of them fall
  back to English rather than failing.

### Upgrading

Nine columns are added to the journal on first start; existing runs are left
alone and keep displaying in English, since they were stored as finished
sentences with no key left to translate. Run a fresh analysis to see the Action
Plan in your language.

### Known limitations

- The risk engine's verdict and the active-strategy evaluator's advice are still
  prose. Neither appears on the Action Plan — the first is behind "Why HOLD?",
  the second only once a bot is registered.

## [0.1.8] — 2026-07-28

0.1.7 was built but never published; use this instead.

### Fixed

- **One decision type was showing in English.** The engine reports a spot-trade
  run as `SPOT_TRADE_RECOMMENDATION`; the display map keyed it as `SPOT_TRADE`,
  so that one case fell through to the generic fallback and read "Spot trade
  recommendation" on a Czech screen. Only visible on a run that proposes a spot
  trade, which is why it survived testing.

### Added

- **The translation tables are now checked against what feeds them.** Each of
  them falls back to English rather than failing — right at runtime, and exactly
  why the gap above was invisible: a value added later simply appears
  untranslated and nothing says so. The tests read the producers themselves (the
  label literals in the journal reader, the branch codes, the decision enums
  across the engine) rather than a list kept by hand, so adding a value without
  its translation now fails the build.

## [0.1.7] — 2026-07-28

Found by reading the Action Plan the way anyone reads a screen — by skimming it.

### Fixed

- **The same paragraph was printed three times.** The Spot Grid blocker added in
  0.1.6 ran to 317 characters, named two config keys, and was repeated verbatim
  in the card summary, the blockers field and the next-review panel — 817
  characters on one card, which is not something anyone reads. The blocker is
  one fact now (73 characters), what to do about it is a setup step, and neither
  advisor inlines its blockers into the summary any more. The grid's scoring
  line lost the words carrying no information: 500 characters to 119.
- **The Action Plan showed one screen in two languages.** The Trade card builds
  its labels in the app and was translated; the Spot Grid and Rebalancing cards
  take theirs from the journal reader, which has no language, so they read
  "Symbol / Range / Grids" beside "Akce / Symbol / Jistota". The next-review
  panel had the same split.
- **Two things were never re-read on a language change.** The Active Strategies
  subtitle — translated in 0.1.5 — kept whatever it resolved to at startup,
  because the signal it depends on was not emitted; and the next-review panel is
  composed when a run loads and nothing recomposed it.
- **AI commentary came back in English beside a Czech screen.** It is the model's
  own prose, so it cannot be translated afterwards the way the app's text is.
  The run now carries the interface language and asks for it.

### Changed

- The antivirus guidance no longer claims the temporary-path exclusion prevents
  the problem. Tested with it in place and matching exactly, Avast sandboxed the
  installer anyway — its Exceptions list does not appear to govern Autosandbox.
  If the first attempt fails, run the installer again; that is what works.

### Known limitations

- **Recommended actions are still English.** Their headline could be translated
  on its own, but the explanation under each one is borrowed from five other
  parts of the engine, so doing half of it would produce exactly the mixed
  screen this release removes elsewhere. It needs the same treatment the setup
  steps got in 0.1.4, as its own change.

## [0.1.6] — 2026-07-28

Found by following the app's own Spot Grid instructions on Binance.

### Fixed

- **The app recommended a grid Binance would refuse to create.** Binance rejects
  any order under 5 USDC, and the shipped defaults fund a grid at 2.50 per
  level — so the recommendation could not place a single order. It was handed
  over with full parameters anyway, and the only way to find out was to fill in
  Binance's form and be told the minimum was more than double. The exchange
  minimum is now enforced whatever the config says, and a grid that cannot meet
  it is blocked with the amount required and the setting to change. Defaults are
  deliberately unchanged: with them a grid is not fundable, and raising someone's
  capital commitment to make a recommendation appear is not the app's call.
- **The setup procedure told you to hand-edit a TOML file.** Step 11 asked the
  reader to copy `state/active_strategies.example.toml`, rename it, and fill in
  values. The app has had a registration dialog since active-strategy monitoring
  was added — Active Strategies → Register active bot → Import latest
  recommendation — and the step simply never pointed at it.
- **Indicators were printed at full computed precision**, so a HOLD was explained
  with `RSI=43.384672227767928463538468495` in the middle of the sentence.
- **Values could not be copied.** Every price, count and threshold in the Action
  Plan exists to be reproduced in Binance's form, and the only way to move one
  was to retype it.

### Changed

- The trading pair is written the way Binance's own picker shows it — `ETH/USDC`,
  not `ETHUSDC` — because that is what you are matching against by eye.
- The Trade card says "A Spot Grid was recommended" rather than
  `GRID_BOT_RECOMMENDATION`, and explains a HOLD in a sentence instead of
  `trend=RISK_OFF`. The stored values stay as they were; only the display
  changed.
- The setup procedure can be copied whole, and individual steps selected.
- README opens with a nav row covering Install and Support the project, and the
  "not financial advice" disclaimer sits at the top rather than only at the
  bottom of a long page.

## [0.1.5] — 2026-07-28

Found by upgrading 0.1.3 in place and working through the app afterwards.

### Fixed

- **An unconfigured AI provider was reported as a model that answered badly.**
  With nothing set up — the default state — the AI summary read "the model
  response was not usable (RuntimeError)", naming a response that never
  existed and a Python exception class, so anyone who had never configured AI
  went looking for a broken model. The trade proposal was quieter and worse: it
  simply returned the deterministic verdict, so ticking "AI proposals" gave an
  answer with nothing saying where it came from. Both now say plainly that no
  provider is configured, and a genuine failure keeps its actual cause.
- **Run History showed every run in UTC.** SQLite records the start time with no
  offset and the list printed it verbatim, so runs looked hours old — while the
  Action Plan's next-review line, which already converted, disagreed with it on
  the same screen.
- **A past run's report could not be opened.** Thirty runs were listed and the
  only report reachable anywhere in the app was the newest one, from the Action
  Plan.
- **Text that appears only after an action was still English in a Czech app**:
  the eight completion toasts, the Active Strategies subtitle and its
  pending-evaluation note. All are composed in Python the moment a run finishes,
  which is how they outlived every earlier localization pass.
- **"Refresh monitoring" gave almost no sign it was working** — a swapped label
  that then sits still for the whole run — on a button that quietly starts a
  full analysis. It now spins, and says what it does on hover. The Overview
  analysis button spins too.

### Changed

- The installer states `CloseApplications` explicitly. Upgrading over a running
  Coinductor already offered to close it rather than demanding a reboot, but as
  an Inno Setup default a future change could have taken it away silently.
  Restart Manager no longer relaunches the app, since the installer's own final
  step already offers to.
- The antivirus guidance names the temporary path a scanner actually inspects.
  The download is a loader that unpacks the real installer into
  `%LOCALAPPDATA%\Temp\is-*.tmp\` and runs that, so excluding the downloaded
  file never covered the process being sandboxed — and a sandboxed installer
  completes its wizard while writing nothing, leaving the previous version
  installed with no sign anything went wrong. The pattern includes the filename
  on purpose: that folder is Inno Setup's generic scratch directory, and
  excluding it alone would exempt every installer built with Inno Setup.

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
