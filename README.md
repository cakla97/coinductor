# Coinductor

**Knowing *when* to act is the hard part of crypto. Coinductor works it out for you — and
never acts without your say-so.**

![Coinductor setup wizard](docs/screenshot-wizard.png)

Most people who want to hold crypto get stuck in the same place. Either they have never
bought any and have no idea what a sensible first portfolio looks like, or they already
hold a few coins and have no idea what to do next. Both end up doing nothing, or acting on
a hunch at the worst possible moment.

Coinductor is a desktop app that sits between those two. It reads your Binance account,
runs a deterministic analysis over it, and tells you plainly what it would do and why —
buy, hold, rebalance, set up a Grid bot, or nothing at all. You decide how far it goes:
recommendations only, or guarded automation where it prepares the order and you confirm it.

## Who it is for

### Starting from zero

Tell it your budget and how much risk you can live with. It proposes a first basket sized
to that budget, in tranches rather than one nervous lump sum, and explains every allocation.
From there the same analysis keeps running, so your first portfolio does not become a
forgotten one.

### Already holding

It classifies what you own — core, stable, protected, dust — and looks for the next
sensible move: rebalancing drift, a range worth running a Grid bot on, idle stablecoins that
could be earning. Your protected assets stay protected; it will tell you it cannot fund
something rather than quietly sell your BTC to do it.

### If you do not trust your own timing

That is the point. The decision to buy runs through a fixed set of checks — trend, EMA200,
RSI band, loss limits, position caps — that do not change because the chart looks exciting.
An AI model can propose; only deterministic code can approve. And nothing reaches your
exchange account until you have unlocked it in stages and typed a confirmation for that
specific action.

Everything runs on your machine: keys in the operating system's credential store, history in
a local SQLite file, nothing uploaded anywhere.

## What it will not do

This is the part worth reading before installing anything that touches an exchange account.

- **It cannot withdraw funds.** The read-only key it asks for first is rejected if it has
  trading, withdrawal, transfer, margin or futures permissions enabled.
- **It cannot place an order on its own.** Live submission requires all of: the safety stage
  raised to `LIVE_ENABLED` by hand, an automation level of *Guarded automation* in your
  profile, verified live-key permissions, and a typed confirmation phrase — per action.
- **No futures, no margin, no leverage.** Spot and Simple Earn Flexible only; Locked Earn is
  read-only.
