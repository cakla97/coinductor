from __future__ import annotations

from pathlib import Path
import sys

from .guide_strings_cs import GUIDE_SECTIONS_CS, GUIDES_CS


def _asset_dir() -> Path:
    # In a PyInstaller build the assets are bundled under _MEIPASS; in a source
    # checkout they sit next to this module.
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "coinductor" / "assets" / "guides"
    return Path(__file__).resolve().parent / "assets" / "guides"


ASSET_DIR = _asset_dir()


def _image(name: str, caption: str) -> dict[str, str]:
    return {"source": (ASSET_DIR / name).as_uri(), "caption": caption}


class GuideService:
    def list_guides(self, language: str = "en") -> list[dict[str, str]]:
        """Guides in the requested language, falling back to English per field."""
        guides = self._english_guides()
        if not str(language).strip().lower().startswith("cs"):
            return guides
        for guide in guides:
            guide["section"] = GUIDE_SECTIONS_CS.get(guide["section"], guide["section"])
            translation = GUIDES_CS.get(guide["id"])
            if not translation:
                continue
            for field in ("title", "summary", "body", "warning"):
                if translation.get(field):
                    guide[field] = translation[field]
            captions = translation.get("images") or []
            for image, caption in zip(guide.get("images", []), captions):
                if caption:
                    image["caption"] = caption
        return guides

    def _english_guides(self) -> list[dict[str, str]]:
        return [
            {
                "id": "local-ai",
                "section": "AI setup",
                "title": "Local AI with Ollama",
                "summary": "Private local assistant for project help, report summaries, and future wizard guidance.",
                "body": "<br>".join(
                    [
                        "Use this path when you want Coinductor to stay local-first.",
                        "",
                        '1. Open <a href="https://ollama.com/">https://ollama.com/</a> and use the Download button to install Ollama for your operating system.',
                        "2. Pick a model that fits your hardware. Use Coinductor's Scan hardware button in the AI setup step for a local recommendation. The scan is local: it reads RAM and GPU/VRAM from OS tools and does not upload hardware details.",
                        '3. On <a href="https://ollama.com/search">https://ollama.com/search</a>, search for the text model recommended in step 2. Pull that exact model. On smaller systems, open a terminal and run: ollama pull qwen3:8b. On stronger GPUs, run: ollama pull qwen3:14b.',
                        "4. Keep Ollama running while Coinductor uses AI features. On Windows this usually means the Ollama icon remains visible in the system tray.",
                        "5. In Coinductor, set the local endpoint to http://127.0.0.1:11434/v1 and enter that tag in Text model.",
                        '6. Optional image support: open <a href="https://ollama.com/library/qwen3-vl">https://ollama.com/library/qwen3-vl</a>, pull a suitable Qwen3-VL tag (for example: ollama pull qwen3-vl:8b), and enter it in Vision model. Coinductor keeps the text model for normal messages and routes only image messages to this model.',
                        "7. Save the settings and run Check AI provider. It must report the text model as ready and, when configured, the vision model as ready.",
                        "",
                        "Model quality note: for portfolio commentary and market reasoning, 14B-class models are the preferred minimum when hardware supports them. Smaller models may still answer basic app questions, but they are more likely to miss context or produce weak recommendations.",
                        "",
                        "What a weak answer looks like, and why it is not a fault: the model may ignore the JSON structure Coinductor asks for, and the commentary comes back as \"AI commentary returned no summary\". It may reply in English even though the request asks for your language. Its trade opinion may be rejected by the risk engine, in which case the deterministic analyst decides and the card says so. None of this changes the analysis - every number, verdict and blocker on the Action Plan is produced without a model.",
                        "Do not enable LLM_VISION_ENABLED just to force a text-only model. That advanced override changes detection only and cannot add image support.",
                        "",
                        "Local AI can explain Coinductor, summarize reports, and help with onboarding. It cannot bypass deterministic safety gates or submit trades by itself.",
                        "",
                        "In the app: configure and test the provider on the <a href=\"guide:page-settings\">Settings page</a>, then use it on the <a href=\"guide:page-ai-assistant\">AI Assistant page</a>.",
                    ]
                ),
                "images": [
                    _image("ollama_download_and_models.png", "Ollama homepage with Download and model search highlighted."),
                    _image("ollama_tray_running.png", "Ollama running in the Windows system tray."),
                ],
            },
            {
                "id": "cloud-ai",
                "section": "AI setup",
                "title": "Cloud AI API",
                "summary": "Optional higher-quality AI path with separate API billing and external data processing.",
                "body": "<br>".join(
                    [
                        "Cloud AI is optional and should be treated as an advanced alternative.",
                        "",
                        "Pricing warning: Chat subscriptions and API usage are usually separate products with separate pricing. ChatGPT Plus/Pro, Claude plans, or Gemini subscriptions do not automatically mean API calls from Coinductor are included.",
                        "",
                        "OpenAI example:",
                        '1. Open <a href="https://platform.openai.com/">https://platform.openai.com/</a> and go to API Keys.',
                        "2. Add billing/limits in the provider dashboard if required.",
                        "3. In Coinductor, use https://api.openai.com/v1 as the endpoint.",
                        "4. Enter the model name you want to use.",
                        "5. Paste the API key and run Check AI provider.",
                        "",
                        "Privacy note: selected report, profile, and question context may be sent to the configured provider. Do not use cloud AI if you want all portfolio context to remain on your computer.",
                        "",
                        "In the app: set the endpoint, model, and key on the <a href=\"guide:page-settings\">Settings page</a> (Configure AI models), then use it on the <a href=\"guide:page-ai-assistant\">AI Assistant page</a>.",
                    ]
                ),
                "warning": "Cloud AI API calls may cost money separately from a normal chat subscription. Set provider-side limits before using it.",
                "images": [
                    _image("openai_api_keys.png", "OpenAI Platform API Keys page with the create-key action highlighted."),
                ],
            },
            {
                "id": "binance-api",
                "section": "Binance",
                "title": "Binance read-only API",
                "summary": "Create a safe read-only Binance API key for portfolio inventory and analysis.",
                "body": "<br>".join(
                    [
                        "Coinductor starts with read-only access. This lets it inspect portfolio balances and status without changing anything on the exchange.",
                        "",
                        "1. In Binance, open User profile > Account > API Management.",
                        "2. Choose Create API > System generated.",
                        "3. Use a clear label such as coinductor-readonly.",
                        "4. Complete two-factor verification.",
                        "5. Copy both the API Key and Secret Key immediately.",
                        "6. In restrictions, keep reading enabled for the read-only key.",
                        "7. Do not enable withdrawals, futures, margin transfer, or universal transfer.",
                        "8. Paste the key and secret into Coinductor and run Check read-only access.",
                        "",
                        "Trading/write access should use a separate later key after testnet and preview checks. Withdrawals should remain disabled.",
                        "",
                        "In the app: run Check read-only access on the <a href=\"guide:page-settings\">Settings page</a>. The inventory it unlocks appears on the <a href=\"guide:page-portfolio\">Portfolio page</a>.",
                    ]
                ),
                "images": [
                    _image("binance_api_management_sanitized.png", "Sanitized Binance dashboard screenshot with API Management highlighted."),
                    _image("binance_read_only_restrictions_sanitized.png", "Sanitized Binance API restrictions screen for a read-only key."),
                ],
            },
            {
                "id": "binance-live-api",
                "section": "Binance",
                "title": "Binance live trading API",
                "summary": "Create a separate Binance API key for guarded Spot trading workflows after read-only setup is trusted.",
                "body": "<br>".join(
                    [
                        "Use this only after read-only access, reports, and preview workflows make sense to you. This key is for guarded Spot trading workflows; it should never allow withdrawals.",
                        "",
                        "1. In Binance, open User profile > Account > API Management.",
                        "2. Choose Create API > System generated.",
                        "3. Use a clear label such as coinductor-live-trading.",
                        "4. Complete two-factor verification and copy both the API Key and Secret Key immediately.",
                        "5. Open Edit restrictions for this new key.",
                        "6. In IP access restrictions, choose Restrict access to trusted IPs only first. Binance may keep trading permissions unavailable until trusted-IP restriction is configured.",
                        '7. Add the public IP address of the machine or server that will run Coinductor. You can check it with a browser page such as <a href="https://ifconfig.me/">https://ifconfig.me/</a> or <a href="https://whatismyipaddress.com/">https://whatismyipaddress.com/</a>.',
                        "8. If your IP changes after router restart or from day to day, treat it as dynamic. Dynamic-IP users should keep live execution locked, update the whitelist manually when needed, or later use a trusted always-on host/VPS with a stable public IP.",
                        "9. After trusted IP access is configured, enable Reading and Enable Spot & Margin & Stock Trading. Do not enable Futures, Margin Loan/Repay/Transfer, Universal Transfer, Prediction Trading, or Withdrawals.",
                        "10. Paste the live trading key into Coinductor Live Actions. Live submit remains locked until a separate safety stage allows it.",
                        "",
                        "Important: use a separate key from the read-only key. Keep withdrawals disabled forever. Coinductor can store this key locally, but it should not make live submit available until deterministic safety gates and explicit confirmations are enabled.",
                        "",
                        "In the app: you paste and manage this key on the <a href=\"guide:page-live-actions\">Live Actions page</a>, and live submit stays locked until you progress the stages in the <a href=\"guide:safety-model\">Safety model</a>.",
                    ]
                ),
                "warning": "A live trading key can place/cancel Spot orders if Binance permissions allow it. Keep withdrawals disabled and restrict the key to trusted IPs only.",
                "images": [
                    _image("binance_api_management_sanitized.png", "Sanitized Binance API Management page."),
                    _image("binance_live_trading_restrictions_sanitized.png", "Sanitized live trading restrictions screen: restrict trusted IP first, then enable Reading and Spot trading; withdrawals stay disabled."),
                ],
            },
            {
                "id": "binance-testnet",
                "section": "Binance",
                "title": "Binance Spot Testnet (practice with virtual funds)",
                "summary": "Create a separate Testnet key so trade logic can be exercised with virtual funds before any real money is involved.",
                "body": "<br>".join(
                    [
                        "Spot Testnet is a separate Binance environment with virtual funds. It uses its own account and its own API keys; it is not connected to your real Binance balance in any way.",
                        "Use it to see how Coinductor previews and (with explicit confirmation) submits orders before ever touching a real key.",
                        "",
                        '1. Open <a href="https://testnet.binance.vision/">https://testnet.binance.vision/</a> and log in with a GitHub account (Testnet uses GitHub for login, not your normal Binance account).',
                        "2. Generate a Testnet API Key and Secret Key from that page.",
                        "3. Paste both values into the Spot Testnet panel below (or in Settings) and press Save Testnet key. They are stored in the local .env file, separate from your read-only and live-trading keys.",
                        "4. Press Check Testnet access to confirm the key can reach the Testnet account.",
                        "5. Testnet orders can also be exercised from a terminal for more control, for example: python -m trading_agent testnet-market-buy --config config.example.toml --symbol BTCUSDT --quote-amount 10. See README.md for the full list of Testnet CLI commands.",
                        "",
                        "Testnet is optional but recommended before any real mainnet order: it costs nothing, risks nothing, and exercises the same order-validation and confirmation-string logic used for real trading.",
                        "",
                        "In the app: Testnet execution is exercised from the <a href=\"guide:page-action-plan\">Action Plan page</a> (including first-portfolio deployment) once the safety stage reaches Testnet ready.",
                    ]
                ),
            },
            {
                "id": "safety-model",
                "section": "Safety",
                "title": "Safety model",
                "summary": "How Coinductor separates recommendations, previews, guarded actions, and live execution.",
                "body": "<br>".join(
                    [
                        "Coinductor is designed so AI can help explain and rank bounded options, while deterministic code owns limits and execution gates.",
                        "",
                        "Safety stages:",
                        "1. Setup: local profile and configuration only.",
                        "2. Read-only connected: portfolio can be analyzed, but exchange-changing actions remain unavailable.",
                        "3. Testnet ready: trade logic can be tested without real funds where supported.",
                        "4. Preview only: mainnet actions can be prepared for review but not submitted.",
                        "5. Guarded live: explicitly enabled workflows can submit actions only after deterministic checks and confirmations.",
                        "",
                        "Coinductor should never enable withdrawals. Loss limits, protected assets, capital caps, and confirmation gates remain deterministic even when AI is connected.",
                        "",
                        "In the app: you progress these stages on the <a href=\"guide:page-live-actions\">Live Actions page</a>, and guarded actions are prepared and confirmed on the <a href=\"guide:page-action-plan\">Action Plan page</a>.",
                    ]
                ),
            },
            {
                "id": "portfolio-roles",
                "section": "Portfolio",
                "title": "Portfolio roles",
                "summary": "Understand protected assets, trading assets, funding sources, and manual overrides.",
                "body": "<br>".join(
                    [
                        "Portfolio roles tell Coinductor what an asset is allowed to do.",
                        "",
                        "System default: remove the manual override and let the latest portfolio classification/config decide.",
                        "Protected core: long-term core holding. Coinductor should avoid using it for routine funding or trading.",
                        "Protected utility: asset kept for another purpose, such as fee discounts or exchange benefits. It is protected like core holdings.",
                        "Trading allowed: asset may be considered for guarded spot-trade recommendations.",
                        "Grid candidate: asset may be considered for Binance Spot Grid parameter recommendations.",
                        "Rebalancing candidate: asset may be included in rebalancing basket recommendations.",
                        "Funding source: asset may provide capital within configured funding limits.",
                        "Dust/airdrop funding: small or unwanted assets may be converted into operating capital when rules allow it.",
                        "Active strategy: asset can be eligible for trading, Grid, and Rebalancing recommendation paths.",
                        "Stable: stablecoin-like holding, usually operating capital or reserve; it is not treated as a protected volatile asset.",
                        "Unclassified: keep visible but do not intentionally assign it to an active role yet.",
                        "",
                        "Manual overrides are available because different users care about different assets. Overrides can change eligibility, but they must not disable global risk limits, loss stops, or confirmation gates.",
                        "",
                        "In the app: you set these overrides on the <a href=\"guide:page-portfolio\">Portfolio page</a>.",
                    ]
                ),
            },
            {
                "id": "page-overview",
                "section": "Using Coinductor",
                "title": "Overview page",
                "summary": "Your dashboard: current portfolio state, safety readiness, the latest decision, and recommended next actions.",
                "body": "<br>".join(
                    [
                        "Overview is the first page and summarizes everything at a glance. Nothing here places an order.",
                        "",
                        "What you see:",
                        "- Metric cards: total portfolio value, liquid vs locked balance, and the current risk gate (for example whether the AI proposal is HOLD).",
                        "- Safety &amp; readiness: the current safety stage and whether guarded live actions are available. See the <a href=\"guide:safety-model\">Safety model</a> guide.",
                        "- Latest decision: the most recent analysis result and why an action was or was not recommended.",
                        "- Recommended actions: the prioritized follow-ups produced by the last run.",
                        "- AI summary: optional plain-language commentary when an AI provider is connected.",
                        "- Finish setup banner: appears when Binance read-only access is not connected yet, with a button back into setup.",
                        "",
                        "What you can do:",
                        "- Run analysis to refresh all of the above from current data.",
                        "- Open the detailed report for the full breakdown, or jump to <a href=\"guide:page-action-plan\">Action Plan</a> to act on a recommendation.",
                        "",
                        "A run reads data and produces recommendations only. Any live action happens later, on <a href=\"guide:page-live-actions\">Live Actions</a> or <a href=\"guide:page-action-plan\">Action Plan</a>, behind explicit confirmation.",
                    ]
                ),
            },
            {
                "id": "page-portfolio",
                "section": "Using Coinductor",
                "title": "Portfolio page",
                "summary": "Full asset inventory with roles, valuations, and manual per-asset role overrides.",
                "body": "<br>".join(
                    [
                        "Portfolio lists every tracked asset with its balance, value, and role. Roles decide what Coinductor is allowed to do with each asset.",
                        "",
                        "What you can do:",
                        "- Review balances and how each asset is valued (assets that cannot be priced are shown as unpriced rather than dropped).",
                        "- Set a manual role override on an asset when you want to change its eligibility for trading, Grid, rebalancing, funding, or dust conversion.",
                        "",
                        "For what each role means and the safe-override rules, see the <a href=\"guide:portfolio-roles\">Portfolio roles</a> guide. Overrides can change eligibility but never disable global risk limits, protected-asset checks, or confirmation gates.",
                    ]
                ),
            },
            {
                "id": "page-live-actions",
                "section": "Using Coinductor",
                "title": "Live Actions page",
                "summary": "Safety-stage controls and the live trading key: how Coinductor moves from read-only toward guarded live submit.",
                "body": "<br>".join(
                    [
                        "Live Actions is where the deliberate, staged progression from read-only to guarded live execution happens. Each step is explicit and reversible.",
                        "",
                        "What you see:",
                        "- The current safety stage and controls to progress it (Setup, Read-only connected, Testnet ready, Preview only, Armed, Live enabled).",
                        "- Live API key management for the separate live trading key (see the <a href=\"guide:binance-live-api\">Binance live trading API</a> guide).",
                        "- Status pills such as VERIFIED, CONFIGURED, and LOCKED that show what is ready and what is still gated.",
                        "",
                        "What you can do:",
                        "- Advance the safety stage by typing the exact confirmation phrase shown for that step. Progression is backed by deterministic checks, not just a button.",
                        "- Lock live submit again at any time.",
                        "",
                        "Nothing becomes live until you deliberately reach the guarded live stage and confirm each action. See the <a href=\"guide:safety-model\">Safety model</a> guide for the full stage list.",
                    ]
                ),
            },
            {
                "id": "page-action-plan",
                "section": "Using Coinductor",
                "title": "Action Plan page",
                "summary": "Turn recommendations into previewed, individually confirmed actions: trades, OCO protection, Earn redeem, and first-portfolio deployment.",
                "body": "<br>".join(
                    [
                        "Action Plan lists the concrete follow-ups from the latest run and opens a detail view for each one. Every money-moving action is preview-first and needs its own typed confirmation.",
                        "",
                        "What you can do (each is separately gated):",
                        "- Preview and, when the safety stage allows, submit a guarded Spot trade.",
                        "- Add OCO protection (a linked take-profit / stop-loss) to an open position.",
                        "- Redeem from Flexible Earn as a liquidity step.",
                        "- Challenge HOLD: ask the risk engine to re-evaluate one allowed symbol for a BUY. It still runs the full deterministic checks and can still reject.",
                        "- First-portfolio deployment: run one basket asset/tranche at a time when building a portfolio from scratch, on Testnet or mainnet.",
                        "",
                        "Every submit requires the exact confirmation phrase for that action and passes bankroll, exposure, stop-loss, kill-switch, and safety-stage checks. See <a href=\"guide:page-live-actions\">Live Actions</a> and the <a href=\"guide:safety-model\">Safety model</a> guide.",
                    ]
                ),
            },
            {
                "id": "page-active-strategies",
                "section": "Using Coinductor",
                "title": "Active Strategies page",
                "summary": "Track the Grid and Rebalancing bots you registered locally, with health and next-review status.",
                "body": "<br>".join(
                    [
                        "Coinductor recommends Grid and Rebalancing bot parameters but does not create the bots; you create them in the Binance app and register them here for local tracking.",
                        "",
                        "What you can do:",
                        "- See each registered bot with its health, next-review timing, and whether price is near the configured range.",
                        "- Update a bot's status to Paused, Stopped, or Closed as you manage it in Binance.",
                        "",
                        "Monitoring is based on local registration and market prices, not on Binance's own bot execution telemetry, so treat it as a review aid rather than a live PnL feed.",
                    ]
                ),
            },
            {
                "id": "page-run-history",
                "section": "Using Coinductor",
                "title": "Run History page",
                "summary": "Browse past analysis runs and open their reports.",
                "body": "<br>".join(
                    [
                        "Run History is a read-only log of previous analysis runs.",
                        "",
                        "What you can do:",
                        "- See when each run happened, in which mode, and its status.",
                        "- Open a run's report to review the portfolio state, decisions, and recommendations captured at that time.",
                        "",
                        "History is useful for comparing how recommendations and portfolio state change between runs.",
                    ]
                ),
            },
            {
                "id": "page-ai-assistant",
                "section": "Using Coinductor",
                "title": "AI Assistant page",
                "summary": "Ask questions about the app, your reports, and portfolio state; attach screenshots. It never executes live actions.",
                "body": "<br>".join(
                    [
                        "The AI Assistant answers questions and can point you to the right screen or guide. It is advisory only: it can never place a trade, redeem Earn, or change a safety gate.",
                        "",
                        "What you can do:",
                        "- Ask how a feature works, what a report section means, or what your current state is.",
                        "- Attach an image (file or clipboard) to ask about a screenshot.",
                        "- Reuse and copy earlier messages from the history.",
                        "",
                        "Deterministic answers about documented app features come first and work even with no AI provider configured. Connecting a provider adds broader free-form answers; see the <a href=\"guide:local-ai\">Local AI with Ollama</a> and <a href=\"guide:cloud-ai\">Cloud AI API</a> guides. Any action the assistant suggests still requires you to confirm it in the normal guarded flow.",
                    ]
                ),
            },
            {
                "id": "page-settings",
                "section": "Using Coinductor",
                "title": "Settings page",
                "summary": "Connection checks, AI provider configuration, language, onboarding profile, privacy & data, and diagnostics.",
                "body": "<br>".join(
                    [
                        "Settings is where you connect services and manage local data. Connection checks only run when you click them.",
                        "",
                        "What you can do:",
                        "- Run the Binance read-only connection check (see the <a href=\"guide:binance-api\">Binance read-only API</a> guide) and the AI provider check, or Configure AI models.",
                        "- Switch the app language between English and Czech.",
                        "- Review or re-open your onboarding profile, or replay the app tour.",
                        "- Privacy &amp; data: Export diagnostics (a sanitized report with no keys or holdings, safe to share for support), Reset onboarding, or Delete local data.",
                        "",
                        "Everything here stays local to this machine. Delete local data only removes the files you select and never touches anything outside the app's own folder.",
                    ]
                ),
            },
            {
                "id": "page-help-guides",
                "section": "Using Coinductor",
                "title": "Help & Guides page",
                "summary": "Browse every built-in guide, including setup walkthroughs and these per-page explanations.",
                "body": "<br>".join(
                    [
                        "Help &amp; Guides collects all built-in guides in one place: AI and Binance setup walkthroughs, the safety model, portfolio roles, and a guide for each app page.",
                        "",
                        "The same guides are also available during onboarding, so you never have to enter the main app to read setup help. Links inside a guide open either an external page (in your browser) or another guide.",
                    ]
                ),
            },
        ]
