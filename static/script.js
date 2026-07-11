const textInput = document.getElementById('text-input');
const wordCount = document.getElementById('word-count');
const loadingOverlay = document.getElementById('loading-overlay');
const loaderText = document.getElementById('loader-text');
const loaderSub = document.getElementById('loader-sub');
let loadingInterval = null;
let analysisHistory = JSON.parse(localStorage.getItem('plagiashield_history') || '[]');
let formatDetectTimeout = null;
let lastDetectedFormat = null;
let lastInputText = '';

const loadingMessages = [
    { text: 'Analyzing text...', sub: 'Running AI detection' },
    { text: 'Scanning patterns...', sub: 'Checking writing style' },
    { text: 'Processing language...', sub: 'Evaluating sentence structure' },
    { text: 'Cross-referencing sources...', sub: 'Searching web for matches' },
    { text: 'Refining results...', sub: 'Generating suggestions' },
];

textInput.addEventListener('input', () => { updateWordCount(); updateProgressBar(); autoResizeTextarea(); scheduleFormatDetect(); });
textInput.addEventListener('paste', () => setTimeout(() => { updateWordCount(); updateProgressBar(); autoResizeTextarea(); scheduleFormatDetect(); }, 50));

function autoResizeTextarea() {
    textInput.style.height = 'auto';
    textInput.style.height = Math.min(textInput.scrollHeight, 400) + 'px';
}

function updateWordCount() {
    const text = textInput.value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    const charCount = document.getElementById('char-count');
    if (charCount) charCount.textContent = `${textInput.value.length.toLocaleString()} / 40,000`;
    wordCount.textContent = `${words} words`;
    updateDetailedStats();
}

function showLoading() {
    loadingOverlay.style.display = 'flex';
    // Safety timeout: auto-hide after 30s
    if (window._loadingSafetyTimer) clearTimeout(window._loadingSafetyTimer);
    window._loadingSafetyTimer = setTimeout(() => {
        hideLoading();
    }, 30000);
    let idx = 0;
    if (loaderText && loaderSub) {
        loaderText.textContent = loadingMessages[0].text;
        loaderSub.textContent = loadingMessages[0].sub;
        loadingInterval = setInterval(() => {
            idx = (idx + 1) % loadingMessages.length;
            loaderText.style.opacity = '0';
            loaderSub.style.opacity = '0';
            setTimeout(() => {
                loaderText.textContent = loadingMessages[idx].text;
                loaderSub.textContent = loadingMessages[idx].sub;
                loaderText.style.opacity = '1';
                loaderSub.style.opacity = '1';
            }, 200);
        }, 2500);
    }
}
function hideLoading() {
    loadingOverlay.style.display = 'none';
    if (window._loadingSafetyTimer) {
        clearTimeout(window._loadingSafetyTimer);
        window._loadingSafetyTimer = null;
    }
    if (loadingInterval) {
        clearInterval(loadingInterval);
        loadingInterval = null;
    }
}

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle', info: 'fa-info-circle' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> ${message}`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('toast-hide');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        runAllChecks();
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'l' && !e.shiftKey) {
        e.preventDefault();
        clearText();
    }
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'P') {
        e.preventDefault();
        pasteText();
    }
});

function clearText() {
    textInput.value = '';
    updateWordCount();
    document.getElementById('quick-stats').style.display = 'none';
    hideAllResults();
}

function pasteText() {
    navigator.clipboard.readText().then(text => {
        textInput.value = text;
        updateWordCount();
        updateProgressBar();
        autoResizeTextarea();
    }).catch(() => {
        textInput.focus();
        document.execCommand('paste');
    });
}

let sampleTexts = [
    "The rapid advancement of artificial intelligence has transformed numerous industries, from healthcare to finance. Machine learning algorithms now power everything from recommendation systems to autonomous vehicles. However, this technological revolution also raises important ethical questions about privacy, job displacement, and the nature of human creativity. As AI systems become more sophisticated, society must grapple with finding the right balance between innovation and regulation. It is crucial that we develop robust frameworks to ensure AI benefits all of humanity while minimizing potential risks.",
    "Climate change represents one of the most significant challenges facing humanity in the twenty-first century. Rising global temperatures have led to more frequent extreme weather events, melting polar ice caps, and shifting ecosystems. Scientists overwhelmingly agree that human activities, particularly the burning of fossil fuels, are the primary drivers of these changes. Transitioning to renewable energy sources, implementing sustainable agricultural practices, and reducing carbon emissions are essential steps. Furthermore, international cooperation is vital for addressing this global crisis effectively.",
    "The internet has fundamentally changed how we communicate, work, and access information. Social media platforms enable instant connection with people across the globe, while remote work technologies have transformed traditional office environments. E-commerce has revolutionized retail, and online education has made learning more accessible than ever before. However, these benefits come with challenges including digital divide issues, online privacy concerns, and the spread of misinformation. Addressing these challenges requires thoughtful policy-making and digital literacy initiatives."
];

if (typeof pdfjsLib !== 'undefined') {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

function handleFileUpload(event) {
    const files = event.target && event.target.files ? event.target.files : (event.files || []);
    const file = files[0];
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['txt', 'docx', 'pdf'].includes(ext)) {
        showToast('Unsupported file format: .' + ext, 'error');
        return;
    }
    showToast('Reading ' + file.name + '...', 'info', 1500);
    const reader = new FileReader();
    reader.onload = (e) => {
        if (ext === 'txt') {
            textInput.value = e.target.result;
            updateWordCount(); updateProgressBar(); autoResizeTextarea();
            showToast('File loaded: ' + file.name, 'success');
        } else if (ext === 'docx') {
            if (typeof mammoth !== 'undefined') {
                mammoth.extractRawText({ arrayBuffer: e.target.result })
                    .then(r => { textInput.value = r.value; updateWordCount(); updateProgressBar(); autoResizeTextarea(); showToast('DOCX loaded: ' + file.name, 'success'); })
                    .catch(() => showToast('Failed to parse DOCX', 'error'));
            } else {
                showToast('DOCX parser not loaded.', 'error');
            }
        } else if (ext === 'pdf') {
            if (typeof pdfjsLib !== 'undefined') {
                pdfjsLib.getDocument({ data: e.target.result }).promise.then(pdf => {
                    const promises = [];
                    for (let i = 1; i <= pdf.numPages; i++)
                        promises.push(pdf.getPage(i).then(page => page.getTextContent().then(tc => tc.items.map(item => item.str).join(' '))));
                    return Promise.all(promises).then(pages => { textInput.value = pages.join('\n\n'); updateWordCount(); updateProgressBar(); autoResizeTextarea(); showToast('PDF loaded: ' + file.name, 'success'); });
                }).catch(() => showToast('Failed to parse PDF', 'error'));
            } else {
                showToast('PDF parser not loaded.', 'error');
            }
        }
    };
    if (ext === 'txt') reader.readAsText(file);
    else reader.readAsArrayBuffer(file);
}

