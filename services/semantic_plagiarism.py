import re
import requests
from urllib.parse import quote

from .semantic_similarity import SemanticSimilarity
from .lexical_similarity import LexicalSimilarity
from .embedding_cache import EmbeddingCache


_has_internet = None

def _check_connectivity():
    global _has_internet
    if _has_internet is not None:
        return _has_internet
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 53))
        s.close()
        _has_internet = True
    except Exception:
        _has_internet = False
    return _has_internet

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

        emb_index = 0

        for i, sentence in enumerate(sentences):
            if len(sentence.split()) < 4:
                continue

            emb = None
            if embeddings is not None and emb_index < len(embeddings):
                emb = embeddings[emb_index]
                emb_index += 1

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

        matched = len(results["matches"])
        total = len(results["sentence_analysis"])

        if total:
            results["score"] = round((matched / total) * 100, 1)
            results["originality"] = round(100 - results["score"], 1)

        return results

    def _check_sentence(self, sentence, index, embedding=None):

        sentence_lower = sentence.lower().strip()

        words = re.findall(r"\b[a-zA-Z]{4,}\b", sentence_lower)

        if len(words) < 3:
            return {
                "index": index,
                "sentence": sentence,
                "matched": False,
                "similarity": 0,
                "sources": []
            }

        cached = self.cache.get(sentence_lower)

        if cached is not None:
            return {
                "index": index,
                "sentence": sentence,
                "matched": cached["matched"],
                "similarity": cached["similarity"],
                "sources": cached.get("sources", []),
                "matched_text": cached.get("matched_text", ""),
                "semantic_match": cached.get("semantic_match", False),
                "paraphrase_match": cached.get("paraphrase_match", False),
            }

        result = self._search_sentence_online(sentence, words, embedding)

        self.cache.put(sentence_lower, result)

        result["index"] = index
        result["sentence"] = sentence

        return result

    def _search_sentence_online(self, sentence, words, embedding=None):
        if not _check_connectivity():
            return self._local_result()

        try:
            query = quote(sentence[:200])
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(
                f"https://html.duckduckgo.com/html/?q={query}",
                headers=headers,
                timeout=5
            )

            if response.status_code != 200:
                return self._local_result()

            return self._parse_results(
                response.text,
                sentence,
                words,
                embedding
            )

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

        semantic_match = False
        paraphrase_match = False

        snippets = re.findall(
            r'<a[^>]*class="result__a"[^>]*>(.*?)</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            html,
            re.DOTALL
        )

        for title, snippet in snippets[:5]:

            title = re.sub(r"<[^>]+>", "", title).strip()

            snippet = re.sub(r"<[^>]+>", "", snippet).strip()

            snippet = re.sub(r"\.\.\.", "", snippet).strip()

            lexical = self._compute_lexical_similarity(sentence, snippet)

            semantic = self._compute_semantic_similarity(sentence, snippet)

            if semantic is None:
                combined = lexical
                semantic = 0
            else:
                combined = lexical * 0.3 + semantic * 0.7

            if combined > max_sim:
                max_sim = combined
                matched_text = snippet[:200]

            if semantic > 0.75:
                semantic_match = True

                if lexical < 0.4:
                    paraphrase_match = True

            sources.append({
                "title": title,
                "snippet": snippet[:200],
                "similarity": round(combined * 100, 1),
                "lexical_similarity": round(lexical * 100, 1),
                "semantic_similarity": round(semantic * 100, 1)
            })

        # IMPORTANT:
        # Do NOT access self.semantic.model here.
        # That forces the transformer to load.

        threshold = 0.4

        return {
            "matched": max_sim > threshold,
            "similarity": round(max_sim * 100, 1),
            "sources": sources,
            "matched_text": matched_text,
            "semantic_match": semantic_match,
            "paraphrase_match": paraphrase_match
        }

    def _local_result(self):
        return {
            "matched": False,
            "similarity": 0,
            "sources": [],
            "matched_text": "",
            "semantic_match": False,
            "paraphrase_match": False
        }

    def _engine_name(self):
        # IMPORTANT:
        # Check _model instead of model property.
        # Accessing self.semantic.model loads the transformer.

        if self.semantic._model is not None:
            return "semantic (shared model)"

        return "lexical (no transformer loaded)"

    def _split_sentences(self, text):

        text = re.sub(r"\s+", " ", text).strip()

        return [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+", text)
            if len(s.strip()) > 5
        ]