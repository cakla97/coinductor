from __future__ import annotations

import json
import os
from pathlib import Path
import urllib.request

from trading_agent.config import default_config_path, load_config

from .models import AiModelDiscoveryResult, AiProviderHealthResult, AiProviderSnapshot
from .secret_store import load_secrets
from .service_strings import service_text


class AiProviderService:
    def __init__(
        self,
        config_path: str | Path | None = None,
        env_path: str | Path = ".env",
        language: str = "en",
    ):
        self.config_path = Path(config_path or default_config_path())
        self.env_path = Path(env_path)
        self.language = language

    def _t(self, key: str) -> str:
        return service_text(key, self.language)

    def inspect(self) -> AiProviderSnapshot:
        checks: list[dict[str, str]] = []
        if not self.config_path.exists():
            return AiProviderSnapshot(
                summary=self._t("ai_config_missing_summary"),
                checks=(
                    {
                        "name": self._t("ai_check_configuration"),
                        "status": "BLOCK",
                        "detail": str(self.config_path),
                    },
                ),
                context_sections=self._context_sections(),
            )

        config = load_config(self.config_path).raw
        env = self._env_values()
        ai = config.get("ai", {})
        provider = str(ai.get("provider", "openai_compatible"))
        base_url_key = str(ai.get("base_url_env", "LLM_BASE_URL"))
        api_key_name = str(ai.get("api_key_env", "LLM_API_KEY"))
        model_key = str(ai.get("model_env", "LLM_MODEL"))
        vision_model_key = str(ai.get("vision_model_env", "LLM_VISION_MODEL"))
        base_url = self._value(env, base_url_key)
        model = self._value(env, model_key)
        vision_model = self._value(env, vision_model_key)
        api_key = self._value(env, api_key_name)

        self._add(checks, self._t("ai_check_provider"), "PASS", provider, self._t("ai_group_ai"))
        self._add(
            checks,
            self._t("ai_check_endpoint"),
            "PASS" if base_url else "WARN",
            self._redact_url(base_url) if base_url else self._t("ai_set_env").format(key=base_url_key),
            self._t("ai_group_ai"),
        )
        self._add(
            checks,
            self._t("ai_check_model"),
            "PASS" if model else "WARN",
            model if model else self._t("ai_set_env").format(key=model_key),
            self._t("ai_group_ai"),
        )
        self._add(
            checks,
            self._t("ai_check_vision_model"),
            "PASS" if vision_model and supports_vision_model(vision_model) else "WARN",
            (
                vision_model
                if vision_model and supports_vision_model(vision_model)
                else self._t("ai_vision_not_recognized").format(model=vision_model)
                if vision_model
                else self._t("ai_vision_optional").format(key=vision_model_key)
            ),
            self._t("ai_group_ai"),
        )
        self._add(
            checks,
            self._t("ai_check_api_key"),
            "PASS" if api_key else "WARN",
            self._t("ai_api_key_configured")
            if api_key
            else self._t("ai_api_key_optional").format(key=api_key_name),
            self._t("ai_group_privacy"),
        )
        self._add(
            checks,
            self._t("ai_check_privacy_mode"),
            "PASS" if self._is_local_url(base_url) else "WARN",
            self._t("ai_privacy_local") if self._is_local_url(base_url) else self._t("ai_privacy_external"),
            self._t("ai_group_privacy"),
        )
        vision_summary = vision_model or (
            model if supports_vision_model(model) else self._t("ai_summary_not_configured")
        )
        summary = self._t("ai_summary").format(
            provider=provider,
            model=model or self._t("ai_summary_not_set"),
            vision=vision_summary,
            endpoint=self._redact_url(base_url) if base_url else self._t("ai_summary_no_endpoint"),
        )
        return AiProviderSnapshot(
            summary=summary,
            checks=tuple(checks),
            context_sections=self._context_sections(),
            base_url=self._redact_url(base_url),
            text_model=model,
            vision_model=vision_model,
        )

    def health_check(self) -> AiProviderHealthResult:
        if not self.config_path.exists():
            return AiProviderHealthResult("BLOCK", f"Missing config: {self.config_path}")

        load_secrets(self.env_path)
        config = load_config(self.config_path).raw
        ai = config.get("ai", {})
        base_url = os.getenv(str(ai.get("base_url_env", "LLM_BASE_URL")), "").rstrip("/")
        api_key = os.getenv(str(ai.get("api_key_env", "LLM_API_KEY")), "")
        text_model = os.getenv(str(ai.get("model_env", "LLM_MODEL")), "").strip()
        vision_model_key = str(ai.get("vision_model_env", "LLM_VISION_MODEL"))
        vision_model = os.getenv(vision_model_key, "").strip()
        if not base_url:
            return AiProviderHealthResult("BLOCK", "LLM_BASE_URL is not set.")
        if not text_model:
            return AiProviderHealthResult("BLOCK", "LLM_MODEL is not set.")
        if vision_model and not supports_vision_model(vision_model):
            return AiProviderHealthResult(
                "BLOCK",
                f"Configured vision model {vision_model} is not recognized as vision-capable.",
            )

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
        model_ids = {
            str(item.get("id", "")).strip().lower()
            for item in models
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        }
        if text_model.lower() not in model_ids:
            return AiProviderHealthResult(
                "BLOCK",
                f"Endpoint reachable, but text model {text_model} was not reported by /models.",
            )
        if vision_model and vision_model.lower() not in model_ids:
            return AiProviderHealthResult(
                "BLOCK",
                f"Text model ready, but vision model {vision_model} was not reported by /models.",
            )
        vision_detail = (
            f" Vision model ready: {vision_model}."
            if vision_model
            else " Vision model is optional and not configured."
        )
        return AiProviderHealthResult(
            "PASS",
            f"Endpoint reachable; {model_count} model(s) reported. Text model ready: {text_model}.{vision_detail}",
        )

    def discover_models(self, base_url: str, api_key: str = "") -> AiModelDiscoveryResult:
        normalized_url = base_url.strip().rstrip("/")
        if not normalized_url:
            return AiModelDiscoveryResult("BLOCK", "Enter the endpoint URL before detecting models.")

        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(f"{normalized_url}/models", headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            return AiModelDiscoveryResult("BLOCK", f"Could not reach {self._redact_url(normalized_url)}: {exc}")

        entries = payload.get("data", []) if isinstance(payload, dict) else []
        model_ids = sorted(
            {
                str(item.get("id", "")).strip()
                for item in entries
                if isinstance(item, dict) and str(item.get("id", "")).strip()
            }
        )
        if not model_ids:
            return AiModelDiscoveryResult(
                "BLOCK",
                f"{self._redact_url(normalized_url)} responded, but reported no installed models.",
            )
        return AiModelDiscoveryResult(
            "PASS",
            f"{len(model_ids)} model(s) reported by {self._redact_url(normalized_url)}.",
            tuple(model_ids),
        )

    def vision_support(self) -> tuple[bool, str]:
        config = load_config(self.config_path).raw if self.config_path.exists() else {}
        ai = config.get("ai", {})
        env = self._env_values()
        model_key = str(ai.get("model_env", "LLM_MODEL"))
        vision_model_key = str(ai.get("vision_model_env", "LLM_VISION_MODEL"))
        text_model = self._value(env, model_key)
        vision_model = self._value(env, vision_model_key)
        model = vision_model or text_model
        override = self._value(env, "LLM_VISION_ENABLED").strip().lower()
        if override in {"1", "true", "yes", "on"}:
            return (True, f"Vision explicitly enabled for {model or 'the configured model'}.")
        if override in {"0", "false", "no", "off"}:
            return (False, f"Vision explicitly disabled for {model or 'the configured model'}.")
        supported = supports_vision_model(model)
        if supported:
            source = "dedicated vision model" if vision_model else "active text model"
            return (True, f"{model} is configured as the {source} and is recognized as vision-capable.")
        return (
            False,
            f"{model or 'The configured model'} is treated as text-only. To analyze screenshots without replacing the text model, configure LLM_VISION_MODEL with a real vision model. LLM_VISION_ENABLED=true is an advanced detection override; it does not add image support and is safe only when the endpoint and model already accept images.",
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
        return tuple(
            {
                "name": service_text(f"ai_context_{slug}_name", self.language),
                "detail": service_text(f"ai_context_{slug}_detail", self.language),
            }
            for slug in ("safety", "portfolio", "privacy", "action")
        )


def supports_vision_model(model: str) -> bool:
    normalized = model.strip().lower().replace("_", "-")
    markers = (
        "vision", "llava", "moondream", "minicpm-v", "qwen2-vl", "qwen2.5-vl", "qwen2.5vl",
        "qwen3-vl", "qwen3vl", "pixtral", "gemma3", "gemma-3", "gpt-4o", "gpt-4.1", "gpt-5",
        "claude-3", "claude-4", "claude-sonnet", "claude-opus", "gemini-1.5", "gemini-2", "gemini-3",
    )
    return any(marker in normalized for marker in markers)
