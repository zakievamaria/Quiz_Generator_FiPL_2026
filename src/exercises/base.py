from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseExercise(ABC):
    """Абстрактный базовый класс для всех типов упражнений"""

    def __init__(self, exercise_id: str, description: str = ""):
        self.id = exercise_id
        self.description = description
        self.question = ""
        self.answer = ""
        self.options: List[Any] = []

    @abstractmethod
    def generate(self, context: Dict[str, Any]) -> None:
        """Генерирует упражнение на основе контекста"""
        pass

    @abstractmethod
    def validate_answer(self, user_answer: Any) -> bool:
        """Проверяет ответ пользователя"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует упражнение в словарь для сохранения"""
        return {
            'id': self.id,
            'type': self.__class__.__name__,
            'description': self.description,
            'question': self.question,
            'answer': self.answer,
            'options': self.options
        }