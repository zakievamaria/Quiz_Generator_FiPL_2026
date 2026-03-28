import random
from typing import Any, Dict, List, Optional

import spacy
from spacy.matcher import Matcher
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from src.exercises.base import BaseExercise

nlp = spacy.load("fr_core_news_sm")
tfs_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
tfs_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")

tfs_matcher = Matcher(nlp.vocab)

tfs_matcher.add("QUANTIFIERS", [
    [{"LOWER": "tout"}],
    [{"LOWER": "tous"}],
    [{"LOWER": "aucun"}],
    [{"LOWER": "aucune"}],
    [{"LOWER": "certains"}],
    [{"LOWER": "certaines"}],
])

tfs_matcher.add("TEMPORAL_MARKERS", [
    [{"LOWER": "toujours"}],
    [{"LOWER": "parfois"}],
    [{"LOWER": "jamais"}],
    [{"LOWER": "souvent"}],
    [{"LOWER": "rarement"}],
    [{"LIKE_NUM": True}],
])

replacements = {
    "QUANTIFIERS": {
        "tous": "certains",
        "aucun": "tous",
        "aucune": "tous",
        "certains": "aucun",
        "certaines": "aucune",
    },
    "TEMPORAL_MARKERS": {
        "toujours": "parfois",
        "parfois": "toujours",
        "jamais": "toujours",
        "rarement": "souvent",
    }
}

def find_markers_in_doc(doc: spacy.tokens.Doc, matcher: Matcher) -> List[Dict[str, Any]]:
    """
    Find pattern‑based fragments (quantifiers, temporal markers etc.) in a spaCy Doc.

    Args:
        doc (spacy.tokens.Doc): Input text wrapped as a spaCy Doc.
        matcher (Matcher): Matcher with defined patterns.

    Returns:
        list[dict]: List of found fragments with label, text, offsets, and sentence bounds.
    """
    results = []
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        label = doc.vocab.strings[match_id]
        results.append({
            "label": label,
            "text": span.text,
            "start": start,
            "end": end,
            "sent_start": span.sent.start,
            "sent_end": span.sent.end,
        })
    return results

def distort_span(sent_span: spacy.tokens.Span, marker: Dict[str, Any]) -> str:
    """
    Replace the marker text inside a sentence‑span.

    Args:
        sent_span (spacy.tokens.Span): Span corresponding to one sentence.
        marker (dict): Marker with "start", "end" in token indices of the whole Doc.

    Returns:
        str: New sentence text with one fragment changed.
    """
    label = marker["label"]
    old_text = marker["text"]
    span_start = marker["start"] - sent_span.start
    span_end = marker["end"] - sent_span.start

    new_word = replacements.get(label, {}).get(old_text.lower(), "toujours")

    left = sent_span[:span_start].text
    right = sent_span[span_end:].text
    new_sent = left + " " + new_word + " " + right
    return new_sent.strip()


def paraphrase(model, tokenizer, sentence: str, num_return_sequences=1) -> List[str]:
    """
    Generate paraphrased versions of a French sentence using a T5‑style model.

    Args:
        model (AutoModelForSeq2SeqLM): Transformer model for paraphrasing.
        tokenizer (AutoTokenizer): Tokenizer compatible with the model.
        sentence (str): French sentence to paraphrase.
        num_return_sequences (int): Number of paraphrases to generate.

    Returns:
        list[str]: List of paraphrased sentences.
    """

    input_text = f"paraphrase en français: {sentence}"
    inputs = tokenizer(
        input_text,
        padding="longest",
        return_tensors="pt",
        truncation=True,
        max_length=256
    )
    outputs = model.generate(
        **inputs,
        num_beams=5,
        num_return_sequences=num_return_sequences,
        max_length=256,
        temperature=0.8,
    )
    paraphrases = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    return paraphrases


class TrueFalseExercise(BaseExercise):
    """
    Generator of True-False Exercises.
    """

    def __init__(self, exercise_id: str):
        super().__init__(
            exercise_id,
            "Определите, верны ли следующие утверждения (Vrai / Faux)"
        )
        self.statements: List[Dict[str, Any]] = []
        self.question: Optional[str] = None
        self.answer: List[bool] = []
        self.options: List[str] = ["Vrai", "Faux"]

    def generate(self, context: Dict[str, Any]) -> None:
        """
        Generate True/False statements from context.

        Args:
            context (dict): Must contain "sentence", optionally "words", "lemmas", "other_words".

        Raises:
            ValueError: If "sentence" is missing or empty.

        Returns:
            None: Mutates self.question, self.statements, self.answer.
        """
        sentence = context.get("sentence", "")

        if not sentence or not sentence.strip():
            raise ValueError("Отсутствует 'sentence' в context для TrueFalseExercise")

        sentences = [sentence]

        doc = nlp(sentence)
        all_markers = find_markers_in_doc(doc, tfs_matcher)

        self.statements = self._generate_statements(sentences, all_markers)

        self.question = (
            "Прочитайте предложение и определите, верны ли утверждения:\n\n"
            f"\"{sentence}\"\n"
        )

        for i, stmt in enumerate(self.statements, 1):
            self.question += f"\n{i}. {stmt['text']}"

        self.answer = [stmt["is_true"] for stmt in self.statements]

    def _get_true_statements(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """
        Create true statements by paraphrasing input sentences.

        Args:
            sentences (list[str]): List of sentences.

        Returns:
            list[dict]: List of true statements with text, is_true, and original.
        """
        true_statements = []
        for sent in sentences:
            paraphrased = paraphrase(tfs_model, tfs_tokenizer, sent)[0]
            true_statements.append({
                "text": paraphrased,
                "is_true": True,
                "original": sent,
            })
        return true_statements

    def _get_false_statements(
        self,
        sentences: List[str],
        all_markers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create false statements by changing one marked fragment per sentence.

        Args:
            sentences (list[str]): List of sentences.
            all_markers (list[dict]): Markers found in those sentences.

        Returns:
            list[dict]: List of false statements with text, is_true, and original.
        """
        false_statements = []
        if not sentences:
            return false_statements

        doc = nlp(" ".join(sentences))
        for sent in doc.sents:
            markers = [m for m in all_markers if m["sent_start"] == sent.start]
            if markers:
                chosen_marker = random.choice(markers)
                sent_span = doc[sent.start: sent.end]
                modified = distort_span(sent_span, chosen_marker)
                false_statements.append({
                    "text": modified,
                    "is_true": False,
                    "original": sent.text,
                })
        return false_statements

    def _generate_statements(
        self,
        sentences: List[str],
        all_markers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Combine true and false statements, shuffle, and limit total count.

        Args:
            sentences (list[str]): Input sentences.
            all_markers (list[dict]): Markers from those sentences.

        Returns:
            list[dict]: Mixed list of statements (True/False).
        """
        true_statements = self._get_true_statements(sentences)
        false_statements = self._get_false_statements(sentences, all_markers)

        statements = true_statements + false_statements
        random.shuffle(statements)
        return statements[:5]

    def validate_answer(self, user_answer: List[bool]) -> bool:
        """
        Check if the user’s answer matches the internal key.

        Args:
            user_answer (list[bool]): User’s True/False choices.

        Returns:
            bool: True if the answer matches the key.
        """
        if not isinstance(user_answer, list) or len(user_answer) != len(self.statements):
            return False
        return user_answer == self.answer
