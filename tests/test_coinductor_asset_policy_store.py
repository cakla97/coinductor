from coinductor.asset_policy_store import AssetPolicyStore


def test_asset_policy_store_saves_and_removes_role(tmp_path) -> None:
    path = tmp_path / "state" / "asset_policy_overrides.toml"
    store = AssetPolicyStore(path)

    store.save_role("bnb", "grid_candidate")

    assert store.load() == {"BNB": "GRID_CANDIDATE"}
    rendered = path.read_text(encoding="utf-8")
    assert "[overrides.BNB]" in rendered
    assert 'role = "GRID_CANDIDATE"' in rendered

    store.save_role("BNB", "SYSTEM_DEFAULT")

    assert store.load() == {}
    assert "overrides.BNB" not in path.read_text(encoding="utf-8")
