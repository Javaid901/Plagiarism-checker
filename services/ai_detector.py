import re
import math
from collections import Counter

class AIDetector:
    def __init__(self):
        self.ai_phrases = [
            "it is important to note", "in conclusion", "furthermore", "moreover",
            "additionally", "in addition", "as a result", "consequently",
            "therefore", "thus", "hence", "notably", "specifically",
            "in particular", "it is worth mentioning", "it should be noted",
            "on the other hand", "in contrast", "on the contrary",
            "in other words", "that is to say", "to illustrate",
            "for instance", "for example", "such as", "including",
            "among others", "et cetera", "and so on", "and so forth",
            "in summary", "to summarize", "overall", "in general",
            "generally speaking", "it can be argued", "it could be said",
            "one might say", "arguably", "presumably",
            "undoubtedly", "without a doubt", "certainly", "definitely",
            "indeed", "surely", "truly", "in fact", "as a matter of fact",
            "the fact that", "the reality is", "the truth is",
            "in today's world", "in the modern world", "in recent years",
            "in recent times", "over the years", "over time",
            "throughout history", "throughout the years",
            "it is widely known", "it is well known", "it is common knowledge",
            "research shows", "studies have shown", "studies indicate",
            "according to", "based on", "as per", "in accordance with",
            "with respect to", "with regard to", "regarding", "concerning",
            "in terms of", "when it comes to", "as far as",
            "from a perspective", "from the perspective of",
            "in the context of", "within the framework of",
            "it is essential", "it is crucial", "it is vital",
            "it is necessary", "it is imperative", "it is important",
            "it is critical", "it is fundamental",
            "one of the most", "some of the most", "many of the",
            "a wide range of", "a variety of", "a number of",
            "a great deal of", "a plethora of", "myriad",
            "countless", "numerous", "various", "diverse",
            "significant", "substantial", "considerable",
            "remarkable", "noteworthy", "notable", "striking",
            "delve into", "delve deeper", "explore the", "explore how",
            "landscape of", "realm of", "world of",
            "transformative", "groundbreaking", "revolutionary",
            "cutting-edge", "state-of-the-art", "bleeding-edge",
            "nuanced", "multifaceted", "multi-faceted",
            "interconnected", "intertwined", "interwoven",
            "paradigm", "paradigm shift", "game-changer",
            "leverage", "utilize", "optimize", "streamline",
            "holistic", "comprehensive", "end-to-end",
            "meaningful", "purposeful", "tailored", "bespoke",
            "navigate the", "navigate this", "grapple with",
            "underscores", "highlights", "emphasizes", "illuminates",
            "foster", "cultivate", "nurture",
            "robust", "scalable", "seamless", "seamlessly",
        ]

        self.transition_words = [
            "however", "nevertheless", "nonetheless", "still", "yet",
            "although", "though", "even though", "despite", "in spite of",
            "meanwhile", "simultaneously", "concurrently",
            "subsequently", "afterward", "later", "thereafter",
            "previously", "earlier", "prior to", "before",
            "firstly", "secondly", "thirdly", "finally", "lastly",
            "next", "then", "after", "before", "while", "during",
            "because", "since", "as", "due to", "owing to",
            "so", "thus", "therefore", "accordingly",
            "if", "unless", "provided", "providing", "assuming",
            "alternatively", "instead", "rather", "otherwise",
        ]

    def analyze(self, text):
        sentences = self._split_sentences(text)
        words = self._tokenize(text)
        word_count = len(words)
        sentence_count = len(sentences)

        if word_count < 10:
            return {
                "score": 0,
                "label": "Insufficient Text",
                "confidence": 0,
                "details": {
                    "ai_phrase_score": 0,
                    "burstiness_score": 0,
                    "repetition_score": 0,
                    "perplexity_score": 0
                },
                "analysis": ["Please provide at least 10 words for analysis."]
            }

        ai_phrase_score = self._check_ai_phrases(text, words)
        burstiness_score = self._check_burstiness(sentences, word_count)
        repetition_score = self._check_repetition(words)
        perplexity_score = self._check_perplexity(text, words)

        features = [ai_phrase_score, burstiness_score, repetition_score, perplexity_score]
        weight_map = [0.35, 0.25, 0.15, 0.25]

        final_score = sum(f * w for f, w in zip(features, weight_map))
        final_score = min(max(final_score, 0), 100)

        if final_score < 25:
            label = "Likely Human-Written"
        elif final_score < 45:
            label = "Possibly AI-Generated"
        elif final_score < 65:
            label = "Likely AI-Generated"
        else:
            label = "Very Likely AI-Generated"

        return {
            "score": round(final_score, 1),
            "label": label,
            "confidence": round(min(final_score + 10, 100), 1),
            "details": {
                "ai_phrase_score": round(ai_phrase_score, 1),
                "burstiness_score": round(burstiness_score, 1),
                "repetition_score": round(repetition_score, 1),
                "perplexity_score": round(perplexity_score, 1)
            },
            "analysis": self._generate_analysis(
                final_score, ai_phrase_score, burstiness_score,
                repetition_score, perplexity_score, word_count
            )
        }

    def _split_sentences(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 3]

    def _tokenize(self, text):
        text = text.lower()
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        return words

    def _check_ai_phrases(self, text, words):
        text_lower = text.lower()
        if len(words) == 0:
            return 0

        phrase_matches = 0
        for phrase in self.ai_phrases:
            if phrase in text_lower:
                phrase_matches += 1
                text_lower = text_lower.replace(phrase, "", 1)

        raw_score = min(phrase_matches * 8, 80)

        transition_count = 0
        for word in words:
            if word in self.transition_words:
                transition_count += 1

        transition_density = (transition_count / len(words)) * 100
        if transition_density > 4:
            raw_score += min((transition_density - 4) * 3, 20)

        return min(raw_score, 100)

    def _check_burstiness(self, sentences, word_count):
        if len(sentences) < 3 or word_count == 0:
            return 50

        sentence_lengths = [len(s.split()) for s in sentences if s.split()]

        if len(sentence_lengths) < 3:
            return 50

        mean_length = sum(sentence_lengths) / len(sentence_lengths)

        if mean_length == 0:
            return 50

        variance = sum((l - mean_length) ** 2 for l in sentence_lengths) / len(sentence_lengths)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_length

        if cv <= 0.35:
            score = 100
        elif cv <= 0.5:
            score = 75 - ((cv - 0.35) / 0.15) * 25
        elif cv <= 0.8:
            score = 30 - ((cv - 0.5) / 0.3) * 20
        else:
            score = 10

        min_len = min(sentence_lengths)
        max_len = max(sentence_lengths)
        range_ratio = max_len / max(min_len, 1)

        if range_ratio < 2:
            score = min(score + 15, 100)
        elif range_ratio > 5:
            score = max(score - 10, 0)

        consecutive_similar = 0
        for i in range(len(sentence_lengths) - 1):
            ratio = max(sentence_lengths[i], sentence_lengths[i+1]) / max(min(sentence_lengths[i], sentence_lengths[i+1]), 1)
            if ratio < 1.3:
                consecutive_similar += 1

        if consecutive_similar > len(sentence_lengths) * 0.4:
            score = min(score + 10, 100)

        return max(0, min(100, score))

    def _check_repetition(self, words):
        if len(words) < 15:
            return 20

        word_freq = Counter(words)
        total_words = len(words)

        top_words_count = sum(count for word, count in word_freq.most_common(10))
        top_ratio = top_words_count / total_words

        if top_ratio > 0.55:
            score = 80 + (top_ratio - 0.55) * 100
        elif top_ratio > 0.45:
            score = 50 + (top_ratio - 0.45) * 300
        elif top_ratio > 0.35:
            score = 25 + (top_ratio - 0.35) * 250
        else:
            score = top_ratio * 70

        repeated_bigrams = 0
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
        bigram_freq = Counter(bigrams)
        for freq in bigram_freq.values():
            if freq > 1:
                repeated_bigrams += freq - 1

        if repeated_bigrams > 3:
            score = min(score + (repeated_bigrams * 2), 100)

        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.4:
            score = min(score + 15, 100)

        return min(score, 100)

    def _check_perplexity(self, text, words):
        if len(words) < 5:
            return 20

        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
        bigram_freq = Counter(bigrams)
        unigram_freq = Counter(words)

        total_bigrams = len(bigrams)
        if total_bigrams == 0:
            return 20

        negative_log_likelihood = 0
        for bigram in bigrams:
            w1, w2 = bigram.split()
            count_w1 = unigram_freq[w1]
            count_bigram = bigram_freq[bigram]
            prob = count_bigram / count_w1 if count_w1 > 0 else 1 / len(words)
            negative_log_likelihood += -math.log2(max(prob, 1e-10))

        avg_neg_log_likelihood = negative_log_likelihood / total_bigrams if total_bigrams > 0 else 0

        repeating_bigrams = sum(1 for f in bigram_freq.values() if f > 1)
        repeat_ratio = repeating_bigrams / len(bigram_freq) if bigram_freq else 0

        if repeat_ratio > 0.35:
            score = 75 + min((repeat_ratio - 0.35) * 30, 25)
        elif avg_neg_log_likelihood < 7:
            score = 65 + max((7 - avg_neg_log_likelihood) * 5, 0)
        elif avg_neg_log_likelihood > 14:
            score = 15
        else:
            score = 50 - (avg_neg_log_likelihood - 10) * 10

        if len(set(words)) / len(words) < 0.45:
            score = min(score + 15, 100)

        return max(0, min(100, score))

    def _generate_analysis(self, final_score, ai_phrase, burstiness, repetition, perplexity, word_count):
        points = []

        if ai_phrase > 50:
            points.append("High frequency of AI-typical phrasing detected")
        elif ai_phrase > 25:
            points.append("Moderate use of AI-typical language patterns")

        if burstiness > 55:
            points.append("Sentence lengths are unusually uniform (typical AI pattern)")
        elif burstiness > 30:
            points.append("Moderate sentence length variation")

        if repetition > 50:
            points.append("High word/phrase repetition detected")
        elif repetition > 25:
            points.append("Some repetitive vocabulary patterns found")

        if perplexity > 50:
            points.append("Text is highly predictable (common in AI writing)")
        elif perplexity > 25:
            points.append("Moderate text predictability")

        if not points:
            points.append("Text shows patterns consistent with human writing across all dimensions")

        points.append(f"Analyzed {word_count} words across 4 detection dimensions")

        return points
