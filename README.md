# Coinductor

A local, offline-first portfolio assistant for Binance Spot. It reads your account,
analyses it with deterministic rules, and explains what it would do — but it never
places an order unless you have explicitly unlocked it and typed a confirmation.

![Coinductor setup wizard](docs/screenshot-wizard.png)

Coinductor is a desktop app (Windows) with a headless Python engine underneath. Everything
runs on your machine: your keys go to the operating system's credential store, your reports
and history stay in a local SQLite file, and nothing is uploaded anywhere.

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
Get-FileHash .\Coinductor-0.1.0-setup.exe -Algorithm SHA256
```

Compare the result with the matching line in `SHA256SUMS.txt`.

### Why Windows warns about this app

The builds are unsigned, because a code-signing certificate is a recurring cost this project
does not carry. Windows will therefore show **"Windows protected your PC"** on first run, and
files extracted from a downloaded ZIP carry a *mark of the web* that can block them outright.

To run it anyway: click **More info → Run anyway** on the SmartScreen dialog. For the ZIP,
right-click it *before* extracting → **Properties** → tick **Unblock** → OK.

Only do this if you trust the source. Check the SHA-256 first — that is what it is for.

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

Everything runs offline out of the box: `app.mock_data = true` serves a fixed example
portfolio, so you can explore the whole app before giving it any key.

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

<!-- TODO before publishing: put your own address here, or delete this section. -->
- BTC: `<your address here>`

## License

Copyright (c) 2026 Coinductor

Released under the MIT License; see [LICENSE](LICENSE) for the full text. You may use, copy,
modify, and distribute the software freely, provided the copyright notice and license are
retained.

The software is provided "as is", without warranty of any kind. **It is a personal portfolio
tool, not financial advice.** You are responsible for every order that reaches your exchange
account, including ones you confirmed through this app.
