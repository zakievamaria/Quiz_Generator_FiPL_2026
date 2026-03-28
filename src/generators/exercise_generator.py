from typing import List, Dict, Any
import random

from src.core.document_loader import DocumentLoader
from src.core.text_processor import TextProcessor
from src.exercises.word_order import WordOrderExercise
from src.exercises.fill_blanks import FillBlanksExercise
from src.exercises.synonyms import SynonymsExercise
from src.exercises.matching import MatchingExercise
from src.exercises.true_false import TrueFalseExercise
from src.formatters.docx_formatter import DocxFormatter


class ExerciseGenerator:
    """Основной класс для генерации упражнений"""

    def __init__(self, language: str = 'french'):
        self.language = language
        self.texts: List[str] = []
        self.processed_sentences: List[Dict] = []
        self.all_words: List[str] = []

        # Инициализируем компоненты
        self.text_processor = TextProcessor(language)
        self.formatter = DocxFormatter()

        # Регистрируем доступные типы упражнений
        self.exercise_types = {
            'word_order': WordOrderExercise,
            'fill_blanks': FillBlanksExercise,
            'multiple_choice': SynonymsExercise,
            'matching': MatchingExercise,
            'true_false': TrueFalseExercise
        }

    def load_texts(self, file_paths: List[str]) -> None:
        """Загружает тексты из файлов"""
        loader = DocumentLoader(file_paths)

        try:
            docs = loader.load()
        except Exception as e:
            print(f"✗ Ошибка загрузки файлов: {e}")
            return

        for doc in docs:
            self.texts.append(doc['content'])
            print(f"✓ Загружен файл: {doc['file_path']}")

        # Обрабатываем загруженные тексты
        self._process_texts()

    def _process_texts(self) -> None:
        """Обрабатывает все загруженные тексты"""
        all_text = ' '.join(self.texts)

        # Получаем предложения с метаданными
        self.processed_sentences = self.text_processor.get_sentences_with_metadata(all_text)

        # Собираем все слова для банка слов
        for sentence in self.processed_sentences:
            self.all_words.extend(sentence['words'])

        print(f"✓ Обработано {len(self.processed_sentences)} предложений")

    def generate_exercises(self, num_per_type: int = 5) -> List[Any]:
        """Генерирует упражнения всех типов"""
        exercises = []

        if not self.processed_sentences:
            raise ValueError("Сначала загрузите тексты с помощью load_texts()")

        for exercise_name, exercise_class in self.exercise_types.items():
            for i in range(num_per_type):
                # Выбираем случайное предложение
                sentence_data = random.choice(self.processed_sentences)

                # Создаем контекст для генерации
                context = {
                    'sentence': sentence_data['text'],
                    'words': sentence_data['words'],
                    'lemmas': [list(d.keys())[0] for d in sentence_data['tagged_lemmas']],
                    'other_words': self.all_words
                }

                # Генерируем упражнение
                exercise_id = f"{exercise_name}_{i + 1}"
                exercise = exercise_class(exercise_id)

                try:
                    exercise.generate(context)
                    exercises.append(exercise)
                    print(f"✓ Сгенерировано: {exercise_id}")
                except Exception as e:
                    print(f"✗ Ошибка генерации {exercise_id}: {e}")

        return exercises

    def save_exercises(self, exercises: List[Any], filename: str) -> None:
        """Сохраняет упражнения в файл"""
        self.formatter.save_exercises(exercises, filename)
        print(f"✓ Упражнения сохранены в {filename}")

    def save_answers(self, exercises: List[Any], filename: str) -> None:
        """Сохраняет ответы в файл"""
        self.formatter.save_answers(exercises, filename)
        print(f"✓ Ответы сохранены в {filename}")