"""How large an order the analysis may propose, read and written from the app.

Distinct from ``order_caps``, and the distinction is the whole point of the
screen. ``order_caps`` is the last backstop before an order reaches an
exchange: it truncates whatever arrives, and exists so a bug or a slipped
decimal cannot cost more than a number the user chose. These settings are one
layer earlier - they are how the analysis decides what an appropriate order
*is*, before anything is submitted.

Every setting here is a ceiling, and the order becomes the smallest of them
together with what the account can actually pay. That is why the screen can
honestly say what each one does: raising any single value can never enlarge an
order on its own, because some other ceiling is then the one that binds.

Three of these had no home at all. ``max_position_pct_per_asset``,
``max_total_trading_capital_pct`` and ``max_risk_per_trade_pct`` were written
by nothing, read by nothing until the sizing change, and visible only in a file
this app tells people they never have to open.
"""

from __future__ import annotations

from pathlib import Path

from .config_fields import Field, FieldGroup

STRATEGY_SECTION = "strategy"
RISK_SECTION = "risk"

# Ordered as they apply, widest intent first, so the screen can list them in an
# order that reads like an explanation rather than like a config file.
GROUP = FieldGroup(
    (
        # 100 means "no percentage ceiling", which is how configs written
        # before portfolio-relative sizing existed did behave.
        Field("tradePct", STRATEGY_SECTION, "max_trade_pct_of_portfolio", percent=True, default="100"),
        Field("tradeAmount", STRATEGY_SECTION, "quote_amount_usdt"),
        Field("positionPct", RISK_SECTION, "max_position_pct_per_asset", percent=True),
        Field("capitalPct", RISK_SECTION, "max_total_trading_capital_pct", percent=True),
        Field("riskPct", RISK_SECTION, "max_risk_per_trade_pct", percent=True),
    )
)


def read_sizing(config_path: str | Path) -> dict[str, str]:
    return GROUP.read(config_path)


def valid_sizing(values: dict[str, object]) -> bool:
    return GROUP.valid(values)


def apply_sizing_to_config(config_path: str | Path, values: dict[str, object]) -> dict[str, str]:
    return GROUP.apply(config_path, values)


def ensure_keys(config_path: str | Path) -> bool:
    return GROUP.ensure_keys(config_path)
