"""The per-order size cap, read and written from Settings.

``max_quote_amount_usdt`` is the last numeric backstop before an order reaches
an exchange. Every other guard - the safety stage, the typed confirmation, the
risk engine - decides *whether* an order goes; this one decides *how big*. If
any of them ever has a bug, or a decimal point slips, this is the number that
bounds what it can cost.

It ships at 10, which is deliberately tiny, and it was only editable by opening
config.toml - the exact thing this app tells users they never have to do. A
first-portfolio tranche planned at 66 USDC submitted 10 and counted itself
complete, because the cap truncates with min() rather than rejecting.

Two separate caps, because they guard different things: the testnet one only
stops a typo wasting play money, the mainnet one stops a real loss.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from trading_agent.config import load_config

from .risk_profile import _apply


TESTNET_SECTION = "testnet_execution"
MAINNET_SECTION = "live_confirm"
CAP_KEY = "max_quote_amount_usdt"

# What share of the portfolio a single live order may be worth before the
# desktop stops calling it conservative. Not a limit - the user may set what
# they like - just the number the suggestion is built from and the threshold
# the warning uses.
SUGGESTED_SHARE = Decimal("0.10")
MINIMUM_SUGGESTION = Decimal("10")


def read_order_caps(config_path: str | Path) -> dict[str, Decimal]:
    """The two caps currently in force, straight from the config."""
    try:
        raw = load_config(str(config_path)).raw
    except Exception:
        return {"testnet": Decimal("0"), "mainnet": Decimal("0")}
    return {
        "testnet": _decimal(raw.get(TESTNET_SECTION, {}).get(CAP_KEY)),
        "mainnet": _decimal(raw.get(MAINNET_SECTION, {}).get(CAP_KEY)),
    }


def suggested_mainnet_cap(portfolio_value: object) -> Decimal:
    """A starting point sized to the portfolio, never below the shipped default.

    Whole units: a cap is a judgement call, and 83.61 reads as if it were
    calculated to the cent from something meaningful.
    """
    value = _decimal(portfolio_value)
    if value <= 0:
        return MINIMUM_SUGGESTION
    suggestion = (value * SUGGESTED_SHARE).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return max(suggestion, MINIMUM_SUGGESTION)


def exceeds_suggestion(mainnet_cap: object, portfolio_value: object) -> bool:
    """Whether a chosen live cap is above what the portfolio suggests.

    Only ever warns. Someone deliberately raising this has a reason, and a
    desktop that refuses the number is a desktop people work around.
    """
    value = _decimal(portfolio_value)
    if value <= 0:
        return False
    return _decimal(mainnet_cap) > suggested_mainnet_cap(value)


def apply_order_caps_to_config(
    config_path: str | Path, testnet_cap: object, mainnet_cap: object
) -> dict[str, str]:
    """Write both caps; return what changed, keyed by the section it moved in.

    A cap of zero or less is refused rather than written: the config validator
    treats it as an error, and a saved zero would block every order with no
    obvious cause.
    """
    changed: dict[str, str] = {}
    for section, value in ((TESTNET_SECTION, testnet_cap), (MAINNET_SECTION, mainnet_cap)):
        amount = _decimal(value)
        if amount <= 0:
            continue
        moved = _apply(config_path, section, {CAP_KEY: _trim(amount)})
        for key, description in moved.items():
            changed[f"{section}.{key}"] = description
    return changed


def _decimal(value: object) -> Decimal:
    try:
        return Decimal(str(value if value is not None else "0").strip().replace(",", "."))
    except (InvalidOperation, ValueError, AttributeError):
        return Decimal("0")


def _trim(value: Decimal) -> str:
    """Render without a trailing .00, so the file keeps reading like a config."""
    normalized = value.normalize()
    text = format(normalized, "f")
    return text
