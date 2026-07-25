"""Maps the onboarding management style onto the deterministic trend gates.

The wizard tells the user that Conservative "is less likely to recommend active
trades" and that Active "can surface more frequent opportunities", but nothing
consumed ``management_style``, so the choice had no effect on trading. This
module materialises it into ``config.toml`` instead of overriding the engine at
run time: the config stays the single source of truth for risk, and the user can
see and hand-edit the resulting numbers.

Deliberately narrow. Only the trend filter - "when do I even consider a buy" -
moves. Everything that limits loss (the EMA200 gate, daily/weekly loss caps,
stop-loss, kill switch, position caps, confirmations, safety stages) is left
alone, which is what the Active description promises.
"""

from __future__ import annotations

from pathlib import Path
import re

# require_price_above_ema200 is intentionally absent: it stays as configured at
# every level, because it is the main protection against buying into a downtrend.
STYLE_GATES: dict[str, dict[str, object]] = {
    "CONSERVATIVE": {"require_risk_on": True, "min_rsi14": 45.0, "max_rsi14": 68.0},
    "BALANCED": {"require_risk_on": False, "min_rsi14": 45.0, "max_rsi14": 70.0},
    "ACTIVE": {"require_risk_on": False, "min_rsi14": 40.0, "max_rsi14": 72.0},
}

DEFAULT_STYLE = "BALANCED"


def gates_for(style: str) -> dict[str, object]:
    return dict(STYLE_GATES.get(str(style).strip().upper(), STYLE_GATES[DEFAULT_STYLE]))


def describe_gates(style: str, language: str) -> str:
    """One sentence describing what the style actually loosens, for the wizard.

    Built from STYLE_GATES rather than hardcoded prose, so the hint can never
    promise something different from what gets written into config.toml.
    """
    from .service_strings import service_text

    gates = gates_for(style)
    key = "style_hint_risk_on" if gates["require_risk_on"] else "style_hint_any_regime"
    trend = service_text(key, language).format(
        min=_trim(gates["min_rsi14"]), max=_trim(gates["max_rsi14"])
    )
    return f"{trend} {service_text('style_hint_shared', language)}"


def _trim(value: object) -> str:
    return str(int(value)) if float(value) == int(float(value)) else str(value)


def _render(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def apply_style_to_config(config_path: str | Path, style: str) -> dict[str, str]:
    """Write the style's trend gates into [consensus]; return what changed.

    Edits line by line rather than re-serialising the file so comments, key
    order, and every unrelated setting survive untouched.
    """
    path = Path(config_path)
    gates = gates_for(style)
    if not path.exists():
        return {}

    lines = path.read_text(encoding="utf-8").splitlines()
    changed: dict[str, str] = {}
    section = ""
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1]
            continue
        if section != "consensus" or "=" not in line or stripped.startswith("#"):
            continue
        key = line.split("=", 1)[0].strip()
        if key not in gates:
            continue
        rendered = _render(gates[key])
        current = line.split("=", 1)[1].split("#", 1)[0].strip()
        if current == rendered:
            continue
        lines[index] = f"{key} = {rendered}"
        changed[key] = f"{current} -> {rendered}"

    if changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed
