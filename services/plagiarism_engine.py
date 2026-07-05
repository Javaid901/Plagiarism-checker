from .lexical_similarity import LexicalSimilarity
from .semantic_similarity import SemanticSimilarity
from .paraphrase_detector import ParaphraseDetector
from .sentence_matcher import SentenceMatcher, ParagraphMatcher
from .writing_style import WritingStyleAnalyzer
from .scoring import ScoringEngine
from .highlight import highlight_text, get_match_color, get_explanation, MATCH_TYPE_ORDER
from .plagiarism_report import PlagiarismReport


class PlagiarismEngine:
    def __init__(self):
        self.lexical = LexicalSimilarity()
        self.semantic = SemanticSimilarity()
        self.paraphrase = ParaphraseDetector()
        self.sentence_matcher = SentenceMatcher()
        self.paragraph_matcher = ParagraphMatcher()
        self.writing_style = WritingStyleAnalyzer()
        self.scoring = ScoringEngine()
        self.report = PlagiarismReport()

    def compare(self, text_a, text_b, compute_style=True):
        sents_a = self.sentence_matcher.split_sentences(text_a)
        sents_b = self.sentence_matcher.split_sentences(text_b)
        paras_a = self.paragraph_matcher.split_paragraphs(text_a) or [text_a]
        paras_b = self.paragraph_matcher.split_paragraphs(text_b) or [text_b]

        # Lexical
        lexical_scores = self.lexical.all_lexical(text_a, text_b)
        lexical_combined = self.lexical.combined_lexical_score(text_a, text_b)

        # Semantic (document-level)
        semantic_doc = self.semantic.sentence_similarity(text_a, text_b)
        semantic_doc_pct = round(semantic_doc * 100, 1) if semantic_doc is not None else None

        # Paraphrase detection
        paraphrase_result = self.paraphrase.detect(text_a, text_b)

        # Sentence matching
        sentence_matches = self.sentence_matcher.match_sentences(sents_a, sents_b)

        # Paragraph matching
        paragraph_matches = self.paragraph_matcher.match_paragraphs(paras_a, paras_b)

        # Sliding window block detection
        block_matches = self.paragraph_matcher.find_similar_blocks(text_a, text_b)

        # Scoring
        scores = self.scoring.compute_scores(
            lexical_combined,
            semantic_doc_pct if semantic_doc_pct is not None else lexical_combined,
            paraphrase_result,
            sentence_matches,
            paragraph_matches
        )

        # Writing style
        style_results = None
        if compute_style:
            style_results = self.writing_style.analyze(text_a)

        # Count match types
        type_counts = {t: 0 for t in MATCH_TYPE_ORDER}
        for m in sentence_matches:
            mt = m["match_type"]
            if mt in type_counts:
                type_counts[mt] += 1

        # Build highlighted text
        highlighted = highlight_text(text_a, sentence_matches, sents_a)

        return {
            "text_a": text_a[:2000],
            "text_b": text_b[:2000],
            "lexical_analysis": lexical_scores,
            "lexical_combined_score": lexical_combined,
            "semantic_similarity": semantic_doc_pct,
            "paraphrase_analysis": paraphrase_result,
            "sentence_matches": sentence_matches,
            "paragraph_matches": paragraph_matches,
            "block_matches": block_matches,
            "scores": scores,
            "match_type_distribution": type_counts,
            "highlighted_text": highlighted,
            "writing_style": style_results,
            "total_sentences_a": len(sents_a),
            "total_sentences_b": len(sents_b),
        }

    def compare_with_references(self, text, references):
        results = []
        for ref in references:
            result = self.compare(text, ref["text"], compute_style=False)
            results.append({
                "document_name": ref.get("name", "Unnamed"),
                "scores": result["scores"],
                "sentence_matches": result["sentence_matches"][:5],
                "paragraph_matches": result["paragraph_matches"][:3],
                "match_type_distribution": result["match_type_distribution"],
            })
        results.sort(key=lambda r: r["scores"]["overall_plagiarism_score"], reverse=True)
        return results

    def generate_report_html(self, text_a, text_b):
        data = self.compare(text_a, text_b)
        return self.report.generate_html(data)

    def generate_report_pdf(self, text_a, text_b, filepath=None):
        data = self.compare(text_a, text_b)
        return self.report.generate_pdf(data, filepath)
