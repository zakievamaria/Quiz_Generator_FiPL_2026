import random
from typing import Dict, Any, List, Tuple
from .base import BaseExercise

class MatchingExercise(BaseExercise):
    """Matching Exercise - сопоставить слова/фразы с определениями"""

    def __init__(self, exercise_id: str):
        super().__init__(exercise_id, "Соотнесите слова из левого столбца с их определениями из правого столбца")
        self.pairs: Dict[str, str] = {}
        self.left_column: List[str] = []
        self.right_column: List[str] = []

    def generate(self, context: Dict[str, Any]) -> None:
        """Генерирует упражнение на соответствие"""
        # Получаем предложение и слова из контекста
        sentence = context.get('sentence', '')
        words = context.get('words', [])
        lemmas = context.get('lemmas', [])

        if len(words) < 4:
            # Если предложение слишком короткое, используем комбинацию из нескольких предложений
            all_words = context.get('all_words', [])
            if len(all_words) >= 6:
                # Берем случайные слова из всего корпуса
                selected_words = random.sample(all_words, min(6, len(all_words)))
                self._create_pairs_from_words(selected_words)
            else:
                raise ValueError("Недостаточно слов для создания упражнения на соответствие")
        else:
            # Используем слова из текущего предложения
            self._create_pairs_from_words(words)

        # Формируем вопрос
        self.question = "Сопоставьте элементы из левого столбца с соответствующими элементами из правого:"

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