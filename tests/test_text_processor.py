import pytest
from src.core.text_processor import TextProcessor


@pytest.fixture
def processor():
    return TextProcessor(language="french")


def test_tokenize_sentences_basic(processor):
    text = "Bonjour! Comment ça va? Je vais bien."
    sentences = processor.tokenize_sentences(text)

    assert len(sentences) == 3
    assert sentences[0] == "Bonjour!"
    assert sentences[1] == "Comment ça va?"
    assert sentences[2] == "Je vais bien."


def test_tokenize_words_basic(processor):
    text = "L'avion est rapide et confortable."
    words = processor.tokenize_words(text)

    assert all(t.isalpha() for t in words)
    assert "est" in words
    assert "rapide" in words
    assert "confortable" in words


def test_normalize_text_basic(processor):
    text = "  Bonjour!!! Comment ça va?   "
    normalized = processor.normalize_text(text)

    assert normalized.startswith("bonjour")
    assert "  " not in normalized
    assert "!!!" in normalized


def test_lemmatize_word(processor):
    word = "chats"
    lemma = processor.lemmatize_word(word)

    assert lemma == "chat"


def test_get_pos_tag(processor):
    word = "manger"
    pos = processor.get_pos_tag(word)

    assert pos in {"NOUN", "VERB", "ADJ", "ADV", "PRON", "DET", "PROPN", "NUM"}


def test_get_sentences_with_metadata_basic(processor):
    text = "Le chat dort. Le chien court."
    result = processor.get_sentences_with_metadata(text)

    assert len(result) == 2
    for sent in result:
        assert "id" in sent
        assert "text" in sent
        assert "words" in sent
        assert "tagged_lemmas" in sent
        assert "word_count" in sent
        assert sent["word_count"] == len(sent["words"])


def test_metadata_contains_correct_lemma_and_pos(processor):
    text = "Les chats mangent."
    metadata = processor.get_sentences_with_metadata(text)[0]

    lemmas = [list(d.keys())[0] for d in metadata["tagged_lemmas"]]
    pos_tags = [list(d.values())[0] for d in metadata["tagged_lemmas"]]

    assert "chat" in lemmas
    assert "manger" in lemmas
    for tag in pos_tags:
        assert tag in {"NOUN", "VERB", "ADJ", "ADV", "PRON", "DET", "PROPN", "NUM"}


def test_empty_text_returns_empty_list(processor):
    result = processor.get_sentences_with_metadata("")
    assert result == []


def test_tokenize_words_with_punctuation(processor):
    text = "Bonjour, je m'appelle Jean!"
    words = processor.tokenize_words(text)
    assert all(word.isalpha() for word in words)
    assert "Bonjour" in words
    assert "Jean" in words
