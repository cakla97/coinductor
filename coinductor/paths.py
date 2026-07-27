from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


def resolve_data_dir() -> Path | None:
    """Where a frozen (installed) build should keep local state.

    Returns None for a source checkout (dev/tests), meaning "leave the
    current working directory alone" - every existing relative-path
    default in the codebase keeps resolving exactly as it does today.
    """
    if not getattr(sys, "frozen", False):
        return None
    override = os.environ.get("COINDUCTOR_DATA_DIR")
    if override:
        return Path(override)
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "Coinductor"
    return Path.home() / ".coinductor"


def data_dir_label() -> str:
    """Where local data actually lives, for showing the user.

    An installed build keeps it under %LOCALAPPDATA%, not next to the exe, so
    "the project folder" is only true for a source checkout.
    """
    resolved = resolve_data_dir()
    return str(resolved) if resolved is not None else str(Path.cwd())


def _bundled_root() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent.parent


def bootstrap_data_dir(data_dir: Path) -> None:
    """Create the local data layout and seed it from bundled templates.

    Safe to call every startup: only fills in what's missing, never
    overwrites an existing config or state file.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "state").mkdir(exist_ok=True)
    (data_dir / "work").mkdir(exist_ok=True)
    (data_dir / "outputs" / "reports").mkdir(parents=True, exist_ok=True)
    (data_dir / "research" / "notes").mkdir(parents=True, exist_ok=True)
    (data_dir / "research" / "requests").mkdir(parents=True, exist_ok=True)

    template = _bundled_root() / "config.example.toml"
    if not template.exists():
        return

    reference = data_dir / "config.example.toml"
    if not reference.exists():
        shutil.copy(template, reference)

    # An installed build must get its own config.toml. Without one,
    # default_config_path() falls back to the template - which ships
    # mock_data = true so the repo and tests run offline - and the app would
    # silently analyse the example portfolio and present it as a result.
    # Writing config.toml also keeps the profile's style/limit writer off the
    # template, which is meant to stay pristine.
    config = data_dir / "config.toml"
    if not config.exists():
        text = template.read_text(encoding="utf-8").replace(
            "mock_data = true", "mock_data = false", 1
        )
        config.write_text(text, encoding="utf-8")
