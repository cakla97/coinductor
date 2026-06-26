from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tomllib


ROLE_OPTIONS = (
    "SYSTEM_DEFAULT",
    "PROTECTED_CORE",
    "PROTECTED_UTILITY",
    "TRADING_ALLOWED",
    "GRID_CANDIDATE",
    "REBALANCING_CANDIDATE",
    "FUNDING_SOURCE",
    "DUST_AIRDROP_FUNDING",
    "ACTIVE_STRATEGY",
    "STABLE",
    "UNCLASSIFIED",
)


def apply_asset_policy_overrides(config: dict, path: str | Path = "state/asset_policy_overrides.toml") -> dict:
    override_path = Path(path)
    if not override_path.exists():
        return config

    with override_path.open("rb") as handle:
        payload = tomllib.load(handle)
    overrides = payload.get("overrides", {})
    if not isinstance(overrides, dict):
        return config

    merged = deepcopy(config)
    for asset, details in overrides.items():
        if not isinstance(details, dict):
            continue
        role = str(details.get("role", "")).upper()
        if role in {"", "SYSTEM_DEFAULT"}:
            continue
        apply_asset_role(merged, str(asset).upper(), role)
    return merged


def apply_asset_role(config: dict, asset: str, role: str) -> None:
    asset = asset.upper()
    role = role.upper()
    quote = _quote_asset(config)
    symbol = f"{asset}{quote}"

    portfolio = config.setdefault("portfolio", {})
    tracked = portfolio.setdefault("tracked_assets", [])
    _append_unique(tracked, asset)
    portfolio.setdefault("asset_roles", {})[asset] = role

    strategy = config.setdefault("strategy", {})
    grid = config.setdefault("grid_bot", {})
    rebalancing_bot = config.setdefault("rebalancing_bot", {})
    capital = config.setdefault("capital_sourcing", {})
    dust = config.setdefault("dust_sourcing", {})

    strategy_symbols = strategy.setdefault("allowed_symbols", [])
    grid_symbols = grid.setdefault("allowed_symbols", [])
    preferred_grid_symbols = grid.setdefault("preferred_symbols", [])
    rebalance_assets = rebalancing_bot.setdefault("allowed_assets", [])
    source_assets = capital.setdefault("allowed_source_assets", [])
    protected_assets = capital.setdefault("protected_assets", [])
    dust_excluded = dust.setdefault("exclude_assets", [])

    if role in {"PROTECTED_CORE", "PROTECTED_UTILITY"}:
        _append_unique(protected_assets, asset)
        _remove_value(source_assets, asset)
        _append_unique(dust_excluded, asset)
        return

    if role != "STABLE":
        _remove_value(protected_assets, asset)

    if role in {"TRADING_ALLOWED", "ACTIVE_STRATEGY"}:
        _append_unique(strategy_symbols, symbol)
    if role in {"GRID_CANDIDATE", "ACTIVE_STRATEGY"}:
        _append_unique(grid_symbols, symbol)
        _append_unique(preferred_grid_symbols, symbol)
    if role in {"REBALANCING_CANDIDATE", "ACTIVE_STRATEGY"}:
        _append_unique(rebalance_assets, asset)
    if role == "FUNDING_SOURCE":
        _append_unique(source_assets, asset)
    if role == "DUST_AIRDROP_FUNDING":
        _remove_value(dust_excluded, asset)


def _quote_asset(config: dict) -> str:
    live_quote = config.get("live_confirm", {}).get("quote_asset")
    app_quote = config.get("app", {}).get("base_currency")
    return str(live_quote or app_quote or "USDC").upper()


def _append_unique(items: list, value: str) -> None:
    normalized = value.upper()
    existing = {str(item).upper() for item in items}
    if normalized not in existing:
        items.append(normalized)


def _remove_value(items: list, value: str) -> None:
    normalized = value.upper()
    items[:] = [item for item in items if str(item).upper() != normalized]
