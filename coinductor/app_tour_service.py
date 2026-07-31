from __future__ import annotations

from pathlib import Path
import tomllib


class AppTourService:
    def __init__(self, path: str | Path = "state/app_ui_state.toml"):
        self.path = Path(path)

    def is_completed(self) -> bool:
        if not self.path.exists():
            return False
        try:
            payload = tomllib.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            return False
        state = payload.get("app_tour", {})
        return bool(state.get("completed", False))

    def mark_completed(self) -> None:
        # Rewrites the whole file, so this must stay the only thing that lives
        # in it. Anything else added here would be erased the first time the
        # tour was replayed - see catch_up.py, which keeps its own file for
        # exactly that reason.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            "# Local Coinductor interface state.\n\n[app_tour]\nversion = 1\ncompleted = true\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def reset(self) -> None:
        if self.path.exists():
            self.path.unlink()
