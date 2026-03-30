"""
The module creates True-False Statements.
"""

import random
from typing import Any, Dict, List, Optional, cast

import spacy
from spacy.matcher import Matcher
from spacy.tokens import Doc, Span
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


def find_markers_in_doc(doc: Doc) -> List[Dict[str, Any]]:
    """
    Find pattern‑based fragments (quantifiers, temporal markers etc.) in a spaCy Doc.

    Args:
        doc (spacy.tokens.Doc): Input text wrapped as a spaCy Doc.

    Returns:
        list[dict]: List of found fragments with label, text, offsets, and sentence bounds.
    """
    results = []
    matches = tfs_matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        label = doc.vocab.strings[match_id]
        results.append({
            "label": label,
            "text": span.text,
            "start": start,
            "end": end,
        })
    return results


def distort_span(sent_span: spacy.tokens.Span, marker: Dict[str, Any]) -> str:
    """
    Replace one phrase in a sentence based on a marker and predefined rules.

    Args:
        sent_span (spacy.tokens.Span): The sentence as a spaCy Span.
        marker (dict): Marker dictionary with label, text, and offsets.

    Returns:
        str: Sentence with one fragment changed.
    """
    label = marker["label"]
    old_text = marker["text"]
    span_start = marker["start"] - sent_span.start
    span_end = marker["end"] - sent_span.start

    new_word = replacements.get(label, {}).get(old_text.lower(), "toujours")
    left = sent_span[:span_start].text
    right = sent_span[span_end:].text
    return f"{left.strip()} {new_word} {right.strip()}".strip()


def paraphrase(model: Any, tokenizer: Any, sentence: str) -> str:
    input_text = f"Reformule la phrase suivante en français sans ajouter ni supprimer \
    d'information : {sentence}"

    inputs = cast(Dict[str, Any], tokenizer(
        input_text,
        return_tensors="pt",
        truncation=True,
        max_length=128
    ))

    outputs = model.generate(
        **inputs,
        max_new_tokens=64,
        num_beams=3,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id
    )

    result = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    return result if result and len(result) > 5 and result != sentence.strip() else sentence


class TrueFalseExercise(BaseExercise):
    """
    True‑False (Vrai/Faux) exercise generator operating on one sentence at a time.
    Creates True (paraphrased) and False (slightly changed) statements.
    """
    def __init__(self, exercise_id: str):
        """
        Initialize a TrueFalse exercise.
        """
        super().__init__(exercise_id, "Определите, верны ли утверждения (Vrai / Faux)")
        self.statements: List[Dict[str, Any]] = []
        self.question: Optional[str] = None
        self.answer: List[bool] = []
        self.options = ["Верно", "Неверно"]

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
        sentence = context.get("sentence", "").strip()
        if not sentence:
            raise ValueError("Missing 'sentence' in context")

        doc = nlp(sentence)
        all_markers = find_markers_in_doc(doc)

        sentences = [sent for sent in doc.sents if sent.text.strip()]
        if not sentences:
            sentences = [doc[:]]

        self.statements = self._generate_statements(sentences, all_markers)

        self.question = f"Прочитайте:\n\"{sentence}\"\n\nУтверждения:\n"
        for i, stmt in enumerate(self.statements, 1):
            self.question += f"{i}. {stmt['text']}\n"

        self.answer = [stmt["is_true"] for stmt in self.statements]

    def _get_true_statements(self, sentences: List[Span]) -> List[Dict[str, Any]]:
        """
        Create true statements by paraphrasing input sentences.

        Args:
            sentences (list[str]): List of sentences.

        Returns:
            list[dict]: List of true statements with text, is_true, and original.
        """
        true_statements = []
        for sent in sentences[:3]:
            paraphrased = paraphrase(tfs_model, tfs_tokenizer, sent.text.strip())
            true_statements.append({
                "text": paraphrased,
                "is_true": True,
                "original": sent.text.strip(),
            })
        return true_statements

    def _get_false_statements(self, sentences: List[Span], all_markers: List[Dict[str, Any]])\
            -> List[Dict[str, Any]]:
        """
        Create false statements by changing one marked fragment per sentence.

        Args:
            sentences (list[str]): List of sentences.
            all_markers (list[dict]): Markers found in those sentences.

        Returns:
            list[dict]: List of false statements with text, is_true, and original.
        """
        false_statements = []

        for sent in sentences:
            sent_text = sent.text.strip()
            sent_start, sent_end = sent.start, sent.end

            sent_markers = [
                m for m in all_markers
                if sent_start <= m["start"] < sent_end
            ]

            if sent_markers:
                marker = random.choice(sent_markers)
                distorted = distort_span(sent, marker)

                false_statements.append({
                    "text": distorted,
                    "is_true": False,
                    "original": sent_text,
                })

                if len(false_statements) >= 3:
                    break

        return false_statements

    def _generate_statements(self, sentences: List[Span], all_markers: List[Dict[str, Any]])\
            -> List[Dict[str, Any]]:
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
        return [stmt for stmt in statements if stmt["text"].strip()][:5]

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
