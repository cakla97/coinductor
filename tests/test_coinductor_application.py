from coinductor.application import CoinductorApplication
from coinductor.models import RunOptions


def test_desktop_options_keep_submission_disabled_by_default() -> None:
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
    assert config["_runtime"]["mainnet_oco_confirm"] == ""


def test_desktop_options_enable_oco_submit_only_when_requested() -> None:
    config = {
        "app": {"mock_data": True},
        "ai": {"commentary_enabled": False, "enabled": False},
        "live_confirm": {"enabled": False},
    }

    CoinductorApplication()._apply_options(
        config,
        RunOptions(
            data_mode="REAL",
            ai_summary=True,
            ai_proposals=True,
            live_preview=True,
            oco_submit=True,
            oco_confirm="CONFIRM_MAINNET_OCO",
        ),
    )

    assert config["_runtime"]["live_submit"] is False
    assert config["_runtime"]["mainnet_confirm"] == ""
    assert config["_runtime"]["oco_protection_submit"] is True
    assert config["_runtime"]["mainnet_oco_confirm"] == "CONFIRM_MAINNET_OCO"


def test_desktop_options_enable_guarded_live_submit_only_when_requested() -> None:
    config = {
        "app": {"mock_data": True},
        "ai": {"commentary_enabled": False, "enabled": False},
        "live_confirm": {"enabled": False},
    }

    CoinductorApplication()._apply_options(
        config,
        RunOptions(
            data_mode="REAL",
            ai_summary=True,
            ai_proposals=True,
            live_preview=True,
            live_submit=True,
            live_confirm="CONFIRM_MAINNET_ORDER",
        ),
    )

    assert config["live_confirm"]["enabled"] is True
    assert config["_runtime"]["live_submit"] is True
    assert config["_runtime"]["mainnet_confirm"] == "CONFIRM_MAINNET_ORDER"
    assert config["_runtime"]["earn_redeem_submit"] is False
    assert config["_runtime"]["oco_protection_submit"] is False
