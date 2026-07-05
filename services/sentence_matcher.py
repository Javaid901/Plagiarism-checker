import re
import numpy as np
from .lexical_similarity import LexicalSimilarity
from .semantic_similarity import SemanticSimilarity
from .paraphrase_detector import ParaphraseDetector

class SentenceMatcher:
    def __init__(self):
        self.semantic = SemanticSimilarity()
        self.lexical = LexicalSimilarity()
        self.paraphrase = ParaphraseDetector()

    def split_sentences(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        sents = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sents if len(s.strip()) > 5]

    def match_type(self, sem_sim, lex_sim):
        if sem_sim is None:
            if lex_sim > 0.85: return "Direct Match"
            elif lex_sim > 0.60: return "Near Copy"
            elif lex_sim > 0.35: return "Weak Match"
            else: return "No Match"
        if sem_sim >= 0.90 and lex_sim >= 0.80: return "Exact Copy"
        if sem_sim >= 0.75 and lex_sim >= 0.50: return "Near Copy"
        if sem_sim >= 0.65:
            if lex_sim < 0.40: return "Paraphrased Match"
            return "Semantic Match"
        if sem_sim >= 0.40: return "Weak Similarity"
        return "No Match"

    def match_sentences(self, sents_a, sents_b):
        results = []
        matrix = self.semantic.batch_similarity_matrix(sents_a, sents_b)

        for i, sa in enumerate(sents_a):
            best = {"index": -1, "semantic": 0, "lexical": 0}
            for j, sb in enumerate(sents_b):
                sem = matrix[i][j] if matrix is not None else None
                lex = self.lexical.combined_lexical_score(sa, sb) / 100.0
                if sem is not None and sem > best["semantic"]:
                    best = {"index": j, "semantic": sem, "lexical": lex}
                elif sem is None and lex > best["lexical"]:
                    best = {"index": j, "semantic": None, "lexical": lex}

            if best["index"] >= 0:
                mt = self.match_type(best["semantic"], best["lexical"])
                results.append({
                    "source_index": i,
                    "source_sentence": sa[:300],
                    "matched_index": best["index"],
                    "matched_sentence": sents_b[best["index"]][:300],
                    "semantic_similarity": round(float(best["semantic"]) * 100, 1) if best["semantic"] is not None else None,
                    "lexical_similarity": round(float(best["lexical"]) * 100, 1),
                    "match_type": mt,
                    "is_paraphrase": mt == "Paraphrased Match",
                    "reason": self._reason(mt, best["semantic"], best["lexical"])
                })
        return results

    def _reason(self, mt, sem, lex):
        reasons = {
            "Exact Copy": "Virtually identical word-for-word match.",
            "Near Copy": "Mostly the same with minor wording differences.",
            "Semantic Match": "Wording differs but the meaning is strongly aligned.",
            "Paraphrased Match": "The wording differs significantly but the meaning remains almost identical — likely paraphrased.",
            "Weak Similarity": "Some shared concepts but significant differences in wording and meaning.",
            "No Match": "No significant similarity detected."
        }
        return reasons.get(mt, "Similarity detected.")


class ParagraphMatcher:
    def __init__(self):
        self.semantic = SemanticSimilarity()
        self.lexical = LexicalSimilarity()
        self.sentence_matcher = SentenceMatcher()

    def split_paragraphs(self, text):
        paras = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paras if len(p.strip()) > 10]

    def sliding_windows(self, text, sizes=[3, 5]):
        sents = self.sentence_matcher.split_sentences(text)
        windows = []
        for size in sizes:
            step = max(1, size // 2)
            for i in range(0, len(sents) - size + 1, step):
                window_text = ' '.join(sents[i:i+size])
                windows.append({
                    "size": size,
                    "start": i,
                    "end": i + size - 1,
                    "text": window_text[:500]
                })
        return windows

    def match_paragraphs(self, paras_a, paras_b):
        results = []
        for i, pa in enumerate(paras_a):
            best = {"index": -1, "score": 0}
            for j, pb in enumerate(paras_b):
                sem = self.semantic.sentence_similarity(pa, pb)
                lex = self.lexical.combined_lexical_score(pa, pb) / 100.0
                score = sem if sem is not None else lex
                if score > best["score"]:
                    best = {"index": j, "score": score, "semantic": sem, "lexical": lex}
            results.append({
                "source_index": i,
                "source_paragraph": pa[:500],
                "matched_index": best["index"],
                "matched_paragraph": paras_b[best["index"]][:500] if best["index"] >= 0 else "",
                "semantic_similarity": round(float(best["semantic"]) * 100, 1) if best.get("semantic") is not None else None,
                "lexical_similarity": round(float(best.get("lexical", 0)) * 100, 1),
                "overall_score": round(float(best["score"]) * 100, 1)
            })
        return results

    def find_similar_blocks(self, text_a, text_b):
        results = []
        windows_a = self.sliding_windows(text_a)
        windows_b = self.sliding_windows(text_b)
        for wa in windows_a[:20]:
            best = {"index": -1, "score": 0}
            for j, wb in enumerate(windows_b[:20]):
                sem = self.semantic.sentence_similarity(wa["text"], wb["text"])
                score = sem if sem is not None else 0
                if score > best["score"]:
                    best = {"index": j, "score": score}
            if best["score"] >= 0.50:
                wb = windows_b[best["index"]]
                results.append({
                    "window_size": wa["size"],
                    "source_start": wa["start"],
                    "source_end": wa["end"],
                    "similarity": round(float(best["score"]) * 100, 1),
                    "match_type": "Semantic Block" if best["score"] >= 0.65 else "Weak Block",
                    "source_text": wa["text"][:300],
                    "matched_text": wb["text"][:300]
                })
        return results
