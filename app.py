import gc
from flask import Flask, render_template, request, jsonify, send_file
from services.ai_detector import AIDetector
from services.semantic_plagiarism import SemanticPlagiarismDetector
from services.plagiarism_engine import PlagiarismEngine
from services.paraphraser import Paraphraser
from services.grammar import GrammarChecker
from services.formatter import TextFormatter
from services.writing_style import WritingStyleAnalyzer
from services.lexical_similarity import LexicalSimilarity
from services.semantic_similarity import SemanticSimilarity
from services.sentence_matcher import SentenceMatcher, ParagraphMatcher
from services.paraphrase_detector import ParaphraseDetector
from services.scoring import ScoringEngine
from services.plagiarism_report import PlagiarismReport
import io, time, os, tempfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Lazy model loading — model only loads on first encode() call
ai_detector = AIDetector()
plagiarism_engine = PlagiarismEngine()
paraphraser = Paraphraser()
grammar_checker = GrammarChecker()
text_formatter = TextFormatter()
writing_style_analyzer = WritingStyleAnalyzer()
lexical_sim = LexicalSimilarity()
semantic_sim = SemanticSimilarity()
sentence_matcher = SentenceMatcher()
paragraph_matcher = ParagraphMatcher()
paraphrase_detector = ParaphraseDetector()
scoring_eng = ScoringEngine()
report_gen = PlagiarismReport()
semantic_plagiarism_detector = SemanticPlagiarismDetector()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/editor')
def editor():
    return render_template('editor.html')

@app.route('/plagiarism-dashboard')
def plagiarism_dashboard():
    return render_template('plagiarism_dashboard.html')

@app.route('/api/ai-detect', methods=['POST'])
def detect_ai():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    if len(text.split()) < 5:
        return jsonify({'error': 'Please provide at least 5 words'}), 400
    result = ai_detector.analyze(text)
    return jsonify(result)

@app.route('/api/plagiarism', methods=['POST'])
def check_plagiarism():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    use_semantic = data.get('semantic', True)
    if use_semantic:
        result = semantic_plagiarism_detector.check_plagiarism(text)
    else:
        result = {"error": "only semantic mode supported", "score": 0}
    return jsonify(result)

# --- NEW: Full hybrid comparison ---

@app.route('/api/plagiarism/compare', methods=['POST'])
def compare_documents():
    data = request.get_json()
    text_a = data.get('text_a', '').strip()
    text_b = data.get('text_b', '').strip()
    if not text_a or not text_b:
        return jsonify({'error': 'Both text_a and text_b required'}), 400
    result = plagiarism_engine.compare(text_a, text_b)
    return jsonify(result)

@app.route('/api/plagiarism/multi', methods=['POST'])
def multi_compare():
    data = request.get_json()
    text = data.get('text', '').strip()
    documents = data.get('documents', [])
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    if not documents:
        return jsonify({'error': 'No reference documents provided'}), 400
    results = plagiarism_engine.compare_with_references(text, documents)
    return jsonify({"input_text": text[:500], "comparisons": results})

@app.route('/api/plagiarism/semantic', methods=['POST'])
def semantic_only():
    data = request.get_json()
    text1 = data.get('text1', '').strip()
    text2 = data.get('text2', '').strip()
    if not text1 or not text2:
        return jsonify({'error': 'Both text1 and text2 required'}), 400
    sem = semantic_sim.sentence_similarity(text1, text2)
    sem_pct = round(sem * 100, 1) if sem is not None else None
    para = paraphrase_detector.detect(text1, text2)
    return jsonify({"semantic_similarity": sem_pct, "paraphrase_analysis": para})

@app.route('/api/plagiarism/sentence', methods=['POST'])
def sentence_match():
    data = request.get_json()
    text_a = data.get('text_a', '').strip()
    text_b = data.get('text_b', '').strip()
    if not text_a or not text_b:
        return jsonify({'error': 'Both text_a and text_b required'}), 400
    sents_a = sentence_matcher.split_sentences(text_a)
    sents_b = sentence_matcher.split_sentences(text_b)
    matches = sentence_matcher.match_sentences(sents_a, sents_b)
    return jsonify({"sentence_matches": matches, "count_a": len(sents_a), "count_b": len(sents_b)})

@app.route('/api/plagiarism/paragraph', methods=['POST'])
def paragraph_match():
    data = request.get_json()
    text_a = data.get('text_a', '').strip()
    text_b = data.get('text_b', '').strip()
    if not text_a or not text_b:
        return jsonify({'error': 'Both text_a and text_b required'}), 400
    paras_a = paragraph_matcher.split_paragraphs(text_a) or [text_a]
    paras_b = paragraph_matcher.split_paragraphs(text_b) or [text_b]
    matches = paragraph_matcher.match_paragraphs(paras_a, paras_b)
    blocks = paragraph_matcher.find_similar_blocks(text_a, text_b)
    return jsonify({"paragraph_matches": matches, "block_matches": blocks})

@app.route('/api/plagiarism/paraphrase', methods=['POST'])
def detect_paraphrase():
    data = request.get_json()
    text1 = data.get('text1', '').strip()
    text2 = data.get('text2', '').strip()
    if not text1 or not text2:
        return jsonify({'error': 'Both text1 and text2 required'}), 400
    result = paraphrase_detector.detect(text1, text2)
    return jsonify(result)

