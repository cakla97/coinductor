"""When Coinductor may start an analysis without being asked.

Automation is strictly additive: the Run analysis dialog behaves exactly as it
always has, for everyone, including someone who never turns this on. What this
adds is a second way for the *same* run to start.

Nothing here can submit an order. An automatic run uses the same read-only path
as a manual one, and `RuntimeFlags` fail closed, so the worst a misconfigured
schedule can do is read the account more often than intended.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from trading_agent.config import load_config

from .risk_profile import _apply

SECTION = "automation"

# Bounds, not preferences. Below the floor the app would hammer the exchange for
# no benefit - a deterministic analysis over the same candles returns the same
# answer - and above the ceiling a "schedule" is indistinguishable from off.
MIN_INTERVAL_HOURS = 1
MAX_INTERVAL_HOURS = 24 * 14

DEFAULTS: dict[str, object] = {
    "enabled": False,
    "interval_hours": 24,
    "ai_summary": False,
    "live_preview": False,
}

# Written verbatim when the section is absent, which is every config created
# before automation existed. _apply only edits keys that already exist, so
# without this an upgrade would accept the settings and silently discard them.
_SECTION_TEMPLATE = """
[automation]
# Coinductor may start an analysis on its own. It never submits an order:
# an automatic run is the same read-only analysis the Run analysis button does.
enabled = false
# How often, in hours. The app must be running for this to fire; see the
# scheduled task in Settings for runs while it is closed.
interval_hours = 24
# What an automatic run includes. Both default to off: unattended runs should
# ask for as little as possible, and the AI summary needs a configured model.
ai_summary = false
live_preview = false
"""


@dataclass(frozen=True)
class AutomationSettings:
    enabled: bool
    interval_hours: int
    ai_summary: bool
    live_preview: bool

    @property
    def interval_seconds(self) -> int:
        return self.interval_hours * 3600


def read_automation(config_path: str | Path) -> AutomationSettings:
    """Current settings, falling back to the defaults for anything absent."""
    try:
        raw = load_config(str(config_path)).raw.get(SECTION, {})
    except Exception:
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    return AutomationSettings(
        enabled=_bool(raw.get("enabled"), False),
        interval_hours=clamp_interval(raw.get("interval_hours")),
        ai_summary=_bool(raw.get("ai_summary"), False),
        live_preview=_bool(raw.get("live_preview"), False),
    )


def clamp_interval(value: object) -> int:
    """Hours, forced into range. An unreadable value becomes the default.

    Refusing outright would leave the caller deciding what to do with a number
    the user typed, and there is no useful answer other than a sane one.
    """
    try:
        hours = int(float(str(value).strip().replace(",", ".")))
    except (TypeError, ValueError):
        return int(DEFAULTS["interval_hours"])
    return max(MIN_INTERVAL_HOURS, min(hours, MAX_INTERVAL_HOURS))


def apply_automation_to_config(
    config_path: str | Path,
    *,
    enabled: bool,
    interval_hours: object,
    ai_summary: bool,
    live_preview: bool,
) -> dict[str, str]:
    """Write the settings; return what changed, empty when nothing did."""
    path = Path(config_path)
    if not path.exists():
        return {}
    ensure_section(path)
    return _apply(
        path,
        SECTION,
        {
            "enabled": bool(enabled),
            "interval_hours": clamp_interval(interval_hours),
            "ai_summary": bool(ai_summary),
            "live_preview": bool(live_preview),
        },
    )


def ensure_section(config_path: str | Path) -> bool:
    """Append [automation] when the config predates it. True if it was added.

    Appending is safe with TOML's flat section syntax: a section at the end of
    the file is a section. It is written only once, and only with the shipped
    defaults, so it can never turn automation on behind someone's back.
    """
    path = Path(config_path)
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if any(line.strip() == f"[{SECTION}]" for line in text.splitlines()):
        return False
    separator = "" if text.endswith("\n") else "\n"
    path.write_text(text + separator + _SECTION_TEMPLATE, encoding="utf-8")
    return True


def _bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return True
    if text in {"false", "0", "no", "off"}:
        return False
    return default
