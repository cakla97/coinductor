from __future__ import annotations

import json
import os
import re
from pathlib import Path
import urllib.error
import urllib.request
from urllib.parse import urlparse

from trading_agent.config import default_config_path, load_config

from .models import AiModelDiscoveryResult, AiProviderHealthResult, AiProviderSnapshot
from .secret_store import SecretStore, load_secrets
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
            return AiProviderHealthResult("BLOCK", self._t("aiph_missing_config").format(path=self.config_path))

        load_secrets(self.env_path)
        config = load_config(self.config_path).raw
        ai = config.get("ai", {})
        base_url_key = str(ai.get("base_url_env", "LLM_BASE_URL"))
        model_key = str(ai.get("model_env", "LLM_MODEL"))
        base_url = os.getenv(base_url_key, "").rstrip("/")
        api_key = os.getenv(str(ai.get("api_key_env", "LLM_API_KEY")), "")
        text_model = os.getenv(model_key, "").strip()
        vision_model_key = str(ai.get("vision_model_env", "LLM_VISION_MODEL"))
        vision_model = os.getenv(vision_model_key, "").strip()
        if not base_url:
            return AiProviderHealthResult("BLOCK", self._t("aiph_no_base_url").format(key=base_url_key))
        if not text_model:
            return AiProviderHealthResult("BLOCK", self._t("aiph_no_model").format(key=model_key))
        if vision_model and not supports_vision_model(vision_model):
            return AiProviderHealthResult(
                "BLOCK", self._t("aiph_vision_not_capable").format(model=vision_model)
            )

        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(f"{base_url}/models", headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            # Described rather than str(exc): a raw HTTPError reads as a network
            # fault, and with a cloud key a 401 is the likeliest failure.
            return AiProviderHealthResult(
                "BLOCK", self._t("aiph_endpoint_failed").format(reason=self._describe(exc))
            )

        models = payload.get("data", []) if isinstance(payload, dict) else []
        model_count = len(models) if isinstance(models, list) else 0
        model_ids = {
            str(item.get("id", "")).strip().lower()
            for item in models
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        }
        if text_model.lower() not in model_ids:
            return AiProviderHealthResult(
                "BLOCK", self._t("aiph_text_model_missing").format(model=text_model)
            )
        if vision_model and vision_model.lower() not in model_ids:
            return AiProviderHealthResult(
                "BLOCK", self._t("aiph_vision_model_missing").format(model=vision_model)
            )
        vision_detail = (
            self._t("aiph_vision_ready").format(model=vision_model)
            if vision_model
            else self._t("aiph_vision_absent")
        )
        return AiProviderHealthResult(
            "PASS",
            self._t("aiph_ok").format(count=model_count, model=text_model, vision=vision_detail),
        )

    def discover_models(self, base_url: str, api_key: str = "") -> AiModelDiscoveryResult:
        normalized_url = base_url.strip().rstrip("/")
        if not normalized_url:
            return AiModelDiscoveryResult("BLOCK", self._t("aidisc_no_url"))

        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(f"{normalized_url}/models", headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            return AiModelDiscoveryResult(
                "BLOCK",
                self._t("aidisc_unreachable").format(
                    url=self._redact_url(normalized_url), reason=self._describe(exc)
                ),
            )

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
                "BLOCK", self._t("aidisc_no_models").format(url=self._redact_url(normalized_url))
            )
        return AiModelDiscoveryResult(
            "PASS",
            self._t("aidisc_ok").format(count=len(model_ids), url=self._redact_url(normalized_url)),
            tuple(model_ids),
        )

    def _describe(self, exc: Exception) -> str:
        return _describe_provider_error(
            exc, czech=self.language.lower().startswith("cs"), technical=True
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
        # The keychain has to be consulted here too: a value saved only there
        # (never written to .env) is otherwise invisible to the status panels,
        # which is how a configured vision model looked "not configured".
        return os.getenv(key, "") or env.get(key, "") or SecretStore(self.env_path).get(key)

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


def _describe_provider_error(exc: Exception, *, czech: bool, technical: bool = False) -> str:
    """Explain a provider failure.

    ``technical`` picks the audience. Settings and the AI provider check are
    diagnostic surfaces where the raw OS reason is the most useful thing on
    screen ("connection refused" means Ollama is not running). The assistant
    chat is a conversation, where "[WinError 10061]" is noise - it gets the
    plain sentence instead.
    """
    if isinstance(exc, RuntimeError):
        return str(exc)
    # HTTPError subclasses OSError, so it has to be handled first. With a cloud
    # provider the usual failure is a rejected key, and reporting that as
    # "connection failed" would send the user chasing their network instead.
    if isinstance(exc, urllib.error.HTTPError):
        hint = _HTTP_HINTS.get(exc.code)
        detail = f" {hint[czech]}" if hint else ""
        return (
            f"poskytovatel AI odpověděl HTTP {exc.code}.{detail}"
            if czech
            else f"the AI provider returned HTTP {exc.code}.{detail}"
        )
    if isinstance(exc, OSError):
        base = (
            "AI endpoint se nepodařilo kontaktovat"
            if czech
            else "the AI endpoint could not be reached"
        )
        if not technical:
            return (
                f"{base} (spojení selhalo nebo vypršel časový limit)."
                if czech
                else f"{base} (connection failed or timed out)."
            )
        # Unwrap URLError, whose str() is the noisy "<urlopen error ...>" form.
        # Socket-level text, so it cannot carry the API key (that is a header).
        inner = getattr(exc, "reason", None)
        source = inner if isinstance(inner, BaseException) else exc
        reason = (getattr(source, "strerror", "") or str(source)).strip()
        return f"{base} ({reason})." if reason else f"{base}."
    return (
        f"neočekávaná chyba ({type(exc).__name__})."
        if czech
        else f"unexpected error ({type(exc).__name__})."
    )


# (Czech, English) hints for the statuses a cloud provider actually returns.
_HTTP_HINTS: dict[int, dict[bool, str]] = {
    401: {
        True: "Klíč API byl odmítnut - zkontrolujte LLM_API_KEY.",
        False: "The API key was rejected - check LLM_API_KEY.",
    },
    403: {
        True: "Přístup zamítnut - klíč nemá oprávnění k tomuto modelu.",
        False: "Access denied - the key is not allowed to use this model.",
    },
    404: {
        True: "Endpoint nebo model neexistuje - zkontrolujte LLM_BASE_URL a LLM_MODEL.",
        False: "Endpoint or model not found - check LLM_BASE_URL and LLM_MODEL.",
    },
    429: {
        True: "Vyčerpán limit požadavků nebo kredit - zkuste to za chvíli.",
        False: "Rate limit or quota reached - try again shortly.",
    },
}


def provider_kind(base_url: str) -> str:
    """Which provider the LLM_* variables currently point at: LOCAL/CLOUD/NONE.

    There is only one set of LLM_* variables, so exactly one provider can be
    active; saving either wizard panel replaces the other. The UI needs to say
    so, because two side-by-side panels read as two independent settings.
    """
    if not base_url.strip():
        return "NONE"
    host = (urlparse(base_url).hostname or "").lower()
    return "LOCAL" if host in {"127.0.0.1", "localhost", "::1"} else "CLOUD"


def supports_vision_model(model: str) -> bool:
    normalized = model.strip().lower().replace("_", "-")
    markers = (
        "vision", "llava", "moondream", "minicpm-v", "qwen2-vl", "qwen2.5-vl", "qwen2.5vl",
        "qwen3-vl", "qwen3vl", "pixtral", "gemma3", "gemma-3", "gpt-4o", "gpt-4.1", "gpt-5",
        "gpt-4-turbo", "gpt-4.5",
        "claude-3", "claude-4", "claude-sonnet", "claude-opus", "gemini-1.5", "gemini-2", "gemini-3",
    )
    if any(marker in normalized for marker in markers):
        return True
    # OpenAI's reasoning models accept images but carry no marker in the name,
    # and a substring match on "o3"/"o4" would fire on unrelated tags, so they
    # are matched against the whole name (with an optional -mini/-pro suffix).
    return bool(re.fullmatch(r"o[1345](-(mini|pro))?", normalized))
