import re
import requests
import numpy as np
from urllib.parse import quote

from .semantic_similarity import SemanticSimilarity
from .lexical_similarity import LexicalSimilarity
from .embedding_cache import EmbeddingCache


class SemanticPlagiarismDetector:
    def __init__(self):
        self.semantic = SemanticSimilarity()
        self.lexical = LexicalSimilarity()
        self.cache = EmbeddingCache()

    def check_plagiarism(self, text):
        sentences = self._split_sentences(text)
        if len(sentences) < 2:
            return {
                "score": 0,
                "status": "Insufficient text. Provide at least 2 sentences.",
                "sources": [],
                "matches": [],
                "originality": 100,
                "engine": self._engine_name()
            }

        results = {
            "score": 0,
            "status": "Analysis complete",
            "sources": [],
            "matches": [],
            "originality": 100,
            "sentence_analysis": [],
            "engine": self._engine_name()
        }

        sent_texts = [s for s in sentences if len(s.split()) >= 4]
        embeddings = self.semantic.encode(sent_texts) if sent_texts else None

        for i, sentence in enumerate(sentences):
            if len(sentence.split()) < 4:
                continue
            emb = embeddings[i] if embeddings is not None and i < len(embeddings) else None
            sentence_result = self._check_sentence(sentence, i, emb)
            results["sentence_analysis"].append(sentence_result)
            if sentence_result["matched"]:
                results["matches"].append(sentence_result)
                results["sources"].extend(sentence_result.get("sources", []))

        unique_sources = []
        seen = set()
        for src in results["sources"]:
            key = src.get("url", "") or src.get("title", "")
            if key not in seen:
                seen.add(key)
                unique_sources.append(src)
        results["sources"] = unique_sources

        matched = sum(1 for m in results["matches"] if m["matched"])
        total = len(results["sentence_analysis"])
        if total > 0:
            results["score"] = round((matched / total) * 100, 1)
            results["originality"] = round(100 - results["score"], 1)

        return results

    def _check_sentence(self, sentence, index, embedding=None):
        sentence_lower = sentence.lower().strip()
        words = re.findall(r'\b[a-zA-Z]{4,}\b', sentence_lower)
        if len(words) < 3:
            return {"index": index, "sentence": sentence, "matched": False, "similarity": 0, "sources": []}

        cache_key = sentence_lower
        cached = self.cache.get(cache_key)
        if cached is not None:
            return {
                "index": index,
                "sentence": sentence,
                "matched": cached["matched"],
                "similarity": cached["similarity"],
                "sources": cached.get("sources", []),
                "matched_text": cached.get("matched_text", ""),
                "semantic_match": cached.get("semantic_match", False),
                "paraphrase_match": cached.get("paraphrase_match", False)
            }

        result = self._search_sentence_online(sentence, words, embedding)
        self.cache.put(cache_key, result)
        result["index"] = index
        result["sentence"] = sentence
        return result

    def _search_sentence_online(self, sentence, words, embedding=None):
        try:
            query = quote(sentence[:200])
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(f"https://html.duckduckgo.com/html/?q={query}", headers=headers, timeout=8)
            if resp.status_code != 200:
                return self._local_result()
            return self._parse_results(resp.text, sentence, words, embedding)
        except Exception:
            return self._local_result()

    def _compute_semantic_similarity(self, s1, s2):
        return self.semantic.sentence_similarity(s1, s2)

    def _compute_lexical_similarity(self, s1, s2):
        return self.lexical.combined_lexical_score(s1, s2) / 100.0

    def _parse_results(self, html, sentence, words, embedding=None):
        sources = []
        max_sim = 0
        matched_text = ""
        is_semantic_match = False
        is_paraphrase_match = False

        snippets = re.findall(
            r'<a[^>]*class="result__a"[^>]*>(.*?)</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )

        for title, snippet in snippets[:5]:
            title_clean = re.sub(r'<[^>]+>', '', title).strip()
            snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
            snippet_clean = re.sub(r'\.\.\.', '', snippet_clean).strip()

            lexical_sim = self._compute_lexical_similarity(sentence, snippet_clean)
            semantic_sim = self._compute_semantic_similarity(sentence, snippet_clean)

            combined = lexical_sim * 0.3 + semantic_sim * 0.7 if semantic_sim is not None else lexical_sim

            if combined > max_sim:
                max_sim = combined
                matched_text = snippet_clean[:200]

            sim_check = semantic_sim if semantic_sim is not None else lexical_sim
            if sim_check and sim_check > 0.75:
                is_semantic_match = True
                if lexical_sim < 0.4:
                    is_paraphrase_match = True

            sources.append({
                "title": title_clean,
                "snippet": snippet_clean[:200],
                "similarity": round(combined * 100, 1),
                "lexical_similarity": round(lexical_sim * 100, 1),
                "semantic_similarity": round(semantic_sim * 100, 1) if semantic_sim is not None else None
            })

        threshold = 0.45 if self.semantic.model is not None else 0.4
        is_matched = max_sim > threshold

        return {
            "matched": is_matched,
            "similarity": round(max_sim * 100, 1),
            "sources": sources,
            "matched_text": matched_text[:200] if matched_text else "",
            "semantic_match": is_semantic_match,
            "paraphrase_match": is_paraphrase_match
        }

    def _local_result(self):
        return {
            "matched": False, "similarity": 0, "sources": [],
            "matched_text": "", "semantic_match": False, "paraphrase_match": False
        }

    def _engine_name(self):
        if self.semantic.model is not None:
            return "semantic (shared model)"
        return "lexical (no transformer model)"

    def _split_sentences(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 5]
