import os
import numpy as np
from gensim.models import Word2Vec
from typing import List, Dict, Optional

# Unused imports removed. If you later add clustering/visualization,
# you can re‑import them inside the respective methods.

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

    def get_vectors(self, words: List[str]) -> Dict[str, np.ndarray]:
        """
        Retrieve vectors for a list of words.

        Args:
            words: List of words to look up.

        Returns:
            Dictionary mapping each word to its vector (if present).

        Populates:
            self.vectors: same dictionary.
            self.found_words: words that were found in the model.
            self.not_found: words that were not found.
        """
        if self.model is None:
            raise ValueError("No Word2Vec model loaded or trained. Call load_model() or train_on_texts() first.")

        self.vectors = {}
        self.found_words = []

        for word in words:
            if word in self.model.wv:
                self.vectors[word] = self.model.wv[word]
                self.found_words.append(word)

        return self.vectors

    def save_model(self, path: str) -> None:
        """Save the current model to disk."""
        if self.model is None:
            raise ValueError("No model to save.")
        self.model.save(path)