import re
import requests
from collections import Counter
from urllib.parse import quote

class PlagiarismDetector:
    def __init__(self):
        self.cache = {}

    def check_plagiarism(self, text):
        sentences = self._split_sentences(text)
        if len(sentences) < 2:
            return {
                "score": 0,
                "status": "Insufficient text. Provide at least 2 sentences.",
                "sources": [],
                "matches": [],
                "originality": 100
            }

        results = {
            "score": 0,
            "status": "Analysis complete",
            "sources": [],
            "matches": [],
            "originality": 100,
            "sentence_analysis": []
        }

        for i, sentence in enumerate(sentences):
            if len(sentence.split()) < 4:
                continue
            sentence_result = self._check_sentence(sentence, i)
            results["sentence_analysis"].append(sentence_result)
            if sentence_result["matched"]:
                results["matches"].append(sentence_result)
                results["sources"].extend(sentence_result.get("sources", []))

        unique_sources = []
        seen_urls = set()
        for src in results["sources"]:
            if src.get("url", "") not in seen_urls:
                seen_urls.add(src.get("url", ""))
                unique_sources.append(src)
        results["sources"] = unique_sources

        matched_count = sum(1 for m in results["matches"] if m["matched"])
        total_analyzed = len(results["sentence_analysis"])
        if total_analyzed > 0:
            results["score"] = round((matched_count / total_analyzed) * 100, 1)
            results["originality"] = round(100 - results["score"], 1)

        return results

    def _check_sentence(self, sentence, index):
        sentence_lower = sentence.lower().strip()
        words = re.findall(r'\b[a-zA-Z]{4,}\b', sentence_lower)
        if len(words) < 3:
            return {"index": index, "sentence": sentence, "matched": False, "similarity": 0, "sources": []}

        if sentence_lower in self.cache:
            cached = self.cache[sentence_lower]
            return {
                "index": index,
                "sentence": sentence,
                "matched": cached["matched"],
                "similarity": cached["similarity"],
                "sources": cached.get("sources", []),
                "matched_text": cached.get("matched_text", "")
            }

        result = self._search_sentence_online(sentence, words)
        self.cache[sentence_lower] = result
        result["index"] = index
        result["sentence"] = sentence
        return result

    def _search_sentence_online(self, sentence, words):
        try:
            query = quote(sentence[:200])
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            resp = requests.get(search_url, headers=headers, timeout=8)
            if resp.status_code != 200:
                return self._local_similarity_check(sentence, words)
            return self._parse_search_results(resp.text, sentence, words)
        except Exception:
            return self._local_similarity_check(sentence, words)

    def _parse_search_results(self, html, sentence, words):
        sources = []
        max_similarity = 0
        matched_text = ""

        snippets = re.findall(
            r'<a[^>]*class="result__a"[^>]*>(.*?)</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )

        for title, snippet in snippets[:5]:
            title_clean = re.sub(r'<[^>]+>', '', title).strip()
            snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
            snippet_clean = re.sub(r'\.\.\.', '', snippet_clean).strip()

            sim = self._text_similarity(sentence, snippet_clean)

            if sim > max_similarity:
                max_similarity = sim
                matched_text = snippet_clean[:200]

            source = {
                "title": title_clean,
                "snippet": snippet_clean[:200],
                "similarity": round(sim * 100, 1)
            }
            sources.append(source)

        is_matched = max_similarity > 0.4
        return {
            "matched": is_matched,
            "similarity": round(max_similarity * 100, 1),
            "sources": sources,
            "matched_text": matched_text[:200] if matched_text else ""
        }

    def _local_similarity_check(self, sentence, words):
        return {
            "matched": False,
            "similarity": 0,
            "sources": [],
            "matched_text": ""
        }

    def _text_similarity(self, s1, s2):
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

    def _split_sentences(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]

    def similarity_check(self, text1, text2):
        s1_words = set(re.findall(r'\b[a-zA-Z]+\b', text1.lower()))
        s2_words = set(re.findall(r'\b[a-zA-Z]+\b', text2.lower()))
        intersection = s1_words & s2_words
        union = s1_words | s2_words
        if not union:
            return 0
        jaccard = len(intersection) / len(union)
        return round(jaccard * 100, 1)
