from coinductor.assistant_history import AssistantHistoryStore


def test_history_store_saves_restores_and_summarizes_chat(tmp_path) -> None:
    store = AssistantHistoryStore(tmp_path / "state" / "assistant_history.json")
    messages = [
        {"role": "assistant", "text": "How can I help?"},
        {"role": "user", "text": "What blocks the current trade?"},
        {"role": "assistant", "text": "The latest decision is HOLD."},
    ]

    store.save("chat-1", messages, "Action Plan")

    summary = store.summaries()[0]
    restored = store.get("chat-1")
    assert summary["title"] == "What blocks the current trade?"
    assert summary["contextPage"] == "Action Plan"
    assert summary["messageCount"] == 3
    assert restored["messages"] == messages


def test_history_store_rotates_conversations_and_message_count(tmp_path) -> None:
    store = AssistantHistoryStore(
        tmp_path / "assistant_history.json",
        max_conversations=2,
        max_messages=3,
    )
    for index in range(3):
        store.save(
            f"chat-{index}",
            [
                {"role": "user", "text": f"Question {index}"},
                {"role": "assistant", "text": "One"},
                {"role": "user", "text": "Two"},
                {"role": "assistant", "text": "Three"},
            ],
            "Overview",
        )

    summaries = store.summaries()
    assert [item["id"] for item in summaries] == ["chat-2", "chat-1"]
    assert summaries[0]["messageCount"] == 3


def test_history_store_preserves_local_image_reference(tmp_path) -> None:
    store = AssistantHistoryStore(tmp_path / "assistant_history.json")
    store.save(
        "image-chat",
        [
            {
                "role": "user",
                "text": "What is shown here?",
                "imageUrl": "file:///D:/Screenshots/example.png",
                "imageName": "example.png",
            },
            {"role": "assistant", "text": "It shows the Overview page."},
        ],
        "AI Assistant",
    )

    restored = store.get("image-chat")

    assert restored["messages"][0]["imageUrl"].endswith("example.png")
    assert restored["messages"][0]["imageName"] == "example.png"
