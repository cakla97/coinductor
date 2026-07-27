import pytest

from coinductor.secret_store import MANAGED_KEYS


@pytest.fixture(autouse=True)
def isolate_credentials(monkeypatch):
    """Start every test with no credentials resolvable from anywhere.

    Two leaks to close, both ending the same way - a test contacting a real
    endpoint with whatever key happened to be lying around:

    * SecretStore reads the OS keychain, so a run would otherwise pick up the
      developer's actual Binance and LLM keys.
    * ``load_env_file`` exports what it reads straight into ``os.environ`` and
      nothing put it back, so a test that wrote a throwaway .env left those
      values visible to every test that ran after it. That was masked while the
      connection checks refused to run without a .env on disk.

    Autouse so tests added later are covered too.
    """
    monkeypatch.setenv("COINDUCTOR_DISABLE_KEYCHAIN", "1")
    for key in MANAGED_KEYS:
        monkeypatch.delenv(key, raising=False)
