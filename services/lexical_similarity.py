import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine

class LexicalSimilarity:
    def __init__(self):
        self._tfidf = None

    @property
    def tfidf(self):
        if self._tfidf is None:
            self._tfidf = TfidfVectorizer(
                max_features=10000,
                ngram_range=(1, 3),
                stop_words='english',
                sublinear_tf=True
            )
        return self._tfidf

    def tfidf_cosine(self, text1, text2):
        texts = [text1, text2]
        try:
            matrix = self.tfidf.fit_transform(texts)
            return float(sklearn_cosine(matrix[0:1], matrix[1:2])[0][0])
        except Exception:
            return 0.0

    def jaccard_similarity(self, text1, text2):
        words1 = set(re.findall(r'\b[a-zA-Z]+\b', text1.lower()))
        words2 = set(re.findall(r'\b[a-zA-Z]+\b', text2.lower()))
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    def word_overlap(self, text1, text2):
        words1 = set(re.findall(r'\b[a-zA-Z]+\b', text1.lower()))
        words2 = set(re.findall(r'\b[a-zA-Z]+\b', text2.lower()))
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        return len(intersection) / min(len(words1), len(words2))

    def ngram_similarity(self, text1, text2, n=3):
        def ngrams(t):
            t = re.sub(r'\s+', ' ', t.lower()).strip()
            return set(t[i:i+n] for i in range(len(t) - n + 1))
        ng1 = ngrams(text1)
        ng2 = ngrams(text2)
        if not ng1 or not ng2:
            return 0.0
        intersection = ng1 & ng2
        union = ng1 | ng2
        return len(intersection) / len(union)

    def all_lexical(self, text1, text2):
        return {
            "tfidf_cosine": round(self.tfidf_cosine(text1, text2) * 100, 1),
            "jaccard": round(self.jaccard_similarity(text1, text2) * 100, 1),
            "word_overlap": round(self.word_overlap(text1, text2) * 100, 1),
            "ngram_3": round(self.ngram_similarity(text1, text2, 3) * 100, 1),
            "ngram_5": round(self.ngram_similarity(text1, text2, 5) * 100, 1),
        }

    def combined_lexical_score(self, text1, text2):
        scores = self.all_lexical(text1, text2)
        return round(
            scores["tfidf_cosine"] * 0.35 +
            scores["jaccard"] * 0.20 +
            scores["word_overlap"] * 0.15 +
            scores["ngram_3"] * 0.20 +
            scores["ngram_5"] * 0.10,
            1
        )
