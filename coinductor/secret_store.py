"""Credential storage backed by the OS keychain, with a .env fallback.

Values the app saves go to the OS keychain (Windows Credential Manager via
``keyring``). Reads prefer the keychain and fall back to ``.env`` so an existing
setup keeps working untouched: this module never writes to or deletes from
``.env`` unless the keychain is unavailable, in which case it degrades to the
previous behaviour rather than losing the user's keys.

A fresh install therefore never stores credentials in plaintext, and there is no
migration step: re-saving a key in the wizard or Settings moves it.
"""

from __future__ import annotations

import os
from pathlib import Path

from .env_writer import EnvWriter

SERVICE_NAME = "Coinductor"

# Credentials. These are the values that must not sit in plaintext.
SECRET_KEYS: tuple[str, ...] = (
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "BINANCE_TESTNET_API_KEY",
    "BINANCE_TESTNET_API_SECRET",
    "BINANCE_LIVE_TRADE_API_KEY",
    "BINANCE_LIVE_TRADE_API_SECRET",
    "LLM_API_KEY",
)

# Endpoint/model settings are not secret, but routing them through the same
# store keeps one write path and honours "the app does not write .env".
MANAGED_KEYS: tuple[str, ...] = SECRET_KEYS + (
    "LLM_BASE_URL",
    "LLM_MODEL",
    "LLM_VISION_MODEL",
)


def _keyring():
    """The keyring module, or None when unusable.

    Import and backend probing are both guarded: a missing dependency or an
    unsupported backend must degrade, never crash the app at startup.

    ``COINDUCTOR_DISABLE_KEYCHAIN=1`` forces the .env-only path. Tests set it so
    a run can never read or write the developer's real credential store, which
    would otherwise make results depend on machine state.
    """
    if os.environ.get("COINDUCTOR_DISABLE_KEYCHAIN", "").strip() not in ("", "0"):
        return None
    try:
        import keyring  # noqa: PLC0415

        backend = keyring.get_keyring()
        if backend is None or "fail" in type(backend).__module__.lower():
            return None
        return keyring
    except Exception:
        return None


class SecretStore:
    def __init__(self, env_path: str | Path = ".env"):
        self.env_path = Path(env_path)

    def available(self) -> bool:
        """Whether the OS keychain can be used on this machine."""
        return _keyring() is not None

    def get(self, key: str) -> str:
        """Keychain first, then .env; empty string when unset."""
        keyring = _keyring()
        if keyring is not None:
            try:
                value = keyring.get_password(SERVICE_NAME, key)
                if value:
                    return value
            except Exception:
                pass
        return self._env_file_values().get(key, "")

    def set_many(self, values: dict[str, str]) -> str:
        """Store values, returning the backend used: 'keychain' or 'env'.

        Falls back to the .env writer when no keychain is available so keys are
        never silently dropped on an unsupported system.
        """
        cleaned = {
            key: value.strip()
            for key, value in values.items()
            if key and value is not None and value.strip()
        }
        if not cleaned:
            return "keychain" if self.available() else "env"

        keyring = _keyring()
        if keyring is None:
            EnvWriter(self.env_path).update(cleaned)
            return "env"

        try:
            for key, value in cleaned.items():
                keyring.set_password(SERVICE_NAME, key, value)
                os.environ[key] = value
        except Exception:
            EnvWriter(self.env_path).update(cleaned)
            return "env"
        return "keychain"

    def delete(self, keys: tuple[str, ...] = MANAGED_KEYS) -> None:
        """Remove values from the keychain. Leaves .env alone."""
        keyring = _keyring()
        if keyring is None:
            return
        for key in keys:
            try:
                keyring.delete_password(SERVICE_NAME, key)
            except Exception:
                # Not stored, or the backend refused: nothing to remove.
                continue

    def stored_keys(self) -> tuple[str, ...]:
        """Managed keys currently held in the keychain."""
        keyring = _keyring()
        if keyring is None:
            return ()
        found: list[str] = []
        for key in MANAGED_KEYS:
            try:
                if keyring.get_password(SERVICE_NAME, key):
                    found.append(key)
            except Exception:
                continue
        return tuple(found)

    def load_into_environ(self) -> None:
        """Populate os.environ: .env first, then let keychain values win.

        Keychain values override because they are what the app itself saved; a
        leftover .env entry must not shadow a key the user just re-entered.
        """
        from trading_agent.env import load_env_file  # noqa: PLC0415

        load_env_file(self.env_path)
        keyring = _keyring()
        if keyring is None:
            return
        for key in MANAGED_KEYS:
            try:
                value = keyring.get_password(SERVICE_NAME, key)
            except Exception:
                continue
            if value:
                os.environ[key] = value

    def _env_file_values(self) -> dict[str, str]:
        values: dict[str, str] = {}
        if not self.env_path.exists():
            return values
        for raw_line in self.env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
        return values


def load_secrets(env_path: str | Path = ".env") -> None:
    """Drop-in for load_env_file that also applies keychain values."""
    SecretStore(env_path).load_into_environ()
