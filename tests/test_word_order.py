import pytest
import random
from src.exercises.word_order import WordOrderExercise


@pytest.fixture
def exercise():
    return WordOrderExercise("test_id")


@pytest.fixture(autouse=True)
def fixed_shuffle(monkeypatch):
    monkeypatch.setattr(random, "shuffle", lambda x: x.reverse())


def test_generate_with_words(exercise):
    context = {
        "sentence": "Je mange une pomme",
        "words": ["Je", "mange", "une", "pomme"]
    }

    exercise.generate(context)

    assert exercise.question == "pomme une mange Je"
    assert exercise.answer == "Je mange une pomme"
    assert exercise.options == []


def test_generate_without_words_uses_sentence_split(exercise):
    context = {
        "sentence": "Je mange une pomme",
        "words": []
    }

    exercise.generate(context)

    assert exercise.question == "pomme une mange Je"
    assert exercise.answer == "Je mange une pomme"


def test_generate_empty_sentence(exercise):
    context = {
        "sentence": "",
        "words": []
    }

    exercise.generate(context)

    assert exercise.question == ""
    assert exercise.answer == ""


def test_validate_correct_answer(exercise):
    exercise.answer = "Je mange une pomme"

    assert exercise.validate_answer("Je mange une pomme")


def test_validate_ignores_case_and_spaces(exercise):
    exercise.answer = "Je mange une pomme"

    assert exercise.validate_answer("  je   mange UNE   pomme  ")


def test_validate_wrong_answer(exercise):
    exercise.answer = "Je mange une pomme"

    assert not exercise.validate_answer("pomme une mange Je")


def test_validate_empty_input(exercise):
    exercise.answer = ""

    assert exercise.validate_answer("")
    assert not exercise.validate_answer("something")
