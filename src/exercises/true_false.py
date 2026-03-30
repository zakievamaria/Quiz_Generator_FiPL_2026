"""
Генератор упражнений «верно / неверно» на основе одного предложения (spaCy + T5).
"""

import random
from typing import Any, Callable, Dict, List, Optional, Union, cast

import spacy
from spacy.matcher import Matcher
from spacy.tokens import Doc, Span
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, PreTrainedModel, PreTrainedTokenizerBase

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


def find_markers_in_doc(
    doc: Doc,
    matcher: Union[Matcher, Callable[[Doc], Any]],
) -> List[Dict[str, Any]]:
    """
    Find pattern-based fragments (quantifiers, temporal markers) in a spaCy Doc.

    Args:
        doc: spaCy document.
        matcher: spaCy Matcher or callable ``doc -> matches`` (for tests).

    Returns:
        List of dicts with label, text, offsets, and sentence bounds.
    """
    results: List[Dict[str, Any]] = []
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


def distort_span(sent_span: Span, marker: Dict[str, Any]) -> str:
    """
    Replace one phrase in a sentence based on a marker and predefined rules.

    Args:
        sent_span: The sentence as a spaCy Span.
        marker: Marker dictionary with label, text, and offsets.

    Returns:
        Sentence with one fragment changed.
    """
    label = marker["label"]
    old_text = marker["text"]
    span_start = marker["start"] - sent_span.start
    span_end = marker["end"] - sent_span.start

    new_word = replacements.get(label, {}).get(old_text.lower(), "toujours")
    left = sent_span[:span_start].text
    right = sent_span[span_end:].text
    return f"{left.strip()} {new_word} {right.strip()}".strip()


def paraphrase(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    sentence: str,
    num_return_sequences: int = 1,
) -> List[str]:
    """
    Generate paraphrased versions of a French sentence using a T5-style model.

    Returns:
        List of paraphrases (length matches ``num_return_sequences`` when possible).
    """
    input_text = (
        "Reformule la phrase suivante en français sans ajouter ni supprimer "
        f"d'information : {sentence}"
    )
    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        truncation=True,
        max_length=128,
    )

    pad_id = getattr(tokenizer, "eos_token_id", None) or getattr(
        tokenizer, "pad_token_id", None,
    )
    gen_kw: Dict[str, Any] = {
        "max_new_tokens": 64,
        "num_beams": 3,
        "do_sample": False,
        "num_return_sequences": num_return_sequences,
    }
    if pad_id is not None:
        gen_kw["pad_token_id"] = pad_id

    outputs = model.generate(**inputs, **gen_kw)

    texts: List[str] = []
    if hasattr(tokenizer, "batch_decode"):
        decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        texts = [d.strip() for d in decoded]
    else:
        for row in outputs:
            decoded = tokenizer.decode(row, skip_special_tokens=True).strip()
            texts.append(decoded)

    if not texts or all(
        not t or len(t) <= 5 or t == sentence.strip() for t in texts
    ):
        return [sentence] * max(1, num_return_sequences)

    return texts[:num_return_sequences] if texts else [sentence]


class TrueFalseExercise(BaseExercise):
    """
    True/False (Vrai/Faux) exercise: one sentence, true (paraphrase) and false variants.
    """

    def __init__(self, exercise_id: str) -> None:
        super().__init__(exercise_id, "Определите, верны ли утверждения (Vrai / Faux)")
        self.statements: List[Dict[str, Any]] = []
        self.question: Optional[str] = None
        self.answer: List[bool] = []
        self.options = ["Верно", "Неверно"]

    def generate(self, context: Dict[str, Any]) -> None:
        sentence = context.get("sentence", "").strip()
        if not sentence:
            raise ValueError("Missing 'sentence' in context")

        doc = nlp(sentence)
        all_markers = find_markers_in_doc(doc, tfs_matcher)

        sents_list = [sent for sent in doc.sents if sent.text.strip()]
        if not sents_list:
            sentences: List[Span] = [doc[0 : len(doc)]]
        else:
            sentences = cast(List[Span], sents_list)

        self.statements = self._generate_statements(sentences, all_markers)

        self.question = f"Прочитайте:\n\"{sentence}\"\n\nУтверждения:\n"
        for i, stmt in enumerate(self.statements, 1):
            self.question += f"{i}. {stmt['text']}\n"

        self.answer = [stmt["is_true"] for stmt in self.statements]

    def _get_true_statements(self, sentences: List[Any]) -> List[Dict[str, Any]]:
        true_statements: List[Dict[str, Any]] = []
        for sent in sentences[:3]:
            if isinstance(sent, str):
                sent_text = sent.strip()
                original = sent_text
            else:
                sent_text = sent.text.strip()
                original = sent.text.strip()
            paraphrased_list = paraphrase(
                tfs_model,
                tfs_tokenizer,
                sent_text,
                num_return_sequences=1,
            )
            paraphrased = paraphrased_list[0] if paraphrased_list else sent_text
            true_statements.append({
                "text": paraphrased,
                "is_true": True,
                "original": original,
            })
        return true_statements

    def _get_false_statements(
        self,
        sentences: List[Any],
        all_markers: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        false_statements: List[Dict[str, Any]] = []

        for sent in sentences:
            if isinstance(sent, str):
                doc = nlp(sent.strip())
                sents = list(doc.sents)
                span = sents[0] if sents else doc[0 : len(doc)]
            else:
                span = cast(Span, sent)

            sent_text = span.text.strip()
            sent_start, sent_end = span.start, span.end

            sent_markers = [
                m for m in all_markers
                if sent_start <= m["start"] < sent_end
            ]

            if sent_markers:
                marker = random.choice(sent_markers)
                distorted = distort_span(span, marker)

                false_statements.append({
                    "text": distorted,
                    "is_true": False,
                    "original": sent_text,
                })

                if len(false_statements) >= 3:
                    break

        return false_statements

    def _generate_statements(
        self,
        sentences: List[Any],
        all_markers: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        true_statements = self._get_true_statements(sentences)
        false_statements = self._get_false_statements(sentences, all_markers)

        statements = true_statements + false_statements
        random.shuffle(statements)
        return [stmt for stmt in statements if stmt["text"].strip()][:5]

    def validate_answer(self, user_answer: List[bool]) -> bool:
        if not isinstance(user_answer, list):
            return False
        if len(user_answer) != len(self.statements):
            return False
        return user_answer == self.answer
