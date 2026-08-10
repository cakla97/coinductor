# Changelog

Notable changes per release. This project follows [Semantic Versioning](https://semver.org),
Since 1.0.0, a breaking change to the config format, the journal schema, or a safety
default takes a major version.

## [1.4.2] — 2026-08-10

### Fixed

- **The unattended-funding switch is now on the screen it belongs to.** 1.4.0 added a whole
  Earn funding panel and left `auto_funding_enabled` readable only in `config.toml` — the
  one file this app promises nobody has to open. It is a checkbox on that panel now, with
  what it does spelled out beside it, and turning it on or off says which it did rather
  than reporting "saved".
- **Turning it on below `LIVE_ENABLED` now says so.** It was already ignored there, which
  meant a switch that silently did nothing. The panel warns while it is on but cannot act.
- A config written before the switch existed gains the key when the toggle is used, rather
  than accepting the change and discarding it.

### Notes

Nothing about when or how much moves changed. Off is still the default, absence still reads
as off, and the limits and safety stage still apply exactly as in 1.4.0.

## [1.4.1] — 2026-08-10

1.4.0 shipped two panels the built-in assistant knew nothing about.

### Added

- **The offline assistant answers questions about everything added since 1.3.0** — order
  sizing, Earn funding, automatic funding, the suggested limits, why an order came out the
  size it did, and how to update. In both languages, as the rest of it already was.
- Two of those entries correct assumptions worth correcting unprompted: **a redemption is
  not a withdrawal**, and **automatic funding does not fund a Grid or Rebalancing bot** —
  those are recommend-only because Binance has no public API to create them, so the money
  would move and the bot would still have to be made by hand.
- **An *Updating* section in the README**, and the same answer in the assistant: quit a
  running Coinductor from the tray before installing. The single-instance guard only
  recognises instances that have it, so an upgrade is the one case where two can run.

### Fixed

- **"Why is it like that" never reached the assistant's knowledge at all.** The question
  gate recognised `why cant` but not plain `why is` or `proc je`, which is how anybody asks
  about a limit — the whole category fell through.
- **Czech typed without diacritics was often answered in English.** The language check
  relied on a short word list, so a question like *k čemu je automatické financování* did
  not read as Czech.
- **Aliases now match Czech declension.** Matching is by substring and Czech declines, so
  `aktualizace` never matched *aktualizaci*.
- The Live Actions tour step described a page that had since grown two panels.

### Notes

Nothing about trading, sizing or funding behaviour changed. The widened question gate is
covered by a test asserting that an unrelated question is still left to the model rather
than answered from a fixed entry.

## [1.4.0] — 2026-08-10

Coinductor can now pay for what it approved, within limits that finally hold.

### Added

- **A run can move Earn to Spot on its own**, when an approved action is already waiting on
  the money. The plan was always built automatically; only the transfer waited, for a
  phrase a schedule can never type — so unattended runs could never fund anything.

  This is a **separate authority**, not a loosening of the existing one. A manual redeem
  still requires `CONFIRM_EARN_REDEEM` typed for the amount in front of you. The automatic
  one requires a switch turned on once **and** the `LIVE_ENABLED` safety stage, reached by
  hand on screen; an unreadable stage is not permission. Off by default.

  A redemption is not an order and not a withdrawal: it moves USDC between parts of one
  account, changes no exposure, can lose nothing to the market, and reverses by
  subscribing again. **Nothing here changes how an order is authorised.**
- **An Earn funding panel in Live Actions**, so the setting that decides whether an
  approved action can be paid for at all is no longer readable only in `config.toml`. Kept
  as its own card, because sizing decides how large an order is worth making and this
  decides how much of your savings the app may reach for.
- **Suggested limits, derived from your portfolio**, on both the sizing and funding panels,
  with a button that applies them. Percentages are suggested as constants — that is the
  point of a percentage — while the flat backstops scale, and are placed well above where
  the percentage binds.
- **Every percentage now shows what it is worth in money**. `3%` and `26 USDC` land very
  differently, and only the second says whether the number you typed is sane.

### Fixed

- **`earn.max_redeem_per_day_usdt` now does something.** It appeared in the validator and
  a test fixture, and no code ever compared anything to it — a daily cap that guaranteed
  nothing. On a two-hourly schedule the per-run limit is twelve times weaker than it looks.
  The day's spend is read from the journal and folded into the per-run bound, so a run is
  sized against the allowance actually left. Only submitted redemptions count; a plan that
  was prepared and never confirmed moved no money.
- **Both Earn limits scale with the portfolio.** Each gained a percentage companion and the
  smaller wins, matching what the order size gained in 1.3.0. The template leads with the
  percentage and keeps the flat amount as a backstop.

### Notes

The daily limit had to start working before the automatic transfer could be offered:
without it, an unattended run bounded only per-run would have had no daily ceiling at all.

Upgrading changes nothing on its own. Automatic funding is off, an absent percentage means
no extra ceiling, and an absent daily cap means no daily limit — which is how every config
written before this behaved.

## [1.3.0] — 2026-08-10

Order size stops being a flat number in a file nobody was meant to open.

### Added

- **Order sizing is derived from the portfolio.** The approved amount is now the smallest
  of what you allow as a share of the portfolio, what the risk limits permit, what the
  analyst proposed, and **what the account can actually pay** — that last one is new, and
  it is why a trade the balance could not fund used to be approved at a size that only
  failed later, against the exchange minimum.
- **`strategy.max_trade_pct_of_portfolio`**, the portfolio-relative companion to the flat
  `quote_amount_usdt`. The shipped template now leads with the percentage and keeps the
  flat amount as a backstop, so the same configuration behaves sensibly on a 500 account
  and a 50,000 one.
- **An order-sizing panel in Live Actions**, below the existing cap, with each setting
  spelled out in terms of what raising and lowering it does. Three of these settings were
  previously readable only by opening `config.toml`.
- **The journal records which ceiling decided the size** (`risk_decisions.binding_limit`),
  and the panel says so in the current language. Added by migration, so existing journals
  open unchanged and simply read as empty.

### Fixed

- **`risk.max_position_pct_per_asset`, `max_total_trading_capital_pct` and
  `max_risk_per_trade_pct` now do something.** They were validated on load, written by the
  wizard, displayed in the app, and read by no engine code at all. The README already
  listed "position caps" among the checks a buy runs through; that sentence is true for
  the first time.
- **An Earn redemption limit no longer caps trade size.** `earn.max_redeem_per_run_usdt`
  is how much Flexible Earn one run may release, and it was bounding orders even when the
  money came entirely from Spot and no redeem was going to happen. It also silently
  truncated confirmed first-portfolio tranches to a number the user never agreed to. Where
  it genuinely applies it is already accounted for, in what the account can pay.

### Notes

The percentage ceilings bound **one order**, not the position it builds towards: what is
already held is not part of the arithmetic, so repeated buys can accumulate past
`max_position_pct_per_asset`. The panel and the config template both say so. Making them
position-aware is a separate change, and a larger one.

Nothing here loosens what may reach an exchange. The per-run Earn draw, the reserve, and
`live_confirm.max_quote_amount_usdt` are all unchanged.

## [1.2.1] — 2026-08-09

Three things the automation got wrong once it had been left running for a week.

### Fixed

- **Launching Coinductor again now returns to the running one** instead of starting a
  rival. The tray's *Open Coinductor* always worked, because it is inside the app; the
  desktop shortcut had nothing to find it with, so a second click built a second schedule,
  a second listing watch and a second writer for one journal. The duplicate schedule was
  the visible half — the half that mattered is that a limit enforced per run or per window
  was being enforced once per process.
- **The Automation page's next-run time now moves when a run happens.** The timer was
  always firing on schedule; the label was derived from it only when something said the
  settings had changed, and a tick said nothing. It showed the run that had just finished,
  which read as a schedule that had stopped.
- **The Windows scheduled task's time survives a restart.** The chosen time was held in
  memory and rebuilt as the 07:30 default on every launch, so from the second launch
  onwards the panel reported 07:30 whatever was really registered — and said the same to
  anyone who had set the time in Task Scheduler rather than in Coinductor. It is now read
  back from the task itself, out of its XML definition, whose tag names are not localised.

### Changed

- The README no longer sends anyone to a text editor to look around the app before
  connecting an account: **Run analysis** has a `REAL`/`MOCK` data source, chosen per run.
  Editing `config.toml` is now described as what it is — how the headless CLI is
  configured, not something the desktop app asks of anyone.

## [1.2.0] — 2026-08-01

The analysis can now run on its own. An order still cannot.

### Added

- **A schedule for the analysis**, as an addition to the Run analysis button and never as
  a replacement — that dialog behaves exactly as it always has, including for anyone who
  never turns this on. A scheduled run cannot submit: the tests assert that the arguments
  which authorise a submission never reach it at all.
- **A tray icon** with Open, Run analysis now, and Quit. Closing to the tray is tied to
  the schedule: a schedule that stops when you close the window is not a schedule, and an
  app that lingers unannounced while holding exchange credentials is a surprise nobody
  should get.
- **A Windows scheduled task**, running this same executable with `--run-once` and no
  window, so the analysis happens with Coinductor closed. That path loads no GUI toolkit
  at all. A run missed because the machine was off happens as soon as it is next on, and
  what ran while you were away is reported when you return.
- **A new-listing watcher** that records and notifies and **never buys**. Buying a listing
  at market in its first minutes is a losing trade from a desktop app; the first seconds
  belong to bots beside the exchange. Its page says so, and offers one deliberate step —
  allow this pair to be analysed — rather than a buy button. From there the ordinary
  analysis, risk checks, funding check and typed confirmation apply as they do for any
  pair.
- **An Automation page** gathering everything that starts on its own, with the wall-clock
  time each runs next. All of it is off on a fresh install.

### Changed

- **The order size cap moved to Live Actions**, beside the safety stage. The stage decides
  whether an order goes and the cap decides how big; someone enabling live trading should
  meet both at once rather than find the second later, after a toast has told them their
  order was quietly truncated.
- The app tour covers the two new pages, and no longer describes Settings as holding what
  has moved off it.

### Notes

`coinductor/standing_authorisation.py` is complete, proven by 22 tests written before it,
and **connected to no submit path**. The reasoning is in `docs/automation-proposal.md`:
connecting it would mean the app typing the confirmation a person types, which does not
add a gate but replaces the one the design rests on. It is one deliberate change away,
and that change has not been made.

Released after four internal release candidates; what testing them found is below.

## [1.2.0-rc4] — 2026-08-01

Not a public release.

### Fixed

- **The order size cap panel drew on top of the page title**, for the second release
  running. The first fix gave it a grid row it was never going to use: the real problem
  was that it had landed inside another card's `Rectangle`, which is not a layout, so its
  `Layout.*` properties did nothing and it sized to zero. Nothing about that is invalid
  QML, so there were no warnings either time. What misled me twice was indentation — the
  block sat at a sibling's indent while nested a level deeper. Measured this time
  (`y=0 h=0 w=0` beside a working card at `y=657 h=330 w=936`), then located with a brace
  matcher that skips strings and comments. That matcher is now a test.
- **The tray notification was cut off mid-word** by Windows. Shortened to what has to
  survive truncation, with a length assertion so the next edit cannot overflow it again.

## [1.2.0-rc3] — 2026-08-01

Not a public release. Everything from rc2, plus what testing it found.

### Fixed

- **Closing the window left an invisible process behind.** `quitOnLastWindowClosed` was set
  False once at startup so hiding to the tray would not end the app; without a schedule
  that meant every close left a process with no window and no tray icon, holding exchange
  credentials and the executable an installer wanted to replace. Found by an installer
  refusing to continue. The flag now follows the tray in both directions. With a schedule
  on, the app is *meant* to keep running, so hiding now says so and how to quit.
- **The order size cap drew on top of the page title.** Live Actions is a grid where every
  child declares its row; the panel moved there declared none, so it landed on row 0. Zero
  QML warnings throughout, because nothing about it is invalid — it is just wrong. A sweep
  now confirms no other child of an explicit-row grid is missing one.
- **"Watching N pairs" kept the language of the last scan.** Stored as a finished sentence
  instead of composed when read — the third time that shape has bitten, so it is a key and
  parameters like everything else.
- **The tour said "Delete local data" was a preview that would not be executed.** It calls
  `rmtree`, `unlink`, and clears the OS keychain. Telling someone a destructive action is
  safe is worse than saying nothing; a test now holds the claim against the code.
- **Rows an earlier build wrote into the listings table are cleared once.** They were a
  baseline, not listings, and showed as hundreds of pairs listed years ago. The repair
  touches only that display table — the detection baseline, runs and history are untouched.

## [1.2.0-rc2] — 2026-07-31

Not a public release. Everything from rc1, plus what testing it found.

### Fixed

- **The listing watcher reported hundreds of false new listings.** The baseline of what is
  already on the exchange lived in the table the retention cap prunes, so the cap
  discarded most of it — and every discarded pair looked new again on the next pass.
  Against 600 real pairs that was 400 false listings on the second scan, which at a
  fifteen-minute interval is a flood of notifications about pairs listed years ago. Found
  by a tester asking what "watching 200 pairs" was supposed to mean; the honest answer was
  that it was the cap talking, not the exchange.
- **A run missed because the PC was off was silently skipped**, contradicting what the
  proposal claimed. `schtasks` has no flag for it and `StartWhenAvailable` defaults to
  false — verified on a real task rather than assumed — so the task is now amended after
  creation. A missed 07:30 runs as soon as the machine is next on.
- **The app tour still described the nine pages it was written against**, walking a new
  user past two sections without mentioning either, and describing a Settings page that no
  longer holds what it said. A test now ties the tour to the navigation in both directions.

### Changed

- **An Automation page** gathers everything that starts on its own — the in-app schedule,
  the Windows task and the listing watch — with the wall-clock time each runs next. Both
  schedule panels moved there from Settings.
- **The order size cap moved to Live Actions**, beside the safety stage. The stage decides
  whether an order goes and the cap decides how big; someone enabling live trading should
  meet both at once rather than find the second later, after a toast has told them their
  order was quietly truncated.
- The scheduled task's next run and status are shown in the app, so nobody needs a
  terminal to see what they scheduled. "Check now" has a busy indicator.

## [1.2.0-rc1] — 2026-07-31

Not a public release. Built from `feature/automation` for testing before anything
reaches `master`.

### Added

- **The analysis can run on a schedule**, as an addition to the Run analysis button and
  never as a replacement — that dialog behaves exactly as it always has, including for
  anyone who never turns this on. A scheduled run cannot submit: the tests assert that the
  arguments which authorise a submission never reach it at all, and it does not take the
  window away from whoever is using it.
- **A tray icon** with Open, Run analysis now, and Quit. Closing to the tray is tied to the
  schedule: a schedule that stops when you close the window is not a schedule, and an app
  that lingers unannounced while holding exchange credentials is a surprise nobody should
  get.
- **Windows scheduled task**, registered from Settings, running this same executable with
  `--run-once`. That path loads no GUI toolkit at all — on a session without a desktop,
  importing one can fail outright. The panel tells you the `schtasks` command to inspect or
  delete it yourself, because the task outlives this app.
- **A report of what ran while the window was closed.** A schedule whose results simply
  appear in Run History with nothing to announce them feels broken even when it worked.
- **A new-listing watcher** that records and notifies and never buys. Its first pass stores
  the existing exchange as a baseline and reports none of it; an outage is reported rather
  than swallowed; one base asset against eight quotes is one listing.
- **A listings page** that says what it is not, and offers one deliberate step — allow this
  pair to be analysed — rather than a buy button. From there the ordinary analysis, risk
  checks, funding check and typed confirmation apply as they do for any pair.

### Notes

`coinductor/standing_authorisation.py` is complete and proven by 22 tests written before
it, and is **not connected to any submit path**. The reasoning is in
`docs/automation-proposal.md`: connecting it would mean the app typing the confirmation a
person types, which does not add a gate but replaces the one the design rests on, and the
result is the one path here I cannot verify safely. It is one deliberate change away.

## [1.1.1] — 2026-07-31

### Fixed

- **A Czech answer about the latest run quoted the report's English inside it**: *"Běh 49
  skončil s výsledkem HOLD. No action is recommended… Nejdůležitější navazující krok:
  Review the Rebalancing Bot USDC funding plan."* 1.1.0 translated the frame and then
  filled it from the run's stored English, which is worse than either language on its
  own. The journal keeps the message behind both the summary and the top action, so those
  are rendered too — with the English sentence still used for runs recorded before those
  columns existed.

## [1.1.0] — 2026-07-31

### Changed

- **The built-in offline help answers in the language it was asked in.** Every reply was
  an English literal, so a Czech question got a Czech greeting from one layer and an
  English answer from the next. For anyone running without a model this is the only
  assistant there is.
- **A question it does not recognise is admitted, not answered anyway.** It used to fall
  through to a summary of what it can do, phrased as though it had understood.
- **Topics match whole words.** Matching was `in`, so *"Co mám dělat v sekci Profile?"* was
  answered with the location of the report files — because "profile" contains "file". That
  one wrong answer is what sent us looking at this corpus at all.

### Added

- Guard tests over the offline help: no prose returned in place of a message, every key
  resolving in both languages, and every topic having the handler its name implies —
  a missing one would have raised at the moment somebody asked a question.

## [1.0.2] — 2026-07-31

### Fixed

- **The wizard's assistant called an unconfigured provider a failure**: *"Poskytovatel AI
  selhal: LLM_BASE_URL is not set."* Nothing had failed and nothing had been asked — the
  built-in offline help had answered, which is what that box offers with or without a
  model. It now says so, and points at the step where a model can be added. A provider
  that genuinely answered badly still reports the failure it was.

### Known gaps

- The wizard assistant's **offline answers are only partly translated**: some match in
  Czech, others reply in English on a Czech screen, and a question it does not recognise
  gets a related answer rather than an admission. It is a separate body of text from the
  message registry and is not covered by the guard tests. Worth doing; not done here.

## [1.0.1] — 2026-07-31

### Added

- **A way to disconnect an AI model.** There was none: clearing the wizard's fields and
  saving wrote nothing, because saving an empty value is how the app avoids wiping a
  stored secret by accident — so the old endpoint simply reloaded. "Delete local data" has
  its own **AI model connection** group now, separate from the credentials group so that
  stepping away from AI does not also take Binance access with it.

### Fixed

- **The wizard's current-provider card spilled past its border.** Its height was a fixed
  104 while the four lines inside wrap, and how far they wrap depends on the endpoint and
  both model names. Content-driven now, like the card directly below it that already was.
- **Detail lines that could only be cut now show in full on hover.** Nine of them, in the
  reset dialog, the AI provider card and Privacy & data — several were the only
  explanation of what a checkbox was about to delete.

### Notes

The `.env` mentioned when deleting API keys is not a leftover: it is the fallback used
when the OS credential store is unavailable, and keys really can live there. Reviewed the
cloud provider path by reading it — the engine, the assistant and the provider check all
send `Authorization: Bearer`, and the save path is symmetric with the local one. Not
exercised against a real cloud endpoint, so that remains unverified rather than tested.

## [1.0.0] — 2026-07-31

First stable release. Nothing in the engine changed for it: the version says the desktop
has been walked through by hand, in both languages, and that the config format and journal
schema are now something to migrate rather than move.

### Fixed

- **Saving the caps already in force reported "a cap must be greater than zero".** Writing
  nothing has two causes — an unusable number, and nothing to change — and both returned
  the same empty result. They are told apart now, and the second says so plainly.
- **With no AI model connected, the assistant accepted the question and answered
  "LLM_BASE_URL is not set."** — an environment variable name, in English, to someone who
  never chose to have one. The assistant now says what is missing and offers Settings; its
  input and Send are disabled; and the two AI options in the run dialog are unavailable
  with a line explaining that the analysis runs exactly the same without them. A guard in
  the controller backs the disabled input, because that is what decides what happens.

## [0.1.21] — 2026-07-31

### Fixed

- **The buttons added over the last few releases were the wrong size.** Three of them —
  Deploy, Copy, and Save caps — carried hand-set heights and widths, which made them the
  only buttons in the app not at the default size, and clipped "Uložit stropy" to
  "Uložit st…". The sizes are gone. The deployment rows that provoked the first one are
  56 px now, tall enough for a normal button, which is what should have been done instead
  of shrinking the button to fit a 40 px row.
- **A refused tranche mixed the two languages**: *"Tranše 2/3 pro BTC na Testnetu se
  neodeslala: Adjusted quote amount 1.67 USDT is below BTCUSDT minNotional 5.00000000."*
  The reason is the useful half of that sentence, and it is also the most actionable
  refusal there is, so it travels as a key and parameters like the rest of the engine's
  text and names the fix: raise the budget or use fewer tranches.

## [0.1.20] — 2026-07-30

### Added

- **The per-order size cap is editable in Settings**, for Testnet and live separately. It
  ships at 10 and could previously only be changed by opening `config.toml` — the one
  thing this app tells people they never have to do, and a step already removed from the
  manual procedure for exactly that reason. The panel says what the cap governs: every
  order Coinductor can place, not only a first-portfolio tranche, and that it truncates
  silently rather than refusing.
- **A suggested live cap sized to the portfolio** (a tenth of it, never below the shipped
  10), with a warning when the saved value is above it. The warning never blocks —
  someone raising this deliberately has a reason, and a desktop that refuses their number
  is one they work around by editing the file again.

### Notes

The shipped defaults stay at 10. A new install still starts at the strictest cap and is
raised deliberately; what changed is that raising it is possible from the app, and that a
truncated order now says so.

## [0.1.19] — 2026-07-30

### Fixed

- **A capped mainnet tranche would have reported the amount it never sent.**
  `live_confirm.max_quote_amount_usdt` caps an order with `min()` rather than rejecting
  it, so a 66 USDC tranche against the default cap of 10 submits 10 — quietly, and the
  tranche then counts as done. The toast quoted the plan. It now reports what the
  exchange actually took, and says so explicitly when the two differ.
- **The remaining tranche messages were English**: the busy, budget, tranche-count and
  safety-stage guards, and the failure notice. Every one of them is the only feedback a
  user gets at that moment.

### Notes

Reviewed the Mainnet path end to end, since it cannot be exercised from an existing
portfolio. It has no equivalent of the validate-only defect — submission is reached only
when the preview succeeds *and* live submit was requested. What guards a live tranche:
the Safety stage, the typed confirmation, the risk engine's kill switch and loss limits,
the bankroll policy, the per-order cap, the exchange filters, and the intent id that stops
a resend. What it deliberately skips: market timing, and the symbol whitelist — the basket
chosen in the wizard is the universe, which is the only way SOL or BNB can be deployed at
all.

## [0.1.18] — 2026-07-30

### Fixed

- **"Validate only" reported itself as a failed confirmation.** It called the submit gate
  with an empty confirmation string and passed the answer straight to the toast:
  *"Confirmation string did not match CONFIRM_TESTNET_ORDER."* True, and completely
  misleading — nobody had asked it to submit — and it read as if the tranche could never
  be sent at all. Validate-only now stops before the gate and says what it actually did.
- **The tranche toast was English**, on the one screen where the message is the whole
  feedback. It is composed in the reader's language now, saying which tranche, which
  asset, and whether anything was sent. A blocked tranche keeps the engine's reason
  verbatim behind a translated lead, because that part is technical by nature.
- **The confirmation phrase could not be copied.** It has to be reproduced exactly, so it
  was the last thing that should have needed retyping from a label. It sits beside the
  instruction now as a copyable value with a Copy button, like every other value that has
  to be carried somewhere by hand.

## [0.1.17] — 2026-07-30

### Fixed

- **The Deploy buttons burst out of their rows** in First portfolio deployment. A Material
  button asks for 52 px and the row is 40, and a `RowLayout` will not shrink a child below
  its implicit minimum, so each button overhung the bottom of its own rounded background.
  Measured offscreen under the style the app actually uses — the default style gives 23 px
  and hides the problem entirely. The row is the fixed thing, so the button is what gives.
  A sweep of every fixed-height container in the QML found no second case.

## [0.1.16] — 2026-07-30

### Fixed

- **The app tour was English in both languages.** Its nine steps were English literals in
  the controller rather than entries in a translation table, so there was nothing to
  switch to. Each step now reuses the navigation label it points at and takes its title,
  detail and tip from `ui_strings`, composed when read so the overlay follows a language
  change.
- **The suggested first basket was English even on a Czech screen** — and for a subtler
  reason than a missing translation. Its prose was keyed off `profile.locale`, which is a
  regional fact, not a language: it decides that someone in Czechia deposits CZK. With
  the default `en-US` profile a Czech reader got an English plan. Language and region are
  now separate — money follows the locale, words follow the reader — and the labels,
  short values and notes that bypassed the mechanism entirely have translations at last.
- The Czech planner strings addressed the reader informally while everything beside them
  used the formal form, and pointed at an English button name the Czech wizard does not
  have.

### Changed

- Guard tests for both surfaces. A missing app tour key renders as a blank step and a
  missing plan key silently falls back to English, so neither would have shown up.

## [0.1.15] — 2026-07-30

### Fixed

- **Switching language did not refresh the Risk gate, Latest decision or the AI summary.**
  0.1.12 changed all three to compose their text when read, which was only half the fix:
  `setWizardLanguage` never emitted their notify signal, so QML had no reason to read
  them again and they kept whatever language the last analysis ran in. The AI summary is
  what made it visible — its "written in another language" line appeared at the *next*
  analysis, because that is when something else happened to emit the signal. Enumerating
  every notify signal against the ones the language switch emits found two more that were
  missing, and a test now asserts they fire.

### Known gaps

- The **app tour** and the **suggested first basket** are still English-only in both
  languages. Neither is a stale translation — the text has no Czech version to fall back
  to. They are separate surfaces from the ones converted so far.

## [0.1.14] — 2026-07-30

### Fixed

- **Switching to English left the AI summary in Czech**, under a heading reading "AI
  summary", with nothing to say why. The model's prose is the one thing on that screen
  that cannot be translated at the display boundary — it was written once, during the
  run, in the language set at the time. The report now records which language that was,
  and the panel adds a line saying so, with the one thing that fixes it: run the analysis
  again. A run recorded before this says nothing rather than guessing which language its
  stored prose is in.

## [0.1.13] — 2026-07-30

### Fixed

- **The AI summary ran off the panel on one line.** It had `wrapMode` set and a width
  bound to `parent.width` — but inside a `ScrollView` the parent is the internal
  Flickable, whose width follows the content rather than the view, so the binding
  resolved to nothing and there was no width to wrap against. Measured offscreen: the
  same text laid out 1932 px wide on one line in a 360 px panel, and 307 px over eight
  lines once bound to the view's `availableWidth`.
- **Two of the three model calls never asked for the reader's language.** Only the
  commentary did, so the Trade card read "AI uvedla: Market context remains unclear…"
  beside an otherwise Czech screen, and the rebalancing assessment came back in English
  too. A test now asserts it per call site rather than on one prompt, because the gap was
  a call site nobody had looked at.
- **The model translated "Grid" to "síť"** — Czech for *network*, naming nothing a reader
  can find in Binance's interface. It also hid a stray Grid mention from the validator
  that strips one, which matches on the word itself. Product names are pinned to English
  in the prompt now.
- **A run started without AI showed the engine's English note** under a heading reading
  "Shrnutí od AI", which reads as a malfunction rather than the setting the user chose.
  The report has always recorded `Enabled`; the desktop simply never read it. It now says
  so plainly, in the reader's language, and separately for "the model returned nothing
  usable".

## [0.1.12] — 2026-07-30

### Fixed

- **The AI summary printed a Python dictionary at you.** Several hundred characters of
  `{'ETHUSDC_Grid': {'blocker': ...}}`, introduced in 0.1.11 by the salvage that was
  supposed to rescue usable answers: it stringified whatever the `summary` key held, and a
  dict is not empty. Only a string counts now, and when a model answers in its own shape
  the sentences are joined in order into a paragraph. The panel scrolls and can be selected
  rather than spilling past its border.
- **Three more sources were writing English onto the first screen**: the trade proposal's
  reason — the Trade card's own sentence, the model's words included — the run's decision
  summary under "Latest decision", and the four explanations behind "Why HOLD?". The
  commentary-disabled line too.
- **The Risk gate and Latest decision showed the previous language after a switch.** They
  were built once when a run loaded. Both are composed when read now, which removes the
  cause rather than the instance; four fields had shown it.

### Changed

- The test that rejects new prose in a converted module covers eight modules instead of
  four. Twice a release claimed every prose source was converted while a module outside
  that list of four was still writing sentences; the modules that feed only the Markdown
  report are now listed explicitly, with the reason each is exempt.

## [0.1.11] — 2026-07-29

The last of the English prose, and the AI answer that was being thrown away.

### Changed

- **The risk engine's verdict is in your language.** It is what the Risk gate tile shows
  and what sits behind "Why HOLD?", and it read "AI proposal is HOLD." on a Czech screen.
  All fourteen outcomes are messages now, and the tile reads the journal rather than a
  sentence parsed back out of the Markdown report.
- **Active-strategy monitoring advice too** — the twelve recommendations about a registered
  grid or rebalancing bot. That is every prose source that reaches the screen; the report
  stays English by design.

### Fixed

- **The AI commentary discarded usable answers.** Models are asked for a `summary` key and
  routinely reply with their own structure, which left the card reading "returned no
  summary" beside 1300 characters of perfectly good prose. It now takes the requested key
  when present and otherwise the longest sentence in the reply — and when there really is
  nothing, it says the model ignored the format rather than implying it broke.

### Added

- `CONTRIBUTING.md`, stating the two rules that are not negotiable: model output never
  reaches a submit path, and user-facing text is a message rather than a finished sentence.
  Both have a test behind them.

### Upgrading

Two more journal columns are added on first start. Existing runs are untouched and keep
displaying as they did.

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
- **What you need on Binance's side, up front.** Coinductor is a desktop application that
  uses the API and never the mobile app — so if you only ever touch crypto from a phone,
  it does not fit, and saying that plainly is fairer than letting someone find out after
  downloading. Which Binance entity serves your country, and under which licence, is
  changing; the README points at Binance's own announcements rather than restating them,
  because anything written here would be stale within weeks.

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
