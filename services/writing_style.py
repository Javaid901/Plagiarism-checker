import re
import numpy as np

class WritingStyleAnalyzer:
    def __init__(self):
        self.transition_words = {
            'addition': ['also', 'furthermore', 'moreover', 'additionally', 'besides', 'likewise', 'similarly'],
            'contrast': ['however', 'nevertheless', 'nonetheless', 'conversely', 'whereas', 'although', 'though', 'but', 'yet', 'while', 'despite', 'instead'],
            'cause': ['because', 'since', 'therefore', 'thus', 'consequently', 'hence', 'accordingly', 'as a result'],
            'sequence': ['first', 'second', 'third', 'next', 'then', 'finally', 'lastly', 'after', 'before', 'subsequently'],
            'emphasis': ['indeed', 'certainly', 'undoubtedly', 'surely', 'clearly', 'obviously', 'notably', 'importantly'],
        }
        self.passive_indicators = ['was', 'were', 'been', 'being', 'is', 'are', 'am', 'be']
        self.passive_pattern = re.compile(r'\b(?:is|are|was|were|been|being|be)\s+\w+ed\b', re.IGNORECASE)

    def analyze(self, text):
        sents = self._split_sentences(text)
        words = text.split()
        if not sents or len(words) < 5:
            return self._empty_result()

        sent_lengths = [len(s.split()) for s in sents]
        word_lengths = [len(w.strip(".,!?;:'\"")) for w in words if w.strip(".,!?;:'\"")]

        vocab = set(w.lower().strip(".,!?;:'\"") for w in words)
        total_words = len(words)

        sent_len_var = np.var(sent_lengths) if len(sent_lengths) > 1 else 0
        vocab_diversity = len(vocab) / total_words if total_words > 0 else 0
        burstiness = sent_len_var / (np.mean(sent_lengths) + 0.01)
        readability = self._flesch_reading_ease(text, sents, words)
        repetition_rate = 1 - vocab_diversity

        transition_count = 0
        for word in words:
            w_clean = word.lower().strip(".,!?;:'\"")
            for cat, tws in self.transition_words.items():
                if w_clean in tws:
                    transition_count += 1
                    break
        transition_freq = transition_count / total_words if total_words > 0 else 0

        passive_count = 0
        for s in sents:
            if self.passive_pattern.search(s):
                passive_count += 1
        passive_freq = passive_count / len(sents) if sents else 0

        avg_sent_complexity = np.mean(sent_lengths) if sent_lengths else 0

        return {
            "total_sentences": len(sents),
            "total_words": total_words,
            "avg_sentence_length": round(np.mean(sent_lengths), 1) if sent_lengths else 0,
            "sentence_length_variance": round(sent_len_var, 1),
            "vocabulary_size": len(vocab),
            "vocabulary_diversity": round(vocab_diversity * 100, 1),
            "burstiness": round(burstiness, 2),
            "readability_score": round(readability, 1),
            "readability_label": self._readability_label(readability),
            "repetition_rate": round(repetition_rate * 100, 1),
            "transition_word_frequency": round(transition_freq * 100, 1),
            "passive_voice_frequency": round(passive_freq * 100, 1),
            "avg_sentence_complexity": round(avg_sent_complexity, 1),
            "avg_word_length": round(np.mean(word_lengths), 1) if word_lengths else 0,
        }

    def _flesch_reading_ease(self, text, sents, words):
        total_syllables = self._count_syllables(text)
        if len(sents) == 0 or len(words) == 0:
            return 0
        return 206.835 - 1.015 * (len(words) / len(sents)) - 84.6 * (total_syllables / len(words))

    def _count_syllables(self, text):
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        count = 0
        for w in words:
            if len(w) <= 3:
                count += 1
                continue
            w = re.sub(r'e$', '', w)
            w = re.sub(r'[^aeiou]+$', '', w)
            vowels = re.findall(r'[aeiou]+', w)
            count += len(vowels) if vowels else 1
        return count

    def _readability_label(self, score):
        if score >= 90: return "Very Easy"
        elif score >= 80: return "Easy"
        elif score >= 70: return "Fairly Easy"
        elif score >= 60: return "Standard"
        elif score >= 50: return "Fairly Difficult"
        elif score >= 30: return "Difficult"
        else: return "Very Difficult"

    def _split_sentences(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        sents = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sents if len(s.strip()) > 2]

    def _empty_result(self):
        return {k: 0 if k != "readability_label" else "N/A" for k in [
            "total_sentences", "total_words", "avg_sentence_length",
            "sentence_length_variance", "vocabulary_size", "vocabulary_diversity",
            "burstiness", "readability_score", "readability_label",
            "repetition_rate", "transition_word_frequency",
            "passive_voice_frequency", "avg_sentence_complexity", "avg_word_length"
        ]}
