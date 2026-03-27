import random
import re
from typing import Any, Dict, List

from core.word_vectorizer import Word2VecAnalyzer
from exercises.base import BaseExercise


class SynonymsExercise(BaseExercise):
    """Exercise where user picks a synonym of a highlighted word."""

    ALLOWED_POS = {'NOUN', 'VERB', 'ADJ'}

    def __init__(self, exercise_id: str):
        super().__init__(exercise_id, "Выберите синоним к выделенному слову")
        self.word_bank: List[str] = []
        self.answer: str = ""
        self.question: str = ""
        self.analyzer: Word2VecAnalyzer = None

    def generate(self, sentences: List[Dict[str, Any]]) -> None:
        """
        Generate a synonym exercise from a list of sentence dictionaries.

        Steps:
        1. Filter sentences that contain at least one noun/verb/adjective.
        2. Pick a random such sentence and a random word of the allowed POS.
        3. Highlight that word in the sentence (surround with **).
        4. Get up to 5 similar words (potential synonyms) using Word2Vec.
        5. Select the most similar as the correct answer, and up to 2 others as distractors.
        6. Build a shuffled word bank and store the exercise.
        """
        if not sentences:
            raise ValueError("No sentences provided.")
        if self.analyzer is None:
            raise ValueError("Word2VecAnalyzer not set.")

        # Filter sentences that contain at least one word of allowed POS
        eligible_sentences = []
        for sent in sentences:
            for item in sent['tagged_lemmas']:
                pos = list(item.values())[0]
                if pos in self.ALLOWED_POS:
                    eligible_sentences.append(sent)
                    break
        if not eligible_sentences:
            raise ValueError("No sentences with nouns, verbs, or adjectives found.")

        # Randomly choose a sentence
        chosen_sentence = random.choice(eligible_sentences)
        original_sentence = chosen_sentence['text']
        tagged_lemmas = chosen_sentence['tagged_lemmas']
        words = chosen_sentence['words']

        # Collect indices where POS is allowed
        allowed_indices = [
            i for i, item in enumerate(tagged_lemmas)
            if list(item.values())[0] in self.ALLOWED_POS
        ]
        idx = random.choice(allowed_indices)
        target_word = words[idx]
        target_pos = list(tagged_lemmas[idx].values())[0]

        # Highlight the word in the sentence
        highlighted_sentence = re.sub(
            rf'\b{re.escape(target_word)}\b',
            f'**{target_word}**',
            original_sentence,
            count=1
        )

        # Get up to 5 similar words (potential synonyms)
        try:
            similar = self.analyzer.get_similar_words(target_word, topn=5, pos=target_pos)
        except ValueError:
            similar = []
        # Ensure we don't include the target word itself
        similar = [w for w in similar if w != target_word]

        # If no similar words, fallback to other words from the same sentence
        if not similar:
            similar = [w for w in words if w != target_word and len(w) > 4][:5]

        # Select correct answer (most similar) and up to 2 distractors
        correct = similar[0] if similar else target_word
        distractors = similar[1:3] if len(similar) > 1 else []

        # Build and shuffle the word bank
        self.word_bank = [correct] + distractors
        random.shuffle(self.word_bank)

        # Store the generated exercise
        self.question = highlighted_sentence
        self.answer = correct

    def validate_answer(self, user_answer: str) -> bool:
        """Check if the user picked the correct synonym."""
        return user_answer.lower().strip() == self.answer.lower()