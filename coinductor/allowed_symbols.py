"""Adding a symbol to the list the risk engine will consider.

A new listing is not tradeable by Coinductor, and that is the whitelist doing
its job rather than a gap to route around. So the listing card does not get a
buy button. It gets one deliberate step - put this pair on the list - after
which the ordinary analysis, the ordinary risk checks, the ordinary funding
check and the ordinary typed confirmation all apply exactly as they do for
BTCUSDC.

That step is the point. Someone who has looked into a coin and decided they
want it can say so once; nothing here shortens the distance between that
decision and an order.
"""

from __future__ import annotations

import re
from pathlib import Path

from trading_agent.config import load_config

SECTION = "strategy"
KEY = "allowed_symbols"

# A guard against the list becoming a place things are added and never removed.
# Well past any reasonable portfolio, and far short of "everything on Binance".
MAX_SYMBOLS = 40

_SYMBOL = re.compile(r"^[A-Z0-9]{4,20}$")


def read_allowed_symbols(config_path: str | Path) -> list[str]:
    try:
        raw = load_config(str(config_path)).raw.get(SECTION, {}).get(KEY, [])
    except Exception:
        return []
    if not isinstance(raw, (list, tuple)):
        return []
    return [str(item).strip().upper() for item in raw if str(item).strip()]


def is_valid_symbol(symbol: str) -> bool:
    """Shape only. Whether Binance actually lists it is the exchange's answer."""
    return bool(_SYMBOL.match(str(symbol).strip().upper()))


def add_allowed_symbol(config_path: str | Path, symbol: str) -> tuple[bool, str]:
    """Add one pair. Returns (changed, reason-key).

    The reason is a key rather than a sentence so the desktop can say it in the
    reader's language, like everything else the engine reports.
    """
    path = Path(config_path)
    normalized = str(symbol).strip().upper()
    if not path.exists():
        return False, "allowed_symbol_no_config"
    if not is_valid_symbol(normalized):
        return False, "allowed_symbol_invalid"

    current = read_allowed_symbols(path)
    if normalized in current:
        return False, "allowed_symbol_already_there"
    if len(current) >= MAX_SYMBOLS:
        return False, "allowed_symbol_list_full"

    updated = [*current, normalized]
    if not _write(path, updated):
        return False, "allowed_symbol_not_written"
    return True, "allowed_symbol_added"


def remove_allowed_symbol(config_path: str | Path, symbol: str) -> bool:
    """Anything that can be added has to be removable from the same screen."""
    path = Path(config_path)
    normalized = str(symbol).strip().upper()
    current = read_allowed_symbols(path)
    if not path.exists() or normalized not in current:
        return False
    return _write(path, [item for item in current if item != normalized])


def _write(path: Path, symbols: list[str]) -> bool:
    """Replace the list in place, leaving comments and every other line alone.

    Edited line by line rather than re-serialised, for the same reason the risk
    profile is: a config full of explanatory comments is worth more than the
    convenience of a TOML dump.
    """
    rendered = "[" + ", ".join(f'"{item}"' for item in symbols) + "]"
    lines = path.read_text(encoding="utf-8").splitlines()
    section = ""
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]") and "=" not in stripped:
            section = stripped[1:-1]
            continue
        if section != SECTION or stripped.startswith("#") or "=" not in line:
            continue
        if line.split("=", 1)[0].strip() != KEY:
            continue
        lines[index] = f"{KEY} = {rendered}"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True
    return False
