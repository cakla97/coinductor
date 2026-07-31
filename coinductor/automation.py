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
    "watch_listings": False,
    "listing_interval_minutes": 15,
    "listing_keep": 200,
}

# Minutes. The floor is a courtesy to the exchange rather than a limit that
# matters: exchangeInfo is a public endpoint, but polling it every few seconds
# to be marginally earlier to a race this app cannot win would be silly.
MIN_LISTING_MINUTES = 5
MAX_LISTING_MINUTES = 24 * 60

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
# Watch for pairs newly listed on Binance and say so. It records and notifies;
# it never buys. Acting on a listing is a separate, deliberate step.
watch_listings = false
listing_interval_minutes = 15
# How many listings the journal keeps. These rows have no run_id, so ordinary
# run retention cannot prune them.
listing_keep = 200
"""


@dataclass(frozen=True)
class AutomationSettings:
    enabled: bool
    interval_hours: int
    ai_summary: bool
    live_preview: bool
    watch_listings: bool = False
    listing_interval_minutes: int = 15
    listing_keep: int = 200

    @property
    def interval_seconds(self) -> int:
        return self.interval_hours * 3600

    @property
    def listing_interval_seconds(self) -> int:
        return self.listing_interval_minutes * 60


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
        watch_listings=_bool(raw.get("watch_listings"), False),
        listing_interval_minutes=clamp_listing_interval(raw.get("listing_interval_minutes")),
        listing_keep=_positive_int(raw.get("listing_keep"), int(DEFAULTS["listing_keep"])),
    )


def clamp_listing_interval(value: object) -> int:
    try:
        minutes = int(float(str(value).strip().replace(",", ".")))
    except (TypeError, ValueError):
        return int(DEFAULTS["listing_interval_minutes"])
    return max(MIN_LISTING_MINUTES, min(minutes, MAX_LISTING_MINUTES))


def _positive_int(value: object, default: int) -> int:
    try:
        number = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


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
    watch_listings: object = None,
    listing_interval_minutes: object = None,
) -> dict[str, str]:
    """Write the settings; return what changed, empty when nothing did.

    The two listing values are optional so the schedule panel can save without
    knowing about listings, and the listing panel without knowing about the
    schedule. Omitted means "leave as it is", not "turn off".
    """
    path = Path(config_path)
    if not path.exists():
        return {}
    ensure_section(path)
    current = read_automation(path)
    values: dict[str, object] = {
        "enabled": bool(enabled),
        "interval_hours": clamp_interval(interval_hours),
        "ai_summary": bool(ai_summary),
        "live_preview": bool(live_preview),
        "watch_listings": current.watch_listings
        if watch_listings is None
        else bool(watch_listings),
        "listing_interval_minutes": current.listing_interval_minutes
        if listing_interval_minutes is None
        else clamp_listing_interval(listing_interval_minutes),
    }
    return _apply(path, SECTION, values)


# Appended one at a time to a section that already exists, for a config written
# against an older version of this feature. Missing a key here means _apply
# accepts a setting and discards it, which is the same silent failure the whole
# section-append exists to prevent - one level down.
_KEY_DEFAULTS: tuple[tuple[str, str], ...] = (
    ("enabled", "false"),
    ("interval_hours", "24"),
    ("ai_summary", "false"),
    ("live_preview", "false"),
    ("watch_listings", "false"),
    ("listing_interval_minutes", "15"),
    ("listing_keep", "200"),
)


def ensure_section(config_path: str | Path) -> bool:
    """Make [automation] complete. True if anything was added.

    Two cases: the section is missing entirely (a config from before automation
    existed), or it is present but lacks keys added since (a config from an
    earlier version of it). Both end with _apply silently discarding a setting,
    so both are repaired here. Only ever written with the shipped defaults, so
    this can never turn anything on behind someone's back.
    """
    path = Path(config_path)
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not any(line.strip() == f"[{SECTION}]" for line in lines):
        separator = "" if text.endswith("\n") else "\n"
        path.write_text(text + separator + _SECTION_TEMPLATE, encoding="utf-8")
        return True

    start = next(index for index, line in enumerate(lines) if line.strip() == f"[{SECTION}]")
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
    missing = [(key, value) for key, value in _KEY_DEFAULTS if key not in present]
    if not missing:
        return False
    # Inserted at the end of the section, before whatever follows it.
    insert_at = end
    while insert_at > start + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1
    for offset, (key, value) in enumerate(missing):
        lines.insert(insert_at + offset, f"{key} = {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
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
