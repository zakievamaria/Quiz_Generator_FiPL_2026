"""
Fixed True-False exercise module without attribute/sent_start errors.
"""

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


def find_markers_in_doc(doc: spacy.tokens.Doc) -> List[Dict[str, Any]]:
    """
    Find quantifiers/temporal markers - NO sent_start/sent_end attributes.
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
    Replace marker text in span - uses only start/end token indices.
    """
    label = marker["label"]
    old_text = marker["text"]
    span_start = marker["start"] - sent_span.start
    span_end = marker["end"] - sent_span.start

    new_word = replacements.get(label, {}).get(old_text.lower(), "toujours")
    left = sent_span[:span_start].text
    right = sent_span[span_end:].text
    return f"{left.strip()} {new_word} {right.strip()}".strip()


def paraphrase(model, tokenizer, sentence: str) -> str:
    """
    Generate paraphrase with fallback.
    """
    input_text = f"paraphrase: {sentence}"
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=128)

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
    def __init__(self, exercise_id: str):
        super().__init__(exercise_id, "Определите, верны ли утверждения (Vrai / Faux)")
        self.statements: List[Dict[str, Any]] = []
        self.question: Optional[str] = None
        self.answer: List[bool] = []
        self.options = ["Vrai", "Faux"]

    def generate(self, context: Dict[str, Any]) -> None:
        """
        Generate from single sentence - splits into sentences automatically.
        """
        sentence = context.get("sentence", "").strip()
        if not sentence:
            raise ValueError("Missing 'sentence' in context")

        doc = nlp(sentence)
        all_markers = find_markers_in_doc(doc)

        # Use document sentences as base units
        sentences = [sent for sent in doc.sents if sent.text.strip()]
        if not sentences:
            sentences = [doc]

        self.statements = self._generate_statements(sentences, all_markers)

        # Build question
        self.question = f"Прочитайте:\n\"{sentence}\"\n\nУтверждения:\n"
        for i, stmt in enumerate(self.statements, 1):
            self.question += f"{i}. {stmt['text']}\n"

        self.answer = [stmt["is_true"] for stmt in self.statements]

    def _get_true_statements(self, sentences) -> List[Dict[str, Any]]:
        """Paraphrase sentences for true statements."""
        true_statements = []
        for sent in sentences[:3]:  # Max 3 true
            paraphrased = paraphrase(tfs_model, tfs_tokenizer, sent.text.strip())
            true_statements.append({
                "text": paraphrased,
                "is_true": True,
                "original": sent.text.strip(),
            })
        return true_statements

    def _get_false_statements(self, sentences, all_markers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Distort markers for false statements."""
        false_statements = []

        for sent in sentences:
            sent_text = sent.text.strip()
            sent_doc = nlp(sent_text)

            # Markers in this sentence bounds
            sent_start, sent_end = sent.start, sent.end
            sent_markers = [m for m in all_markers
                          if sent_start <= m["start"] < sent_end]

            if sent_markers:
                marker = random.choice(sent_markers)
                distorted = distort_span(sent_doc, marker)
                false_statements.append({
                    "text": distorted,
                    "is_true": False,
                    "original": sent_text,
                })
                if len(false_statements) >= 3:
                    break

        return false_statements

    def _generate_statements(self, sentences, all_markers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine true/false, shuffle, limit to 5."""
        true_statements = self._get_true_statements(sentences)
        false_statements = self._get_false_statements(sentences, all_markers)

        statements = true_statements + false_statements
        random.shuffle(statements)
        return [stmt for stmt in statements if stmt["text"].strip()][:5]

    def validate_answer(self, user_answer: List[bool]) -> bool:
        """Validate user answer."""
        if not isinstance(user_answer, list) or len(user_answer) != len(self.statements):
            return False
        return user_answer == self.answer