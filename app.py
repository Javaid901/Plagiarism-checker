from flask import Flask, render_template, request, jsonify
from services.ai_detector import AIDetector
from services.plagiarism import PlagiarismDetector
from services.paraphraser import Paraphraser
from services.grammar import GrammarChecker
from services.formatter import TextFormatter
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50000

ai_detector = AIDetector()
plagiarism_detector = PlagiarismDetector()
paraphraser = Paraphraser()
grammar_checker = GrammarChecker()
text_formatter = TextFormatter()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/editor')
def editor():
    return render_template('editor.html')

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
    result = plagiarism_detector.check_plagiarism(text)
    return jsonify(result)

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
    score = plagiarism_detector.similarity_check(text1, text2)
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
        results['plagiarism'] = plagiarism_detector.check_plagiarism(text)
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

if __name__ == '__main__':
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)

    app.run(host='0.0.0.0', port=5000, debug=True)
