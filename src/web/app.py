from __future__ import annotations

import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from flask import Flask, Response, jsonify, render_template, request, session

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.text_processor import TextProcessor
from src.core.word_vectorizer import Word2VecAnalyzer
from src.exercises.fill_blanks import FillBlanksExercise
from src.exercises.synonyms import SynonymsExercise
from src.exercises.word_order import WordOrderExercise

app = Flask(__name__)
app.secret_key = 'quiz-generator-web-secret'
text_processor = TextProcessor(language='french')
strong_pattern = re.compile(r'\*\*(.+?)\*\*')


def load_default_text() -> str:
    path = PROJECT_ROOT / 'example1.txt'
    if path.exists():
        return path.read_text(encoding='utf-8').strip()
    return (
        'L’algorithme a atteint une convergence rapide sur l’ensemble d’entraînement. '
        'Les étudiants aiment apprendre le français avec des cartes interactives. '
        'Le chat dort tranquillement sur le balcon. '
        'La maison reste calme pendant la nuit.'
    )


DEFAULT_PREVIEW_TEXT = load_default_text()


# -------------------- Подготовка текста --------------------

def get_text(raw_text: Any) -> str:
    text = (raw_text or '').strip()
    if text:
        return text
    return session.get('current_text', '').strip() or DEFAULT_PREVIEW_TEXT


def get_sentences(text: str) -> List[Dict[str, Any]]:
    return text_processor.get_sentences_with_metadata(text)


def get_all_words(sentences: List[Dict[str, Any]]) -> List[str]:
    words: List[str] = []
    for sentence in sentences:
        words.extend(sentence['words'])
    return words


def get_context(sentence: Dict[str, Any], all_words: List[str]) -> Dict[str, Any]:
    return {
        'id': sentence['id'],
        'text': sentence['text'],
        'sentence': sentence['text'],
        'words': sentence['words'],
        'tagged_lemmas': sentence['tagged_lemmas'],
        'lemmas': [list(item.keys())[0] for item in sentence['tagged_lemmas']],
        'word_count': sentence['word_count'],
        'other_words': all_words,
        'all_words': all_words,
    }


def pick_sentence(
    sentences: List[Dict[str, Any]],
    min_words: int = 4,
    max_words: int = 18,
) -> Dict[str, Any]:
    suitable = [s for s in sentences if min_words <= len(s['words']) <= max_words]
    return random.choice(suitable or sentences)


def build_analyzer(sentences: List[Dict[str, Any]]) -> Word2VecAnalyzer:
    analyzer = Word2VecAnalyzer()
    analyzer.train_on_texts(
        [sentence['words'] for sentence in sentences],
        vector_size=50,
    )
    return analyzer


def get_random_words(
    words: List[str],
    excluded_words: List[str],
    count: int = 2,
) -> List[str]:
    excluded = {word.lower() for word in excluded_words}
    unique_words: List[str] = []
    seen: set[str] = set()

    for word in words:
        lowered = word.lower()
        if len(lowered) < 3 or lowered in excluded or lowered in seen:
            continue
        seen.add(lowered)
        unique_words.append(word)

    random.shuffle(unique_words)
    return unique_words[:count]


def underline_word(text: str) -> str:
    return strong_pattern.sub(r'<u>\1</u>', text)


# -------------------- Генерация карточек --------------------

def generate_true_false_card(text: str) -> Dict[str, Any]:
    from src.exercises.true_false import TrueFalseExercise

    sentences = get_sentences(text)
    all_words = get_all_words(sentences)
    exercise = TrueFalseExercise('true_false_web')
    exercise.generate(get_context(pick_sentence(sentences, 4, 20), all_words))
    statement = random.choice(exercise.statements)

    return {
        'id': exercise.id,
        'type': 'truefalse',
        'description': 'Определите верность утверждения, основываясь на тексте в превью.',
        'question': statement['text'],
        'answer': 'true' if statement['is_true'] else 'false',
    }


