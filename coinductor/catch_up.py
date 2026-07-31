"""What ran while Coinductor was closed.

A scheduled run writes to the journal and nothing else. Without this the result
is simply sitting in Run History the next time someone opens the app, with
nothing to say it arrived - which makes a schedule feel broken even when it
worked perfectly.

Its own file rather than a section in app_ui_state.toml: AppTourService rewrites
that file wholesale, so a second section there would be silently erased the
first time someone replayed the tour.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

DEFAULT_PATH = "state/last_seen_run.toml"


@dataclass(frozen=True)
class CatchUp:
    """Runs recorded since this app last looked."""

    count: int
    latest_run_id: int
    latest_decision: str

    @property
    def any(self) -> bool:
        return self.count > 0


class CatchUpService:
    def __init__(self, path: str | Path = DEFAULT_PATH):
        self.path = Path(path)

    def last_seen(self) -> int:
        if not self.path.exists():
            return 0
        try:
            payload = tomllib.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            return 0
        try:
            return int(payload.get("runs", {}).get("last_seen_id", 0))
        except (TypeError, ValueError):
            return 0

    def mark_seen(self, run_id: object) -> None:
        try:
            value = int(run_id)
        except (TypeError, ValueError):
            return
        if value <= self.last_seen():
            # Never move the marker backwards: a snapshot from an older run
            # would otherwise make already-reported runs unseen again.
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            "# The newest run this desktop has already shown you.\n"
            "# Used only to say what arrived while the window was closed.\n\n"
            f"[runs]\nversion = 1\nlast_seen_id = {value}\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def since_last_seen(self, runs: list[dict[str, object]]) -> CatchUp:
        """Given the run history newest-first, what has not been reported.

        Takes the rows rather than a Storage so it can be reasoned about - and
        tested - without a database.
        """
        marker = self.last_seen()
        unseen = []
        for row in runs:
            try:
                run_id = int(row.get("id") or row.get("runId") or 0)
            except (TypeError, ValueError):
                continue
            if run_id > marker:
                unseen.append((run_id, str(row.get("decision", "") or "")))
        if not unseen:
            return CatchUp(0, marker, "")
        unseen.sort(reverse=True)
        newest_id, newest_decision = unseen[0]
        # A first launch has no marker, so everything already in the journal
        # would count as news. Record where we are and report nothing.
        if marker == 0:
            self.mark_seen(newest_id)
            return CatchUp(0, newest_id, "")
        return CatchUp(len(unseen), newest_id, newest_decision)
