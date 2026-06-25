from __future__ import annotations

import os
from pathlib import Path
import sys

from trading_agent.config import load_config
from trading_agent.config_validator import ConfigValidator

from .models import SetupSnapshot


class SetupService:
    def __init__(
        self,
        config_path: str | Path = "config.example.toml",
        env_path: str | Path = ".env",
    ):
        self.config_path = Path(config_path)
        self.env_path = Path(env_path)

    def inspect(self) -> SetupSnapshot:
        checks: list[dict[str, str]] = []
        self._add(checks, "Python", "PASS", sys.version.split()[0], "Runtime")

        if not self.config_path.exists():
            self._add(checks, "Configuration", "BLOCK", str(self.config_path), "Runtime")
            return self._snapshot(checks)

        config = load_config(self.config_path)
        validation = ConfigValidator().validate(config.raw)
        errors = [issue for issue in validation.issues if issue.severity == "ERROR"]
        warnings = [issue for issue in validation.issues if issue.severity == "WARNING"]
        if validation.has_errors:
            detail = f"{len(errors)} error(s), {len(warnings)} warning(s)"
            self._add(checks, "Configuration", "BLOCK", detail, "Runtime")
        elif warnings:
            self._add(
                checks,
                "Configuration",
                "WARN",
                f"Valid with {len(warnings)} warning(s)",
                "Runtime",
            )
        else:
            self._add(checks, "Configuration", "PASS", "Valid", "Runtime")

        env = self._env_values()
        self._add(
            checks,
            "Environment file",
            "PASS" if self.env_path.exists() else "WARN",
            "Present" if self.env_path.exists() else "Create .env before connecting services",
            "Runtime",
        )
        self._credential_check(
            checks,
            env,
            "Binance read-only",
            "BINANCE_API_KEY",
            "BINANCE_API_SECRET",
            "Required for real portfolio analysis",
        )
        self._credential_check(
            checks,
            env,
            "Binance Spot Testnet",
            "BINANCE_TESTNET_API_KEY",
            "BINANCE_TESTNET_API_SECRET",
            "Recommended before mainnet",
        )
        self._credential_check(
            checks,
            env,
            "Binance live trading",
            "BINANCE_LIVE_TRADE_API_KEY",
            "BINANCE_LIVE_TRADE_API_SECRET",
            "Optional; guarded execution only",
        )

        ai_config = config.raw.get("ai", {})
        base_url_key = str(ai_config.get("base_url_env", "LLM_BASE_URL"))
        model_key = str(ai_config.get("model_env", "LLM_MODEL"))
        base_url = self._value(env, base_url_key)
        model = self._value(env, model_key)
        if base_url and model:
            self._add(checks, "Local AI endpoint", "PASS", f"Configured model: {model}", "AI")
        else:
            self._add(
                checks,
                "Local AI endpoint",
                "WARN",
                "Optional; offline help remains available",
                "AI",
            )

        required_dirs = (
            config.reports_dir,
            Path(config.raw.get("research", {}).get("notes_dir", "research/notes")),
            Path(config.raw.get("research", {}).get("requests_dir", "research/requests")),
            config.database_path.parent,
        )
        missing = [str(path) for path in required_dirs if not path.exists()]
        self._add(
            checks,
            "Local data folders",
            "PASS" if not missing else "WARN",
            "Ready" if not missing else f"Created on first run: {', '.join(missing)}",
            "Storage",
        )
        return self._snapshot(checks)

    def _credential_check(
        self,
        checks: list[dict[str, str]],
        env: dict[str, str],
        name: str,
        key_name: str,
        secret_name: str,
        missing_detail: str,
    ) -> None:
        configured = bool(self._value(env, key_name) and self._value(env, secret_name))
        self._add(
            checks,
            name,
            "PASS" if configured else "WARN",
            "Configured" if configured else missing_detail,
            "Binance",
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

    def _add(
        self,
        checks: list[dict[str, str]],
        name: str,
        status: str,
        detail: str,
        group: str,
    ) -> None:
        checks.append({"name": name, "status": status, "detail": detail, "group": group})

    def _snapshot(self, checks: list[dict[str, str]]) -> SetupSnapshot:
        return SetupSnapshot(
            checks=tuple(checks),
            passed=sum(item["status"] == "PASS" for item in checks),
            warnings=sum(item["status"] == "WARN" for item in checks),
            blocked=sum(item["status"] == "BLOCK" for item in checks),
        )
