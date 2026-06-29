from __future__ import annotations

import os
from pathlib import Path


class EnvWriter:
    def __init__(self, path: str | Path = ".env"):
        self.path = Path(path)

    def update(self, values: dict[str, str]) -> None:
        cleaned = {key: value.strip() for key, value in values.items() if key and value.strip()}
        if not cleaned:
            return

        lines = self.path.read_text(encoding="utf-8").splitlines() if self.path.exists() else []
        seen: set[str] = set()
        rendered: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in line:
                rendered.append(line)
                continue
            key, _value = line.split("=", 1)
            normalized = key.strip()
            if normalized in cleaned:
                rendered.append(f"{normalized}={self._quote(cleaned[normalized])}")
                os.environ[normalized] = cleaned[normalized]
                seen.add(normalized)
            else:
                rendered.append(line)

        if rendered and rendered[-1].strip():
            rendered.append("")
        for key in cleaned:
            if key not in seen:
                rendered.append(f"{key}={self._quote(cleaned[key])}")
                os.environ[key] = cleaned[key]

        self.path.write_text("\n".join(rendered) + "\n", encoding="utf-8")

    def _quote(self, value: str) -> str:
        if any(char.isspace() for char in value) or "#" in value:
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        return value
