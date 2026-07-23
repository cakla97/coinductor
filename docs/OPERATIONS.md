# Operations and Setup

Practical guidance for running Coinductor beyond the quick start: Binance API key
permissions, dynamic-IP allowlists, remote/always-on operation, and AI provider presets.

Binance policies and endpoints change over time. Where this document describes Binance
behavior, verify the current rules in Binance's own API Management documentation before
relying on them. Coinductor is a personal portfolio tool, not financial advice.

## Binance API keys and permissions

Coinductor uses up to three separate keys, each with the narrowest permissions needed:

| Key (`.env`) | Purpose | Permissions to enable | Never enable |
|---|---|---|---|
| `BINANCE_API_KEY` / `_SECRET` | Read-only portfolio analysis | Reading only | Spot/margin trading, withdrawals, transfers, futures |
| `BINANCE_TESTNET_API_KEY` / `_SECRET` | Spot Testnet practice | Testnet spot trading | (testnet has no real funds) |
| `BINANCE_LIVE_TRADE_API_KEY` / `_SECRET` | Guarded live spot submit only | Reading + spot trading | Withdrawals, transfers, margin, futures |

Coinductor independently checks permissions before it does anything: the read-only key is
rejected if trading/withdrawal/transfer/margin/futures permissions are enabled, and guarded
live submit is a separate key behind explicit typed confirmations and the safety-stage gates.
Enabling withdrawals on any key used with Coinductor is never required and never recommended.

Baseline hardening:

- use a dedicated Binance sub-account for automation;
- keep read-only and live-trade keys separate (never reuse one key for both);
- disable withdrawals on every key;
- restrict keys by IP where practical (see below);
- start live activity with tiny amounts and keep `allow_locked_redeem = false`.

## Dynamic IP and IP allowlists

Binance API keys can be restricted to an IP allowlist. This is one of the strongest
protections for a trading key, but it lists **IP addresses, not hostnames**, so dynamic
DNS (DDNS) does not satisfy it directly. Options, strongest first:

1. **Static egress IP.** Run Coinductor behind a fixed IP: a business ISP static IP, a small
   VPS you own, or a VPN/proxy with a dedicated static exit IP. Add that one IP to the key's
   allowlist and you rarely touch it again. Best for a live-trade key.
2. **Update the allowlist on change.** With a dynamic home IP, restrict the key to your
   current IP and re-edit the allowlist in Binance API Management whenever your ISP changes
   it. Binance does not expose an API to change a key's own IP restriction, so this step is
   manual. Practical for occasional, hands-on use.
3. **Unrestricted read-only key.** For the read-only analysis key only, an unrestricted key is
   a defensible trade-off because it cannot trade or withdraw and Coinductor rejects it if it
   ever gains those permissions. Do **not** leave a live-trade key unrestricted.

Binance may require an IP allowlist for certain sensitive permissions and applies reduced
validity to unrestricted keys in some cases; check the current API Management rules when you
create the key.

## Remote and always-on operation

Coinductor is a **desktop GUI application designed for periodic, hands-on runs**, not a 24/7
unattended bot. Guarded live actions always require explicit typed confirmations, so it is
deliberately not "set and forget". Practical patterns:

- **Home machine you leave on.** Run the desktop app on a machine that stays powered, and
  reach it remotely with Windows Remote Desktop (RDP) or a VNC tool when you want to review or
  act. State lives under `%LOCALAPPDATA%\Coinductor` on that machine.
- **Headless analysis via the CLI.** `python -m trading_agent run` (and `doctor`,
  `readiness`, `last-report`, `research-request`) run without the GUI and write reports to
  disk, so they can be scheduled or run over SSH for read-only analysis. Guarded submit still
  requires the explicit confirmation flags and is not meant for unattended scheduling.
- **VPS.** A small always-on VPS gives you a fixed IP (good for the key allowlist) and can run
  the CLI for scheduled read-only analysis. The GUI needs a desktop session (RDP/VNC/X).

A fully headless, always-on worker with notifications is future scope (see
[ROADMAP.md](ROADMAP.md), Stage C), behind the same deterministic safety contract.

## AI provider presets

The AI assistant is optional; deterministic help works with no provider configured. When you
do connect one, it must be an OpenAI-compatible endpoint. Set these in `.env` (or via the
in-app wizard / Settings):

| Provider | `LLM_BASE_URL` | `LLM_API_KEY` | `LLM_MODEL` (example) | Notes |
|---|---|---|---|---|
| Ollama | `http://127.0.0.1:11434/v1` | (leave empty) | `qwen3:14b` | Local, private. Vision e.g. `qwen3-vl:8b`. |
| LM Studio | `http://127.0.0.1:1234/v1` | `lm-studio` | (name of the loaded model) | Local. Start its local server first. |
| Open WebUI | `http://<host>:<port>/v1` | (per install) | (server-side model id) | Local/self-hosted gateway. |
| Cloud (OpenAI-compatible) | provider's base URL | provider API key | provider model id | Data leaves this machine — see privacy below. |

- `LLM_VISION_MODEL` is optional; set it to route image messages (screenshots) to a separate
  vision model without changing the text model. Health checks validate both.
- **Privacy:** with a local endpoint, prompts and report context stay on your machine. With a
  cloud provider, the selected prompt and report/portfolio context are sent to that provider.
  Coinductor discloses this in the wizard's privacy step and never sends `.env` secrets to a
  model.
- Recommended local models by hardware are suggested in the wizard's "Local AI with Ollama"
  panel; "Detect installed models" lists what your endpoint actually reports.
