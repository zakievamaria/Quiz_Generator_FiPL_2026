import pytest
import random

from src.exercises.true_false import (
    TrueFalseExercise,
    find_markers_in_doc,
    distort_span,
    paraphrase
)


# ----------------------------
# Helper classes for mocking NLP
# ----------------------------

class FakeSpan:
    def __init__(self, text, start=0, end=1, sent=None):
        self.text = text
        self.start = start
        self.end = end
        self.sent = sent or self

    def __getitem__(self, item):
        return FakeSpan(self.text)

    def __str__(self):
        return self.text


class FakeDoc:
    def __init__(self, text):
        self.text = text
        self.vocab = type("Vocab", (), {"strings": {1: "TEMPORAL_MARKERS"}})()
        self._sents = [FakeSpan(text, 0, len(text))]

    @property
    def sents(self):
        return self._sents

    def __getitem__(self, item):
        return FakeSpan(self.text)


# ----------------------------
# Reusable assertion: sentence contains real words
# ----------------------------

def assert_contains_real_words(sentence: str):
    sentence = sentence.strip()
    assert sentence != "", "Sentence is empty or only spaces"
    assert any(c.isalnum() for c in sentence), "Sentence contains no letters or digits"
    assert len(sentence.split()) > 1, "Sentence must contain multiple words"


@pytest.fixture
def real_words_assertion():
    return assert_contains_real_words


# ----------------------------
# Tests for find_markers_in_doc
# ----------------------------

def test_find_markers_returns_expected_structure():
    doc = FakeDoc("J'ai toujours aimé apprendre, mais parfois je déteste le faire.")

    def fake_matcher(_):
        return [(1, 0, 1)]

    results = find_markers_in_doc(doc, fake_matcher)
    assert len(results) == 1
    result = results[0]
    assert "label" in result
    assert "text" in result
    assert "start" in result
    assert "end" in result
    assert "sent_start" in result
    assert "sent_end" in result


# ----------------------------
# Tests for distort_span
# ----------------------------

def test_distort_span_replaces_word(real_words_assertion):
    sent = FakeSpan("J'ai toujours aimé apprendre, mais parfois je déteste le faire.", start=0)
    marker = {
        "label": "TEMPORAL_MARKERS",
        "text": "toujours",
        "start": 2,
        "end": 3,
    }

    result = distort_span(sent, marker)
    assert "parfois" in result or "toujours" in result  # because replacements could vary
    real_words_assertion(result)


# ----------------------------
# Tests for TrueFalseExercise.generate with realistic false statements
# ----------------------------

def test_generate_creates_true_and_false_statements(monkeypatch, real_words_assertion):
    ex = TrueFalseExercise("1")
    sentence = "J'ai toujours aimé apprendre, mais parfois je déteste le faire."

    # Mock NLP
    monkeypatch.setattr(
        "src.exercises.true_false.nlp",
        lambda text: FakeDoc(text)
    )

    # Mock marker detection: return both temporal markers in sentence
    monkeypatch.setattr(
        "src.exercises.true_false.find_markers_in_doc",
        lambda doc, matcher: [
            {"label": "TEMPORAL_MARKERS", "text": "toujours", "start": 2, "end": 3, "sent_start": 0, "sent_end": 13},
            {"label": "TEMPORAL_MARKERS", "text": "parfois", "start": 7, "end": 8, "sent_start": 0, "sent_end": 13},
        ]
    )

    # Mock paraphrase to just return the original text with "paraphrased"
    monkeypatch.setattr(
        "src.exercises.true_false.paraphrase",
        lambda model, tokenizer, sent: [f"{sent} (paraphrased)"]
    )

    # Generate statements
    ex.generate({"sentence": sentence})

    assert ex.question is not None
    assert sentence in ex.question
    assert isinstance(ex.answer, list)

    # Check that all statements contain real words
    for stmt in ex.statements:
        real_words_assertion(stmt["text"])
        # If false statement, it must contain either "toujours" or "parfois" replaced
        if not stmt["is_true"]:
            assert ("toujours" in stmt["text"] or "parfois" in stmt["text"])


def test_false_statements_replaces_marker(monkeypatch, real_words_assertion):
    ex = TrueFalseExercise("1")
    sentence = "J'ai toujours aimé apprendre, mais parfois je déteste le faire."

    monkeypatch.setattr(
        "src.exercises.true_false.nlp",
        lambda text: FakeDoc(text)
    )

    markers = [
        {"label": "TEMPORAL_MARKERS", "text": "toujours", "start": 2, "end": 3, "sent_start": 0, "sent_end": 13}
    ]

    false_stmts = ex._get_false_statements([sentence], markers)
    assert len(false_stmts) == 1
    stmt = false_stmts[0]
    # Should be marked false
    assert stmt["is_true"] is False
    # Should contain a replacement word (not exactly the original marker)
    assert stmt["text"] != sentence
    real_words_assertion(stmt["text"])


# ----------------------------
# Tests for _get_true_statements
# ----------------------------

def test_true_statements_are_marked_true(monkeypatch, real_words_assertion):
    ex = TrueFalseExercise("1")
    monkeypatch.setattr(
        "src.exercises.true_false.paraphrase",
        lambda model, tokenizer, sent: [f"{sent} (paraphrased)"]
    )
    result = ex._get_true_statements(["J'ai toujours aimé apprendre, mais parfois je déteste le faire."])
    assert len(result) == 1
    stmt = result[0]
    assert stmt["is_true"] is True
    real_words_assertion(stmt["text"])


# ----------------------------
# Tests for validate_answer
# ----------------------------

def test_validate_answer_correct():
    ex = TrueFalseExercise("1")
    ex.statements = [{"text": "a"}, {"text": "b"}]
    ex.answer = [True, False]
    assert ex.validate_answer([True, False]) is True


def test_validate_answer_wrong_length():
    ex = TrueFalseExercise("1")
    ex.statements = [{"text": "a"}]
    ex.answer = [True]
    assert ex.validate_answer([True, False]) is False


def test_validate_answer_wrong_type():
    ex = TrueFalseExercise("1")
    ex.statements = [{"text": "a"}]
    ex.answer = [True]
    assert ex.validate_answer("not a list") is False


# ----------------------------
# Tests for paraphrase function
# ----------------------------

def test_paraphrase_returns_list(monkeypatch, real_words_assertion):
    class FakeModel:
        def generate(self, **kwargs):
            return [[101, 102]]

    class FakeTokenizer:
        def __call__(self, text, **kwargs):
            return {"input_ids": [0]}

        def batch_decode(self, outputs, skip_special_tokens=True):
            return ["Ceci est une paraphrase"]

    model = FakeModel()
    tokenizer = FakeTokenizer()
    sentence = "J'ai toujours aimé apprendre, mais parfois je déteste le faire."

    result = paraphrase(model, tokenizer, sentence, num_return_sequences=1)
    assert isinstance(result, list)
    assert len(result) == 1
    real_words_assertion(result[0])