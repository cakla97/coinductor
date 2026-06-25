from coinductor.application import CoinductorApplication
from coinductor.models import RunOptions


def test_desktop_options_never_enable_submission() -> None:
    config = {
        "app": {"mock_data": True},
        "ai": {"commentary_enabled": False, "enabled": True},
        "live_confirm": {"enabled": False},
    }

    CoinductorApplication()._apply_options(
        config,
        RunOptions(
            data_mode="REAL",
            ai_summary=True,
            ai_proposals=False,
            live_preview=True,
        ),
    )

    assert config["app"]["mock_data"] is False
    assert config["ai"]["commentary_enabled"] is True
    assert config["ai"]["enabled"] is False
    assert config["live_confirm"]["enabled"] is True
    assert config["_runtime"]["live_submit"] is False
    assert config["_runtime"]["earn_redeem_submit"] is False
    assert config["_runtime"]["oco_protection_submit"] is False
