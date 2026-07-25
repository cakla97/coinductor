import os

from coinductor import secret_store as secret_store_module
from coinductor.secret_store import MANAGED_KEYS, SECRET_KEYS, SecretStore


class FakeKeyring:
    """Stands in for the OS keychain so tests never touch the real one."""

    def __init__(self, fail: bool = False):
        self.storage: dict[tuple[str, str], str] = {}
        self.fail = fail

    def get_password(self, service, key):
        if self.fail:
            raise RuntimeError("backend unavailable")
        return self.storage.get((service, key))

    def set_password(self, service, key, value):
        if self.fail:
            raise RuntimeError("backend unavailable")
        self.storage[(service, key)] = value

    def delete_password(self, service, key):
        if self.fail:
            raise RuntimeError("backend unavailable")
        del self.storage[(service, key)]


def _use(monkeypatch, keyring):
    monkeypatch.setattr(secret_store_module, "_keyring", lambda: keyring)


def test_every_credential_key_is_managed() -> None:
    # Managed keys are what load_into_environ applies; a secret missing from it
    # would silently keep reading from .env only.
    assert set(SECRET_KEYS) <= set(MANAGED_KEYS)
    for key in ("BINANCE_API_KEY", "BINANCE_LIVE_TRADE_API_SECRET", "LLM_API_KEY"):
        assert key in SECRET_KEYS


def test_keychain_value_wins_over_env_file(monkeypatch, tmp_path) -> None:
    fake = FakeKeyring()
    fake.set_password("Coinductor", "BINANCE_API_KEY", "from-keychain")
    _use(monkeypatch, fake)
    env = tmp_path / ".env"
    env.write_text("BINANCE_API_KEY=from-env\n", encoding="utf-8")

    assert SecretStore(env).get("BINANCE_API_KEY") == "from-keychain"


def test_env_file_is_the_fallback(monkeypatch, tmp_path) -> None:
    _use(monkeypatch, FakeKeyring())
    env = tmp_path / ".env"
    env.write_text('BINANCE_API_SECRET="from-env"\n', encoding="utf-8")

    assert SecretStore(env).get("BINANCE_API_SECRET") == "from-env"
    assert SecretStore(env).get("NOT_SET_ANYWHERE") == ""


def test_saving_uses_the_keychain_and_leaves_env_untouched(monkeypatch, tmp_path) -> None:
    """The app must not write credentials into .env when a keychain exists."""
    fake = FakeKeyring()
    _use(monkeypatch, fake)
    env = tmp_path / ".env"
    env.write_text("BINANCE_API_KEY=old-value\n# keep me\n", encoding="utf-8")
    before = env.read_text(encoding="utf-8")

    backend = SecretStore(env).set_many({"BINANCE_API_KEY": "new-value"})

    assert backend == "keychain"
    assert fake.storage[("Coinductor", "BINANCE_API_KEY")] == "new-value"
    assert env.read_text(encoding="utf-8") == before, ".env was modified"


def test_saving_falls_back_to_env_when_no_keychain(monkeypatch, tmp_path) -> None:
    """Without a keychain the keys must still be stored, not dropped."""
    monkeypatch.setattr(secret_store_module, "_keyring", lambda: None)
    env = tmp_path / ".env"

    backend = SecretStore(env).set_many({"BINANCE_API_KEY": "fallback-value"})

    assert backend == "env"
    assert "fallback-value" in env.read_text(encoding="utf-8")


def test_saving_falls_back_when_the_backend_raises(monkeypatch, tmp_path) -> None:
    _use(monkeypatch, FakeKeyring(fail=True))
    env = tmp_path / ".env"

    backend = SecretStore(env).set_many({"BINANCE_API_KEY": "value"})

    assert backend == "env"
    assert "value" in env.read_text(encoding="utf-8")


def test_load_into_environ_lets_the_keychain_override_a_stale_env(monkeypatch, tmp_path) -> None:
    fake = FakeKeyring()
    fake.set_password("Coinductor", "BINANCE_API_KEY", "current")
    _use(monkeypatch, fake)
    env = tmp_path / ".env"
    env.write_text("BINANCE_API_KEY=stale\nBINANCE_API_SECRET=only-in-env\n", encoding="utf-8")
    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_API_SECRET", raising=False)

    SecretStore(env).load_into_environ()

    assert os.environ["BINANCE_API_KEY"] == "current"
    # Keys only in .env still load, so an existing setup keeps working.
    assert os.environ["BINANCE_API_SECRET"] == "only-in-env"


def test_store_degrades_quietly_without_a_backend(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(secret_store_module, "_keyring", lambda: None)
    store = SecretStore(tmp_path / ".env")

    assert store.available() is False
    assert store.stored_keys() == ()
    store.delete()  # must not raise
