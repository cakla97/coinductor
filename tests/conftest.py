import pytest


@pytest.fixture(autouse=True)
def isolate_keychain(monkeypatch):
    """Keep the real OS keychain out of every test.

    SecretStore reads the keychain when resolving credentials, so without this a
    run would pick up the developer's actual Binance/LLM keys: results would
    depend on machine state and a health check could contact a real endpoint.
    Autouse so tests added later are covered too.
    """
    monkeypatch.setenv("COINDUCTOR_DISABLE_KEYCHAIN", "1")
