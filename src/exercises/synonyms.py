import random
import re
from typing import Any, Dict, List, Tuple, Union

from src.core.word_vectorizer import Word2VecAnalyzer
from src.exercises.base import BaseExercise


class SynonymsExercise(BaseExercise):
    """Exercise where user picks a synonym of a highlighted word."""

    ALLOWED_POS = {'NOUN', 'VERB', 'ADJ'}

    def __init__(self, exercise_id: str):
        super().__init__(exercise_id, "Выберите синоним к выделенному слову")
        self.word_bank: List[str] = []
        self.answer: str = ""
        self.question: str = ""
        self.analyzer: Word2VecAnalyzer = Word2VecAnalyzer()

    def set_analyzer(self, analyzer):
        self.analyzer = analyzer

    def _parse_tagged_item(self, item: Union[Dict, Tuple, List, str]) -> Tuple[str, str]:
        """
        Универсальный парсер для разных форматов tagged_lemmas.
        Возвращает кортеж (слово, POS).
        """
        if isinstance(item, dict):
            word = list(item.keys())[0]
            pos = item[word]
        elif isinstance(item, (tuple, list)) and len(item) >= 2:
            word = item[0]
            pos = item[1]
        elif isinstance(item, str):
            word = item
            pos = 'UNKNOWN'
        else:
            word = str(item)
            pos = 'UNKNOWN'

        return word, pos

    def generate(self, context: Dict[str, Any]) -> None:
        """
        Generate a synonym exercise from context dictionary.
        """
        if self.analyzer is None:
            raise ValueError("Word2VecAnalyzer not set.")

        # Получаем данные из контекста
        tagged_lemmas = context.get('tagged_lemmas', [])
        words = context.get('words', [])
        original_sentence = context.get('sentence', '')

        if not tagged_lemmas or not words:
            raise ValueError("Нет данных для генерации упражнения")

        # Парсим tagged_lemmas в универсальный формат
        parsed_items = [self._parse_tagged_item(item) for item in tagged_lemmas]

        # Фильтруем слова с разрешёнными частями речи
        allowed_indices = [
            i for i, (word, pos) in enumerate(parsed_items)
            if pos in self.ALLOWED_POS and len(word) > 3
        ]

        if not allowed_indices:
            # Fallback: берём любое длинное слово
            allowed_indices = [i for i, word in enumerate(words) if len(word) > 3]

        if not allowed_indices:
            raise ValueError("Нет подходящих слов для упражнения")

        # Выбираем случайное слово
        idx = random.choice(allowed_indices)
        target_word = words[idx]
        target_pos = parsed_items[idx][1]

        # Выделяем слово в предложении
        highlighted_sentence = re.sub(
            rf'\b{re.escape(target_word)}\b',
            f'**{target_word}**',
            original_sentence,
            count=1,
            flags=re.IGNORECASE
        )

        # Получаем синонимы
        try:
            similar = self.analyzer.get_similar_words(target_word, topn=5, pos=target_pos)
        except Exception as e:
            print(f"⚠ Ошибка поиска синонимов: {e}")
            similar = []

        # Убираем само целевое слово
        similar = [w for w in similar if w.lower() != target_word.lower()]

        # Fallback если нет синонимов
        if not similar:
            similar = [w for w in words if w != target_word and len(w) > 3][:5]

        if not similar:
            raise ValueError("Не найдено слов для вариантов ответа")

        # Формируем варианты ответа
        correct = similar[0] if similar else target_word
        distractors = similar[1:3] if len(similar) > 1 else []

        self.word_bank = [correct] + distractors
        random.shuffle(self.word_bank)

        self.question = highlighted_sentence
        self.answer = correct

    def validate_answer(self, user_answer: str) -> bool:
        """Check if the user picked the correct synonym."""
        return user_answer.lower().strip() == self.answer.lower()