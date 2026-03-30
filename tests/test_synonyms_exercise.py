import pytest
from src.exercises.synonyms import SynonymsExercise


class DummyAnalyzer:
    def __init__(self, similar_map=None):
        self.similar_map = similar_map or {}

    def get_similar_words(self, word):
        return self.similar_map.get(word, [])


@pytest.fixture
def exercise():
    return SynonymsExercise("test_id")


@pytest.fixture
def dummy_analyzer():
    return DummyAnalyzer(similar_map={
        "chat": ["félin", "animal", "pet", "minou"],
        "rapide": ["vite", "prompt", "léger"],
    })


def test_parse_tagged_item(exercise):
    assert exercise._parse_tagged_item({"chat": "NOUN"}) == ("chat", "NOUN")
    assert exercise._parse_tagged_item(("dort", "VERB")) == ("dort", "VERB")
    assert exercise._parse_tagged_item(["noir", "ADJ"]) == ("noir", "ADJ")
    assert exercise._parse_tagged_item("chien") == ("chien", "UNKNOWN")
    assert exercise._parse_tagged_item(None) == ("None", "UNKNOWN")


def test_generate_with_synonyms(exercise, dummy_analyzer):
    exercise.set_analyzer(dummy_analyzer)
    context = {
        "sentence": "Le chat dort sur le canapé.",
        "words": ["Le", "chat", "dort", "sur", "le", "canapé"],
        "tagged_lemmas": [
            ("Le", "DET"),
            ("chat", "NOUN"),
            ("dort", "VERB"),
            ("sur", "ADP"),
            ("le", "DET"),
            ("canapé", "NOUN"),
        ]
    }
    exercise.generate(context)

    assert "**" in exercise.question
    assert exercise.answer in exercise.word_bank
    assert len(exercise.word_bank) >= 2


def test_generate_with_no_synonyms_fallback(exercise):
    class EmptyAnalyzer:
        def get_similar_words(self, word):
            return []

    exercise.set_analyzer(EmptyAnalyzer())
    context = {
        "sentence": "Le chat dort sur le canapé.",
        "words": ["Le", "chat", "dort", "sur", "le", "canapé"],
        "tagged_lemmas": [
            ("Le", "DET"),
            ("chat", "NOUN"),
            ("dort", "VERB"),
            ("sur", "ADP"),
            ("le", "DET"),
            ("canapé", "NOUN"),
        ]
    }
    exercise.generate(context)
    assert exercise.answer in exercise.word_bank
    assert len(exercise.word_bank) >= 2


def test_generate_no_long_words_raises(exercise):
    class EmptyAnalyzer:
        def get_similar_words(self, word, topn=5, pos=None):
            return []
    exercise.set_analyzer(EmptyAnalyzer())
    context = {
        "sentence": "Il est là",
        "words": ["Il", "est", "là"],
        "tagged_lemmas": [("Il", "PRON"), ("est", "VERB"), ("là", "ADV")]
    }
    with pytest.raises(ValueError, match="Нет подходящих слов для упражнения"):
        exercise.generate(context)


def test_generate_insufficient_options_raises(exercise):
    class Analyzer:
        def get_similar_words(self, word, topn=5, pos=None):
            return [word]
    exercise.set_analyzer(Analyzer())
    context = {
        "sentence": "chat dort",
        "words": ["chat", "dort"],
        "tagged_lemmas": [("chat", "NOUN"), ("dort", "VERB")]
    }
    with pytest.raises(ValueError, match="Недостаточно вариантов для упражнения на синонимы"):
        exercise.generate(context)


def test_validate_answer(exercise, dummy_analyzer):
    exercise.set_analyzer(dummy_analyzer)

    context = {
        "sentence": "Le chat dort sur le canapé confortable",
        "words": ["Le", "chat", "dort", "sur", "canapé", "confortable"],
        "tagged_lemmas": [
            ("Le", "DET"),
            ("chat", "NOUN"),
            ("dort", "VERB"),
            ("sur", "ADP"),
            ("canapé", "NOUN"),
            ("confortable", "ADJ"),
        ]
    }

    exercise.generate(context)

    assert exercise.validate_answer(exercise.answer)

    wrong = next(w for w in exercise.word_bank if w != exercise.answer)
    assert not exercise.validate_answer(wrong)
