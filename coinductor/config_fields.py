"""Reading and writing a group of numeric config values from a screen.

Extracted when the Earn funding panel turned out to need exactly what the
order-sizing panel already did: read a set of numbers out of `config.toml`,
refuse the ones that cannot be written, create any the config predates, and
report what actually moved. Two copies of that would be two places to fix the
`_apply` trap, where a key that does not already exist is accepted and
silently discarded.

A field is a screen name, the section it lives in, and its key. Percentages
are named so a figure above 100 can be caught as the typo it is; defaults name
the fields that may be missing from an older config and what their absence
means.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

from trading_agent.config import load_config

from .risk_profile import _apply


@dataclass(frozen=True)
class Field:
    name: str
    section: str
    key: str
    # Percentages are of portfolio value, so anything above 100 is a slip.
    percent: bool = False
    # Written into the config when it is missing entirely. None means the
    # field has always existed and its absence is not something to repair.
    default: str | None = None
    # Zero is refused by default, because for a limit it means "stop
    # everything" and reads as a mistake. For a reserve it is a real answer -
    # keep nothing back - and the shipped template uses it.
    allow_zero: bool = False


@dataclass(frozen=True)
class FieldGroup:
    fields: tuple[Field, ...] = field(default_factory=tuple)

    def read(self, config_path: str | Path) -> dict[str, str]:
        """Current values, as text ready for a screen."""
        try:
            raw = load_config(str(config_path)).raw
        except Exception:
            raw = {}
        return {
            item.name: _trim(_decimal(raw.get(item.section, {}).get(item.key, item.default or "0")))
            for item in self.fields
        }

    def valid(self, values: dict[str, object]) -> bool:
        """Whether every value could be written at all.

        Zero is refused rather than saved: the config validator treats a
        non-positive limit as an error, and a saved zero would silently stop
        the thing it governs with no visible cause.
        """
        for item in self.fields:
            amount = _decimal(values.get(item.name))
            if amount < 0 or (amount == 0 and not item.allow_zero):
                return False
            if item.percent and amount > 100:
                return False
        return True

    def apply(self, config_path: str | Path, values: dict[str, object]) -> dict[str, str]:
        """Write the values; return what changed, keyed by section and key."""
        path = Path(config_path)
        if not path.exists() or not self.valid(values):
            return {}
        self.ensure_keys(path)
        changed: dict[str, str] = {}
        for item in self.fields:
            moved = _apply(path, item.section, {item.key: _trim(_decimal(values.get(item.name)))})
            for key, description in moved.items():
                changed[f"{item.section}.{key}"] = description
        return changed

    def ensure_keys(self, config_path: str | Path) -> bool:
        """Add any field the config predates. True when something was added.

        `_apply` only edits keys that already exist, so without this a new
        setting is accepted, reported as saved, and thrown away.
        """
        path = Path(config_path)
        if not path.exists():
            return False
        lines = path.read_text(encoding="utf-8").splitlines()
        added = False
        for item in self.fields:
            if item.default is None:
                continue
            start = _section_start(lines, item.section)
            if start is None:
                continue
            end = _section_end(lines, start)
            present = {
                line.split("=", 1)[0].strip()
                for line in lines[start + 1 : end]
                if "=" in line and not line.strip().startswith("#")
            }
            if item.key in present:
                continue
            insert_at = end
            while insert_at > start + 1 and not lines[insert_at - 1].strip():
                insert_at -= 1
            lines.insert(insert_at, f"{item.key} = {item.default}")
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
