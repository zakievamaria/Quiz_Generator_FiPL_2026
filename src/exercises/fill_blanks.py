import random
import re
from typing import Any, Dict, List, Tuple, Union

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

    def _parse_tagged_item(
        self,
        item: Union[Dict, Tuple, List, str],
    ) -> Tuple[str, str]:
        """Универсально извлекает (lemma, POS) из разных форматов tagged_lemmas."""
        if isinstance(item, dict) and item:
            word = list(item.keys())[0]
            pos = item[word]
            return str(word), str(pos)
        if isinstance(item, (tuple, list)) and len(item) >= 2:
            return str(item[0]), str(item[1])
        if isinstance(item, str):
            return item, "UNKNOWN"
        return str(item), "UNKNOWN"

    def generate(self, context: Dict[str, Any]) -> None:
        if not context:
            raise ValueError("No context provided.")
        if self.analyzer is None:
            raise ValueError("Word2VecAnalyzer not set.")

        original_sentence = context.get("sentence", "")
        words = context.get("words", [])
        tagged_lemmas = context.get("tagged_lemmas", [])

        if not original_sentence or not words:
            raise ValueError("No sentence data provided.")

        parsed = [self._parse_tagged_item(item) for item in tagged_lemmas]
        if len(parsed) < len(words):
            parsed.extend([("UNKNOWN", "UNKNOWN")] * (len(words) - len(parsed)))

        allowed_indices = [
            i for i, (_, pos) in enumerate(parsed[:len(words)])
            if pos in self.ALLOWED_POS and len(words[i]) >= self.MIN_WORD_LENGTH
        ]
        if not allowed_indices:
            allowed_indices = [
                i for i, w in enumerate(words)
                if len(w) >= self.MIN_WORD_LENGTH
            ]
        if not allowed_indices:
            raise ValueError("No suitable words found for fill-blanks.")

        idx = random.choice(allowed_indices)
        blank_word = words[idx]
        blank_pos = parsed[idx][1] if idx < len(parsed) else "UNKNOWN"

        try:
            similar = self.analyzer.get_similar_words(blank_word, topn=6, pos=blank_pos)
        except Exception:
            similar = []

        unique_similar: List[str] = []
        for w in similar:
            if not isinstance(w, str):
                continue
            normalized = w.strip()
            if (
                normalized
                and normalized.lower() != blank_word.lower()
                and normalized.lower() not in {x.lower() for x in unique_similar}
            ):
                unique_similar.append(normalized)

        distractors = unique_similar[:3]
        if len(distractors) < 2:
            extra = [
                w for w in words
                if w.lower() != blank_word.lower() and len(w) >= self.MIN_WORD_LENGTH
            ]
            for w in extra:
                if w.lower() not in {d.lower() for d in distractors}:
                    distractors.append(w)
                if len(distractors) >= 3:
                    break

        options = [blank_word] + distractors[:3]
        deduplicated_options: List[str] = []
        for option in options:
            if option.lower() not in {o.lower() for o in deduplicated_options}:
                deduplicated_options.append(option)
        if len(deduplicated_options) < 2:
            raise ValueError("Not enough answer options for fill-blanks.")

        random.shuffle(deduplicated_options)
        sentence_blank = re.sub(
            rf'\b{re.escape(blank_word)}\b',
            '___',
            original_sentence,
            count=1,
        )

        self.question = sentence_blank
        self.answer = blank_word
        self.word_bank = deduplicated_options
        self.options = deduplicated_options

    def validate_answer(self, user_answer: str) -> bool:
        """Реализация абстрактного метода"""
        return user_answer.strip().lower() == self.answer.strip().lower()
