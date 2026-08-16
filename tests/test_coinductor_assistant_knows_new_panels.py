"""The offline assistant has to know about a feature the moment it ships.

The knowledge base is what answers before any model is consulted, so a panel
added without an entry here is a panel the assistant confidently knows nothing
about — and it answers in whichever language the question was asked, so both
have to be checked.

These are the questions somebody would actually type, not the aliases. The
aliases exist to make these work; asserting on them instead would pass while
every real phrasing missed.
"""

import pytest

from coinductor.ui_knowledge import UiKnowledgeService, is_czech

ENGLISH = (
    "what is the order sizing panel",
    "what is auto funding",
    "why is my order this size",
    "what does use suggested do",
    "how do i update coinductor",
    "how much can move from earn to spot",
    "what is start with windows",
    "how to set the order size",
)

CZECH = (
    "co dela panel velikost prikazu",
    "k cemu je automaticke financovani",
    "proc je prikaz takhle velky",
    "co dela tlacitko pouzit doporucene",
    "jak mam udelat aktualizaci",
    "kolik se muze presunout z earnu na spot",
    "k cemu je spoustet s windows",
    "jak zaridit spusteni po prihlaseni",
)


@pytest.fixture
def service() -> UiKnowledgeService:
    return UiKnowledgeService()


@pytest.mark.parametrize("question", ENGLISH)
def test_an_english_question_is_answered(service: UiKnowledgeService, question: str) -> None:
    assert service.answer(question), f"no entry answers {question!r}"


@pytest.mark.parametrize("question", CZECH)
def test_a_czech_question_is_answered(service: UiKnowledgeService, question: str) -> None:
    assert service.answer(question), f"no entry answers {question!r}"


@pytest.mark.parametrize("question", CZECH)
def test_a_czech_question_is_answered_in_czech(service: UiKnowledgeService, question: str) -> None:
    """Typed without diacritics, which is how people actually type."""
    assert is_czech(question) is True, f"{question!r} was not recognised as Czech"


@pytest.mark.parametrize("question", ENGLISH)
def test_an_english_question_is_not_taken_for_czech(service: UiKnowledgeService, question: str) -> None:
    assert is_czech(question) is False, f"{question!r} was mistaken for Czech"


def test_the_two_new_panels_are_described_in_both_languages(service: UiKnowledgeService) -> None:
    english = service.answer("what is the earn funding panel")
    czech = service.answer("co dela panel financovani z earnu")

    assert english and czech
    assert english != czech


def test_the_assistant_says_a_redemption_is_not_a_withdrawal(service: UiKnowledgeService) -> None:
    """The word invites the wrong fear, in both languages."""
    assert "not a withdrawal" in service.answer("what is auto funding")
    assert "ne o výběr" in service.answer("co dela panel financovani z earnu")


def test_the_assistant_says_bots_are_not_auto_funded(service: UiKnowledgeService) -> None:
    """The obvious wrong assumption, and the one worth correcting unprompted.

    Grid and Rebalancing bots are recommend-only because Binance has no public
    API to create them, so funding one automatically would move money and
    leave the bot still to be made by hand.
    """
    answer = service.answer("k cemu je automaticke financovani")

    assert "Grid" in answer and "Rebalancing" in answer


def test_the_autostart_answer_says_it_starts_into_the_tray(service: UiKnowledgeService) -> None:
    """The choice most likely to surprise: no window appears at logon."""
    assert "notification area" in service.answer("what is start with windows")
    assert "oznamovací oblasti" in service.answer("k cemu je spoustet s windows")


def test_the_upgrade_answer_mentions_quitting_first(service: UiKnowledgeService) -> None:
    assert "tray" in service.answer("how do i update coinductor").lower()
    assert "Quit" in service.answer("jak mam udelat aktualizaci")


def test_an_unrelated_question_is_left_to_the_model(service: UiKnowledgeService) -> None:
    """The knowledge base answers what it knows and declines the rest.

    Widening the question gate must not turn it into something that answers
    everything from a fixed entry.
    """
    assert service.answer("why is bitcoin falling today") is None
    assert service.answer("kolik stoji bitcoin") is None
    # "jak nastavit" was added to the gate for settings questions; it must not
    # turn every "how do I set up X" into a canned answer.
    assert service.answer("jak nastavit budik") is None