function loadSample() {
    textInput.value = sampleTexts[Math.floor(Math.random() * sampleTexts.length)];
    updateWordCount();
    updateProgressBar();
    autoResizeTextarea();
}

function toggleTheme() {
    const html = document.documentElement;
    const btn = document.getElementById('theme-toggle');
    if (html.getAttribute('data-theme') === 'light') {
        html.removeAttribute('data-theme');
        btn.innerHTML = '<i class="fas fa-moon"></i>';
        localStorage.setItem('plagiashield_theme', 'dark');
    } else {
        html.setAttribute('data-theme', 'light');
        btn.innerHTML = '<i class="fas fa-sun"></i>';
        localStorage.setItem('plagiashield_theme', 'light');
    }
}

function updateTabIndicator(tab) {
    const indicator = document.getElementById('tab-indicator');
    if (!indicator) return;
    indicator.style.left = tab.offsetLeft + 'px';
    indicator.style.width = tab.offsetWidth + 'px';
}

function updateDetailedStats() {
    const panel = document.getElementById('stats-panel');
    if (!panel) return;
    const text = textInput.value.trim();
    if (!text) { panel.style.display = 'none'; return; }
    const words = text.split(/\s+/);
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const chars = text.length;
    const letters = text.replace(/[^a-zA-Z]/g, '').length;
    const syllables = text.toLowerCase().split(/[aeiou]/g).length - 1;
    const avgWordLen = words.length > 0 ? (letters / words.length) : 0;
    const avgSentenceLen = sentences.length > 0 ? (words.length / sentences.length) : 0;
    const readingTime = Math.ceil(words.length / 200);
    const speakingTime = Math.ceil(words.length / 150);
    const readability = 206.835 - 1.015 * avgSentenceLen - 84.6 * (syllables / Math.max(words.length, 1));
    const readabilityLabel = readability > 80 ? 'Easy' : readability > 60 ? 'Fairly Easy' : readability > 40 ? 'Standard' : readability > 20 ? 'Difficult' : 'Very Difficult';

    panel.style.display = 'grid';
    panel.innerHTML = `
        <div class="stat-mini"><div class="stat-num">${words.length.toLocaleString()}</div><div class="stat-label">Words</div></div>
        <div class="stat-mini"><div class="stat-num">${sentences.length.toLocaleString()}</div><div class="stat-label">Sentences</div></div>
        <div class="stat-mini"><div class="stat-num">${chars.toLocaleString()}</div><div class="stat-label">Characters</div></div>
        <div class="stat-mini"><div class="stat-num">${readingTime}m</div><div class="stat-label">Read Time</div></div>
        <div class="stat-mini"><div class="stat-num">${avgWordLen.toFixed(1)}</div><div class="stat-label">Avg Word Len</div></div>
        <div class="stat-mini"><div class="stat-num">${avgSentenceLen.toFixed(0)}</div><div class="stat-label">Avg Sent Len</div></div>
        <div class="stat-mini"><div class="stat-num">${readability.toFixed(0)}</div><div class="stat-label">Readability</div></div>
        <div class="stat-mini"><div class="stat-num" style="font-size:12px;">${readabilityLabel}</div><div class="stat-label">Level</div></div>
    `;
}

function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tc => tc.style.display = 'none');
    const tab = document.querySelector(`.tab[data-tab="${tabId}"]`);
    tab.classList.add('active');
    document.getElementById(`tab-${tabId}`).style.display = 'block';
    updateTabIndicator(tab);
    if (tabId === 'format') scheduleFormatDetect();
}

function addRippleEffect(e) {
    const btn = e.currentTarget;
    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    const ripple = document.createElement('span');
    ripple.className = 'ripple-effect';
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    btn.appendChild(ripple);
    ripple.addEventListener('animationend', () => ripple.remove());
}

function updateProgressBar() {
    const bar = document.getElementById('progress-bar');
    if (!bar) return;
    const maxLen = 40000;
    const len = textInput.value.length;
    const pct = Math.min((len / maxLen) * 100, 100);
    bar.style.width = pct + '%';
    bar.classList.remove('warning', 'danger');
    if (pct > 85) bar.classList.add('danger');
    else if (pct > 65) bar.classList.add('warning');
}

function hideAllResults() {
    const tabMap = {
        'tab-ai-detect': { icon: 'robot', title: 'AI Content Detection', desc: 'Analyze text to determine if it was generated by AI.', action: 'runAIDetect()', btn: 'Check for AI' },
        'tab-plagiarism': { icon: 'copy', title: 'Plagiarism Check', desc: 'Check text against web sources to detect potential plagiarism.', action: 'runPlagiarism()', btn: 'Check Plagiarism' },
        'tab-paraphrase': { icon: 'pen-fancy', title: 'Paraphrasing Tool', desc: 'Rewrite text while preserving meaning. Choose from low, medium, or high intensity.', action: 'runParaphrase()', btn: 'Paraphrase' },
        'tab-humanize': { icon: 'user', title: 'Humanize Text', desc: 'Transform AI-generated or robotic text into natural, human-like writing.', action: 'runHumanize()', btn: 'Humanize Text' },
        'tab-grammar': { icon: 'spell-check', title: 'Grammar Check', desc: 'Check text for grammar, spelling, and style issues. Get correction suggestions.', action: 'runGrammar()', btn: 'Check Grammar' },
        'tab-bypass': { icon: 'shield', title: 'Bypass AI Detection', desc: 'Advanced transformation that restructures text to evade AI detection systems.', action: 'runBypass()', btn: 'Bypass AI Detection' },
        'tab-format': { icon: 'paragraph', title: 'Smart Document Formatter', desc: 'Intelligently detects headings, bullet points, numbered lists, and paragraphs — auto-structures your text.', action: "runFormat('auto')", btn: 'Auto-Format' },
        'tab-summary': { icon: 'compress', title: 'Text Summarization', desc: 'Generate a concise extractive summary of your text.', action: 'runSummarization()', btn: 'Summarize' },
        'tab-tone': { icon: 'chart-simple', title: 'Writing Tone Analysis', desc: 'Analyze formality, conciseness, passive voice, and complexity.', action: 'runToneAnalysis()', btn: 'Analyze Tone' },
    };
    document.querySelectorAll('.tab-content').forEach(tc => {
        const info = tabMap[tc.id] || { icon: 'robot', title: 'Tool', desc: '', action: '', btn: 'Run' };
        tc.innerHTML = `<div class="result-placeholder">
            <i class="fas fa-${info.icon}"></i>
            <h3>${info.title}</h3>
            <p>${info.desc}</p>
            <button class="btn btn-primary" onclick="${info.action}"><i class="fas fa-play"></i> ${info.btn}</button>
        </div>`;
    });
}