- **The AI never decides anything.** It proposes; deterministic code disposes. See
  [the invariant](#the-invariant) below.
- **It is not a 24/7 bot.** It runs when you open it and press a button.

## Platform support

| | Status |
| --- | --- |
| **Windows 10/11 (64-bit)** — installer or portable ZIP | Supported. This is the shipping platform. |
| **Engine and CLI** (`trading_agent`) on Linux / macOS | Works. Pure Python 3.11+, and CI runs the full suite on Linux every push. |
| **Desktop app** on Linux / macOS, from source | Untested. PySide6 is cross-platform so it may well run, but nothing here has been verified there and no packaged build exists. |

Two things to expect if you try the desktop app off Windows: there is no installer, and
without an OS credential store (Secret Service, Keychain) your API keys fall back to a
plaintext `.env`. The app tells you which one is in use under *Settings → Privacy & data*.

## Install

Windows 10/11, 64-bit. No Python needed for the packaged builds.

### Installer (recommended)

Download `Coinductor-<version>-setup.exe` from the [latest release](../../releases/latest)
and run it. It installs per-user — no admin rights, no UAC prompt — and adds a Start Menu
shortcut and an uninstaller.

### Portable ZIP

Download `Coinductor-<version>-portable.zip`, extract it anywhere, and run
`Coinductor\Coinductor.exe`. Nothing is written outside the data folder described below.

> Launching straight after extracting can fail with "Access is denied" while Windows
> Defender is still scanning the files. Wait a few seconds and try again.

### Verify your download

Every release ships `SHA256SUMS.txt`. The binaries are **not code-signed** (see below), so
the checksum is the only way to tell a genuine download from a tampered one:

```powershell
Get-FileHash .\Coinductor-<version>-setup.exe -Algorithm SHA256
```

Compare the result with the matching line in `SHA256SUMS.txt`.

### Why Windows warns about this app

The builds are unsigned, because a code-signing certificate is a recurring cost this project
does not carry. Windows will therefore show **"Windows protected your PC"** on first run, and
files extracted from a downloaded ZIP carry a *mark of the web* that can block them outright.

To run it anyway: click **More info → Run anyway** on the SmartScreen dialog. For the ZIP,
right-click it *before* extracting → **Properties** → tick **Unblock** → OK.

Only do this if you trust the source. Check the SHA-256 first — that is what it is for.

### If your antivirus blocks it

Third-party antivirus reacts to the same thing SmartScreen does: an unsigned executable,
freshly downloaded, that almost nobody else is running yet. Avast in particular has been
observed to

- refuse the installer with **"Unable to execute file in the temporary directory. Setup
  aborted. Error 5"**, or Windows' own **"Windows cannot access the specified device, path,
  or file"** — its CyberCapture holding the extracted setup stub, and
- run the installed app and the uninstaller inside its **Autosandbox**, which makes the
  install look like it finished while the app is nowhere to be found, and can leave an
  uninstall only partly applied.

None of this is a fault in the installer, and none of it says so. It often clears on its own
once the vendor's cloud check finishes — trying again a minute later frequently just works.

To stop it happening, exclude the install folder. This is the one worth adding, because it
covers the app itself and every version you ever install:

```text
%LOCALAPPDATA%\Programs\Coinductor\
```

The installer is a separate file, and **its name changes with every release** — an exclusion
for `Coinductor-0.1.2-setup.exe` does nothing for `0.1.3`. Either re-add it after each
update, or use a wildcard if your product supports one:

```text
%USERPROFILE%\Downloads\Coinductor-*-setup.exe
```

In Avast: *Menu → Settings → General → Exceptions*. Other products have an equivalent.
Verify the SHA-256 before you exclude anything.

Reporting the file to your vendor as a false positive helps everyone: once it is
whitelisted, the next person does not have to do this at all.

### From source

```powershell
git clone <repository-url>
cd binance-trading-agent
python -m pip install -e ".[desktop]"
coinductor                                                 # desktop app
python -m trading_agent run --config config.example.toml    # headless CLI
```

Python 3.11+. Without the `desktop` extra you still get the full engine and CLI.

## First run

The setup wizard walks through it, and **nothing in the wizard touches your exchange
account** — it only writes a local profile and shows what still needs verifying.

1. Create a Binance API key with **read-only** permissions and paste it in. Coinductor
   verifies the permissions and refuses the key if it can do more than read.
2. Optionally point it at an AI provider — local (Ollama and similar) or a cloud API key.
   It works fine with no AI at all.
3. Run an analysis. The first one is read-only by definition.

Live trading stays locked until you deliberately walk the safety stages in **Live Actions**.

An installed build starts with `app.mock_data = false`, so an analysis works on your real
account or honestly fails - it will never present example figures as if they were yours. To
explore the app before connecting anything, set `mock_data = true` in `config.toml`; that is
also how the repository and the test suite run fully offline.

`config.example.toml` is the tracked, neutral template. Copy it to `config.toml` (gitignored)
and edit that; when a `config.toml` exists the CLI and the app both pick it up automatically.
Set `COINDUCTOR_CONFIG` to point somewhere else.

## Where your data lives

| Build | Location |
| --- | --- |
| Installed / portable | `%LOCALAPPDATA%\Coinductor` |
| From source | the repository folder |

That holds `config.toml`, the SQLite journal, reports, research notes, your onboarding
profile and the safety stage. **API keys are not in there** — they go to Windows Credential
Manager. If no OS credential store is available they fall back to a plaintext `.env`, and the
app says so in *Settings → Privacy & data*.

## Removing Coinductor

Uninstalling removes the program. Your data and API keys survive on purpose, so reinstalling
or upgrading does not wipe your history — but the uninstaller **offers** to delete both, and
saying yes clears the data folder and your stored keys from Windows Credential Manager.

You can also do it from inside the app at any time: **Settings → Delete local data** lets you
pick exactly what goes, including the credentials.

## The invariant

**The LLM proposes; deterministic code decides.**

`AiAnalyst` only ever returns a *candidate* action. `RiskEngine.evaluate()` governs whether
anything happens, and every execution path is gated behind it. The model cannot widen the
trading universe, relax a loss limit, skip a stop-loss, or reach a submit path — not by being
wrong, and not by being talked into it.

The onboarding profile can only ever *tighten*: choosing "Recommendations only" vetoes every
submit even at `LIVE_ENABLED`, and no profile setting can grant a permission the safety stage
withholds.

## Documentation

| Document | What it covers |
| --- | --- |
| [docs/ENGINE.md](docs/ENGINE.md) | Engine reference: modes, strategy decisions, previews, bankroll, research |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Day-to-day operation: monitoring, guarded submits, what to check |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | API key permissions, dynamic-IP allowlists, remote operation, AI presets |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Direction and planned work |
| [SECURITY.md](SECURITY.md) | Reporting a vulnerability, and what the app does with your keys |

In-app guides cover the same ground per screen, in English and Czech.

## Development

```powershell
python -m pip install -e ".[dev,desktop]"
python -m pytest -q                                    # fully offline
python -m ruff check trading_agent coinductor tests
```

Two packages, one direction of dependency: `trading_agent/` is the headless engine and knows
nothing about the UI; `coinductor/` is the PySide6/QML app and imports the engine, never the
reverse. `CLAUDE.md` documents the conventions that are easiest to break.

To build the release artifacts:

```powershell
python -m pip install -e ".[build]"
python packaging\build_release.py
```

That produces the bundle, a portable ZIP, an installer (if Inno Setup 6 is present) and
`SHA256SUMS.txt` in `dist/`.

## Support the project

Coinductor is free and unsigned, which is a polite way of saying nobody is paying for the
certificate. If it is useful to you:

The network is stated on purpose: sending coins across the wrong one loses them, and
"BTC" on BNB Smart Chain is BTCB, a wrapped token, not native bitcoin.

- **Bitcoin** (BTC network, native segwit): `bc1qqmfafr7wmxe37lwhh2cl5f8dj93r52z70kl2df`

## License

Copyright (c) 2026 Coinductor

Released under the MIT License; see [LICENSE](LICENSE) for the full text. You may use, copy,
modify, and distribute the software freely, provided the copyright notice and license are
retained.

The software is provided "as is", without warranty of any kind. **It is a personal portfolio
tool, not financial advice.** You are responsible for every order that reaches your exchange
account, including ones you confirmed through this app.
