import pytest
from src.exercises.fill_blanks import FillBlanksExercise


@pytest.fixture
def exercise():
    return FillBlanksExercise("test1")


def test_parse_tagged_item_variants(exercise):
    lemma, pos = exercise._parse_tagged_item({"chat": "NOUN"})
    assert lemma == "chat" and pos == "NOUN"

    lemma, pos = exercise._parse_tagged_item(("dort", "VERB"))
    assert lemma == "dort" and pos == "VERB"

    lemma, pos = exercise._parse_tagged_item(["noir", "ADJ"])
    assert lemma == "noir" and pos == "ADJ"

    lemma, pos = exercise._parse_tagged_item("canapé")
    assert lemma == "canapé" and pos == "UNKNOWN"

    lemma, pos = exercise._parse_tagged_item(None)
    assert lemma == "None" and pos == "UNKNOWN"


def test_generate_creates_question_and_options(exercise):
    class DummyAnalyzer:
        def get_similar_words(self, word):
            return [f"{word}_sim1", f"{word}_sim2"]

    exercise.analyzer = DummyAnalyzer()

    context = {
        "sentence": "Le chat noir dort sur le canapé confortable.",
        "words": ["chat", "noir", "dort", "canapé", "confortable"],
        "tagged_lemmas": [
            ("chat", "NOUN"),
            ("noir", "ADJ"),
            ("dort", "VERB"),
            ("canapé", "NOUN"),
            ("confortable", "ADJ")
        ]
    }

    exercise.generate(context)

    assert "___" in exercise.question
    assert exercise.answer in exercise.options
    assert len(exercise.options) >= 2
    assert all(isinstance(opt, str) for opt in exercise.options)


def test_generate_with_insufficient_similar_words(exercise):
    class EmptyAnalyzer:
        def get_similar_words(self, word, topn=6, pos="UNKNOWN"):
            return []

    exercise.analyzer = EmptyAnalyzer()

    context = {
        "sentence": "Le chat noir dort sur le canapé confortable.",
        "words": ["chat", "noir", "dort", "canapé", "confortable"],
        "tagged_lemmas": [
            ("chat", "NOUN"),
            ("noir", "ADJ"),
            ("dort", "VERB"),
            ("canapé", "NOUN"),
            ("confortable", "ADJ")
        ]
    }

    exercise.generate(context)

    assert exercise.answer in exercise.options
    assert len(exercise.options) >= 2
    assert "___" in exercise.question


def test_validate_answer(exercise):
    exercise.answer = "canapé"

    assert exercise.validate_answer("canapé") is True
    assert exercise.validate_answer("  Canapé  ") is True
    assert exercise.validate_answer("chat") is False
    assert exercise.validate_answer("") is False


def test_generate_raises_without_context(exercise):
    with pytest.raises(ValueError, match="No context provided."):
        exercise.generate({})


def test_generate_raises_no_suitable_words(exercise):
    context = {
        "sentence": "Le chat dort.",
        "words": ["Le", "chat", "dort"],
        "tagged_lemmas": [("Le", "DET"), ("chat", "NOUN"), ("dort", "VERB")]
    }

    with pytest.raises(ValueError, match="No suitable words found for fill-blanks."):
        exercise.generate(context)


def test_generate_deduplicates_options(exercise):
    class DuplicateAnalyzer:
        def get_similar_words(self, word):
            return [word, f"{word}_sim1", f"{word}_sim1"]

    exercise.analyzer = DuplicateAnalyzer()

    context = {
        "sentence": "Le chat confortable dort sur le canapé.",
        "words": ["chat", "confortable", "dort", "canapé"],
        "tagged_lemmas": [
            ("chat", "NOUN"),
            ("confortable", "ADJ"),
            ("dort", "VERB"),
            ("canapé", "NOUN"),
        ]
    }

    exercise.generate(context)

    lower_options = [o.lower() for o in exercise.options]
    assert len(lower_options) == len(set(lower_options))
