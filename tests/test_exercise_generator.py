import pytest
from unittest.mock import MagicMock, patch

from src.generators.exercise_generator import ExerciseGenerator


@pytest.fixture
def generator():
    return ExerciseGenerator(language="french")


@pytest.fixture
def mock_sentences():
    return [
        {
            "text": "Bonjour le monde",
            "words": ["Bonjour", "le", "monde"],
            "tagged_lemmas": [
                {"bonjour": "INTJ"},
                ("le", "DET"),
                "monde"
            ]
        }
    ]


def test_initialization(generator):
    assert generator.language == "french"
    assert generator.texts == []
    assert generator.processed_sentences == []
    assert generator.all_words == []
    assert "word_order" in generator.exercise_types


@patch("src.generators.exercise_generator.DocumentLoader")
def test_load_texts_success(mock_loader_cls, generator):
    mock_loader = MagicMock()
    mock_loader.load.return_value = [
        {"content": "Hello world", "file_path": "file1.txt"}
    ]
    mock_loader_cls.return_value = mock_loader

    with patch.object(generator, "_process_texts") as mock_process:
        generator.load_texts(["file1.txt"])

    assert generator.texts == ["Hello world"]
    mock_process.assert_called_once()


@patch("src.generators.exercise_generator.DocumentLoader")
def test_load_texts_failure(mock_loader_cls, generator):
    mock_loader = MagicMock()
    mock_loader.load.side_effect = Exception("fail")
    mock_loader_cls.return_value = mock_loader

    generator.load_texts(["file1.txt"])

    assert generator.texts == []


def test_process_texts(generator, mock_sentences):
    generator.texts = ["Some text"]

    generator.text_processor = MagicMock()
    generator.text_processor.get_sentences_with_metadata.return_value = mock_sentences

    generator.analyzer = MagicMock()

    generator._process_texts()

    assert generator.processed_sentences == mock_sentences
    assert generator.all_words == ["Bonjour", "le", "monde"]

    generator.analyzer.train_on_texts.assert_called_once()


def test_generate_exercises_success(generator, mock_sentences):
    generator.processed_sentences = mock_sentences
    generator.all_words = ["Bonjour", "le", "monde"]

    mock_exercise = MagicMock()
    mock_exercise.generate.return_value = None

    mock_class = MagicMock(return_value=mock_exercise)

    generator.exercise_types = {
        "word_order": mock_class
    }

    exercises = generator.generate_exercises(num_per_type=2)

    assert len(exercises) == 2
    assert mock_exercise.generate.call_count == 2


def test_generate_exercises_no_sentences(generator):
    with pytest.raises(ValueError):
        generator.generate_exercises()


def test_generate_exercises_handles_exceptions(generator, mock_sentences):
    generator.processed_sentences = mock_sentences
    generator.all_words = ["Bonjour"]

    mock_exercise = MagicMock()
    mock_exercise.generate.side_effect = Exception("fail")

    mock_class = MagicMock(return_value=mock_exercise)

    generator.exercise_types = {
        "word_order": mock_class
    }

    exercises = generator.generate_exercises(num_per_type=1)

    assert exercises == []


def test_lemma_extraction_various_formats(generator):
    generator.processed_sentences = [
        {
            "text": "test",
            "words": ["a"],
            "tagged_lemmas": [
                {"run": "VERB"},
                ("eat", "VERB"),
                ["go", "VERB"],
                "play",
                123
            ]
        }
    ]
    generator.all_words = ["a"]

    mock_exercise = MagicMock()
    mock_class = MagicMock(return_value=mock_exercise)

    generator.exercise_types = {
        "word_order": mock_class
    }

    generator.generate_exercises(num_per_type=1)

    args, kwargs = mock_exercise.generate.call_args
    context = args[0]

    assert context["lemmas"] == ["run", "eat", "go", "play", "123"]


def test_save_exercises(generator):
    generator.formatter = MagicMock()

    generator.save_exercises(["ex1"], "file.docx")

    generator.formatter.save_exercises.assert_called_once_with(["ex1"], "file.docx")


def test_save_answers(generator):
    generator.formatter = MagicMock()

    generator.save_answers(["ex1"], "answers.docx")

    generator.formatter.save_answers.assert_called_once_with(["ex1"], "answers.docx")
