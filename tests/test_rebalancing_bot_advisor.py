from decimal import Decimal

from trading_agent.models import PortfolioAnalysis, PortfolioAssetValuation
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
            "allowed_assets": ["BTC", "ETH", "SOL"],
            "min_assets": 2,
            "threshold_pct": 5,
            "min_asset_value_usdt": 25,
            "min_investment_usdt": 50,
            "max_investment_usdt": 100,
            "max_portfolio_pct": 20,
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

    result = RebalancingBotAdvisor(_config()).recommend(portfolio)

    assert result.deployment_allowed is True
    assert result.investment_usdt == Decimal("100.00")
    assert sum((item.target_weight_pct for item in result.assets), Decimal("0")) == Decimal("100.0")
    assert [item.asset for item in result.assets] == ["BTC", "ETH", "SOL"]
    assert "BNB" in result.excluded_assets


def test_material_wbeth_informs_eth_weight_without_forcing_conversion() -> None:
    portfolio = _portfolio(
        _asset("BTC", "CORE", "300", "50"),
        _asset("WBETH", "PROTECTED", "200", "33.3"),
        _asset("SOL", "CAPITAL_SOURCE", "100", "16.7"),
    )

    result = RebalancingBotAdvisor(_config()).recommend(portfolio)

    assert result.deployment_allowed is True
    assert not result.blockers
    assert [item.asset for item in result.assets] == ["BTC", "ETH", "SOL"]
    assert result.assets[1].status == "FUNDED_FROM_USDC"
    assert any("Keep existing WBETH outside" in step for step in result.manual_steps)
