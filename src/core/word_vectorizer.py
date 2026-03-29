import os
import numpy as np
from gensim.models import Word2Vec
from typing import List, Dict, Optional, Tuple, Union


class Word2VecAnalyzer:
    """Analyze text using Word2Vec embeddings (обучение с нуля)."""

    def __init__(self, language: str = 'french'):
        """
        Initialize the analyzer.

        :param language: Язык текстов (для сообщений)
        """
        self.model: Optional[Word2Vec] = None
        self.pos_vectors: Dict[str, Dict[str, np.ndarray]] = {}
        self.language = language
        self._model_loaded = False

    def train_on_texts(self, sentences: List[List[str]], vector_size: int = 200) -> 'Word2VecAnalyzer':
        """
        Train a new Word2Vec model on the provided tokenized sentences.

        :param sentences: Список предложений, каждое — список токенов (слов)
        :param vector_size: Размерность векторов
        :return: self для цепочки вызовов
        """
        if not sentences:
            raise ValueError("Список предложений пуст")

        # Фильтрация пустых предложений
        valid_sentences = [sent for sent in sentences if sent and len(sent) > 0]

        if len(valid_sentences) < 10:
            print(f"⚠ Предупреждение: Мало данных для обучения ({len(valid_sentences)} предложений)")

        print("ℹ Обучение модели Word2Vec...")
        print(f"   Предложений: {len(valid_sentences)}")
        print(f"   Размерность векторов: {vector_size}")

        try:
            self.model = Word2Vec(
                sentences=valid_sentences,
                vector_size=vector_size,
                window=5,
                min_count=2,
                workers=4,
                epochs=15,
                sg=1  # Skip-gram
            )
            self._model_loaded = True
            print("✓ Модель обучена")
            print(f"   Размер словаря: {len(self.model.wv)} слов")
        except Exception as e:
            print(f"✗ Ошибка обучения модели: {e}")
            raise

        return self

    def build_pos_vectors(self, tagged_words: List[Union[Dict[str, str], Tuple[str, str]]]) -> None:
        """
        Build a dictionary mapping POS tags to word vectors.

        :param tagged_words: Список тегированных слов. Формат:
                            - [{'слово': 'POS'}, ...] или
                            - [('слово', 'POS'), ...]
        """
        if self.model is None:
            raise ValueError("No Word2Vec model loaded or trained.")

        self.pos_vectors = {}
        processed_count = 0

        for item in tagged_words:
            try:
                # Поддержка разных форматов
                if isinstance(item, dict):
                    word, pos = list(item.items())[0]
                elif isinstance(item, (tuple, list)) and len(item) >= 2:
                    word, pos = item[0], item[1]
                else:
                    continue

                # Проверяем наличие слова в модели
                if word in self.model.wv:
                    if pos not in self.pos_vectors:
                        self.pos_vectors[pos] = {}
                    self.pos_vectors[pos][word] = self.model.wv[word]
                    processed_count += 1

            except Exception as e:
                # Пропускаем проблемные элементы
                continue

        print(f"✓ Построено POS-словарей: {len(self.pos_vectors)}")
        print(f"   Всего обработано слов: {processed_count}")

    def get_similar_words(
            self,
            word: str,
            topn: int = 10,
            pos: Optional[str] = None
    ) -> List[str]:
        """
        Retrieve the most similar words to the given word.

        :param word: Слово для поиска синонимов
        :param topn: Количество возвращаемых слов
        :param pos: Фильтр по части речи (опционально)
        :return: Список похожих слов
        """
        if self.model is None:
            raise ValueError("No Word2Vec model loaded or trained.")

        # Нормализация входного слова
        if not isinstance(word, str):
            word = str(word)

        word = word.strip().lower()

        if not word:
            return []

        if word not in self.model.wv:
            return []

        # 1. Поиск с фильтром по части речи (POS)
        if pos is not None and pos in self.pos_vectors:
            try:
                target_vector = self.model.wv[word]
                candidates = self.pos_vectors[pos]
                similarities = []

                for cand_word, cand_vector in candidates.items():
                    if cand_word != word and len(cand_word) > 2:
                        # Косинусное сходство
                        norm_target = np.linalg.norm(target_vector)
                        norm_cand = np.linalg.norm(cand_vector)

                        if norm_target > 0 and norm_cand > 0:
                            sim = np.dot(target_vector, cand_vector) / (norm_target * norm_cand)
                            similarities.append((cand_word, float(sim)))

                # Сортировка по убыванию сходства
                similarities.sort(key=lambda x: x[1], reverse=True)
                result = [w for w, _ in similarities[:topn]]

                if result:
                    return result

            except Exception as e:
                print(f"⚠ Ошибка POS-фильтра: {e}")
                # Fallback к стандартному поиску

        # 2. Стандартный поиск (Fallback)
        try:
            candidates = self.model.wv.most_similar(word, topn=topn * 2)
            filtered = [
                w for w, _ in candidates
                if len(w) > 2 and w.lower() != word.lower()
            ]
            return filtered[:topn]
        except KeyError:
            return []
        except Exception as e:
            print(f"⚠ Ошибка поиска синонимов: {e}")
            return []

    def get_word_vector(self, word: str) -> Optional[np.ndarray]:
        """
        Get the vector representation of a word.

        :param word: Слово
        :return: Вектор слова или None
        """
        if self.model is None:
            return None

        if not isinstance(word, str):
            word = str(word)

        word = word.strip().lower()

        if word in self.model.wv:
            return self.model.wv[word]
        return None

    def is_word_in_vocab(self, word: str) -> bool:
        """Check if a word exists in the model vocabulary."""
        if self.model is None:
            return False

        if not isinstance(word, str):
            word = str(word)

        return word.strip().lower() in self.model.wv

    def save_model(self, path: str) -> None:
        """Save the current model to disk."""
        if self.model is None:
            raise ValueError("No model to save.")

        # Создаём директорию, если не существует
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        self.model.save(path)
        print(f"✓ Модель сохранена: {path}")

    def get_vocab_size(self) -> int:
        """Get the size of the model vocabulary."""
        if self.model is None:
            return 0
        return len(self.model.wv)

    def is_ready(self) -> bool:
        """Check if the analyzer is ready to use."""
        return self._model_loaded and self.model is not None