from __future__ import annotations

import os
from pathlib import Path
import sys

from trading_agent.config import default_config_path, load_config
from trading_agent.config_validator import ConfigValidator

from .models import SetupSnapshot
from .secret_store import SecretStore
from .service_strings import service_text


class SetupService:
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

    def inspect(self) -> SetupSnapshot:
        checks: list[dict[str, str]] = []
        self._add(checks, self._t("setup_check_python"), "PASS", sys.version.split()[0], self._t("setup_group_runtime"))

        if not self.config_path.exists():
            self._add(checks, self._t("setup_check_configuration"), "BLOCK", str(self.config_path), self._t("setup_group_runtime"))
            return self._snapshot(checks)

        config = load_config(self.config_path)
        validation = ConfigValidator().validate(config.raw)
        errors = [issue for issue in validation.issues if issue.severity == "ERROR"]
        warnings = [issue for issue in validation.issues if issue.severity == "WARNING"]
        if validation.has_errors:
            detail = self._t("setup_config_errors").format(errors=len(errors), warnings=len(warnings))
            self._add(checks, self._t("setup_check_configuration"), "BLOCK", detail, self._t("setup_group_runtime"))
        elif warnings:
            self._add(
                checks,
                self._t("setup_check_configuration"),
                "WARN",
                self._t("setup_config_valid_with_warnings").format(warnings=len(warnings)),
                self._t("setup_group_runtime"),
            )
        else:
            self._add(checks, self._t("setup_check_configuration"), "PASS", self._t("setup_config_valid"), self._t("setup_group_runtime"))

        env = self._env_values()
        # Credential storage, not file presence: with an OS keychain there is
        # deliberately no .env, so checking for the file would warn the user to
        # create something they must not need.
        keychain = SecretStore(env_path=self.env_path).available()
        self._add(
            checks,
            self._t("setup_check_credential_store"),
            "PASS" if keychain or self.env_path.exists() else "WARN",
            self._t("setup_creds_keychain")
            if keychain
            else self._t("setup_creds_envfile")
            if self.env_path.exists()
            else self._t("setup_creds_none"),
            self._t("setup_group_runtime"),
        )
        self._credential_check(
            checks,
            env,
            self._t("setup_check_binance_readonly"),
            "BINANCE_API_KEY",
            "BINANCE_API_SECRET",
            self._t("setup_binance_readonly_missing"),
            code="BINANCE_READONLY",
        )
        self._credential_check(
            checks,
            env,
            self._t("setup_check_binance_testnet"),
            "BINANCE_TESTNET_API_KEY",
            "BINANCE_TESTNET_API_SECRET",
            self._t("setup_binance_testnet_missing"),
            code="BINANCE_TESTNET",
        )
        self._credential_check(
            checks,
            env,
            self._t("setup_check_binance_live"),
            "BINANCE_LIVE_TRADE_API_KEY",
            "BINANCE_LIVE_TRADE_API_SECRET",
            self._t("setup_binance_live_missing"),
            code="BINANCE_LIVE",
        )

        ai_config = config.raw.get("ai", {})
        base_url_key = str(ai_config.get("base_url_env", "LLM_BASE_URL"))
        model_key = str(ai_config.get("model_env", "LLM_MODEL"))
        base_url = self._value(env, base_url_key)
        model = self._value(env, model_key)
        if base_url and model:
            self._add(
                checks,
                self._t("setup_check_local_ai"),
                "PASS",
                self._t("setup_ai_configured_model").format(model=model),
                self._t("setup_group_ai"),
            )
        else:
            self._add(
                checks,
                self._t("setup_check_local_ai"),
                "WARN",
                self._t("setup_ai_missing"),
                self._t("setup_group_ai"),
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
            self._t("setup_check_data_folders"),
            "PASS" if not missing else "WARN",
            self._t("setup_folders_ready")
            if not missing
            else self._t("setup_folders_created").format(paths=", ".join(missing)),
            self._t("setup_group_storage"),
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
        code: str = "",
    ) -> None:
        configured = bool(self._value(env, key_name) and self._value(env, secret_name))
        self._add(
            checks,
            name,
            "PASS" if configured else "WARN",
            self._t("setup_credentials_configured") if configured else missing_detail,
            self._t("setup_group_binance"),
            code=code,
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
        # Include the keychain, or a credential stored only there reads as missing.
        return os.getenv(key, "") or env.get(key, "") or SecretStore(self.env_path).get(key)

    def _add(
        self,
        checks: list[dict[str, str]],
        name: str,
        status: str,
        detail: str,
        group: str,
        code: str = "",
    ) -> None:
        # `code` is a stable identifier: other services match on it instead of
        # the translated `name`.
        checks.append({"code": code, "name": name, "status": status, "detail": detail, "group": group})

    def _snapshot(self, checks: list[dict[str, str]]) -> SetupSnapshot:
        return SetupSnapshot(
            checks=tuple(checks),
            passed=sum(item["status"] == "PASS" for item in checks),
            warnings=sum(item["status"] == "WARN" for item in checks),
            blocked=sum(item["status"] == "BLOCK" for item in checks),
        )
