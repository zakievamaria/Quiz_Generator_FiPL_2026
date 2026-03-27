import random
from typing import Any, Dict

from exercises.base import BaseExercise


class WordOrderExercise(BaseExercise):
    """Упражнение на восстановление порядка слов"""

    def __init__(self, exercise_id: str):
        super().__init__(exercise_id, "Восстановите правильный порядок слов в предложении")

    def generate(self, context: Dict[str, Any]) -> None:
        """Генерирует упражнение из предложения"""
        sentence = context.get('sentence', '')
        words = context.get('words', [])

        if not words:
            words = sentence.split()
            random.shuffle(words)
            self.question = ' '.join(words)
        else:
            shuffled = words.copy()
            random.shuffle(shuffled)
            self.question = ' '.join(shuffled)

        self.answer = sentence
        self.options = []  # Не требуется для этого типа

    def validate_answer(self, user_answer: str) -> bool:
        """Проверяет, правильно ли восстановлен порядок слов"""
        # Нормализуем ответ (убираем лишние пробелы, приводим к нижнему регистру)
        normalized_user = ' '.join(user_answer.lower().split())
        normalized_correct = ' '.join(self.answer.lower().split())
        return normalized_user == normalized_correct