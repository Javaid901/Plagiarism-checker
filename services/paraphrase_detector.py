import numpy as np
from .semantic_similarity import SemanticSimilarity
from .lexical_similarity import LexicalSimilarity

class ParaphraseDetector:
    def __init__(self):
        self.semantic = SemanticSimilarity()
        self.lexical = LexicalSimilarity()

    def detect(self, text1, text2):
        sem_sim = self.semantic.sentence_similarity(text1, text2)
        lex_sim = self.lexical.combined_lexical_score(text1, text2) / 100.0

        if sem_sim is None:
            return {
                "is_paraphrase": False,
                "semantic_similarity": None,
                "lexical_similarity": round(lex_sim * 100, 1),
                "paraphrase_confidence": 0,
                "reason": "Semantic model unavailable"
            }

        sem_pct = round(sem_sim * 100, 1)
        lex_pct = round(lex_sim * 100, 1)

        # Paraphrase = high semantic, low lexical
        if sem_sim >= 0.65 and lex_sim < 0.40:
            confidence = round((sem_sim - lex_sim) * 100, 1)
            return {
                "is_paraphrase": True,
                "semantic_similarity": sem_pct,
                "lexical_similarity": lex_pct,
                "paraphrase_confidence": confidence,
                "reason": "Semantic meaning is preserved but wording differs significantly — likely paraphrased."
            }
        elif sem_sim >= 0.65:
            return {
                "is_paraphrase": False,
                "semantic_similarity": sem_pct,
                "lexical_similarity": lex_pct,
                "paraphrase_confidence": 0,
                "reason": "High semantic and lexical overlap — likely a direct match or near-copy."
            }
        elif sem_sim >= 0.50 and lex_sim < 0.30:
            return {
                "is_paraphrase": True,
                "semantic_similarity": sem_pct,
                "lexical_similarity": lex_pct,
                "paraphrase_confidence": round((sem_sim - lex_sim) * 50, 1),
                "reason": "Moderate semantic similarity with low lexical overlap — possible loose paraphrase."
            }
        else:
            return {
                "is_paraphrase": False,
                "semantic_similarity": sem_pct,
                "lexical_similarity": lex_pct,
                "paraphrase_confidence": 0,
                "reason": "Low semantic and lexical similarity — content appears different."
            }

    def batch_detect(self, sents_a, sents_b):
        results = []
        matrix = self.semantic.batch_similarity_matrix(sents_a, sents_b)
        if matrix is None:
            matrix = [[0]*len(sents_b) for _ in sents_a]
        for i, sa in enumerate(sents_a):
            best_j = int(np.argmax(matrix[i])) if hasattr(matrix[i], '__len__') else 0
            best_score = float(matrix[i][best_j]) if hasattr(matrix[i], '__len__') else 0
            lex = float(self.lexical.combined_lexical_score(sa, sents_b[int(best_j)] if int(best_j) < len(sents_b) else "") / 100.0)
            results.append({
                "source_index": i,
                "source_sentence": sa[:200],
                "target_index": int(best_j),
                "semantic_similarity": round(float(best_score) * 100, 1),
                "lexical_similarity": round(lex * 100, 1),
                "is_paraphrase": best_score >= 0.5 and lex < 0.4
            })
        return results
