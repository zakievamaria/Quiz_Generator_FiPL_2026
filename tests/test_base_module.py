import pytest
from typing import Any, Dict

from src.exercises.base import BaseExercise


class DummyExercise(BaseExercise):
    """Concrete implementation for testing"""

    def generate(self, context: Dict[str, Any]) -> None:
        self.question = context.get("question", "default question")
        self.answer = context.get("answer", "42")
        self.options = context.get("options", [])

    def validate_answer(self, user_answer: Any) -> bool:
        return user_answer == self.answer


def test_initialization():
    ex = DummyExercise("ex1", "test description")

    assert ex.id == "ex1"
    assert ex.description == "test description"
    assert ex.question == ""
    assert ex.answer == ""
    assert ex.options == []


def test_generate_sets_fields():
    ex = DummyExercise("ex1")

    context = {
        "question": "What is 2+2?",
        "answer": "4",
        "options": ["3", "4", "5"]
    }

    ex.generate(context)

    assert ex.question == "What is 2+2?"
    assert ex.answer == "4"
    assert ex.options == ["3", "4", "5"]


def test_validate_answer_correct():
    ex = DummyExercise("ex1")
    ex.answer = "yes"

    assert ex.validate_answer("yes") is True


def test_validate_answer_incorrect():
    ex = DummyExercise("ex1")
    ex.answer = "yes"

    assert ex.validate_answer("no") is False


def test_to_dict():
    ex = DummyExercise("ex1", "desc")
    ex.question = "Q?"
    ex.answer = "A"
    ex.options = [1, 2, 3]

    result = ex.to_dict()

    assert result == {
        "id": "ex1",
        "type": "DummyExercise",
        "description": "desc",
        "question": "Q?",
        "answer": "A",
        "options": [1, 2, 3],
    }


def test_cannot_instantiate_abstract_class():
    with pytest.raises(TypeError):
        BaseExercise("ex1")