@app.route('/api/plagiarism/lexical', methods=['POST'])
def lexical_check():
    data = request.get_json()
    text1 = data.get('text1', '').strip()
    text2 = data.get('text2', '').strip()
    if not text1 or not text2:
        return jsonify({'error': 'Both text1 and text2 required'}), 400
    result = lexical_sim.all_lexical(text1, text2)
    result["combined_score"] = lexical_sim.combined_lexical_score(text1, text2)
    return jsonify(result)

@app.route('/api/plagiarism/style', methods=['POST'])
def writing_style_check():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    result = writing_style_analyzer.analyze(text)
    return jsonify(result)

@app.route('/api/plagiarism/report', methods=['POST'])
def generate_report():
    data = request.get_json()
    text_a = data.get('text_a', '').strip()
    text_b = data.get('text_b', '').strip()
    fmt = data.get('format', 'html')
    if not text_a or not text_b:
        return jsonify({'error': 'Both text_a and text_b required'}), 400
    if fmt == 'pdf':
        pdf_data = plagiarism_engine.generate_report_pdf(text_a, text_b)
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='plagiarism_report.pdf'
        )
    html = plagiarism_engine.generate_report_html(text_a, text_b)
    return jsonify({"report_html": html})

@app.route('/api/paraphrase', methods=['POST'])
def paraphrase():
    data = request.get_json()
    text = data.get('text', '').strip()
    intensity = data.get('intensity', 'medium')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    result = paraphraser.paraphrase(text, intensity)
    return jsonify(result)

@app.route('/api/humanize', methods=['POST'])
def humanize():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    result = paraphraser.humanize(text)
    return jsonify(result)

@app.route('/api/bypass', methods=['POST'])
def bypass_ai():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    result = paraphraser.bypass_ai_detection(text)
    before_score = ai_detector.analyze(text)["score"]
    after_score = ai_detector.analyze(result["bypassed"])["score"]
    result["before_ai_score"] = before_score
    result["after_ai_score"] = after_score
    result["score_reduction"] = round(before_score - after_score, 1)
    return jsonify(result)

@app.route('/api/grammar', methods=['POST'])
def check_grammar():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    result = grammar_checker.check(text)
    return jsonify(result)

@app.route('/api/grammar-suggestions', methods=['POST'])
def grammar_suggestions():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    result = grammar_checker.check_sentence_suggestions(text)
    return jsonify(result)

@app.route('/api/similarity', methods=['POST'])
def similarity():
    data = request.get_json()
    text1 = data.get('text1', '').strip()
    text2 = data.get('text2', '').strip()
    if not text1 or not text2:
        return jsonify({'error': 'Both texts are required'}), 400
    score = lexical_sim.combined_lexical_score(text1, text2)
    return jsonify({'similarity': score})

@app.route('/api/format', methods=['POST'])
def format_text():
    data = request.get_json()
    text = data.get('text', '').strip()
    format_type = data.get('format_type', 'blog-post')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    result = text_formatter.format(text, format_type)
    return jsonify(result)

@app.route('/api/batch', methods=['POST'])
def batch_process():
    data = request.get_json()
    text = data.get('text', '').strip()
    features = data.get('features', ['ai_detect', 'plagiarism', 'paraphrase', 'grammar'])
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    results = {}
    if 'ai_detect' in features:
        results['ai_detect'] = ai_detector.analyze(text)
        results['ai_detect']['type'] = 'ai_detect'
    if 'plagiarism' in features:
        results['plagiarism'] = semantic_plagiarism_detector.check_plagiarism(text)
        results['plagiarism']['type'] = 'plagiarism'
    if 'paraphrase' in features:
        results['paraphrase'] = paraphraser.paraphrase(text)
        results['paraphrase']['type'] = 'paraphrase'
    if 'grammar' in features:
        results['grammar'] = grammar_checker.check(text)
        results['grammar']['type'] = 'grammar'
    if 'bypass' in features:
        bypass_result = paraphraser.bypass_ai_detection(text)
        bypass_result['before_ai_score'] = ai_detector.analyze(text)["score"]
        bypass_result['after_ai_score'] = ai_detector.analyze(bypass_result["bypassed"])["score"]
        bypass_result['score_reduction'] = round(bypass_result['before_ai_score'] - bypass_result['after_ai_score'], 1)
        bypass_result['type'] = 'bypass'
        results['bypass'] = bypass_result

    return jsonify(results)

@app.route('/api/memory/status', methods=['GET'])
def memory_status():
    import os as _os
    try:
        import psutil
        proc = psutil.Process()
        mem = proc.memory_info()
        info = {
            "rss_mb": round(mem.rss / 1024 / 1024, 1),
            "vms_mb": round(mem.vms / 1024 / 1024, 1),
            "model_loaded": semantic_sim.model is not None,
            "cache_size": semantic_sim.cache.size(),
        }
    except ImportError:
        import tracemalloc
        info = {"model_loaded": semantic_sim.model is not None, "cache_size": semantic_sim.cache.size()}
    return jsonify(info)

if __name__ == '__main__':
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)

    # Use debug=False on Render (512MB limit); set FLASK_DEBUG=1 for local dev
    import os as _os
    debug_mode = _os.environ.get('FLASK_DEBUG', '0') == '1'

    # Pre-load model in background to warm up before first request
    if _os.environ.get('PRELOAD_MODEL', '0') == '1':
        import threading
        threading.Thread(target=semantic_sim.model, daemon=True).start()

    # Run garbage collector after startup
    gc.collect()

    app.run(host='0.0.0.0', port=int(_os.environ.get('PORT', 5000)), debug=debug_mode)
