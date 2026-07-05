MATCH_COLORS = {
    "Exact Copy": "#ef4444",
    "Near Copy": "#f97316",
    "Paraphrased Match": "#f59e0b",
    "Semantic Match": "#eab308",
    "Weak Similarity": "#fbbf24",
    "No Match": "#22c55e"
}

EXPLANATIONS = {
    "Exact Copy": "Word-for-word identical. The text matches the source exactly.",
    "Near Copy": "Mostly the same with minor wording changes (tense, articles, punctuation).",
    "Semantic Match": "The wording differs but the meaning is strongly aligned with the source.",
    "Paraphrased Match": "The wording differs significantly but the meaning remains almost identical. Likely rewritten to avoid detection.",
    "Weak Similarity": "Some shared concepts or keywords but significant differences in structure and meaning.",
    "No Match": "No significant similarity detected. Content appears original."
}

def get_match_color(match_type):
    return MATCH_COLORS.get(match_type, "#6b7280")

def get_explanation(match_type):
    return EXPLANATIONS.get(match_type, "")

def highlight_text(text, matches, original_sentences):
    """Build highlighted HTML segments with clickable annotations."""
    parts = []
    for i, sent in enumerate(original_sentences):
        match_info = next((m for m in matches if m.get("source_index") == i), None)
        if match_info and match_info["match_type"] != "No Match":
            color = get_match_color(match_info["match_type"])
            mt = match_info["match_type"]
            sim = match_info.get("semantic_similarity") or match_info.get("lexical_similarity", 0)
            reason = get_explanation(mt)
            parts.append(
                f'<span class="plag-highlight" style="background:{color}22;border-bottom:2px solid {color};'
                f'cursor:pointer;position:relative;" '
                f'onclick="showMatchInfo(\'{mt}\',{sim},\'{reason}\',this)" '
                f'title="{mt}: {sim}% similarity">'
                f'{sent}</span>'
            )
        else:
            parts.append(f'<span class="plag-unique">{sent}</span>')
    return ' '.join(parts)


MATCH_TYPE_ORDER = [
    "Exact Copy",
    "Near Copy",
    "Paraphrased Match",
    "Semantic Match",
    "Weak Similarity",
    "No Match"
]
