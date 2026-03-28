import os
import numpy as np
from gensim.models import Word2Vec
from typing import List, Dict, Optional


class Word2VecAnalyzer:
    """Analyze text using Word2Vec embeddings."""

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the analyzer.

        Args:
            model_path: Path to a pre‑trained Word2Vec model.
        """
        self.model = None
        self.vectors = {}
        self.found_words = []
        self.not_found = []

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def load_model(self, model_path: str) -> None:
        """Load a pre‑trained Word2Vec model."""
        self.model = Word2Vec.load(model_path)

    def train_on_texts(self, sentences: List[List[str]], vector_size: int = 200):
        """
        Train a new Word2Vec model on the provided tokenized sentences.

        Args:
            sentences: List of tokenized sentences (list of lists of strings).
            vector_size: Dimension of the word vectors.

        Returns:
            self (for method chaining).
        """
        self.model = Word2Vec(
            sentences=sentences,
            vector_size=vector_size,
            window=5,
            min_count=2,
            workers=4,
            epochs=15,
            sg=1
        )
        return self

    def build_pos_vectors(self, tagged_words: List[Dict[str, str]]) -> None:
        """
        Build a dictionary mapping POS tags to word vectors for the given tagged words.
        Stores the result in self.pos_vectors for later use.
        """
        if self.model is None:
            raise ValueError("No Word2Vec model loaded or trained.")
        self.pos_vectors = {}
        for item in tagged_words:
            for word, pos in item.items():
                if word in self.model.wv:
                    if pos not in self.pos_vectors:
                        self.pos_vectors[pos] = []
                    self.pos_vectors[pos].append({word: self.model.wv[word]})

    def get_similar_words(self, word: str, topn: int = 10, pos: Optional[str] = None) -> List[str]:
        """
        Retrieve the most similar words to the given word, with optional POS filtering.

        If `pos` is provided and self.pos_vectors exists, only words of that POS are considered.
        Otherwise, the model's built-in most_similar is used, with length filtering.

        Returns a list of up to `topn` similar words (excluding the target itself) with length > 4.
        """
        if self.model is None:
            raise ValueError("No Word2Vec model loaded or trained.")
        if word not in self.model.wv:
            raise ValueError(f"Word '{word}' not in vocabulary.")

        # If we have a pos and pos_vectors built, use them to compute similarities manually.
        if pos is not None and hasattr(self, 'pzos_vectors') and pos in self.pos_vectors:
            # Compute similarity with all words in that POS group.
            target_vector = self.model.wv[word]
            candidates = self.pos_vectors[pos]
            # Calculate cosine similarity for each candidate.
            # Each candidate is a dict {w: vector}. We'll store (word, similarity)
            similarities = []
            for cand_dict in candidates:
                for cand_word, cand_vector in cand_dict.items():
                    if cand_word != word and len(cand_word) > 4:  # length filter
                        sim = np.do
        else:
            # Fallback to original method
            candidates = self.model.wv.most_similar(word, topn=topn * 2)
            filtered = [w for w, _ in candidates if len(w) > 4 and w != word]
            return filtered[:topn]

    def save_model(self, path: str) -> None:
        """Save the current model to disk."""
        if self.model is None:
            raise ValueError("No model to save.")
        self.model.save(path)