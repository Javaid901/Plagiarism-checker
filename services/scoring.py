class ScoringEngine:
    def __init__(self):
        self.weights = {
            "lexical": 0.15,
            "semantic": 0.25,
            "paraphrase": 0.20,
            "sentence_match": 0.20,
            "paragraph_match": 0.20
        }

    def compute_scores(self, lexical, semantic, paraphrase, sentence_matches, paragraph_matches):
        lexical_score = lexical if lexical is not None else 0
        semantic_score = semantic if semantic is not None else 0

        paraphrase_score = paraphrase["paraphrase_confidence"] if isinstance(paraphrase, dict) and paraphrase.get("is_paraphrase") else 0
        if isinstance(paraphrase, dict):
            paraphrase_score = paraphrase.get("paraphrase_confidence", 0)
            if paraphrase.get("is_paraphrase"):
                paraphrase_score = max(paraphrase_score, paraphrase.get("semantic_similarity", 0) * 0.8)

        sentence_match_score = self._sentence_match_score(sentence_matches) if sentence_matches else 0
        paragraph_match_score = self._paragraph_match_score(paragraph_matches) if paragraph_matches else 0

        weighted = (
            lexical_score * self.weights["lexical"] +
            semantic_score * self.weights["semantic"] +
            paraphrase_score * self.weights["paraphrase"] +
            sentence_match_score * self.weights["sentence_match"] +
            paragraph_match_score * self.weights["paragraph_match"]
        )
        weighted = min(100, max(0, weighted))

        unique_content = 100 - weighted
        confidence = self._confidence(weighted, semantic_score, sentence_match_score)

        return {
            "lexical_similarity": float(round(lexical_score, 1)),
            "semantic_similarity": float(round(semantic_score, 1)),
            "paraphrase_score": float(round(paraphrase_score, 1)),
            "sentence_match_score": float(round(sentence_match_score, 1)),
            "paragraph_match_score": float(round(paragraph_match_score, 1)),
            "overall_plagiarism_score": float(round(weighted, 1)),
            "unique_content": float(round(unique_content, 1)),
            "confidence": float(round(confidence, 1))
        }

    def _sentence_match_score(self, matches):
        if not matches:
            return 0
        scores = []
        for m in matches:
            if m["match_type"] in ("Exact Copy", "Near Copy"):
                scores.append(m.get("semantic_similarity", m.get("lexical_similarity", 80)))
            elif m["match_type"] == "Semantic Match":
                scores.append(m.get("semantic_similarity", 60))
            elif m["match_type"] == "Paraphrased Match":
                scores.append(m.get("semantic_similarity", 50) * 0.8)
            elif m["match_type"] == "Weak Similarity":
                scores.append(m.get("semantic_similarity", 30) * 0.5)
        return sum(scores) / len(scores) if scores else 0

    def _paragraph_match_score(self, matches):
        if not matches:
            return 0
        scores = [m["overall_score"] for m in matches if m["overall_score"] > 30]
        return sum(scores) / len(scores) if scores else 0

    def _confidence(self, overall, semantic, sentence):
        base = 70
        if semantic > 50:
            base += 10
        if sentence > 50:
            base += 10
        if overall > 80:
            base += 5
        elif overall < 20:
            base += 5
        return min(99, base)