def generate_matching_card(text: str) -> Dict[str, Any]:
    return {
        'id': 'matching_web',
        'type': 'matching',
        'description': 'Matching cards will be added later.',
        'question': 'Matching cards are not connected yet.',
        'pairs': [],
    }


def generate_word_order_card(text: str) -> Dict[str, Any]:
    sentences = get_sentences(text)
    all_words = get_all_words(sentences)
    sentence = pick_sentence(sentences, 4, 9)
    context = get_context(sentence, all_words)

    exercise = WordOrderExercise('word_order_web')
    exercise.generate(context)

    shuffled_words = exercise.question.split()

    return {
        'id': exercise.id,
        'type': 'wordorder',
        'description': 'Восстанови предложение из текста в превью.',
        'question': ' / '.join(shuffled_words),
        'words': shuffled_words,
        'answer': context['words'],
    }


def generate_fill_blanks_card(text: str) -> Dict[str, Any]:
    sentences = get_sentences(text)
    all_words = get_all_words(sentences)
    analyzer = build_analyzer(sentences)
    pool = [s for s in sentences if 4 <= len(s['words']) <= 14]
    random.shuffle(pool)

    blanks: List[Dict[str, Any]] = []
    lines: List[str] = []

    for sentence in pool:
        if len(blanks) == 2:
            break

        context = get_context(sentence, all_words)

        exercise = FillBlanksExercise(f'fill_blanks_{len(blanks)}')
        exercise.analyzer = analyzer
        exercise.generate(context)

        placeholder = f'[[BLANK_{len(blanks)}]]'
        line = exercise.question.replace('___', placeholder, 1)
        lines.append(f'{len(blanks) + 1}. {line}')
        blanks.append({
            'index': len(blanks),
            'answer': exercise.answer,
            'options': exercise.word_bank,
        })

    return {
        'id': 'fill_blanks_web',
        'type': 'fillblanks',
        'description': 'Выбери пропущенные в тексте слова из выпадающего списка.',
        'question': '<br>'.join(lines),
        'blanks': blanks,
    }


def generate_multiple_choice_card(text: str) -> Dict[str, Any]:
    sentences = get_sentences(text)
    all_words = get_all_words(sentences)
    sentence = pick_sentence(sentences, 4, 16)

    exercise = SynonymsExercise('multiple_choice_web')
    exercise.analyzer = build_analyzer(sentences)
    exercise.generate(get_context(sentence, all_words))

    return {
        'id': exercise.id,
        'type': 'multiplechoice',
        'description': 'Choose the synonym of the underlined word.',
        'question': underline_word(exercise.question),
        'options': exercise.word_bank,
        'answer': exercise.answer,
    }


def generate_card_by_type(exercise_type: str, text: str) -> Dict[str, Any]:
    if exercise_type == 'truefalse':
        return generate_true_false_card(text)
    if exercise_type == 'matching':
        return generate_matching_card(text)
    if exercise_type == 'wordorder':
        return generate_word_order_card(text)
    if exercise_type == 'fillblanks':
        return generate_fill_blanks_card(text)
    if exercise_type == 'multiplechoice':
        return generate_multiple_choice_card(text)
    raise ValueError(f'Unsupported exercise type: {exercise_type}')


# -------------------- Проверка ответов --------------------

def validate_true_false(
    exercise: Dict[str, Any],
    user_answer: Any,
) -> Dict[str, Any]:
    correct_answer = exercise.get('answer')
    is_correct = str(user_answer).lower() == str(correct_answer).lower()

    return {
        'correct': is_correct,
        'correct_answer': correct_answer,
    }


def validate_matching(
    exercise: Dict[str, Any],
    user_answer: Any,
) -> Dict[str, Any]:
    user_answer = user_answer or {}
    results: List[Dict[str, Any]] = []
    is_correct = True

    for pair in exercise.get('pairs', []):
        word = pair['word']
        expected_answer = pair['answer']
        current_user_answer = user_answer.get(word, '')
        pair_is_correct = current_user_answer == expected_answer

        if not pair_is_correct:
            is_correct = False

        results.append({
            'word': word,
            'correct': pair_is_correct,
            'correct_answer': expected_answer,
            'user_answer': current_user_answer,
        })

    return {
        'correct': is_correct,
        'results': results,
    }


