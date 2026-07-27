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


def test_disable_flag_keeps_the_real_keychain_out_of_tests(monkeypatch, tmp_path) -> None:
    """conftest sets this for the whole suite.

    Without it a test run resolves the developer's real credentials, so results
    depend on machine state and a health check can reach a live endpoint.
    """
    monkeypatch.setenv("COINDUCTOR_DISABLE_KEYCHAIN", "1")
    assert secret_store_module._keyring() is None

    env = tmp_path / ".env"
    env.write_text("BINANCE_API_KEY=only-from-env\n", encoding="utf-8")
    store = SecretStore(env)
    assert store.available() is False
    assert store.get("BINANCE_API_KEY") == "only-from-env"

    monkeypatch.setenv("COINDUCTOR_DISABLE_KEYCHAIN", "0")
    # "0" means enabled, so the flag cannot be left on by accident. What that
    # then resolves to is the machine's business: a headless CI runner has no
    # Secret Service, and _keyring() correctly degrades to None there. Assert
    # against the platform's own answer so this checks our logic, not the OS.
    import keyring

    backend = keyring.get_keyring()
    platform_has_one = backend is not None and "fail" not in type(backend).__module__.lower()
    assert (secret_store_module._keyring() is not None) is platform_has_one


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


def test_status_panels_see_keychain_only_values(monkeypatch, tmp_path) -> None:
    """Status readers must consult the keychain, not just os.environ/.env.

    They previously read only those two, so a value saved to the keychain and
    never written to .env - which is now the normal case - showed as missing:
    a configured vision model reported "not configured".
    """
    from coinductor.ai_provider import AiProviderService
    from coinductor.setup_service import SetupService

    fake = FakeKeyring()
    fake.set_password("Coinductor", "LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    fake.set_password("Coinductor", "LLM_MODEL", "qwen3:14b")
    fake.set_password("Coinductor", "LLM_VISION_MODEL", "qwen3-vl:8b-thinking")
    fake.set_password("Coinductor", "BINANCE_API_KEY", "k")
    fake.set_password("Coinductor", "BINANCE_API_SECRET", "s")
    _use(monkeypatch, fake)

    monkeypatch.chdir(tmp_path)
    for key in ("LLM_BASE_URL", "LLM_MODEL", "LLM_VISION_MODEL", "BINANCE_API_KEY", "BINANCE_API_SECRET"):
        monkeypatch.delenv(key, raising=False)
    config = tmp_path / "config.toml"
    config.write_text(
        """
[app]
mode = "DRY_RUN"
mock_data = true
database_path = "work/t.sqlite3"
reports_dir = "outputs/reports"

[strategy]
allowed_symbols = ["BTCUSDC"]

[ai]
enabled = true
""",
        encoding="utf-8",
    )
    env = tmp_path / ".env"  # deliberately absent

    snapshot = AiProviderService(config, env).inspect()
    assert snapshot.vision_model == "qwen3-vl:8b-thinking"
    assert AiProviderService(config, env).vision_support()[0] is True

    checks = {c["code"]: c for c in SetupService(config, env).inspect().checks if c["code"]}
    assert checks["BINANCE_READONLY"]["status"] == "PASS"
