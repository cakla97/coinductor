# Proposal: unattended analysis, notifications, and the limits of automation

Status: **draft for discussion**. Nothing here is built.

Coinductor today is entirely pull-based. A person opens the app, presses *Run analysis*,
reads the Action Plan, and types a confirmation if they want anything to happen. That is
deliberate and it is why the app can be trusted with API keys. But it means the app is
only useful in the minutes someone is looking at it, and a recommendation that arrives
while the window is closed does not arrive at all.

This document proposes three separable pieces, in the order I would build them, and
argues against a fourth.

---

## The constraint that shapes everything

**A local-first desktop app is alive only while the machine is on.** There is no server,
no account, and no cloud scheduler, and adding one would trade away the property the
README leads with. Every design below inherits that limit. It should be stated in the UI
rather than discovered: a schedule that silently did not run is worse than no schedule.

---

## Part A — Background analysis while the app is open

**Shape.** The window closes to a tray icon instead of exiting. A timer fires on the
cadence already in the user profile (`run_cadence`: daily, twice weekly, weekly, manual).
Each firing runs exactly the analysis the *Run analysis* dialog runs today, with AI and
mainnet preview settings remembered from the last manual run.

**Notification.** `QSystemTrayIcon.showMessage()` — native Windows toast, no new
dependency. One line: the decision, and the single highest-priority action. Clicking it
opens the app on the Action Plan.

**What it must not do.** Submit anything. This part is read-only by construction; it
reuses `AgentRunner.run()` with `RuntimeFlags` left at their defaults, which fail closed.

**Cost.** Small. The runner, the journal and the notification plumbing all exist. The new
surface is a tray icon, a `QTimer`, and a Settings panel to turn it on and pick a cadence.

**Open question.** Whether closing the window should minimise to tray by default. I would
say no — surprising people about whether an app is still running is how you lose trust in
a tool that holds exchange credentials. Opt-in, with the tray icon always visible while
active.

---

## Part B — Analysis while the app is closed

**Shape.** A Windows Scheduled Task invoking the existing CLI:

```
python -m trading_agent run --config %LOCALAPPDATA%\Coinductor\config.toml
```

It writes to the same SQLite journal, so the result is simply *there* in Run History the
next time the app opens. No synchronisation problem: the journal is already the single
source of truth, and the desktop reads it rather than holding state.

**Registration from the app.** Settings creates and removes the task via `schtasks`, so
nobody has to open `taskschd.msc`. Wake-to-run stays off; "run as soon as possible after a
missed start" stays on.

**Notification without a GUI.** A scheduled run has no tray icon to post from. Two
options: have the CLI raise a toast directly (PowerShell's notification API), or have the
app report on next launch what happened while it was away. I lean towards the second — it
is honest about the app not having been there, and it needs no new code path in the
engine.

**Cost.** Small-to-medium, and almost all of it in the Settings UI and in telling the user
clearly what a scheduled task is and how to remove it.

**Risk.** A scheduled run uses real API keys with nobody watching. Read-only keys make
that uninteresting, which is exactly why the read-only key exists — this part should
refuse to run at all if the profile's live key is the one configured for analysis.

---

## Part C — Pre-authorised submission (the hard one)

Parts A and B produce *notifications*. Turning a notification into an order without a
person present means answering a question the app has so far avoided:

> Under what conditions may Coinductor submit without a human in the room?

Today the answer is "never": a typed phrase gates every path, and no timer can type. That
is a good default and I would not remove it. What could exist beside it is a **standing
authorisation**, narrow enough to be reasoned about:

| Bound | Why |
| --- | --- |
| Expires | A permission with no end date is a permission nobody remembers granting. 7 days, re-armed by hand. |
| One symbol, one direction | "You may buy BTCUSDC" is checkable. "You may trade" is not. |
| Hard per-order cap | Already exists as `live_confirm.max_quote_amount_usdt`. |
| Hard total cap across the window | The per-order cap alone permits unlimited orders. |
| Requires `LIVE_ENABLED` | Reuses the safety stage rather than inventing a parallel one. |
| Revocable from the tray | Without opening the app, in one click. |
| Every use written to the journal | Including the authorisation it acted under. |

**This is a design, not a plan.** It is the part I would want to sit on longest, and the
part where I would want the tests written before the feature. It is also the part that
makes the listing feature below theoretically possible — which is a reason for caution,
not for enthusiasm.

---

## Part D — New listing watcher

**What I would build: notification only.**

Poll `/api/v3/exchangeInfo` on a short interval, diff the symbol set against the last
seen, and raise a toast when something appears with `status: TRADING`. Open a card showing
the first prices, spread and book depth. The user decides.

Cheap, useful, and it cannot lose money by itself. It also produces the one thing missing
from the argument below: **a log of what actually happened in the first minutes of each
listing, on this machine, with this latency.** After a dozen listings that is real
evidence rather than either of our intuitions.

---

## Why I would not build listing sniping

The proposal was to buy immediately on listing and sell quickly. Three objections, in
descending order of how much they matter.

**1. The latency is not competitive and cannot be made so.** The first seconds of a
Binance listing are contested by bots colocated with the matching engine, with warmed
connections and pre-signed order templates. A home connection from Czechia is on the order
of 50–100 ms away before any of our own code runs. Being 200 ms late to a market that
resolves in tens of milliseconds is not a tuning problem.

**2. The fill is the trap.** A new listing opens on a thin book. A market order into that
book fills across whatever depth exists, and slippage measured in tens of percent is
ordinary rather than exceptional. The exchange filters that protect against nonsense
elsewhere — `minNotional`, `LOT_SIZE` — say nothing about price. The spike that looks like
the opportunity on a chart afterwards *is* the mechanism that transfers money from late
market buyers to early limit sellers.

**3. It inverts the one claim the project makes.** "The LLM proposes; deterministic code
decides; the human confirms" is the invariant in `CLAUDE.md`, the first line of the README,
and the reason someone might trust this app over the dozens that promise returns. Sniping
requires removing the human from the loop by definition. Spending the project's one
distinguishing property on a strategy with, at best, unproven expectancy is a bad trade
independently of whether the strategy works.

None of this is a claim that nobody makes money on listings. It is a claim that **the
people who do are not running a Python desktop app on a residential connection**, and that
we should find out from Part D's data rather than from a drawdown.

---

## Suggested order

1. **Part A** — tray, timer, toast. Useful on its own, and nothing else depends on it.
2. **Part D** — listing watcher, notification only. Small, and starts collecting evidence.
3. **Part B** — scheduled task. Wider reach, more explaining to do in the UI.
4. **Part C** — standing authorisation. Only if Parts A–B prove the automation is wanted,
   and with tests written first.

Parts A, B and D never submit an order. Part C is the only one that changes what the app
is allowed to do, and it can be deferred indefinitely without making the others pointless.
