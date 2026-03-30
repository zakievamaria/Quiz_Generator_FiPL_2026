import pytest
import numpy as np
from src.core.word_vectorizer import Word2VecAnalyzer


@pytest.fixture
def sample_sentences():
    return [
        ["chat", "noir", "dort"],
        ["chien", "blanc", "court"],
        ["oiseau", "bleu", "vole"],
        ["chat", "blanc", "mange"],
        ["chien", "noir", "aboie"],
        ["oiseau", "rouge", "chante"],
        ["chat", "gris", "saute"],
        ["chien", "gris", "dort"],
        ["oiseau", "jaune", "vole"],
        ["chat", "rouge", "court"]
    ]


@pytest.fixture
def analyzer(sample_sentences):
    w2v = Word2VecAnalyzer()
    w2v.train_on_texts(sample_sentences, vector_size=20)
    return w2v


def test_train_on_texts_returns_self(sample_sentences):
    analyzer = Word2VecAnalyzer()
    result = analyzer.train_on_texts(sample_sentences, vector_size=10)
    assert result is analyzer
    assert analyzer.model is not None
    assert analyzer.is_ready()


def test_train_on_empty_raises():
    analyzer = Word2VecAnalyzer()
    with pytest.raises(ValueError, match="Список предложений пуст"):
        analyzer.train_on_texts([])


def test_get_word_vector_returns_vector(analyzer):
    vec = analyzer.get_word_vector("chat")
    assert vec is not None
    assert isinstance(vec, np.ndarray)
    assert vec.shape[0] == analyzer.model.vector_size


def test_get_word_vector_unknown_returns_none(analyzer):
    vec = analyzer.get_word_vector("inconnu")
    assert vec is None


def test_is_word_in_vocab_true_false(analyzer):
    assert analyzer.is_word_in_vocab("chat") is True
    assert analyzer.is_word_in_vocab("inconnu") is False


def test_build_pos_vectors_creates_dict(analyzer):
    tagged_words = [{"chat": "NOUN"}, {"dort": "VERB"}, ("noir", "ADJ")]
    analyzer.build_pos_vectors(tagged_words)
    assert isinstance(analyzer.pos_vectors, dict)
    assert "NOUN" in analyzer.pos_vectors
    assert "VERB" in analyzer.pos_vectors
    assert "ADJ" in analyzer.pos_vectors
    for pos_dict in analyzer.pos_vectors.values():
        for vec in pos_dict.values():
            assert isinstance(vec, np.ndarray)


def test_get_similar_words_basic(analyzer):
    similar = analyzer.get_similar_words("chat", topn=3)
    assert isinstance(similar, list)
    assert all(isinstance(w, str) for w in similar)
    assert "chat" not in similar


def test_get_similar_words_with_pos(analyzer):
    tagged_words = [{"chat": "NOUN"}, {"chien": "NOUN"}, {"oiseau": "NOUN"}]
    analyzer.build_pos_vectors(tagged_words)
    similar = analyzer.get_similar_words("chat", topn=2, pos="NOUN")
    assert isinstance(similar, list)
    for w in similar:
        assert w in analyzer.pos_vectors["NOUN"]


def test_get_similar_words_unknown_word(analyzer):
    result = analyzer.get_similar_words("inconnu")
    assert result == []


def test_save_model_creates_file(tmp_path, analyzer):
    path = tmp_path / "w2v.model"
    analyzer.save_model(str(path))
    assert path.exists()


def test_get_vocab_size_and_is_ready(analyzer):
    vocab_size = analyzer.get_vocab_size()
    assert vocab_size == len(analyzer.model.wv)
    assert analyzer.is_ready() is True


def test_get_similar_words_fallback_if_pos_missing(analyzer):
    similar = analyzer.get_similar_words("chat", topn=2, pos="XYZ")
    assert isinstance(similar, list)
    assert all(isinstance(w, str) for w in similar)


def test_get_similar_words_empty_string(analyzer):
    result = analyzer.get_similar_words("")
    assert result == []


def test_get_similar_words_non_string_input(analyzer):
    result = analyzer.get_similar_words(12345)
    assert result == []


def test_build_pos_vectors_without_model_raises():
    analyzer = Word2VecAnalyzer()
    tagged_words = [{"chat": "NOUN"}]
    with pytest.raises(ValueError, match="No Word2Vec model loaded or trained."):
        analyzer.build_pos_vectors(tagged_words)
