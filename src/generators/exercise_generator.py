from typing import Any, Dict, List, Type, Union
import random

from src.core.document_loader import DocumentLoader
from src.core.text_processor import TextProcessor
from src.core.word_vectorizer import Word2VecAnalyzer

from src.exercises.word_order import WordOrderExercise
from src.exercises.fill_blanks import FillBlanksExercise
from src.exercises.synonyms import SynonymsExercise
from src.exercises.matching import MatchingExercise
from src.formatters.docx_formatter import DocxFormatter

ExerciseImpl = Union[
    Type[WordOrderExercise],
    Type[FillBlanksExercise],
    Type[SynonymsExercise],
    Type[MatchingExercise],
]


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
        self.analyzer = Word2VecAnalyzer(language="french")

        # Регистрируем доступные типы упражнений (только конкретные классы)
        self.exercise_types: Dict[str, ExerciseImpl] = {
            'word_order': WordOrderExercise,
            'fill_blanks': FillBlanksExercise,
            'multiple_choice': SynonymsExercise,
            'matching': MatchingExercise,
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
        self.processed_sentences = (
            self.text_processor.get_sentences_with_metadata(all_text)
        )

        for sentence in self.processed_sentences:
            self.all_words.extend(sentence['words'])

        tokenized_sentences = [s['words'] for s in self.processed_sentences]

        print(f"✓ Обработано {len(self.processed_sentences)} предложений")

        # Исправлено: было analyzer.tain_on_texts(...)
        self.analyzer.train_on_texts(tokenized_sentences)

    def generate_exercises(self, num_per_type: int = 5) -> List[Any]:
        """Генерирует упражнения всех типов"""
        exercises = []

        if not self.processed_sentences:
            raise ValueError("Сначала загрузите тексты с помощью load_texts()")

        for exercise_name, exercise_class in self.exercise_types.items():
            for i in range(num_per_type):
                sentence_data = random.choice(self.processed_sentences)

                # Безопасное извлечение лемм
                lemmas = []
                tagged_lemmas = sentence_data.get('tagged_lemmas', [])

                for item in tagged_lemmas:
                    if isinstance(item, dict):
                        lemmas.append(list(item.keys())[0])
                    elif isinstance(item, (tuple, list)) and len(item) >= 2:
                        lemmas.append(item[0])
                    elif isinstance(item, str):
                        lemmas.append(item)
                    else:
                        lemmas.append(str(item))

                context = {
                    'sentence': sentence_data['text'],
                    'words': sentence_data['words'],
                    'lemmas': lemmas,
                    'tagged_lemmas': tagged_lemmas,  # ← ДОБАВЛЕНО
                    'other_words': self.all_words,
                    'analyzer': self.analyzer  # ← ДОБАВЛЕНО
                }

                exercise_id = f"{exercise_name}_{i + 1}"
                exercise = exercise_class(exercise_id)

                # Передаём анализатор в упражнение
                if exercise_name in ['fill_blanks', 'multiple_choice']:
                    if hasattr(exercise, 'set_analyzer'):
                        exercise.set_analyzer(self.analyzer)
                    else:
                        exercise.analyzer = self.analyzer

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
