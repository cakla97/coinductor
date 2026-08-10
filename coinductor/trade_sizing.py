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

Two of these had no home at all. ``max_position_pct_per_asset``,
``max_total_trading_capital_pct`` and ``max_risk_per_trade_pct`` were written
by nothing, read by nothing until the sizing change, and visible only in a file
this app tells people they never have to open.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

from trading_agent.config import load_config

from .risk_profile import _apply

STRATEGY_SECTION = "strategy"
RISK_SECTION = "risk"

# Ordered as they apply, widest intent first, so the screen can list them in an
# order that reads like an explanation rather than like a config file.
FIELDS: tuple[tuple[str, str, str], ...] = (
    ("tradePct", STRATEGY_SECTION, "max_trade_pct_of_portfolio"),
    ("tradeAmount", STRATEGY_SECTION, "quote_amount_usdt"),
    ("positionPct", RISK_SECTION, "max_position_pct_per_asset"),
    ("capitalPct", RISK_SECTION, "max_total_trading_capital_pct"),
    ("riskPct", RISK_SECTION, "max_risk_per_trade_pct"),
)

# Everything except the flat amount is a percentage of portfolio value, so a
# figure above 100 is a typo rather than a preference.
PERCENT_KEYS = frozenset({"tradePct", "positionPct", "capitalPct", "riskPct"})

# Absent from configs written before portfolio-relative sizing existed. 100
# means "no percentage ceiling", which is what those configs behaved like.
DEFAULTS: dict[str, str] = {"tradePct": "100"}


def read_sizing(config_path: str | Path) -> dict[str, str]:
    """The five ceilings currently in force, as text ready for the screen."""
    try:
        raw = load_config(str(config_path)).raw
    except Exception:
        raw = {}
    values: dict[str, str] = {}
    for name, section, key in FIELDS:
        stored = raw.get(section, {}).get(key, DEFAULTS.get(name, "0"))
        values[name] = _trim(_decimal(stored))
    return values


def valid_sizing(values: dict[str, object]) -> bool:
    """Whether every value could be written at all.

    Zero is refused rather than saved: the config validator treats a
    non-positive risk percentage as an error, and a saved zero would size every
    order to nothing with no visible cause.
    """
    for name, _, _ in FIELDS:
        amount = _decimal(values.get(name))
        if amount <= 0:
            return False
        if name in PERCENT_KEYS and amount > 100:
            return False
    return True


def apply_sizing_to_config(config_path: str | Path, values: dict[str, object]) -> dict[str, str]:
    """Write the ceilings; return what changed, keyed by section and key.

    `_apply` only edits keys that already exist, so `max_trade_pct_of_portfolio`
    is created first for configs written before it existed - otherwise the
    setting is accepted and silently discarded, which is the trap the
    `[automation]` section already had to be taught to avoid.
    """
    path = Path(config_path)
    if not path.exists() or not valid_sizing(values):
        return {}
    ensure_keys(path)
    changed: dict[str, str] = {}
    for name, section, key in FIELDS:
        moved = _apply(path, section, {key: _trim(_decimal(values.get(name)))})
        for moved_key, description in moved.items():
            changed[f"{section}.{moved_key}"] = description
    return changed


def ensure_keys(config_path: str | Path) -> bool:
    """Add any ceiling the config predates. True when something was added."""
    path = Path(config_path)
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    added = False
    for name, section, key in FIELDS:
        if name not in DEFAULTS:
            continue
        start = _section_start(lines, section)
        if start is None:
            continue
        end = _section_end(lines, start)
        present = {
            line.split("=", 1)[0].strip()
            for line in lines[start + 1 : end]
            if "=" in line and not line.strip().startswith("#")
        }
        if key in present:
            continue
        insert_at = end
        while insert_at > start + 1 and not lines[insert_at - 1].strip():
            insert_at -= 1
        lines.insert(insert_at, f"{key} = {DEFAULTS[name]}")
        added = True
    if added:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return added


def _section_start(lines: list[str], section: str) -> int | None:
    for index, line in enumerate(lines):
        if line.strip() == f"[{section}]":
            return index
    return None


def _section_end(lines: list[str], start: int) -> int:
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("[") and stripped.endswith("]") and "=" not in stripped:
            return index
    return len(lines)


def _decimal(value: object) -> Decimal:
    try:
        return Decimal(str(value if value is not None else "0").strip().replace(",", "."))
    except (InvalidOperation, ValueError, AttributeError):
        return Decimal("0")


def _trim(value: Decimal) -> str:
    """Render without trailing zeros, so the file keeps reading like a config."""
    return format(value.normalize(), "f")
