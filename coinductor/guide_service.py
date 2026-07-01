from __future__ import annotations


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
                        "1. Install Ollama from the official Ollama website.",
                        "2. Pick a model that fits your hardware. Smaller PCs should start with smaller models; stronger GPUs can try 14B-class models.",
                        "3. Pull the model in Ollama, for example qwen3:8b or qwen3:14b.",
                        "4. Keep Ollama running while Coinductor uses AI features.",
                        "5. In Coinductor, set the local endpoint to http://127.0.0.1:11434/v1 and the model name to the model you pulled.",
                        "6. Run Check AI provider before relying on report summaries or assistant answers.",
                        "",
                        "Local AI can explain Coinductor, summarize reports, and help with onboarding. It cannot bypass deterministic safety gates or submit trades by itself.",
                    ]
                ),
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
                        "Important: Chat subscriptions and API usage are usually separate products. ChatGPT Plus/Pro, Claude plans, or Gemini subscriptions do not automatically mean API calls from Coinductor are included.",
                        "",
                        "OpenAI example:",
                        "1. Open OpenAI Platform and create an API key.",
                        "2. Add billing/limits in the provider dashboard if required.",
                        "3. In Coinductor, use https://api.openai.com/v1 as the endpoint.",
                        "4. Enter the model name you want to use.",
                        "5. Paste the API key and run Check AI provider.",
                        "",
                        "Privacy note: selected report, profile, and question context may be sent to the configured provider. Do not use cloud AI if you want all portfolio context to remain on your computer.",
                    ]
                ),
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
                        "Protected assets are treated as long-term holdings and should not be used as routine funding.",
                        "Trading assets can be considered for guarded spot-trade recommendations.",
                        "Funding sources can provide capital within configured limits.",
                        "Dust or airdrop assets are small holdings that may be converted into operating capital when rules allow it.",
                        "",
                        "Manual overrides are available because different users care about different assets. Overrides can change eligibility, but they must not disable global risk limits, loss stops, or confirmation gates.",
                    ]
                ),
            },
        ]
