from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path


class AssistantHistoryStore:
    def __init__(
        self,
        path: str | Path = "state/assistant_history.json",
        *,
        max_conversations: int = 20,
        max_messages: int = 60,
    ):
        self.path = Path(path)
        self.max_conversations = max_conversations
        self.max_messages = max_messages

    def summaries(self) -> list[dict[str, object]]:
        return [self._summary(item) for item in self._load()]

    def get(self, conversation_id: str) -> dict[str, object] | None:
        return next((item for item in self._load() if item.get("id") == conversation_id), None)

    def save(
        self,
        conversation_id: str,
        messages: list[dict[str, str]],
        context_page: str,
    ) -> None:
        normalized = []
        for item in messages:
            if item.get("role") not in {"user", "assistant"} or not str(item.get("text", "")).strip():
                continue
            message = {
                "role": str(item.get("role", "")),
                "text": str(item.get("text", ""))[:4000],
            }
            if item.get("imageUrl"):
                message["imageUrl"] = str(item["imageUrl"])
                message["imageName"] = str(item.get("imageName", "Attached image"))
            normalized.append(message)
        normalized = normalized[-self.max_messages :]
        first_user = next((item["text"] for item in normalized if item["role"] == "user"), "")
        if not first_user:
            return

        records = [item for item in self._load() if item.get("id") != conversation_id]
        records.insert(
            0,
            {
                "id": conversation_id,
                "title": _truncate(first_user, 72),
                "contextPage": context_page,
                "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "messages": normalized,
            },
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"conversations": records[: self.max_conversations]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        records = payload.get("conversations", []) if isinstance(payload, dict) else []
        return [item for item in records if isinstance(item, dict)][: self.max_conversations]

    def _summary(self, item: dict[str, object]) -> dict[str, object]:
        messages = item.get("messages", [])
        preview = next(
            (
                str(message.get("text", ""))
                for message in reversed(messages)
                if isinstance(message, dict) and message.get("role") == "assistant"
            ),
            "",
        )
        return {
            "id": str(item.get("id", "")),
            "title": str(item.get("title", "Untitled chat")),
            "contextPage": str(item.get("contextPage", "Unknown")),
            "updatedAt": str(item.get("updatedAt", "")),
            "messageCount": len(messages) if isinstance(messages, list) else 0,
            "preview": _truncate(preview, 140),
        }


def _truncate(value: str, limit: int) -> str:
    text = " ".join(value.split())
    return text if len(text) <= limit else f"{text[: limit - 3]}..."
