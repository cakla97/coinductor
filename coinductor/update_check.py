"""Whether a newer Coinductor has been published, and how quietly to say so.

An app that installs itself from a GitHub release has no other way to tell you
that a fix exists - but a check that reaches a remote host on every launch is a
change in what "local-first" means here, so it is written down in the config
template, switchable off in Settings, and does nothing at all when off.

The reporting is deliberately unpushy. There is no dialog: a dialog that
appears every time the app opens is one people learn to dismiss without reading,
which defeats the point of showing it. A line on the Overview page stays until
the upgrade happens, costs nothing to ignore, and can be put away for a version
if it is not wanted.

Nothing here decides anything. It reports a version string, and every failure -
no network, a rate limit, a tag that will not parse - reports nothing rather
than guessing, because a false "you are out of date" is worse than silence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from pathlib import Path
import json
import os
import re
import tomllib
import urllib.error
import urllib.request

from trading_agent import __version__ as CURRENT_VERSION
from trading_agent.config import load_config

from .risk_profile import _apply

DEFAULT_PATH = "state/update_check.toml"
RELEASES_API = "https://api.github.com/repos/cakla97/coinductor/releases/latest"
RELEASES_PAGE = "https://github.com/cakla97/coinductor/releases/latest"

# One a day. The check exists so a fix is not missed for weeks, not so the app
# can tell you about it twice in one afternoon.
CHECK_INTERVAL_HOURS = 24
TIMEOUT_SECONDS = 6

_VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def parse_version(text: object) -> tuple[int, int, int] | None:
    """`v1.4.3` and `1.4.3` both parse; anything else is None.

    Pre-releases and tags with a suffix return None on purpose. This decides
    whether to tell someone they are out of date, and the honest answer to a
    version shape we do not understand is to say nothing.
    """
    match = _VERSION.match(str(text or "").strip())
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def is_newer(candidate: object, current: object) -> bool:
    parsed_candidate = parse_version(candidate)
    parsed_current = parse_version(current)
    if parsed_candidate is None or parsed_current is None:
        return False
    return parsed_candidate > parsed_current


@dataclass(frozen=True)
class UpdateState:
    latest_version: str = ""
    checked_at: str = ""
    dismissed_version: str = ""


class UpdateCheckService:
    """Reads and writes the record; the network call is one method, alone."""

    def __init__(
        self,
        path: str | Path = DEFAULT_PATH,
        current_version: str = CURRENT_VERSION,
        api_url: str = RELEASES_API,
    ) -> None:
        self.path = Path(path)
        self.current_version = str(current_version)
        self.api_url = api_url

    # -- the record ---------------------------------------------------------

    def read(self) -> UpdateState:
        if not self.path.exists():
            return UpdateState()
        try:
            payload = tomllib.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            return UpdateState()
        section = payload.get("updates", {})
        if not isinstance(section, dict):
            return UpdateState()
        return UpdateState(
            latest_version=str(section.get("latest_version", "") or ""),
            checked_at=str(section.get("checked_at", "") or ""),
            dismissed_version=str(section.get("dismissed_version", "") or ""),
        )

    def _write(self, state: UpdateState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            "# Written by Coinductor. Safe to delete.\n"
            "[updates]\n"
            f'latest_version = "{state.latest_version}"\n'
            f'checked_at = "{state.checked_at}"\n'
            f'dismissed_version = "{state.dismissed_version}"\n',
            encoding="utf-8",
        )

    def due(self, now: datetime | None = None) -> bool:
        """Whether enough time has passed to ask GitHub again."""
        checked = self.read().checked_at
        if not checked:
            return True
        try:
            last = datetime.fromisoformat(checked)
        except ValueError:
            return True
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        moment = now or datetime.now(UTC)
        return moment - last >= timedelta(hours=CHECK_INTERVAL_HOURS)

    def record(self, latest_version: str, now: datetime | None = None) -> None:
        state = self.read()
        moment = (now or datetime.now(UTC)).isoformat()
        self._write(
            UpdateState(
                latest_version=str(latest_version or "").strip(),
                checked_at=moment,
                dismissed_version=state.dismissed_version,
            )
        )

    def dismiss(self) -> None:
        """Put the current finding away. A later release says so again."""
        state = self.read()
        self._write(
            UpdateState(
                latest_version=state.latest_version,
                checked_at=state.checked_at,
                dismissed_version=state.latest_version,
            )
        )

    # -- what the screen asks ------------------------------------------------

    def available(self) -> str:
        """The version worth mentioning, or empty when there is nothing to say."""
        state = self.read()
        if not is_newer(state.latest_version, self.current_version):
            return ""
        if state.dismissed_version == state.latest_version:
            return ""
        return state.latest_version

    # -- the network ---------------------------------------------------------

    def fetch(self) -> str:
        """The latest published tag, or empty. Never raises."""
        request = urllib.request.Request(
            self.api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"Coinductor/{self.current_version}",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return ""
        if not isinstance(payload, dict):
            return ""
        # A draft is not published and a prerelease is not for everybody.
        if payload.get("draft") or payload.get("prerelease"):
            return ""
        tag = str(payload.get("tag_name", "") or "").strip()
        return tag if parse_version(tag) is not None else ""


# -- the switch, in the config ----------------------------------------------

SECTION = "updates"
KEY = "check_on_start"

_SECTION_TEMPLATE = """
[updates]
# Ask GitHub once a day whether a newer Coinductor has been released. It reads
# the public releases feed, sends nothing about you, and never downloads or
# installs anything.
check_on_start = true
"""


# Same shape as COINDUCTOR_DISABLE_KEYCHAIN, and set by the same autouse
# fixture: the test suite is offline by contract, and a check that runs on
# controller construction would have every Qt test reach github.com.
DISABLE_ENV = "COINDUCTOR_DISABLE_UPDATE_CHECK"


def read_check_on_start(config_path: str | Path) -> bool:
    """Absent means yes: every shipped template carries the section switched on.

    The opposite of the earn switch on purpose. Failing closed there means "do
    not move money"; here it would mean "never mention a fix exists", which is
    the outcome this is for avoiding. Nothing is risked by asking.
    """
    if os.environ.get(DISABLE_ENV):
        return False
    try:
        raw = load_config(str(config_path)).raw
    except Exception:
        return False
    return bool(raw.get(SECTION, {}).get(KEY, True))


def ensure_section(config_path: str | Path) -> bool:
    """Add [updates] to a config written before it existed. True if it changed.

    `_apply` only edits keys that already exist, so without this the Settings
    checkbox would report success and change nothing - and the direction that
    would fail silently is turning the check *off*, which is the one someone
    doing it actually cares about.
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
    if KEY in present:
        return False
    insert_at = end
    while insert_at > start + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines.insert(insert_at, f"{KEY} = true")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def apply_check_on_start(config_path: str | Path, enabled: object) -> dict[str, str]:
    """Write the switch; returns what changed, empty when nothing did."""
    path = Path(config_path)
    if not path.exists():
        return {}
    ensure_section(path)
    return _apply(path, SECTION, {KEY: bool(enabled)})
