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

from trading_agent.config import load_config

from .config_fields import Field, FieldGroup
from .risk_profile import _apply

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


# The switch itself, kept out of the FieldGroup because that machinery is for
# numbers with ceilings and this is a yes/no. It shipped readable only in
# config.toml, which is the one thing this app promises nobody has to open -
# and it is the single most consequential setting on the screen.
AUTO_KEY = "auto_funding_enabled"


def read_auto_funding(config_path: str | Path) -> bool:
    """Whether a run may move Earn to Spot unattended. Absent means no."""
    try:
        raw = load_config(str(config_path)).raw
    except Exception:
        return False
    return bool(raw.get(SECTION, {}).get(AUTO_KEY, False))


def apply_auto_funding(config_path: str | Path, enabled: object) -> dict[str, str]:
    """Write the switch; return what changed, empty when nothing did."""
    path = Path(config_path)
    if not path.exists():
        return {}
    ensure_auto_key(path)
    return _apply(path, SECTION, {AUTO_KEY: bool(enabled)})


def ensure_auto_key(config_path: str | Path) -> bool:
    """Create the key for a config written before the switch existed.

    `_apply` only edits keys that already exist, so without this the toggle
    reports success and changes nothing - and unlike a limit, silently failing
    to turn this *off* would be the dangerous direction.
    """
    path = Path(config_path)
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == f"[{SECTION}]"), None)
    if start is None:
        return False
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("[") and stripped.endswith("]") and "=" not in stripped:
            end = index
            break
    present = {
        line.split("=", 1)[0].strip()
        for line in lines[start + 1 : end]
        if "=" in line and not line.strip().startswith("#")
    }
    if AUTO_KEY in present:
        return False
    insert_at = end
    while insert_at > start + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines.insert(insert_at, f"{AUTO_KEY} = false")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def read_funding(config_path: str | Path) -> dict[str, str]:
    return GROUP.read(config_path)


def valid_funding(values: dict[str, object]) -> bool:
    return GROUP.valid(values)


def apply_funding_to_config(config_path: str | Path, values: dict[str, object]) -> dict[str, str]:
    return GROUP.apply(config_path, values)


def ensure_keys(config_path: str | Path) -> bool:
    return GROUP.ensure_keys(config_path)