function getText() {
    const text = textInput.value.trim();
    if (!text) {
        alert('Please enter some text first.');
        return null;
    }
    if (text.split(/\s+/).length < 3) {
        alert('Please enter at least 3 words.');
        return null;
    }
    return text;
}

async function apiCall(endpoint, data) {
    const resp = await fetch(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.error || 'API error');
    }
    return resp.json();
}

async function runAllChecks() {
    const text = getText();
    if (!text) return;

    showLoading();
    try {
        const results = await apiCall('/api/batch', { text, features: ['ai_detect', 'plagiarism', 'paraphrase', 'grammar', 'bypass'] });
        hideLoading();
        document.getElementById('quick-stats').style.display = 'grid';

        if (results.ai_detect) {
            const ai = results.ai_detect;
            const statAi = document.getElementById('stat-ai');
            statAi.querySelector('.stat-value').textContent = `${ai.score}%`;
            statAi.style.color = ai.score > 60 ? 'var(--danger)' : ai.score > 30 ? 'var(--warning)' : 'var(--success)';
        }

        if (results.plagiarism) {
            const p = results.plagiarism;
            const statP = document.getElementById('stat-plagiarism');
            statP.querySelector('.stat-value').textContent = `${p.score}%`;
            statP.style.color = p.score > 30 ? 'var(--danger)' : p.score > 10 ? 'var(--warning)' : 'var(--success)';
        }

        if (results.grammar) {
            const g = results.grammar;
            const statG = document.getElementById('stat-grammar');
            statG.querySelector('.stat-value').textContent = `${g.score}%`;
            statG.style.color = g.score < 70 ? 'var(--danger)' : g.score < 90 ? 'var(--warning)' : 'var(--success)';
        }

        const statW = document.getElementById('stat-words');
        statW.querySelector('.stat-value').textContent = text.split(/\s+/).length;

        if (results.ai_detect) renderAIResults(results.ai_detect);
        if (results.plagiarism) renderPlagiarismResults(results.plagiarism);
        if (results.paraphrase) renderParaphraseResults(results.paraphrase);
        if (results.grammar) renderGrammarResults(results.grammar);
        if (results.bypass) renderBypassResults(results.bypass);

        switchTab('ai-detect');
        saveToHistory('Full Analysis', text.substring(0, 80) + '...');
        setTimeout(() => {
            document.getElementById('results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 150);
    } catch (err) {
        hideLoading();
        alert('Error: ' + err.message);
    }
}

async function runBypass() {
    const text = getText();
    if (!text) return;
    showLoading();
    try {
        const result = await apiCall('/api/bypass', { text });
        renderBypassResults(result);
        document.getElementById('quick-stats').style.display = 'grid';
        hideLoading();
        switchTab('bypass');
    } catch (err) { hideLoading(); alert(err.message); }
}

async function runAIDetect() {
    const text = getText();
    if (!text) return;
    showLoading();
    try {
        const result = await apiCall('/api/ai-detect', { text });
        renderAIResults(result);
        document.getElementById('quick-stats').style.display = 'grid';
        document.getElementById('stat-ai').querySelector('.stat-value').textContent = `${result.score}%`;
        hideLoading();
        switchTab('ai-detect');
    } catch (err) { hideLoading(); alert(err.message); }
}

async function runPlagiarism() {
    const text = getText();
    if (!text) return;
    showLoading();
    try {
        const result = await apiCall('/api/plagiarism', { text });
        renderPlagiarismResults(result);
        document.getElementById('quick-stats').style.display = 'grid';
        document.getElementById('stat-plagiarism').querySelector('.stat-value').textContent = `${result.score}%`;
        hideLoading();
        switchTab('plagiarism');
    } catch (err) { hideLoading(); alert(err.message); }
}

async function runParaphrase() {
    const text = getText();
    if (!text) return;
    const intensity = document.getElementById('paraphrase-intensity').value;
    showLoading();
    try {
        const result = await apiCall('/api/paraphrase', { text, intensity });
        renderParaphraseResults(result);
        hideLoading();
        switchTab('paraphrase');
    } catch (err) { hideLoading(); alert(err.message); }
}

async function runHumanize() {
    const text = getText();
    if (!text) return;
    showLoading();
    try {
        const result = await apiCall('/api/humanize', { text });
        renderHumanizeResults(result);
        hideLoading();
        switchTab('humanize');
    } catch (err) { hideLoading(); alert(err.message); }
}

async function runGrammar() {
    const text = getText();
    if (!text) return;
    showLoading();
    try {
        const result = await apiCall('/api/grammar', { text });
        renderGrammarResults(result);
        document.getElementById('quick-stats').style.display = 'grid';
        document.getElementById('stat-grammar').querySelector('.stat-value').textContent = `${result.score}%`;
        hideLoading();
        switchTab('grammar');
    } catch (err) { hideLoading(); alert(err.message); }
}

function scheduleFormatDetect() {
    if (formatDetectTimeout) clearTimeout(formatDetectTimeout);
    const tab = document.getElementById('tab-format');
    if (!tab || tab.style.display === 'none') return;
    formatDetectTimeout = setTimeout(autoDetectFormat, 400);
}

async function autoDetectFormat() {
    const text = getText();
    const badge = document.getElementById('format-detect-badge');
    if (!badge) return;
    if (!text) { badge.innerHTML = ''; return; }
    try {
        const resp = await apiCall('/api/format/detect', { text });
        const d = resp.detected_structure;
        lastInputText = text;
        lastDetectedFormat = d;
        if (d.type === 'empty') { badge.innerHTML = ''; return; }
        badge.innerHTML = `<i class="fas fa-list-tree"></i> ${escapeHtml(d.label)}`;
    } catch (e) { /* silent */ }
}

async function runFormat(formatType) {
    const text = getText();
    if (!text) return;
    showLoading();
    try {
        const result = await apiCall('/api/format', { text, format_type: formatType });
        renderFormatResults(result);
        hideLoading();
    } catch (err) { hideLoading(); alert(err.message); }
}

function openEditor() {
    const text = textInput.value.trim();
    localStorage.setItem('plagiashield_editor_text', text || '');
    window.location.href = '/editor';
}

function renderFormatResults(result) {
    const area = document.getElementById('format-results-area');
    if (!area) return;
    const detected = result.detected_structure;
    const badgeHtml = detected && detected.type !== 'empty'
        ? `<div class="structure-badge"><i class="fas fa-list-tree"></i> Detected: ${escapeHtml(detected.label)}</div>`
        : '';
    const typeLabel = result.format_type.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    area.innerHTML = `
        <div class="result-card">
            <h4>Original Text (${result.word_count_original} words)</h4>
            ${badgeHtml}
            <div class="output-text diff-original">${escapeHtml(result.original)}</div>
        </div>
        <div class="result-card">
            <h4>Formatted &mdash; ${typeLabel} (${result.word_count_new} words)</h4>
            <div class="output-text diff-corrected formatted-output">${result.formatted}</div>
            <div class="action-btns">
                <button class="copy-btn" onclick="copyFormatted(this)"><i class="fas fa-copy"></i> Copy HTML</button>
                <button class="btn btn-secondary btn-small" onclick="copyFormattedText(this)"><i class="fas fa-file-lines"></i> Copy Text</button>
            </div>
        </div>
    `;
}

function formatRestoreBtn() {
    if (!lastDetectedFormat || lastDetectedFormat.type === 'empty') return '';
    return `<button class="btn btn-secondary btn-small restore-format-btn" onclick="restoreFormatFromResult(this)" style="margin-left:4px;"><i class="fas fa-wand-magic-sparkles"></i> Re-apply Format</button>`;
}

async function restoreFormatFromResult(btn) {
    const card = btn.closest('.result-card');
    const textEl = card ? card.querySelector('.output-text.diff-corrected, .output-text:last-child') : null;
    const text = textEl ? (textEl.textContent || textEl.innerText) : '';
    if (!text) { showToast('No text found to format', 'error'); return; }
    showLoading();
    try {
        const result = await apiCall('/api/format', { text, format_type: 'auto' });
        hideLoading();
        renderFormatResults(result);
        switchTab('format');
        showToast('Format restored from detected structure', 'success');
    } catch (err) { hideLoading(); alert(err.message); }
}

function copyFormatted(btn) {
    const html = btn.parentElement.parentElement.querySelector('.formatted-output').innerHTML;
    navigator.clipboard.writeText(html).then(() => {
        showToast('HTML copied!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

function copyFormattedText(btn) {
    const el = btn.parentElement.parentElement.querySelector('.formatted-output');
    const text = el.textContent || el.innerText;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Text copied!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

function renderAIResults(result) {
    const tab = document.getElementById('tab-ai-detect');
    const scoreClass = result.score > 60 ? 'high' : result.score > 30 ? 'medium' : 'low';
    const badgeClass = result.score < 30 ? 'human' : result.score < 50 ? 'possibly' : result.score < 70 ? 'likely' : 'very-likely';

    tab.innerHTML = `
        <div class="result-card">
            <h4>AI Detection Result</h4>
            <div class="value" style="color: ${result.score > 60 ? 'var(--danger)' : result.score > 30 ? 'var(--warning)' : 'var(--success)'}">
                ${result.score}%
            </div>
            <span class="label-badge ${badgeClass}">${result.label}</span>
            <div class="score-bar">
                <div class="score-bar-fill ${scoreClass}" style="width: ${result.score}%"></div>
            </div>
        </div>
        <div class="detail-grid">
            <div class="detail-item">
                <div class="detail-label">AI Phrases</div>
                <div class="detail-value" style="color: ${result.details.ai_phrase_score > 50 ? 'var(--danger)' : 'var(--warning)'}">${result.details.ai_phrase_score}%</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Burstiness</div>
                <div class="detail-value" style="color: ${result.details.burstiness_score > 50 ? 'var(--danger)' : 'var(--warning)'}">${result.details.burstiness_score}%</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Repetition</div>
                <div class="detail-value" style="color: ${result.details.repetition_score > 50 ? 'var(--danger)' : 'var(--warning)'}">${result.details.repetition_score}%</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Predictability</div>
                <div class="detail-value" style="color: ${result.details.perplexity_score > 50 ? 'var(--danger)' : 'var(--warning)'}">${result.details.perplexity_score}%</div>
            </div>
        </div>
        <div class="result-card">
            <h4>Analysis</h4>
            <ul class="analysis-points">
                ${result.analysis.map(p => `<li>${p}</li>`).join('')}
            </ul>
        </div>
        <div class="action-btns">
            <button class="btn btn-secondary btn-small" onclick="switchTab('humanize')"><i class="fas fa-user"></i> Humanize This Text</button>
            <button class="btn btn-secondary btn-small" onclick="switchTab('paraphrase')"><i class="fas fa-pen-fancy"></i> Paraphrase</button>
        </div>
    `;
}

function renderPlagiarismResults(result) {
    const tab = document.getElementById('tab-plagiarism');
    const scoreClass = result.score > 30 ? 'high' : result.score > 10 ? 'medium' : 'low';
    const engine = result.engine || 'lexical';
    const isSemantic = engine.includes('semantic');

    let sentenceHtml = '';
    if (result.sentence_analysis) {
        sentenceHtml = result.sentence_analysis.map(s => {
            const isPara = s.paraphrase_match;
            const isSem = s.semantic_match;
            let badge = '';
            if (isPara) badge = '<span class="match-badge paraphrase-badge" title="Semantically similar but worded differently"><i class="fas fa-pen-fancy"></i> Paraphrased</span>';
            else if (isSem) badge = '<span class="match-badge semantic-badge" title="Semantically similar content"><i class="fas fa-brain"></i> Semantic</span>';
            return `
            <div class="sentence-match ${isPara ? 'paraphrase-match' : isSem ? 'semantic-match' : ''}">
                <span class="match-text">${s.sentence.length > 80 ? s.sentence.substring(0, 80) + '...' : s.sentence}</span>
                <span class="match-score" style="color: ${s.similarity > 40 ? 'var(--danger)' : s.similarity > 20 ? 'var(--warning)' : 'var(--success)'}">
                    ${s.matched ? s.similarity + '% match' : 'Unique'}
                </span>
                ${badge}
            </div>`;
        }).join('');
    }

    tab.innerHTML = `
        <div class="plagiarism-summary">
            <div class="detail-item">
                <div class="detail-label">Plagiarism Score</div>
                <div class="detail-value" style="color: ${result.score > 30 ? 'var(--danger)' : result.score > 10 ? 'var(--warning)' : 'var(--success)'}">${result.score}%</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Originality</div>
                <div class="detail-value" style="color: ${result.originality > 80 ? 'var(--success)' : result.originality > 50 ? 'var(--warning)' : 'var(--danger)'}">${result.originality}%</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Matches Found</div>
                <div class="detail-value">${result.matches ? result.matches.length : 0}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Engine</div>
                <div class="detail-value" style="font-size:11px;opacity:0.8;">${isSemantic ? '<i class="fas fa-brain" style="color:var(--accent);"></i> ' : ''}${engine}</div>
            </div>
        </div>
        <div class="score-bar">
            <div class="score-bar-fill ${scoreClass}" style="width: ${result.score}%"></div>
        </div>
        ${result.sources && result.sources.length > 0 ? `
        <div class="result-card">
            <h4>Web Sources ${result.sources.length > 0 ? `(${result.sources.length})` : ''}</h4>
            <div class="sources-list">
                ${result.sources.map(s => {
                    const extra = (s.semantic_similarity !== undefined && s.semantic_similarity !== null) ?
                        `&middot; Semantic: ${s.semantic_similarity}%` : '';
                    return `
                    <div class="source-item">
                        <div class="source-title">${s.title || 'Web Source'}</div>
                        <div class="source-snippet">${s.snippet ? s.snippet.substring(0, 150) : 'Source found'}</div>
                        <div class="source-similarity">Lexical: ${s.similarity}% ${extra}</div>
                    </div>`;
                }).join('')}
            </div>
        </div>
        ` : ''}
        ${sentenceHtml ? `
        <div class="result-card">
            <h4>Sentence Analysis <span style="font-weight:400;font-size:12px;opacity:0.6;">${isSemantic ? '&middot; Semantic + Lexical comparison' : '&middot; Lexical comparison'}</span></h4>
            <div class="sentence-analysis-grid">${sentenceHtml}</div>
        </div>
        ` : ''}
        <div class="action-btns">
            <button class="btn btn-secondary btn-small" onclick="switchTab('paraphrase')"><i class="fas fa-pen-fancy"></i> Paraphrase to Reduce Plagiarism</button>
        </div>
    `;
}

function renderParaphraseResults(result) {
    const tab = document.getElementById('tab-paraphrase');
    tab.innerHTML = `
        <div class="result-card">
            <h4>Paraphrased (${result.word_count_new} words &middot; ${result.changes} changes &middot; ${result.intensity} intensity)</h4>
            <div class="split-view">
                <div class="split-pane">
                    <h4><i class="fas fa-file-lines"></i> Original (${result.word_count_original} words)</h4>
                    <div class="output-text diff-original">${escapeHtml(result.original)}</div>
                </div>
                <div class="split-pane">
                    <h4><i class="fas fa-pen-fancy"></i> Paraphrased</h4>
                    <div class="output-text diff-corrected">${escapeHtml(result.paraphrased)}</div>
                </div>
            </div>
            <div class="action-btns" style="margin-top:12px;">
                <button class="copy-btn" onclick="copySplitRight(this)"><i class="fas fa-copy"></i> Copy Paraphrased</button>
                <button class="btn btn-secondary btn-small" onclick="exportResult('${escapeHtml(result.paraphrased)}', 'paraphrased')"><i class="fas fa-download"></i> Export</button>
                ${formatRestoreBtn()}
            </div>
        </div>
    `;
}

function renderHumanizeResults(result) {

function renderHumanizeResults(result) {
    const tab = document.getElementById('tab-humanize');
    tab.innerHTML = `
        <div class="result-card">
            <h4>Humanized (${result.changes} refinements)</h4>
            <div class="split-view">
                <div class="split-pane">
                    <h4><i class="fas fa-file-lines"></i> Original</h4>
                    <div class="output-text diff-original">${escapeHtml(result.original)}</div>
                </div>
                <div class="split-pane">
                    <h4><i class="fas fa-user"></i> Humanized</h4>
                    <div class="output-text diff-corrected">${escapeHtml(result.humanized)}</div>
                </div>
            </div>
            <div class="action-btns" style="margin-top:12px;">
                <button class="copy-btn" onclick="copySplitRight(this)"><i class="fas fa-copy"></i> Copy Humanized</button>
                <button class="btn btn-secondary btn-small" onclick="exportResult('${escapeHtml(result.humanized)}', 'humanized')"><i class="fas fa-download"></i> Export</button>
                ${formatRestoreBtn()}
            </div>
        </div>
    `;
}

function renderBypassResults(result) {

function renderBypassResults(result) {
    const tab = document.getElementById('tab-bypass');
    const reductionClass = result.score_reduction > 20 ? 'high' : result.score_reduction > 10 ? 'medium' : 'low';
    const success = result.after_ai_score < 30;

    tab.innerHTML = `
        <div class="result-card">
            <h4>AI Score Before vs After</h4>
            <div class="plagiarism-summary">
                <div class="detail-item">
                    <div class="detail-label">Before</div>
                    <div class="detail-value" style="color: ${result.before_ai_score > 50 ? 'var(--danger)' : 'var(--warning)'}">${result.before_ai_score}%</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">After</div>
                    <div class="detail-value" style="color: ${result.after_ai_score < 30 ? 'var(--success)' : result.after_ai_score < 50 ? 'var(--warning)' : 'var(--danger)'}">${result.after_ai_score}%</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Reduction</div>
                    <div class="detail-value" style="color: ${result.score_reduction > 20 ? 'var(--success)' : 'var(--warning)'}">-${result.score_reduction}%</div>
                </div>
            </div>
            <div class="score-bar">
                <div class="score-bar-fill ${reductionClass}" style="width: ${Math.min(result.score_reduction * 3, 100)}%"></div>
            </div>
            ${success ? '<p style="color: var(--success); margin-top: 8px;"><i class="fas fa-check-circle"></i> Text now registers as human-written</p>' : '<p style="color: var(--warning); margin-top: 8px;"><i class="fas fa-exclamation-triangle"></i> Some AI patterns remain — try running again</p>'}
        </div>
        <div class="result-card">
            <h4>Side-by-Side Comparison</h4>
            <div class="split-view">
                <div class="split-pane">
                    <h4><i class="fas fa-file-lines"></i> Original (${result.word_count_original} words &middot; ${result.before_ai_score}% AI)</h4>
                    <div class="output-text diff-original">${escapeHtml(result.original)}</div>
                </div>
                <div class="split-pane">
                    <h4><i class="fas fa-shield"></i> Bypassed (${result.word_count_new} words &middot; ${result.changes} changes &middot; ${result.after_ai_score}% AI)</h4>
                    <div class="output-text diff-corrected">${escapeHtml(result.bypassed)}</div>
                </div>
            </div>
            <div class="action-btns" style="margin-top:12px;">
                <button class="copy-btn" onclick="copySplitRight(this)"><i class="fas fa-copy"></i> Copy Bypassed</button>
                <button class="btn btn-secondary btn-small" onclick="runGrammarCheckOnBypassed()"><i class="fas fa-spell-check"></i> Check Grammar</button>
                <button class="btn btn-secondary btn-small" onclick="exportResult('${escapeHtml(result.bypassed)}', 'bypassed')"><i class="fas fa-download"></i> Export</button>
                ${formatRestoreBtn()}
            </div>
        </div>
    `;
    window._bypassedText = result.bypassed;
}

function runGrammarCheckOnBypassed() {
    if (window._bypassedText) {
        textInput.value = window._bypassedText;
        updateWordCount();
        switchTab('grammar');
        runGrammar();
    }
}

function annotateErrors(text, errors) {
    if (!errors || errors.length === 0) return escapeHtml(text);

    const sorted = [...errors].sort((a, b) => a.offset - b.offset || b.length - a.length);
    const dropped = [];
    for (let i = 0; i < sorted.length; i++) {
        const e = sorted[i];
        for (let j = i + 1; j < sorted.length; j++) {
            if (sorted[j].offset >= e.offset && sorted[j].offset < e.offset + e.length) {
                dropped.push(j);
            }
        }
    }
    const filtered = sorted.filter((_, i) => !dropped.includes(i));

    let result = '';
    let pos = 0;
    for (const err of filtered) {
        if (err.offset > pos) {
            result += escapeHtml(text.substring(pos, err.offset));
        }
        const errText = text.substring(err.offset, err.offset + err.length);
        const repl = err.replacements && err.replacements[0] ? err.replacements[0] : '';
        result += `<span class="grammar-error" title="${escapeHtml(err.message)}${repl ? ' \u2192 ' + escapeHtml(repl) : ''}">${escapeHtml(errText)}</span>`;
        pos = err.offset + err.length;
    }
    if (pos < text.length) {
        result += escapeHtml(text.substring(pos));
    }
    return result;
}

function renderGrammarResults(result) {
    const tab = document.getElementById('tab-grammar');
    const scoreClass = result.score < 70 ? 'high' : result.score < 90 ? 'medium' : 'low';
    const hasIssues = result.errors && result.errors.length > 0;

    let errorsHtml = '';
    if (hasIssues) {
        errorsHtml = result.errors.map((e, i) => `
            <div class="error-item" id="error-${i}">
                <div class="error-msg">
                    <strong>${escapeHtml(e.message)}</strong>
                    ${e.replacements && e.replacements.length > 0 ? `<div class="error-suggestion">Suggestion: ${escapeHtml(e.replacements.join(', '))}</div>` : ''}
                </div>
                <div class="error-actions">
                    <span class="error-type">${e.category || 'Issue'}</span>
                    ${e.replacements && e.replacements.length > 0 ? `<button class="btn btn-xs btn-secondary" onclick="applyGrammarFix(${i})"><i class="fas fa-check"></i> Apply</button>` : ''}
                </div>
            </div>
        `).join('');
    }

    tab.innerHTML = `
        <div class="plagiarism-summary">
            <div class="detail-item">
                <div class="detail-label">Grammar Score</div>
                <div class="detail-value" style="color: ${result.score < 70 ? 'var(--danger)' : result.score < 90 ? 'var(--warning)' : 'var(--success)'}">${result.score}%</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Issues Found</div>
                <div class="detail-value">${result.error_count || 0}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Words Checked</div>
                <div class="detail-value">${result.word_count || 0}</div>
            </div>
        </div>
        <div class="score-bar">
            <div class="score-bar-fill ${scoreClass}" style="width: ${result.score}%"></div>
        </div>
        <div class="result-card">
            <h4>Summary</h4>
            <p style="color: var(--text-secondary)">${result.summary}</p>
        </div>
        ${result.original ? `
        <div class="result-card">
            <h4>Original Text ${hasIssues ? '<span style="color:var(--danger);font-weight:500;font-size:13px;">&mdash; errors underlined</span>' : ''}</h4>
            <div class="output-text diff-original annotated-text">${annotateErrors(result.original, result.errors)}</div>
            <button class="copy-btn" onclick="copyText(this)"><i class="fas fa-copy"></i> Copy</button>
        </div>
        ` : ''}
        ${result.corrected_text && result.corrected_text !== result.original ? `
        <div class="result-card">
            <h4>Corrected Version</h4>
            <div class="output-text diff-corrected">${escapeHtml(result.corrected_text)}</div>
            <div class="action-btns">
                <button class="btn btn-primary btn-small" onclick="applyAllGrammarFixes()"><i class="fas fa-check-double"></i> Fix All</button>
                <button class="copy-btn" onclick="copyText(this)"><i class="fas fa-copy"></i> Copy</button>
                ${formatRestoreBtn()}
            </div>
        </div>
        ` : ''}
        ${errorsHtml ? `
        <div class="result-card">
            <h4>Issues (${result.errors.length})</h4>
            ${errorsHtml}
        </div>
        ` : '<div class="result-card"><p style="color: var(--success)"><i class="fas fa-check-circle"></i> No issues found!</p></div>'}
    `;
    window._grammarResult = result;
}

function applyAllGrammarFixes() {
    const r = window._grammarResult;
    if (r && r.corrected_text) {
        textInput.value = r.corrected_text;
        updateWordCount();
        runGrammar();
    }
}

function applyGrammarFix(index) {
    const r = window._grammarResult;
    if (!r || !r.errors || !r.errors[index]) return;

    const err = r.errors[index];
    const replacement = err.replacements && err.replacements[0];
    if (!replacement) return;

    let text = textInput.value;
    text = text.substring(0, err.offset) + replacement + text.substring(err.offset + err.length);
    textInput.value = text;
    updateWordCount();
    runGrammar();
}

function copySplitRight(btn) {
    const pane = btn.closest('.result-card').querySelector('.split-pane:last-child .output-text');
    if (!pane) return;
    const text = pane.textContent || pane.innerText;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

function exportResult(text, label) {
    const cleaned = text.replace(/<[^>]*>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
    const blob = new Blob([cleaned], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `plagiashield_${label}_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
    showToast('File downloaded!', 'success');
}

/* ===== History ===== */
function saveToHistory(label, text) {
    const preview = text.replace(/<[^>]*>/g, '').substring(0, 80);
    analysisHistory.unshift({ label, preview, text, time: Date.now() });
    if (analysisHistory.length > 20) analysisHistory.pop();
    localStorage.setItem('plagiashield_history', JSON.stringify(analysisHistory));
    renderHistory();
}

function renderHistory() {
    const list = document.getElementById('history-list');
    if (!list) return;
    if (analysisHistory.length === 0) {
        list.innerHTML = '<div class="history-empty"><i class="fas fa-history"></i><p>No history yet.<br>Run an analysis to see it here.</p></div>';
        return;
    }
    list.innerHTML = analysisHistory.map((item, i) => {
        const time = new Date(item.time).toLocaleString();
        return `<div class="history-item" onclick="loadHistoryItem(${i})">
            <div class="history-preview">${escapeHtml(item.preview)}</div>
            <div class="history-meta"><span>${item.label}</span><span>${time}</span></div>
        </div>`;
    }).join('');
}

function loadHistoryItem(index) {
    const item = analysisHistory[index];
    if (item) {
        textInput.value = item.text;
        updateWordCount();
        updateProgressBar();
        autoResizeTextarea();
        toggleHistory();
        showToast('History item loaded', 'info');
    }
}

function toggleHistory() {
    document.getElementById('history-panel').classList.toggle('open');
}

/* ===== Summarization (client-side extractive) ===== */
function runSummarization() {
    const text = getText();
    if (!text) return;

    const sentences = text.match(/[^.!?\n]+[.!?]*/g) || [text];
    if (sentences.length < 3) {
        showToast('Text is too short for summarization (need 3+ sentences)', 'error');
        return;
    }

    const words = text.toLowerCase().split(/\W+/).filter(w => w.length > 2);
    const freq = {};
    words.forEach(w => { freq[w] = (freq[w] || 0) + 1; });
    const maxFreq = Math.max(...Object.values(freq), 1);

    const scored = sentences.map((s, i) => {
        const sWords = s.toLowerCase().split(/\W+/).filter(w => w.length > 2);
        let score = 0;
        sWords.forEach(w => { score += (freq[w] || 0) / maxFreq; });
        // Boost first sentence
        if (i === 0) score *= 1.4;
        // Prefer medium-length sentences
        const len = sWords.length;
        if (len >= 8 && len <= 25) score *= 1.2;
        return { sentence: s.trim(), score, index: i };
    });

    scored.sort((a, b) => b.score - a.score);
    const targetLen = Math.max(2, Math.ceil(sentences.length * 0.3));
    const topSentences = scored.slice(0, targetLen).sort((a, b) => a.index - b.index);
    const summary = topSentences.map(s => s.sentence).join(' ');

    const tab = document.getElementById('tab-summary');
    tab.innerHTML = `
        <div class="result-card">
            <h4>Summary (${topSentences.length} of ${sentences.length} sentences)</h4>
            <div class="summary-text">${escapeHtml(summary)}</div>
            <div class="summary-stats">
                <span class="summary-stat"><strong>${summary.split(/\s+/).length}</strong> words</span>
                <span class="summary-stat"><strong>${((summary.split(/\s+/).length / Math.max(text.split(/\s+/).length, 1)) * 100).toFixed(0)}%</strong> of original</span>
            </div>
            <div class="action-btns" style="margin-top:12px;">
                <button class="copy-btn" onclick="copyText(this)"><i class="fas fa-copy"></i> Copy Summary</button>
                <button class="btn btn-secondary btn-small" onclick="exportResult('${escapeHtml(summary)}', 'summary')"><i class="fas fa-download"></i> Export</button>
            </div>
        </div>
        <div class="result-card">
            <h4>Original Text</h4>
            <div class="output-text diff-original" style="max-height:200px;overflow-y:auto;">${escapeHtml(text)}</div>
        </div>
    `;
    switchTab('summary');
    saveToHistory('Summary', summary);
}

/* ===== Tone Analysis ===== */
function runToneAnalysis() {
    const text = getText();
    if (!text) return;

    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const words = text.split(/\s+/).filter(w => w.length > 0);
    const totalWords = words.length;

    // Formality: ratio of longer words, articles, prepositions
    const formalIndicators = ['the', 'which', 'therefore', 'however', 'furthermore', 'consequently', 'nevertheless', 'moreover', 'regarding', 'utilize', 'demonstrate', 'possess', 'establish', 'indicate', 'procedure', 'objective', 'implement'];
    const informalIndicators = ['like', 'really', 'just', 'basically', 'actually', 'pretty', 'kind of', 'sort of', 'stuff', 'thing', 'gonna', 'wanna', 'gotta', 'yeah', 'nah', 'cool', 'awesome', 'okay'];
    let formalScore = 0, informalScore = 0;
    const lowerText = text.toLowerCase();
    formalIndicators.forEach(w => { if (lowerText.includes(w)) formalScore++; });
    informalIndicators.forEach(w => { if (lowerText.includes(w)) informalScore++; });
    const longWords = words.filter(w => w.length > 6).length;
    const formalityPct = Math.min(Math.round((formalScore / Math.max(totalWords, 1)) * 200 + (longWords / Math.max(totalWords, 1)) * 100), 100);

    // Conciseness: average sentence length, filler words
    const fillerWords = ['very', 'really', 'quite', 'basically', 'actually', 'literally', 'just', 'simply', 'extremely', 'highly', 'significantly'];
    let fillerCount = 0;
    words.forEach(w => { if (fillerWords.includes(w.toLowerCase())) fillerCount++; });
    const avgSentLen = totalWords / Math.max(sentences.length, 1);
    const concisenessPct = Math.min(Math.round(Math.max(0, 100 - (avgSentLen - 15) * 2 - fillerCount * 3)), 100);
    const invConciseness = 100 - concisenessPct;

    // Passive voice detection
    const passivePattern = /\b(am|is|are|was|were|be|been|being)\s+\w+ed\b/gi;
    const passiveMatches = text.match(passivePattern);
    const passiveCount = passiveMatches ? passiveMatches.length : 0;
    const passivePct = Math.min(Math.round((passiveCount / Math.max(sentences.length, 1)) * 100), 100);

    // Complexity: syllables, long words
    const syllableCount = text.toLowerCase().split(/[aeiou]/g).length - 1;
    const complexWords = words.filter(w => w.length > 8).length;
    const complexityPct = Math.min(Math.round((complexWords / Math.max(totalWords, 1)) * 100 + (syllableCount / Math.max(totalWords, 1)) * 20), 100);

    // Labels
    const formalityLabel = formalityPct > 60 ? 'Formal' : formalityPct > 30 ? 'Neutral' : 'Casual';
    const concisenessLabel = concisenessPct > 60 ? 'Concise' : concisenessPct > 30 ? 'Moderate' : 'Wordy';
    const passiveLabel = passivePct > 30 ? 'High Passive' : passivePct > 15 ? 'Moderate' : 'Low Passive';
    const complexityLabel = complexityPct > 40 ? 'Complex' : complexityPct > 20 ? 'Moderate' : 'Simple';

    const tab = document.getElementById('tab-tone');
    tab.innerHTML = `
        <div class="result-card">
            <h4>Writing Style Analysis</h4>
            <p style="color:var(--text-secondary);margin-bottom:16px;font-size:13px;">Analysis based on ${totalWords} words, ${sentences.length} sentences</p>

            <div class="tone-indicator">
                <span class="tone-label">${formalityLabel}</span>
                <div class="tone-bar"><div class="tone-bar-fill formal" style="width:${formalityPct}%"></div></div>
                <span class="tone-value">${formalityPct}%</span>
            </div>
            <div style="font-size:11px;color:var(--text-muted);margin:-8px 0 14px 100px;">Formality</div>

            <div class="tone-indicator">
                <span class="tone-label">${concisenessLabel}</span>
                <div class="tone-bar"><div class="tone-bar-fill concise" style="width:${concisenessPct}%"></div></div>
                <span class="tone-value">${concisenessPct}%</span>
            </div>
            <div style="font-size:11px;color:var(--text-muted);margin:-8px 0 14px 100px;">Conciseness</div>

            <div class="tone-indicator">
                <span class="tone-label">${passiveLabel}</span>
                <div class="tone-bar"><div class="tone-bar-fill passive" style="width:${passivePct}%"></div></div>
                <span class="tone-value">${passivePct}%</span>
            </div>
            <div style="font-size:11px;color:var(--text-muted);margin:-8px 0 14px 100px;">Passive Voice Usage</div>

            <div class="tone-indicator">
                <span class="tone-label">${complexityLabel}</span>
                <div class="tone-bar"><div class="tone-bar-fill complex" style="width:${complexityPct}%"></div></div>
                <span class="tone-value">${complexityPct}%</span>
            </div>
            <div style="font-size:11px;color:var(--text-muted);margin:-8px 0 14px 100px;">Vocabulary Complexity</div>
        </div>
        <div class="result-card">
            <h4>Details</h4>
            <div class="detail-grid">
                <div class="detail-item"><div class="detail-label">Filler Words</div><div class="detail-value">${fillerCount} (${((fillerCount/totalWords)*100).toFixed(1)}%)</div></div>
                <div class="detail-item"><div class="detail-label">Avg Sent Length</div><div class="detail-value">${avgSentLen.toFixed(1)} words</div></div>
                <div class="detail-item"><div class="detail-label">Long Words (>6)</div><div class="detail-value">${longWords} (${((longWords/totalWords)*100).toFixed(1)}%)</div></div>
                <div class="detail-item"><div class="detail-label">Complex Words (>8)</div><div class="detail-value">${complexWords} (${((complexWords/totalWords)*100).toFixed(1)}%)</div></div>
                <div class="detail-item"><div class="detail-label">Passive Constructions</div><div class="detail-value">${passiveCount}</div></div>
                <div class="detail-item"><div class="detail-label">Est. Syllables</div><div class="detail-value">${syllableCount}</div></div>
            </div>
        </div>
    `;
    switchTab('tone');
    saveToHistory('Tone Analysis', text.substring(0, 100) + '...');
}

function copyText(btn) {
    const text = btn.parentElement.querySelector('.output-text')?.textContent || '';
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', () => {
    // Theme init
    const savedTheme = localStorage.getItem('plagiashield_theme');
    if (savedTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
        document.getElementById('theme-toggle').innerHTML = '<i class="fas fa-sun"></i>';
    }

    // History init
    renderHistory();

    // Load text from editor if coming back
    const editorText = localStorage.getItem('plagiashield_editor_text');
    if (editorText) {
        textInput.value = editorText;
        localStorage.removeItem('plagiashield_editor_text');
        updateWordCount();
        updateProgressBar();
        autoResizeTextarea();
        // Trigger format detection if format tab is active
        const formatTab = document.getElementById('tab-format');
        if (formatTab && formatTab.style.display !== 'none') {
            scheduleFormatDetect();
        }
    }

    updateWordCount();
    updateProgressBar();
    textInput.focus();
    const activeTab = document.querySelector('.tab.active');
    if (activeTab) setTimeout(() => updateTabIndicator(activeTab), 50);
    document.querySelectorAll('.btn').forEach(b => b.addEventListener('click', addRippleEffect));

    // Scroll-to-top
    const scrollBtn = document.getElementById('scroll-top-btn');
    if (scrollBtn) {
        window.addEventListener('scroll', () => {
            scrollBtn.classList.toggle('visible', window.scrollY > 400);
        });
    }

    // Drag-drop upload zone
    const zone = document.getElementById('upload-zone');
    if (zone) {
        zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
        zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) {
                const input = document.getElementById('file-input');
                const dt = new DataTransfer();
                dt.items.add(file);
                input.files = dt.files;
                handleFileUpload({ target: { files: [file] } });
            }
        });
    }
});
