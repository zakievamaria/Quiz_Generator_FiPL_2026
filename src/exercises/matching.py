import random
from typing import Any, Dict, List, Tuple

from .base import BaseExercise


class MatchingExercise(BaseExercise):
    """Matching Exercise - сопоставить слова/фразы с определениями"""

    def __init__(self, exercise_id: str):
        desc = (
            "Соотнесите слова из левого столбца с их определениями "
            "из правого столбца"
        )
        super().__init__(exercise_id, desc)
        self.pairs: Dict[str, str] = {}
        self.left_column: List[str] = []
        self.right_column: List[str] = []

    def generate(self, context: Dict[str, Any]) -> None:
        """Генерирует упражнение на соответствие"""
        words = context.get('words', [])

        if len(words) < 4:
            # Короткое предложение — берём слова из всего корпуса
            all_words = context.get('all_words', [])
            if len(all_words) >= 6:
                n = min(6, len(all_words))
                selected_words = random.sample(all_words, n)
                self._create_pairs_from_words(selected_words)
            else:
                msg = "Недостаточно слов для упражнения на соответствие"
                raise ValueError(msg)
        else:
            # Используем слова из текущего предложения
            self._create_pairs_from_words(words)

        # Формируем вопрос
        self.question = (
            "Сопоставьте элементы из левого столбца с элементами из правого:"
        )

        # Перемешиваем правый столбец для усложнения задания
        random.shuffle(self.right_column)

    def _create_pairs_from_words(self, words: List[str]) -> None:
        """Создает пары слово-определение из списка слов"""
        self.pairs = {}
        self.left_column = []
        self.right_column = []

        # Словарь определений
        definitions = {

        }

        # Берем до 6 слов для упражнения
        selected_words = words[:min(6, len(words))]

        for word in selected_words:
            # Приводим к нижнему регистру для поиска в словаре
            word_lower = word.lower()

            # Ищем определение
            if word_lower in definitions:
                definition = definitions[word_lower]
            else:
                # Если определения нет, создаем простое
                definition = f"это {word}"

            self.pairs[word] = definition
            self.left_column.append(word)
            self.right_column.append(definition)

    def validate_answer(self, user_answer: Dict[str, str]) -> bool:
        """Проверяет правильность соответствия"""
        if not isinstance(user_answer, dict):
            return False

        # Проверяем каждую пару
        for key, value in user_answer.items():
            if key in self.pairs and self.pairs[key] != value:
                return False

        return True

    def get_correct_matches(self) -> List[Tuple[str, str]]:
        """Возвращает правильные соответствия в виде списка кортежей"""
        return [(k, v) for k, v in self.pairs.items()]