def validate_word_order(
    exercise: Dict[str, Any],
    user_answer: Any,
) -> Dict[str, Any]:
    expected_answer = exercise.get('answer', [])
    user_answer = user_answer or []

    results: List[Dict[str, Any]] = []
    is_correct = True

    for index, expected_word in enumerate(expected_answer):
        current_user_word = ''
        if index < len(user_answer):
            current_user_word = user_answer[index]

        word_is_correct = current_user_word == expected_word
        if not word_is_correct:
            is_correct = False

        results.append({
            'index': index,
            'correct': word_is_correct,
            'correct_answer': expected_word,
            'user_answer': current_user_word,
        })

    return {
        'correct': is_correct,
        'results': results,
        'correct_answer': expected_answer,
    }


def validate_fill_blanks(
    exercise: Dict[str, Any],
    user_answer: Any,
) -> Dict[str, Any]:
    user_answer = user_answer or {}
    results: List[Dict[str, Any]] = []
    is_correct = True

    for blank in exercise.get('blanks', []):
        index = blank['index']
        expected_answer = blank['answer']
        current_user_answer = user_answer.get(str(index), '')
        blank_is_correct = current_user_answer == expected_answer

        if not blank_is_correct:
            is_correct = False

        results.append({
            'index': index,
            'correct': blank_is_correct,
            'correct_answer': expected_answer,
            'user_answer': current_user_answer,
        })

    return {
        'correct': is_correct,
        'results': results,
    }


def validate_multiple_choice(
    exercise: Dict[str, Any],
    user_answer: Any,
) -> Dict[str, Any]:
    correct_answer = exercise.get('answer')
    is_correct = user_answer == correct_answer

    return {
        'correct': is_correct,
        'correct_answer': correct_answer,
    }


def validate_current_exercise(
    exercise: Dict[str, Any],
    user_answer: Any,
) -> Dict[str, Any]:
    exercise_type = exercise.get('type')

    if exercise_type == 'truefalse':
        return validate_true_false(exercise, user_answer)

    if exercise_type == 'matching':
        return validate_matching(exercise, user_answer)

    if exercise_type == 'wordorder':
        return validate_word_order(exercise, user_answer)

    if exercise_type == 'fillblanks':
        return validate_fill_blanks(exercise, user_answer)

    if exercise_type == 'multiplechoice':
        return validate_multiple_choice(exercise, user_answer)

    raise ValueError(f'Unsupported exercise type: {exercise_type}')


# -------------------- Маршруты --------------------

@app.route('/')
def index() -> str:
    return render_template('index.html', default_preview_text=DEFAULT_PREVIEW_TEXT)


@app.route('/about')
def about() -> str:
    return render_template('about.html')


@app.route('/api/generate', methods=['POST'])
def generate_exercise() -> Union[Response, Tuple[Response, int]]:
    data = request.get_json(silent=True) or {}
    exercise_type = data.get('exercise_type', 'truefalse')
    text = get_text(data.get('text'))

    try:
        exercise = generate_card_by_type(exercise_type, text)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        return jsonify({'error': f'Exercise generation failed: {error}'}), 500

    session['current_text'] = text
    session['current_exercise'] = exercise

    response_data = dict(exercise)
    response_data.pop('answer', None)

    return jsonify({'success': True, 'exercise': response_data})


@app.route('/api/validate', methods=['POST'])
def validate_answer() -> Union[Response, Tuple[Response, int]]:
    data = request.get_json(silent=True) or {}
    user_answer = data.get('user_answer')
    exercise = session.get('current_exercise')

    if not exercise:
        return jsonify({'error': 'No exercise generated yet'}), 400

    try:
        validation_result = validate_current_exercise(exercise, user_answer)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        return jsonify({'error': f'Validation failed: {error}'}), 500

    return jsonify({'success': True, 'validation': validation_result})


if __name__ == '__main__':
    app.run(debug=True)
