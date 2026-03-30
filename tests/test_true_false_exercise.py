from src.exercises.true_false import (
    TrueFalseExercise,
    find_markers_in_doc,
    distort_span,
    paraphrase
)


# Helper classes for mocking NLP
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


# Reusable assertion: sentence contains real words
def assert_contains_real_words(sentence: str):
    sentence = sentence.strip()
    assert sentence != "", "Sentence is empty or only spaces"
    assert any(c.isalnum() for c in sentence), "Sentence contains no letters or digits"
    assert len(sentence.split()) > 1, "Sentence must contain multiple words"


# Tests for find_markers_in_doc
def test_find_markers_returns_expected_structure(monkeypatch):
    doc = FakeDoc("J'ai toujours aimé apprendre, mais parfois je déteste le faire.")

    monkeypatch.setattr("src.exercises.true_false.tfs_matcher", lambda doc: [(1, 0, 1)])

    results = find_markers_in_doc(doc)
    assert len(results) == 1
    result = results[0]
    assert "label" in result
    assert "text" in result
    assert "start" in result
    assert "end" in result


# Tests for distort_span
def test_distort_span_replaces_word():
    sent = FakeSpan("J'ai toujours aimé apprendre, mais parfois je déteste le faire.", start=0)
    marker = {
        "label": "TEMPORAL_MARKERS",
        "text": "toujours",
        "start": 2,
        "end": 3,
    }

    result = distort_span(sent, marker)
    assert "toujours" in result or "parfois" in result
    assert_contains_real_words(result)


# Tests for TrueFalseExercise.generate
def test_generate_creates_true_and_false_statements(monkeypatch):
    ex = TrueFalseExercise("1")
    sentence = "J'ai toujours aimé apprendre, mais parfois je déteste le faire."

    monkeypatch.setattr(
        "src.exercises.true_false.nlp",
        lambda text: FakeDoc(text)
    )

    monkeypatch.setattr(
        "src.exercises.true_false.find_markers_in_doc",
        lambda doc: [
            {"label": "TEMPORAL_MARKERS", "text": "toujours", "start": 2, "end": 3},
            {"label": "TEMPORAL_MARKERS", "text": "parfois", "start": 7, "end": 8},
        ]
    )

    monkeypatch.setattr(
        "src.exercises.true_false.paraphrase",
        lambda model, tokenizer, sent: f"{sent} (paraphrased)"
    )

    ex.generate({"sentence": sentence})

    assert ex.question is not None
    assert sentence in ex.question
    assert isinstance(ex.answer, list)

    for stmt in ex.statements:
        assert_contains_real_words(stmt["text"])
        if not stmt["is_true"]:
            assert "toujours" in stmt["text"] or "parfois" in stmt["text"]


# Tests for _get_false_statements
def test_false_statements_replaces_marker(monkeypatch):
    ex = TrueFalseExercise("1")
    sentence_span = FakeSpan(
        "J'ai toujours aimé apprendre, mais parfois je déteste le faire.",
        start=0,
        end=13
    )

    markers = [
        {"label": "TEMPORAL_MARKERS", "text": "toujours", "start": 2, "end": 3}
    ]

    false_stmts = ex._get_false_statements([sentence_span], markers)
    assert len(false_stmts) == 1
    stmt = false_stmts[0]
    assert stmt["is_true"] is False
    assert stmt["text"] != sentence_span.text
    assert_contains_real_words(stmt["text"])


# Tests for _get_true_statements
def test_true_statements_are_marked_true(monkeypatch):
    ex = TrueFalseExercise("1")
    monkeypatch.setattr(
        "src.exercises.true_false.paraphrase",
        lambda model, tokenizer, sent: f"{sent} (paraphrased)"
    )

    sentence_span = FakeSpan("J'ai toujours aimé apprendre, mais parfois je déteste le faire.")
    result = ex._get_true_statements([sentence_span])
    assert len(result) == 1
    stmt = result[0]
    assert stmt["is_true"] is True
    assert_contains_real_words(stmt["text"])


# Tests for validate_answer
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


# Tests for paraphrase
def test_paraphrase_returns_str(monkeypatch):
    class FakeModel:
        def generate(self, **kwargs):
            return [[101, 102]]

    class FakeTokenizer:
        eos_token_id = 0  # добавлено

        def __call__(self, text, **kwargs):
            return {"input_ids": [0]}

        def decode(self, output, skip_special_tokens=True):
            return "Ceci est une paraphrase"

    model = FakeModel()
    tokenizer = FakeTokenizer()
    sentence = "J'ai toujours aimé apprendre, mais parfois je déteste le faire."

    result = paraphrase(model, tokenizer, sentence)
    assert isinstance(result, str)
    assert_contains_real_words(result)
