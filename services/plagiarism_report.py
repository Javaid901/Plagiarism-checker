import io
from datetime import datetime

try:
    from fpdf import FPDF
    _HAS_FPDF = True
except ImportError:
    _HAS_FPDF = False


class PlagiarismReport:
    def generate_html(self, data):
        scores = data.get("scores", {})
        sentence_matches = data.get("sentence_matches", [])
        paragraph_matches = data.get("paragraph_matches", [])
        writing_style = data.get("writing_style", {})
        sources = data.get("sources", [])

        html_parts = ["""
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8">
        <style>
            body { font-family: 'Inter', Arial, sans-serif; padding: 40px; color: #1f2937; background: #f8fafc; }
            .report-header { border-bottom: 3px solid #6366f1; padding-bottom: 20px; margin-bottom: 30px; }
            .report-title { font-size: 28px; font-weight: 800; color: #111827; }
            .report-date { color: #6b7280; font-size: 14px; margin-top: 4px; }
            .score-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 20px 0; }
            .score-card { background: white; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }
            .score-card .label { font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }
            .score-card .value { font-size: 28px; font-weight: 700; color: #111827; margin: 8px 0; }
            .score-card .value.high { color: #ef4444; }
            .score-card .value.medium { color: #f59e0b; }
            .score-card .value.low { color: #22c55e; }
            table { width: 100%; border-collapse: collapse; margin: 16px 0; }
            th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid #e5e7eb; font-size: 13px; }
            th { background: #f3f4f6; font-weight: 600; color: #374151; }
            .match-exact { border-left: 4px solid #ef4444; }
            .match-paraphrase { border-left: 4px solid #f59e0b; }
            .match-semantic { border-left: 4px solid #eab308; }
            .section-title { font-size: 18px; font-weight: 700; color: #111827; margin: 24px 0 12px; }
            .writing-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }
            .metric { background: white; border-radius: 8px; padding: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
            .metric .metric-label { font-size: 11px; color: #6b7280; }
            .metric .metric-value { font-size: 16px; font-weight: 600; color: #111827; }
            .recommendations { background: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 20px; margin: 20px 0; }
            .footer { text-align: center; color: #9ca3af; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; }
        </style></head><body>
        <div class="report-header">
            <div class="report-title">PlagiaShield Plagiarism Report</div>
            <div class="report-date">Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</div>
        </div>
        """]

        # Score cards
        overall = scores.get("overall_plagiarism_score", 0)
        cls = "high" if overall > 50 else ("medium" if overall > 20 else "low")
        html_parts.append(f"""
        <div class="score-grid">
            <div class="score-card"><div class="label">Overall Plagiarism</div><div class="value {cls}">{overall}%</div></div>
            <div class="score-card"><div class="label">Unique Content</div><div class="value {'low' if overall > 50 else 'high'}">{scores.get('unique_content', 0)}%</div></div>
            <div class="score-card"><div class="label">Confidence</div><div class="value">{scores.get('confidence', 0)}%</div></div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px;">
            <div class="score-card"><div class="label">Lexical</div><div class="value">{scores.get('lexical_similarity', 0)}%</div></div>
            <div class="score-card"><div class="label">Semantic</div><div class="value">{scores.get('semantic_similarity', 0)}%</div></div>
            <div class="score-card"><div class="label">Paraphrase</div><div class="value">{scores.get('paraphrase_score', 0)}%</div></div>
        </div>
        """)

        # Sentence matches
        if sentence_matches:
            html_parts.append('<div class="section-title">Sentence Matches</div><table><tr><th>#</th><th>Source</th><th>Matched</th><th>Type</th><th>Similarity</th></tr>')
            for i, m in enumerate(sentence_matches[:20]):
                cls = "match-exact" if m["match_type"] in ("Exact Copy", "Near Copy") else ("match-paraphrase" if m["match_type"] == "Paraphrased Match" else "match-semantic")
                html_parts.append(f'<tr class="{cls}"><td>{i+1}</td><td>{m["source_sentence"][:80]}</td><td>{m["matched_sentence"][:80]}</td><td>{m["match_type"]}</td><td>{m["semantic_similarity"] or m["lexical_similarity"]}%</td></tr>')
            html_parts.append('</table>')

        # Paragraph matches
        if paragraph_matches:
            html_parts.append(f'<div class="section-title">Paragraph Matches</div><table><tr><th>#</th><th>Score</th><th>Type</th></tr>')
            for i, m in enumerate(paragraph_matches[:10]):
                html_parts.append(f'<tr><td>{i+1}</td><td>{m["overall_score"]}%</td><td>{"Direct" if m["overall_score"] > 60 else "Semantic"} Match</td></tr>')
            html_parts.append('</table>')

        # Writing style
        if writing_style and writing_style.get("total_words", 0) > 0:
            html_parts.append(f'<div class="section-title">Writing Style Analysis</div><div class="writing-metrics">')
            metrics = [
                ("Readability", writing_style.get("readability_label", "N/A")),
                ("Vocab Diversity", f'{writing_style.get("vocabulary_diversity", 0)}%'),
                ("Burstiness", writing_style.get("burstiness", 0)),
                ("Repetition", f'{writing_style.get("repetition_rate", 0)}%'),
            ]
            for label, val in metrics:
                html_parts.append(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{val}</div></div>')
            html_parts.append('</div>')

        # Recommendations
        html_parts.append(f"""
        <div class="section-title">Recommendations</div>
        <div class="recommendations">
            <ul style="margin:0;padding-left:20px;">
                {f'<li>High plagiarism detected ({overall}%). Consider paraphrasing or properly citing sources.</li>' if overall > 50 else ''}
                {f'<li>Content appears largely original ({scores.get("unique_content", 0)}% unique).</li>' if scores.get("unique_content", 0) > 70 else ''}
                {f'<li>Paraphrase score is elevated — some sections may be rewritten from sources.</li>' if scores.get("paraphrase_score", 0) > 40 else ''}
                <li>Review highlighted matches for proper attribution.</li>
                <li>Use the Paraphrase or Humanize tools to reduce similarity if needed.</li>
            </ul>
        </div>
        """)

        html_parts.append('<div class="footer">Generated by PlagiaShield &mdash; AI-Powered Plagiarism Detection Engine</div></body></html>')
        return '\n'.join(html_parts)

    def generate_pdf(self, data, filepath=None):
        if not _HAS_FPDF:
            html = self.generate_html(data)
            return html.encode('utf-8')
        html = self.generate_html(data)
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Helvetica", size=10)
            for line in html.split('\n'):
                clean = line.strip()
                if clean and not clean.startswith('<'):
                    pdf.cell(0, 6, clean[:120], ln=True)
            if filepath:
                pdf.output(filepath)
                return filepath
            return pdf.output(dest='S').encode('latin-1', errors='replace')
        except Exception:
            return html.encode('utf-8')
