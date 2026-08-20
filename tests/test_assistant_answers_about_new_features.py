"""The assistant answers about the newest screens, in both languages.

Czech inflects and the matcher's prefix rule cannot bridge verze/verzi or
historie/historii, so declined forms have to be listed as aliases. And the
commonest ways to ask - "co je to X", "kde vypnu X" - were not recognised as
questions at all, so a documented answer was never even looked for.
"""

import pytest

from coinductor.ui_knowledge import UiKnowledgeService


@pytest.fixture
def service() -> UiKnowledgeService:
    return UiKnowledgeService()


CZECH = [
    "Co znamená ta hláška o nové verzi?",
    "Kde vypnu kontrolu aktualizací?",
    "Jak odeberu symbol z analýzy?",
    "Kde najdu povolené symboly?",
    "Proč se liší navržená a schválená částka?",
    "Proč se s tou mincí neobchoduje, má krátkou historii?",
    "Co je to krátká historie u nové mince?",
]

ENGLISH = [
    "What does the new version notice do?",
    "How do I remove an allowed symbol?",
    "Why is the approved amount different from the proposed one?",
    "What is insufficient price history?",
]


@pytest.mark.parametrize("question", CZECH)
def test_czech_questions_are_answered_in_czech(service, question) -> None:
    answer = service.answer(question)

    assert answer, question
    # A Czech question answered in English is a miss even when it matched.
    assert any(character in answer for character in "áčďéěíňóřšťúůýž"), question


@pytest.mark.parametrize("question", ENGLISH)
def test_english_questions_are_answered(service, question) -> None:
    assert service.answer(question), question


UPDATING = [
    "Jak mám aktualizovat Coinductor?",
    "Musím před aktualizací odinstalovat?",
    "Kde najdu odinstalátor?",
    "Přijdu odinstalací o data?",
    "How do I update Coinductor?",
    "Do I have to uninstall before updating?",
    "Will uninstalling delete my journal?",
]


@pytest.mark.parametrize("question", UPDATING)
def test_updating_is_explained_however_it_is_asked(service, question) -> None:
    """Installing over the top leaves a mixture that fails obscurely, so the
    three steps have to be findable by every ordinary phrasing of the question."""
    answer = service.answer(question)

    assert answer, question
    lowered = answer.lower()
    assert "odinstal" in lowered or "uninstall" in lowered, question


def test_the_update_answer_says_data_survives(service) -> None:
    """The reason uninstall-then-install is safe advice at all."""
    answer = service.answer("Will uninstalling delete my journal?").lower()

    assert "survive" in answer or "zůstan" in answer


def test_the_update_answer_says_it_installs_nothing(service) -> None:
    """The reassurance is the point: it is an outbound request, and people ask."""
    answer = service.answer("What does the new version notice do?")

    assert "never downloads or installs" in answer


def test_the_history_answer_survives_consensus_being_off(service) -> None:
    answer = service.answer("What is insufficient price history?")

    assert "consensus" in answer


def test_an_unrelated_question_still_matches_nothing(service) -> None:
    """The widened question gate must not turn everything into a match."""
    assert service.answer("banana") is None
