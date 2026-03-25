import random
import re
import numpy as np
import spacy
from typing import Dict, Any, List
from exercises.base import BaseExercise
from core.word_vectorizer import Word2VecAnalyzer


class FillBlanksExercise(BaseExercise):
    """"Exercise for filling in blanks"""

    def __init__(self, exercise_id: str):
        super().__init__(exercise_id, "Fill in the blanks with appropriate words")
        self.word_bank: List[str] = []
        self.answer: str = ""
        self.question: str = ""
        self.analyzer: Word2VecAnalyzer = Word2VecAnalyzer()

    def generate(self, sentences: List[Dict[str, Any]]) -> None:
        """
        Create a fill-in-the-blank exercise from a list of sentence dictionaries.

        Steps:
        1. Randomly pick a sentence.
        2. Randomly pick a word from that sentence.
        3. Replace the first occurrence of that word with "___".
        4. Try to get up to 5 similar words (distractors) from the Word2Vec model.
           If the model returns fewer than 5, fill the remaining slots with random
           words from the same sentence (excluding the blank).
        5. Store the exercise.
        """
        if not sentences:
            raise ValueError("No sentences provided.")

        if self.analyzer is None:
            raise ValueError(
                "Word2VecAnalyzer not set. Please assign an instance to self.analyzer before calling generate()."
            )
        nlp = spacy.load('fr_core_news_sm')

        # 1. Randomly choose a sentence
        chosen_sentence = random.choice(sentences)
        original_sentence = chosen_sentence['text']
        words = chosen_sentence['words']

        if not words:
            raise ValueError("Selected sentence contains no words.")

        # 2. Randomly choose a word
        blank_word = random.choice(words)
        blank_lemma = nlp(blank_word)[0].lemma_

        # 3. Replace first occurrence with "___"
        sentence_blank = re.sub(rf'\b{re.escape(blank_word)}\b', '___', original_sentence, count=1)

        def generate(self, sentences: List[Dict[str, Any]]) -> None:
            # ... existing code ...
            # 4. Try to get similar words as distractors (now topn=3)
            similar = []
            try:
                similar = self.analyzer.get_similar_words(blank_word, topn=3, pos=blank_pos)  # changed from 5
            except ValueError:
                pass

            # Remove the blank word itself
            other_words = [w for w in similar if w != blank_word]

            # If we have fewer than 3 distractors, add random words from the sentence
            if len(other_words) < 3:
                candidates = [w for w in words if w != blank_word and len(w) > 4]
                if candidates:
                    needed = 3 - len(other_words)
                    additional = random.sample(candidates, min(needed, len(candidates)))
                    other_words.extend(additional)

            self.question = sentence_blank
            self.answer = blank_word
            self.word_bank = other_words

    def validate_answer(self, user_answer: str) -> bool:
        """Проверяет, правильно ли заполнен пропуск"""
        return user_answer.lower().strip() == self.answer.lower()