from __future__ import annotations

import json
import os
from pathlib import Path
import urllib.request

from trading_agent.config import load_config
from trading_agent.env import load_env_file

from .models import AiProviderHealthResult, AiProviderSnapshot


class AiProviderService:
    def __init__(
        self,
        config_path: str | Path = "config.example.toml",
        env_path: str | Path = ".env",
    ):
        self.config_path = Path(config_path)
        self.env_path = Path(env_path)

    def inspect(self) -> AiProviderSnapshot:
        checks: list[dict[str, str]] = []
        if not self.config_path.exists():
            return AiProviderSnapshot(
                summary="AI settings are unavailable because config is missing.",
                checks=({"name": "Configuration", "status": "BLOCK", "detail": str(self.config_path)},),
                context_sections=self._context_sections(),
            )

        config = load_config(self.config_path).raw
        env = self._env_values()
        ai = config.get("ai", {})
        provider = str(ai.get("provider", "openai_compatible"))
        base_url_key = str(ai.get("base_url_env", "LLM_BASE_URL"))
        api_key_name = str(ai.get("api_key_env", "LLM_API_KEY"))
        model_key = str(ai.get("model_env", "LLM_MODEL"))
        base_url = self._value(env, base_url_key)
        model = self._value(env, model_key)
        api_key = self._value(env, api_key_name)

        self._add(checks, "Provider", "PASS", provider, "AI")
        self._add(
            checks,
            "Endpoint",
            "PASS" if base_url else "WARN",
            self._redact_url(base_url) if base_url else f"Set {base_url_key}",
            "AI",
        )
        self._add(
            checks,
            "Model",
            "PASS" if model else "WARN",
            model if model else f"Set {model_key}",
            "AI",
        )
        self._add(
            checks,
            "API key",
            "PASS" if api_key else "WARN",
            "Configured" if api_key else f"Optional for local providers; set {api_key_name} for cloud providers",
            "Privacy",
        )
        self._add(
            checks,
            "Privacy mode",
            "PASS" if self._is_local_url(base_url) else "WARN",
            "Local endpoint" if self._is_local_url(base_url) else "External/cloud endpoint or not configured",
            "Privacy",
        )
        summary = (
            f"{provider}: {model or 'model not set'} at {self._redact_url(base_url) if base_url else 'no endpoint'}"
        )
        return AiProviderSnapshot(
            summary=summary,
            checks=tuple(checks),
            context_sections=self._context_sections(),
        )

    def health_check(self) -> AiProviderHealthResult:
        if not self.config_path.exists():
            return AiProviderHealthResult("BLOCK", f"Missing config: {self.config_path}")

        load_env_file(self.env_path)
        config = load_config(self.config_path).raw
        ai = config.get("ai", {})
        base_url = os.getenv(str(ai.get("base_url_env", "LLM_BASE_URL")), "").rstrip("/")
        api_key = os.getenv(str(ai.get("api_key_env", "LLM_API_KEY")), "")
        if not base_url:
            return AiProviderHealthResult("BLOCK", "LLM_BASE_URL is not set.")

        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(f"{base_url}/models", headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            return AiProviderHealthResult("BLOCK", f"AI endpoint check failed: {exc}")

        models = payload.get("data", []) if isinstance(payload, dict) else []
        model_count = len(models) if isinstance(models, list) else 0
        return AiProviderHealthResult("PASS", f"Endpoint reachable; {model_count} model(s) reported.")

    def vision_support(self) -> tuple[bool, str]:
        config = load_config(self.config_path).raw if self.config_path.exists() else {}
        ai = config.get("ai", {})
        env = self._env_values()
        model_key = str(ai.get("model_env", "LLM_MODEL"))
        model = self._value(env, model_key)
        override = self._value(env, "LLM_VISION_ENABLED").strip().lower()
        if override in {"1", "true", "yes", "on"}:
            return (True, f"Vision explicitly enabled for {model or 'the configured model'}.")
        if override in {"0", "false", "no", "off"}:
            return (False, f"Vision explicitly disabled for {model or 'the configured model'}.")
        supported = supports_vision_model(model)
        if supported:
            return (True, f"{model} is recognized as a vision-capable model.")
        return (
            False,
            f"{model or 'The configured model'} is treated as text-only. To analyze screenshots, configure a real vision model. LLM_VISION_ENABLED=true is an advanced detection override; it does not add image support and is safe only when the endpoint and model already accept images.",
        )

    def _env_values(self) -> dict[str, str]:
        values: dict[str, str] = {}
        if self.env_path.exists():
            for raw_line in self.env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
        return values

    def _value(self, env: dict[str, str], key: str) -> str:
        return os.getenv(key, "") or env.get(key, "")

    def _redact_url(self, value: str) -> str:
        if not value:
            return ""
        return value.rstrip("/")

    def _is_local_url(self, value: str) -> bool:
        lowered = value.lower()
        return lowered.startswith("http://127.0.0.1") or lowered.startswith("http://localhost")

    def _add(
        self,
        checks: list[dict[str, str]],
        name: str,
        status: str,
        detail: str,
        group: str,
    ) -> None:
        checks.append({"name": name, "status": status, "detail": detail, "group": group})

    def _context_sections(self) -> tuple[dict[str, str], ...]:
        return (
            {
                "name": "Safety contract",
                "detail": "AI can explain, summarize, rank bounded options, and prepare intents; deterministic code owns execution limits.",
            },
            {
                "name": "Portfolio context",
                "detail": "Assistant context includes latest real run, portfolio roles, strategy recommendations, and local report paths.",
            },
            {
                "name": "Privacy boundary",
                "detail": "Local providers keep prompts on this machine; cloud providers may receive selected report and portfolio context.",
            },
            {
                "name": "Action boundary",
                "detail": "Changing policy, funding, or execution state will require structured intents, validation, and confirmation.",
            },
        )


def supports_vision_model(model: str) -> bool:
    normalized = model.strip().lower().replace("_", "-")
    markers = (
        "vision", "llava", "moondream", "minicpm-v", "qwen2-vl", "qwen2.5-vl", "qwen2.5vl",
        "qwen3-vl", "qwen3vl", "pixtral", "gemma3", "gemma-3", "gpt-4o", "gpt-4.1", "gpt-5",
        "claude-3", "claude-4", "claude-sonnet", "claude-opus", "gemini-1.5", "gemini-2", "gemini-3",
    )
    return any(marker in normalized for marker in markers)
