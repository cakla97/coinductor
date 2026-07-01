from __future__ import annotations

from pathlib import Path


ASSET_DIR = Path(__file__).resolve().parent / "assets" / "guides"


def _image(name: str, caption: str) -> dict[str, str]:
    return {"source": (ASSET_DIR / name).as_uri(), "caption": caption}


class GuideService:
    def list_guides(self) -> list[dict[str, str]]:
        return [
            {
                "id": "local-ai",
                "section": "AI setup",
                "title": "Local AI with Ollama",
                "summary": "Private local assistant for project help, report summaries, and future wizard guidance.",
                "body": "\n".join(
                    [
                        "Use this path when you want Coinductor to stay local-first.",
                        "",
                        "1. Open https://ollama.com/ and use the Download button to install Ollama for your operating system.",
                        "2. Pick a model that fits your hardware. Use Coinductor's Scan hardware button in the AI setup step for a local recommendation. Do not run random online PC scanners just to choose a model.",
                        "3. On https://ollama.com/search, search for the model recommended in step 2. Pull that exact model, for example qwen3:8b on smaller systems or qwen3:14b on stronger GPUs.",
                        "4. Keep Ollama running while Coinductor uses AI features. On Windows this usually means the Ollama icon remains visible in the system tray.",
                        "5. In Coinductor, set the local endpoint to http://127.0.0.1:11434/v1 and the model name to the model you pulled.",
                        "6. Run Check AI provider before relying on report summaries or assistant answers.",
                        "",
                        "Local AI can explain Coinductor, summarize reports, and help with onboarding. It cannot bypass deterministic safety gates or submit trades by itself.",
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
                "body": "\n".join(
                    [
                        "Cloud AI is optional and should be treated as an advanced alternative.",
                        "",
                        "Pricing warning: Chat subscriptions and API usage are usually separate products with separate pricing. ChatGPT Plus/Pro, Claude plans, or Gemini subscriptions do not automatically mean API calls from Coinductor are included.",
                        "",
                        "OpenAI example:",
                        "1. Open https://platform.openai.com/ and go to API Keys.",
                        "2. Add billing/limits in the provider dashboard if required.",
                        "3. In Coinductor, use https://api.openai.com/v1 as the endpoint.",
                        "4. Enter the model name you want to use.",
                        "5. Paste the API key and run Check AI provider.",
                        "",
                        "Privacy note: selected report, profile, and question context may be sent to the configured provider. Do not use cloud AI if you want all portfolio context to remain on your computer.",
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
                "body": "\n".join(
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
                    ]
                ),
                "images": [
                    _image("binance_api_management_sanitized.png", "Sanitized Binance dashboard screenshot with API Management highlighted."),
                    _image("binance_read_only_restrictions_sanitized.png", "Sanitized Binance API restrictions screen for a read-only key."),
                ],
            },
            {
                "id": "safety-model",
                "section": "Safety",
                "title": "Safety model",
                "summary": "How Coinductor separates recommendations, previews, guarded actions, and live execution.",
                "body": "\n".join(
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
                    ]
                ),
            },
            {
                "id": "portfolio-roles",
                "section": "Portfolio",
                "title": "Portfolio roles",
                "summary": "Understand protected assets, trading assets, funding sources, and manual overrides.",
                "body": "\n".join(
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
                    ]
                ),
            },
        ]
