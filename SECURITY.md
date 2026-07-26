# Security

Coinductor asks for Binance API keys, so it is worth being precise about what it does with
them and what it can do to your account.

## Reporting a vulnerability

Please **do not open a public issue** for anything that could be used against someone's
exchange account.

Open a [private security advisory](../../security/advisories/new) instead. Include what you
found, how to reproduce it, and what an attacker would gain. This is a single-maintainer
hobby project, so expect a first reply in days rather than hours; there is no bounty.

If the report concerns a dependency rather than this code, say so — those are usually fixed
by a version bump.

## What Coinductor can and cannot do to your account

| | |
| --- | --- |
| Withdraw funds | **No.** The app checks key permissions and refuses a read-only key that has withdrawal, transfer, trading, margin or futures enabled. |
| Place an order unprompted | **No.** See the gates below. |
| Trade futures / margin / with leverage | **No.** Spot and Simple Earn Flexible only. |
| Read your balances and history | Yes — that is the point. |

Live order submission requires **all** of these at once:

1. Safety stage raised to `LIVE_ENABLED` by hand, one stage at a time, each with a typed
   confirmation phrase.
2. Automation level set to *Guarded automation* in your profile. *Recommendations only*
   vetoes every submit regardless of the stage.
3. Guarded spot trades enabled in your profile.
4. Live-key permissions verified in the current session.
5. A typed confirmation phrase for that specific action.

A profile setting can only ever *remove* permission. Nothing in the profile, and nothing the
AI returns, can grant a permission the safety stage withholds.

## Where your keys are stored

Keys go to the operating system credential store — Windows Credential Manager, via `keyring`.
They are never written to reports, logs, the SQLite journal, or any user-facing error message.

If no OS credential store is available, the app falls back to a plaintext `.env` in the data
folder and says so in *Settings → Privacy & data*. That fallback is the weaker path; protect
the folder accordingly.

Switching the AI provider from cloud to local deletes the stored cloud API key, so it cannot
be sent to a local endpoint.

To remove keys: **Settings → Delete local data → API keys**, or accept the uninstaller's offer
to delete them. Uninstalling *without* accepting leaves them in place deliberately, so an
upgrade does not destroy your setup.

## What leaves your machine

Nothing, unless you configure it.

- **Binance API** — only when you run a check or an analysis, and only reads.
- **Cloud AI provider** — only if you configure one. Then the selected prompt and report
  context is sent to that provider. Your API keys are never part of that payload. A local
  provider (Ollama and similar) keeps everything on the machine.
- **No telemetry, no analytics, no update pings.**

## Recommended setup

- Give the app a **read-only** key first and keep it that way until you actually want to
  trade from it.
- Use a **separate key** for live trading, with an IP allowlist. See
  [docs/OPERATIONS.md](docs/OPERATIONS.md) for dynamic-IP handling.
- Keep live trading locked (`PREVIEW_ONLY` or lower) unless you are actively using it. The
  **Lock live submit** button in *Live Actions* returns you there at any time.
- Verify the SHA-256 of anything you download. The builds are unsigned, so the checksum in
  `SHA256SUMS.txt` is the only integrity check available.

## Unsigned builds

Releases are not code-signed; a certificate is a recurring cost this project does not carry.
Windows SmartScreen will warn on first run. This means the usual Authenticode guarantee —
that the binary is from a known publisher and unmodified — is not available, and the
published SHA-256 is what replaces it.

If that trade-off is not acceptable for you, build from source; the process is in the README
and needs only Python and `pip install -e ".[build]"`.

## Supported versions

This is a pre-1.0 project. Fixes land on the latest release only.
