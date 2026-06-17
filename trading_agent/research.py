from __future__ import annotations

from pathlib import Path
import json

from .models import ResearchBundle, ResearchNote


class ResearchLoader:
    def __init__(self, config: dict):
        self.config = config

    def load(self) -> ResearchBundle:
        research_config = self.config.get("research", {})
        if not research_config.get("enabled", False):
            return ResearchBundle(enabled=False, notes=())

        notes_dir = Path(str(research_config.get("notes_dir", "research/notes")))
        if not notes_dir.exists():
            return ResearchBundle(enabled=True, notes=())

        max_notes = int(research_config.get("max_notes", 5))
        max_chars = int(research_config.get("max_chars_per_note", 3000))
        files = sorted(
            [
                path
                for path in notes_dir.iterdir()
                if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json"}
            ],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        notes = tuple(self._read_note(path, max_chars) for path in files[:max_notes])
        return ResearchBundle(enabled=True, notes=notes)

    def _read_note(self, path: Path, max_chars: int) -> ResearchNote:
        raw = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".json":
            return self._read_json_note(path, raw, max_chars)
        return ResearchNote(
            source=path.name,
            title=path.stem,
            content=raw.strip()[:max_chars],
        )

    def _read_json_note(self, path: Path, raw: str, max_chars: int) -> ResearchNote:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return ResearchNote(source=path.name, title=path.stem, content=raw.strip()[:max_chars])
        title = str(data.get("title") or data.get("query") or path.stem)
        source = str(data.get("source") or path.name)
        content = data.get("content") or data.get("summary") or data
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False, indent=2)
        return ResearchNote(source=source, title=title, content=content.strip()[:max_chars])

