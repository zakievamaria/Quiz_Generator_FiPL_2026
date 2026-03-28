import re
import nltk
from typing import List, Dict, Any, Optional
import spacy
nlp = spacy.load('fr_core_news_sm')

# Download punkt if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('omw-1.4')
    nltk.download('punkt_tab')


class TextProcessor:
    """Process and normalize text for French"""

    def __init__(self, language: str = 'french'):
        self.language = language
        if language == 'french':
            try:
                self.nlp = spacy.load('fr_core_news_sm')
            except OSError:
                # Download model if missing
                spacy.cli.download('fr_core_news_sm')
                self.nlp = spacy.load('fr_core_news_sm')
        else:
            self.nlp = None

    def tokenize_sentences(self, text: str) -> List[str]:
        sentences = nltk.sent_tokenize(text, language=self.language)
        return [s.strip() for s in sentences if s.strip()]

    def tokenize_words(self, text: str) -> List[str]:
        # Using NLTK's word tokenizer (handles contractions like "l'avion")
        tokens = nltk.word_tokenize(text, language=self.language)
        # Keep only alphabetic tokens (you might also want to keep apostrophe‑words)
        return [t for t in tokens if t.isalpha()]

    def normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        # Keep French‑specific characters; adjust as needed
        text = re.sub(r'[^\w\s.,!?;:()«»–—’]', '', text)
        return text.strip()

    def lemmatize_word(self, word: str) -> str:
        """True lemmatization for French (using spaCy)"""
        if self.nlp:
            # Process the word with spaCy (a full document is more efficient,
            # but for a single word this is fine)
            doc = self.nlp(word)
            return doc[0].lemma_
        return word


    def get_pos_tag(self, word: str) -> str:
        """Return coarse-grained POS tag for a single word (e.g., NOUN, VERB)."""
        if self.nlp:
            doc = self.nlp(word)
            return doc[0].pos_
        return ''

    def get_sentences_with_metadata(self, text: str) -> List[Dict[str, Any]]:
        sentences = self.tokenize_sentences(text)
        result = []

        for i, sentence in enumerate(sentences):
            words = self.tokenize_words(sentence)
            # Build list of dicts: each dict maps lemma -> POS tag
            tagged_lemmas = []
            for w in words:
                lemma = self.lemmatize_word(w)
                pos = self.get_pos_tag(w)
                tagged_lemmas.append({lemma: pos})

            result.append({
                'id': i,
                'text': sentence,
                'words': words,
                'tagged_lemmas': tagged_lemmas,   # new field, replaces plain lemmas list
                'word_count': len(words)
            })

        return result