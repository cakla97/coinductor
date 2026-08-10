"""How much may move from Flexible Earn to Spot, read and written from the app.

Kept apart from ``trade_sizing`` because it answers a different question.
Sizing decides how large an order is worth making; this decides how much of
your savings the app may reach for to pay for one. Putting them on one screen
would repeat the confusion that had an Earn redemption limit capping trade
size for as long as it did.

Nothing here is a withdrawal. A redemption moves USDC from Simple Earn
Flexible to Spot inside the same account, and Coinductor refuses an API key
that could withdraw at all. What it costs is forgone yield, and it is
reversible by subscribing again.

Each limit is a flat amount and a percentage of portfolio value, and the
smaller wins - the same shape as the order size, for the same reason: a flat
number means something different on a 500 account and a 50,000 one.
"""

from __future__ import annotations

from pathlib import Path

from .config_fields import Field, FieldGroup

SECTION = "earn"

# Ordered per-run first, then per-day, then what is left behind: the order
# somebody reads when asking "how much can it take, and how fast".
GROUP = FieldGroup(
    (
        # The percentages and the daily cap are absent from every config
        # written before they meant anything. Their defaults are what those
        # configs already behaved like: no percentage ceiling, and - for the
        # daily amount - the value the template ships.
        Field("runPct", SECTION, "max_auto_redeem_pct_of_portfolio", percent=True, default="100"),
        Field("runAmount", SECTION, "max_auto_redeem_usdc_per_run"),
        Field("dayPct", SECTION, "max_redeem_pct_of_portfolio_per_day", percent=True, default="100"),
        Field("dayAmount", SECTION, "max_redeem_per_day_usdt", default="250"),
        Field("reserve", SECTION, "min_auto_redeem_reserve_usdc", allow_zero=True),
    )
)


def read_funding(config_path: str | Path) -> dict[str, str]:
    return GROUP.read(config_path)


def valid_funding(values: dict[str, object]) -> bool:
    return GROUP.valid(values)


def apply_funding_to_config(config_path: str | Path, values: dict[str, object]) -> dict[str, str]:
    return GROUP.apply(config_path, values)


def ensure_keys(config_path: str | Path) -> bool:
    return GROUP.ensure_keys(config_path)
