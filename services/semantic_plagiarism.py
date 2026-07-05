import re
import requests
import numpy as np
from urllib.parse import quote
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    _HAS_TRANSFORMERS = True
except ImportError:
    _HAS_TRANSFORMERS = False


class SemanticPlagiarismDetector:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.cache = {}
        self._model = None
        self._model_name = model_name
        self.tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words='english')

    @property
    def model(self):
        if self._model is None and _HAS_TRANSFORMERS:
            try:
                self._model = SentenceTransformer(self._model_name)
            except Exception:
                pass
        return self._model

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

        # Encode all sentences at once if model available
        if self.model is not None:
            sent_texts = [s for s in sentences if len(s.split()) >= 4]
            if sent_texts:
                try:
                    embeddings = self.model.encode(sent_texts, show_progress_bar=False)
                except Exception:
                    embeddings = None
            else:
                embeddings = None
        else:
            embeddings = None

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
        seen_urls = set()
        for src in results["sources"]:
            key = src.get("url", "") or src.get("title", "")
            if key not in seen_urls:
                seen_urls.add(key)
                unique_sources.append(src)
        results["sources"] = unique_sources

        matched_count = sum(1 for m in results["matches"] if m["matched"])
        total_analyzed = len(results["sentence_analysis"])
        if total_analyzed > 0:
            results["score"] = round((matched_count / total_analyzed) * 100, 1)
            results["originality"] = round(100 - results["score"], 1)

        return results

    def _check_sentence(self, sentence, index, embedding=None):
        sentence_lower = sentence.lower().strip()
        words = re.findall(r'\b[a-zA-Z]{4,}\b', sentence_lower)
        if len(words) < 3:
            return {"index": index, "sentence": sentence, "matched": False, "similarity": 0, "sources": []}

        cache_key = sentence_lower
        if cache_key in self.cache:
            cached = self.cache[cache_key]
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
        self.cache[cache_key] = result
        result["index"] = index
        result["sentence"] = sentence
        return result

    def _search_sentence_online(self, sentence, words, embedding=None):
        try:
            query = quote(sentence[:200])
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            resp = requests.get(search_url, headers=headers, timeout=8)
            if resp.status_code != 200:
                return self._local_similarity_check(sentence, words, embedding)
            return self._parse_search_results(resp.text, sentence, words, embedding)
        except Exception:
            return self._local_similarity_check(sentence, words, embedding)

    def _compute_semantic_similarity(self, s1, s2):
        if self.model is None:
            return None
        try:
            emb1 = self.model.encode([s1], show_progress_bar=False)
            emb2 = self.model.encode([s2], show_progress_bar=False)
            sim = float(cosine_similarity(emb1, emb2)[0][0])
            return round(sim, 4)
        except Exception:
            return None

    def _compute_lexical_similarity(self, s1, s2):
        words1 = set(re.findall(r'\b[a-zA-Z]+\b', s1.lower()))
        words2 = set(re.findall(r'\b[a-zA-Z]+\b', s2.lower()))
        if not words1 or not words2:
            return 0
        intersection = words1 & words2
        if len(words1) < 5 or len(words2) < 5:
            return len(intersection) / max(len(words1), len(words2))
        jaccard = len(intersection) / len(words1 | words2)
        overlap = len(intersection) / min(len(words1), len(words2))
        return (jaccard * 0.5 + overlap * 0.5)

    def _parse_search_results(self, html, sentence, words, embedding=None):
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

            # Lexical similarity (word overlap)
            lexical_sim = self._compute_lexical_similarity(sentence, snippet_clean)

            # Semantic similarity (transformer embedding)
            semantic_sim = self._compute_semantic_similarity(sentence, snippet_clean)

            # Combined score
            if semantic_sim is not None:
                combined = lexical_sim * 0.3 + semantic_sim * 0.7
            else:
                combined = lexical_sim

            if combined > max_sim:
                max_sim = combined
                matched_text = snippet_clean[:200]

            # Classify match type
            sim_for_check = semantic_sim if semantic_sim is not None else lexical_sim
            if sim_for_check and sim_for_check > 0.75:
                is_semantic_match = True
                # High semantic but low lexical = paraphrased plagiarism
                if lexical_sim < 0.4:
                    is_paraphrase_match = True

            sources.append({
                "title": title_clean,
                "snippet": snippet_clean[:200],
                "similarity": round(combined * 100, 1),
                "lexical_similarity": round(lexical_sim * 100, 1),
                "semantic_similarity": round(semantic_sim * 100, 1) if semantic_sim is not None else None
            })

        threshold = 0.45 if self.model is not None else 0.4
        is_matched = max_sim > threshold

        return {
            "matched": is_matched,
            "similarity": round(max_sim * 100, 1),
            "sources": sources,
            "matched_text": matched_text[:200] if matched_text else "",
            "semantic_match": is_semantic_match,
            "paraphrase_match": is_paraphrase_match
        }

    def _local_similarity_check(self, sentence, words, embedding=None):
        return {
            "matched": False,
            "similarity": 0,
            "sources": [],
            "matched_text": "",
            "semantic_match": False,
            "paraphrase_match": False
        }

    def similarity_check(self, text1, text2):
        s1_words = set(re.findall(r'\b[a-zA-Z]+\b', text1.lower()))
        s2_words = set(re.findall(r'\b[a-zA-Z]+\b', text2.lower()))
        intersection = s1_words & s2_words
        union = s1_words | s2_words
        if not union:
            return 0
        jaccard = len(intersection) / len(union)
        return round(jaccard * 100, 1)

    def semantic_similarity_check(self, text1, text2):
        if self.model is None:
            return self.similarity_check(text1, text2)
        try:
            emb1 = self.model.encode([text1], show_progress_bar=False)
            emb2 = self.model.encode([text2], show_progress_bar=False)
            sim = float(cosine_similarity(emb1, emb2)[0][0])
            return round(sim * 100, 1)
        except Exception:
            return self.similarity_check(text1, text2)

    def paraphrase_detection(self, text1, text2):
        lexical = self._compute_lexical_similarity(text1, text2)
        semantic = self._compute_semantic_similarity(text1, text2)
        if semantic is None:
            return {"paraphrased": False, "lexical_similarity": round(lexical * 100, 1), "semantic_similarity": None}
        is_paraphrased = semantic > 0.7 and lexical < 0.4
        return {
            "paraphrased": is_paraphrased,
            "lexical_similarity": round(lexical * 100, 1),
            "semantic_similarity": round(semantic * 100, 1)
        }

    def _engine_name(self):
        if self.model is not None:
            return f"semantic ({self._model_name})"
        if _HAS_TRANSFORMERS:
            return "semantic (model load failed, fallback to lexical)"
        return "lexical (sentence-transformers not installed)"

    def _split_sentences(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]
