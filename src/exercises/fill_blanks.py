import random
import re
from typing import Any, Dict, List

from src.core.word_vectorizer import Word2VecAnalyzer
from src.exercises.base import BaseExercise


class FillBlanksExercise(BaseExercise):
    ALLOWED_POS = {'NOUN', 'VERB', 'ADJ'}
    MIN_WORD_LENGTH = 5   # words longer than 4 characters

    def __init__(self, exercise_id: str):
        super().__init__(exercise_id, "Заполните пропуски подходящими словами")
        self.word_bank: List[str] = []
        self.answer: str = ""
        self.question: str = ""
        self.analyzer: Word2VecAnalyzer = Word2VecAnalyzer()

    def generate(self, sentences: List[Dict[str, Any]]) -> None:
        if not sentences:
            raise ValueError("No sentences provided.")
        if self.analyzer is None:
            raise ValueError("Word2VecAnalyzer not set.")

        max_attempts = 10
        for attempt in range(max_attempts):
            chosen_sentence = random.choice(sentences)
            original_sentence = chosen_sentence['text']
            words = chosen_sentence['words']
            tagged_lemmas = chosen_sentence['tagged_lemmas']

            # Filter indices: allowed POS and word length > 4
            allowed_indices = []
            for i, d in enumerate(tagged_lemmas):
                pos = list(d.values())[0]
                word = words[i]
                if pos in self.ALLOWED_POS and len(word) >= self.MIN_WORD_LENGTH:
                    allowed_indices.append(i)
            if not allowed_indices:
                continue

            idx = random.choice(allowed_indices)
            blank_word = words[idx]
            blank_pos = list(tagged_lemmas[idx].values())[0]

            # Try to get similar words (distractors) of same POS
            try:
                similar = self.analyzer.get_similar_words(blank_word, topn=5, pos=blank_pos)
            except ValueError:
                similar = []

            # Remove blank word itself
            similar = [w for w in similar if w != blank_word]

            if len(similar) >= 2:
                distractors = similar[:2]
                word_bank = [blank_word] + distractors
                random.shuffle(word_bank)

                sentence_blank = re.sub(rf'\b{re.escape(blank_word)}\b', '___', original_sentence, count=1)

                self.question = sentence_blank
                self.answer = blank_word
                self.word_bank = word_bank
                return

        # Fallback: use random words from the sentence (including the answer) to build the bank
        print("Warning: Could not find enough similar words. Using fallback word bank from sentence.")
        # Try once more to find a sentence with an allowed word of sufficient length
        for _ in range(max_attempts):
            chosen_sentence = random.choice(sentences)
            words = chosen_sentence['words']
            tagged_lemmas = chosen_sentence['tagged_lemmas']
            allowed_indices = []
            for i, d in enumerate(tagged_lemmas):
                pos = list(d.values())[0]
                word = words[i]
                if pos in self.ALLOWED_POS and len(word) >= self.MIN_WORD_LENGTH:
                    allowed_indices.append(i)
            if allowed_indices:
                idx = random.choice(allowed_indices)
                blank_word = words[idx]
                break
        else:
            # Ultimate fallback: any sentence, any word with length > 4 (if possible)
            for _ in range(max_attempts):
                chosen_sentence = random.choice(sentences)
                words = chosen_sentence['words']
                long_words = [w for w in words if len(w) >= self.MIN_WORD_LENGTH]
                if long_words:
                    blank_word = random.choice(long_words)
                    break
            else:
                # If still no word, pick any word
                blank_word = random.choice(words)

        original_sentence = chosen_sentence['text']
        sentence_blank = re.sub(rf'\b{re.escape(blank_word)}\b', '___', original_sentence, count=1)

        # Build word bank: include blank_word and two other unique words from the sentence
        other_words = [w for w in chosen_sentence['words'] if w != blank_word]
        other_words = list(dict.fromkeys(other_words))  # unique
        if len(other_words) >= 2:
            selected_others = random.sample(other_words, 2)
            word_bank = [blank_word] + selected_others
        else:
            word_bank = [blank_word] + other_words
            while len(word_bank) < 3:
                word_bank.append(blank_word)  # pad with blank_word if needed

        random.shuffle(word_bank)
        self.question = sentence_blank
        self.answer = blank_word
        self.word_bank = word_bank

    def validate_answer(self, user_answer: str) -> bool:
        """Реализация абстрактного метода"""
        return user_answer.strip().lower() == self.answer.strip().lower()