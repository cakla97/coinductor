"""Disconnecting the model must not take Binance access with it."""
from coinductor.local_data_reset import AI_PROVIDER_KEYS, LocalDataResetService


def test_the_ai_group_clears_only_the_model_keys(tmp_path, monkeypatch) -> None:
    """Stepping away from AI is not the same as removing every credential.

    CREDENTIALS already existed and clears everything; a user who simply wants
    to disconnect a model would have lost their Binance keys with it.
    """
    cleared: list[tuple[str, ...]] = []

    class FakeStore:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def stored_keys(self):
            return ("BINANCE_API_KEY", "BINANCE_API_SECRET", "LLM_BASE_URL", "LLM_MODEL")

        def clear(self, keys) -> None:
            cleared.append(tuple(keys))

    import coinductor.secret_store as secret_store

    monkeypatch.setattr(secret_store, "SecretStore", FakeStore)

    service = LocalDataResetService(root=tmp_path)
    service.execute(["AI_PROVIDER"])

    assert cleared == [("LLM_BASE_URL", "LLM_MODEL")]
    assert "BINANCE_API_KEY" not in cleared[0]


def test_the_credentials_group_still_clears_everything(tmp_path, monkeypatch) -> None:
    cleared: list[tuple[str, ...]] = []

    class FakeStore:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def stored_keys(self):
            return ("BINANCE_API_KEY", "LLM_BASE_URL")

        def clear(self, keys) -> None:
            cleared.append(tuple(keys))

    import coinductor.secret_store as secret_store

    monkeypatch.setattr(secret_store, "SecretStore", FakeStore)

    LocalDataResetService(root=tmp_path).execute(["CREDENTIALS"])

    assert cleared == [("BINANCE_API_KEY", "LLM_BASE_URL")]


def test_the_ai_group_names_every_key_the_wizard_writes() -> None:
    """A key the wizard writes but this list forgets stays connected."""
    from coinductor.secret_store import MANAGED_KEYS

    llm_keys = tuple(key for key in MANAGED_KEYS if key.startswith("LLM_"))
    assert set(AI_PROVIDER_KEYS) == set(llm_keys)
