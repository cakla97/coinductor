"""Per-invocation execution authority, kept out of the config file.

These flags decide whether a run may actually send an order, so they never come
from ``config.toml``: the CLI and the desktop app set them from explicit
command-line switches or button presses. They travel inside the config mapping
under ``_runtime`` because that mapping is what every collaborator already
receives, but this module is the only place that knows those key names.

Every gate is fail-closed. A missing, misspelled or wrongly typed entry parses
back to "do not submit" rather than to an accidental live order, which is why
:meth:`RuntimeFlags.from_config` never raises.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

RUNTIME_CONFIG_KEY = "_runtime"


@dataclass(frozen=True)
class RuntimeFlags:
    """What this particular run has been authorised to submit."""

    # Live mainnet spot buy.
    live_submit: bool = False
    mainnet_confirm: str = ""
    # Flexible Earn redeem.
    earn_redeem_submit: bool = False
    earn_redeem_confirm: str = ""
    # OCO protection for an open live position.
    oco_protection_submit: bool = False
    mainnet_oco_confirm: str = ""
    # Spot Testnet order. No real funds, but still gated.
    testnet_confirm: str = ""
    # Operator asked the analyst to assess one specific symbol.
    manual_override_symbol: str = ""

    @classmethod
    def from_config(cls, config: dict) -> RuntimeFlags:
        """Read the flags out of a config mapping, defaulting to no authority."""
        raw = config.get(RUNTIME_CONFIG_KEY) or {}
        if not isinstance(raw, dict):
            return cls()
        return cls(
            live_submit=bool(raw.get("live_submit", False)),
            mainnet_confirm=str(raw.get("mainnet_confirm", "") or ""),
            earn_redeem_submit=bool(raw.get("earn_redeem_submit", False)),
            earn_redeem_confirm=str(raw.get("earn_redeem_confirm", "") or ""),
            oco_protection_submit=bool(raw.get("oco_protection_submit", False)),
            mainnet_oco_confirm=str(raw.get("mainnet_oco_confirm", "") or ""),
            testnet_confirm=str(raw.get("testnet_confirm", "") or ""),
            # Stripped, not upper-cased: the desktop already normalises the case
            # when it writes the value and the runner only ever stripped it.
            manual_override_symbol=str(raw.get("manual_override_symbol", "") or "").strip(),
        )

    def store_in(self, config: dict) -> None:
        """Write the flags into a config mapping for collaborators to pick up."""
        config[RUNTIME_CONFIG_KEY] = asdict(self)
