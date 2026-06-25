from decimal import Decimal

from trading_agent.models import Balance, PortfolioAnalysis, PortfolioAssetValuation
from trading_agent.rebalancing_bot_advisor import RebalancingBotAdvisor


def _asset(asset: str, role: str, value: str, allocation: str) -> PortfolioAssetValuation:
    amount = Decimal(value)
    return PortfolioAssetValuation(
        asset=asset,
        role=role,
        price_usdt=Decimal("1"),
        spot_value_usdt=amount,
        flexible_value_usdt=Decimal("0"),
        locked_value_usdt=Decimal("0"),
        total_value_usdt=amount,
        allocation_pct=Decimal(allocation),
        target_pct=None,
        gap_pct=None,
        rebalance_action="HOLD",
    )


def _portfolio(*assets: PortfolioAssetValuation) -> PortfolioAnalysis:
    total = sum((item.total_value_usdt for item in assets), Decimal("0"))
    return PortfolioAnalysis(total, total, Decimal("0"), Decimal("0"), total, Decimal("0"), assets, (), (), "", "")


def _config() -> dict:
    return {
        "rebalancing_bot": {
            "enabled": True,
            "mode": "THRESHOLD",
            "allocation_method": "CUSTOM",
            "auto_rebalance_mode": "BY_RATIO",
            "allowed_assets": ["BTC", "ETH", "SOL"],
            "min_assets": 2,
            "threshold_pct": 5,
            "min_asset_value_usdt": 25,
            "min_investment_usdt": 200,
            "max_investment_usdt": 200,
            "max_portfolio_pct": 100,
            "trigger_price_enabled": False,
            "stop_trigger_enabled": False,
            "sell_all_coins_on_stop": False,
            "funding": {
                "source_priority": ["PEPE", "DOGE", "ADA", "DOT", "WLD", "SOL"],
                "full_exit_assets": ["PEPE", "DOGE", "ADA", "DOT"],
                "reserve_source_assets": ["WLD", "SOL"],
                "max_source_pct_per_reserve_asset": 15,
                "max_source_pct_wld": 30,
                "min_remaining_value_usdt": 50,
            },
        },
        "capital_sourcing": {"protected_assets": ["BTC", "ETH", "WBETH", "BNB"]},
    }


def test_preserves_relative_weights_and_caps_investment() -> None:
    portfolio = _portfolio(
        _asset("BTC", "CORE", "300", "50"),
        _asset("ETH", "CORE", "150", "25"),
        _asset("SOL", "CAPITAL_SOURCE", "75", "12.5"),
        _asset("BNB", "PROTECTED_UTILITY", "75", "12.5"),
    )

    result = RebalancingBotAdvisor(_config()).recommend(
        portfolio,
        [Balance("USDC", Decimal("200"))],
    )

    assert result.deployment_allowed is True
    assert result.investment_usdt == Decimal("200.00")
    assert sum((item.target_weight_pct for item in result.assets), Decimal("0")) == Decimal("100.0")
    assert [item.asset for item in result.assets] == ["BTC", "ETH", "SOL"]
    assert "BNB" in result.excluded_assets


def test_material_wbeth_informs_eth_weight_without_forcing_conversion() -> None:
    portfolio = _portfolio(
        _asset("BTC", "CORE", "300", "50"),
        _asset("WBETH", "PROTECTED", "200", "33.3"),
        _asset("SOL", "CAPITAL_SOURCE", "100", "16.7"),
    )

    result = RebalancingBotAdvisor(_config()).recommend(
        portfolio,
        [Balance("USDC", Decimal("200"))],
    )

    assert result.deployment_allowed is True
    assert not result.blockers
    assert [item.asset for item in result.assets] == ["BTC", "ETH", "SOL"]
    assert result.assets[1].status == "FUNDED_FROM_USDC"
    assert any("Keep existing WBETH outside" in step for step in result.manual_steps)
    assert any("Select Equal" in step for step in result.manual_steps)
    assert any("By Ratio" in step for step in result.manual_steps)
    assert any("Sell All Coins on Stop: OFF" in step for step in result.manual_steps)


def test_funding_plan_uses_legacy_then_capped_reserves_and_reports_gap() -> None:
    portfolio = _portfolio(
        _asset("BTC", "CORE", "214", "26.5"),
        _asset("WBETH", "PROTECTED", "95", "11.8"),
        _asset("SOL", "CAPITAL_SOURCE", "96", "11.9"),
        _asset("WLD", "SPECULATIVE_SOURCE", "60", "7.4"),
        _asset("PEPE", "SPECULATIVE_LEGACY", "14", "1.7"),
        _asset("DOGE", "SPECULATIVE_LEGACY", "12", "1.5"),
        _asset("ADA", "LEGACY_ALT", "13", "1.6"),
        _asset("DOT", "LEGACY_ALT", "1", "0.1"),
        _asset("USDC", "STABLE", "12", "1.5"),
    )

    result = RebalancingBotAdvisor(_config()).recommend(
        portfolio,
        [Balance("USDC", Decimal("0"), flexible_amount=Decimal("12"))],
    )

    assert result.investment_usdt == Decimal("200.00")
    assert result.deployment_allowed is False
    assert result.funding_plan is not None
    assert [item.asset for item in result.funding_plan.items] == ["PEPE", "DOGE", "ADA", "DOT", "WLD", "SOL"]
    assert result.funding_plan.items[4].value_usdt == Decimal("10.00")
    assert result.funding_plan.items[5].value_usdt == Decimal("14.40")
    assert any("uncovered" in blocker for blocker in result.blockers)
    assert any("After funding is complete" in step for step in result.manual_steps)
    assert any("By Ratio" in step for step in result.manual_steps)
