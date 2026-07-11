const editor = document.getElementById('editor');
const wordCountEl = document.getElementById('word-count');
const charCountEl = document.getElementById('char-count');

// Load theme
const savedTheme = localStorage.getItem('plagiashield_theme');
if (savedTheme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
}

// Load initial text from localStorage (passed from main page)
const savedText = localStorage.getItem('plagiashield_editor_text');
if (savedText) {
    editor.innerHTML = savedText.replace(/\n/g, '<br>');
    localStorage.removeItem('plagiashield_editor_text');
}

function updateStats() {
    const text = editor.innerText || '';
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    const chars = text.length;
    wordCountEl.textContent = words + ' words';
    charCountEl.textContent = chars + ' chars';
}

editor.addEventListener('input', updateStats);
editor.addEventListener('keyup', updateStats);
updateStats();

// Toolbar commands
function execCmd(command, value = null) {
    document.execCommand(command, false, value);
    editor.focus();
    updateActiveStates();
}

function execCmdWithArg(command, arg) {
    document.execCommand(command, false, arg);
    editor.focus();
    updateActiveStates();
}

// Font size
document.getElementById('font-size').addEventListener('change', function() {
    execCmd('fontSize', this.value);
});

// Font name
document.getElementById('font-family').addEventListener('change', function() {
    execCmd('fontName', this.value);
});

// Headings
document.getElementById('heading-select').addEventListener('change', function() {
    const val = this.value;
    if (val === 'p') {
        execCmd('formatBlock', '<p>');
    } else {
        execCmd('formatBlock', '<' + val + '>');
    }
    this.value = '';
});

// Text color
document.getElementById('text-color').addEventListener('input', function() {
    execCmd('foreColor', this.value);
});

// Highlight color
document.getElementById('bg-color').addEventListener('input', function() {
    execCmd('hiliteColor', this.value);
});

// Links
function insertLink() {
    const url = prompt('Enter URL:', 'https://');
    if (url) execCmd('createLink', url);
}

// Images
function insertImage() {
    const url = prompt('Enter image URL:', 'https://');
    if (url) execCmd('insertImage', url);
}

// Horizontal rule
function insertHR() {
    execCmd('insertHorizontalRule');
}

// Clear formatting
function clearFormatting() {
    execCmd('removeFormat');
}

// Undo / Redo
function undoAction() { execCmd('undo'); }
function redoAction() { execCmd('redo'); }

// Indent / Outdent
function indentAction() { execCmd('indent'); }
function outdentAction() { execCmd('outdent'); }

// Code block
function insertCode() {
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    const range = sel.getRangeAt(0);
    const pre = document.createElement('pre');
    const code = document.createElement('code');
    code.textContent = range.extractContents().textContent || 'code';
    pre.appendChild(code);
    range.insertNode(pre);
    editor.focus();
}

// Blockquote
function insertQuote() {
    execCmd('formatBlock', '<blockquote>');
}

// Update active states for toggle buttons
function updateActiveStates() {
    const cmds = ['bold', 'italic', 'underline', 'strikeThrough', 'insertUnorderedList', 'insertOrderedList', 'justifyLeft', 'justifyCenter', 'justifyRight', 'justifyFull'];
    cmds.forEach(cmd => {
        const btn = document.querySelector(`[data-cmd="${cmd}"]`);
        if (btn) {
            btn.classList.toggle('active', document.queryCommandState(cmd));
        }
    });
}

editor.addEventListener('mouseup', updateActiveStates);
editor.addEventListener('keyup', updateActiveStates);

// Keyboard shortcuts
editor.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        downloadHTML();
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        setTimeout(updateActiveStates, 0);
    }
});

// Export functions
function downloadHTML() {
    const content = editor.innerHTML;
    const style = document.querySelector('link[href*="editor.css"]') ? '<link rel="stylesheet" href="/static/editor.css">' : '';
    const doc = `<!DOCTYPE html><html><head><meta charset="UTF-8">${style}</head><body>${content}</body></html>`;
    const blob = new Blob([doc], { type: 'text/html' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'document.html';
    a.click();
    URL.revokeObjectURL(a.href);
}

function downloadText() {
    const text = editor.innerText;
    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'document.txt';
    a.click();
    URL.revokeObjectURL(a.href);
}

function copyHTML() {
    const html = editor.innerHTML;
    navigator.clipboard.writeText(html).then(() => {
        showEditorToast('HTML copied to clipboard', 'success');
    }).catch(() => {
        showEditorToast('Failed to copy', 'error');
    });
}

function copyText() {
    const text = editor.innerText;
    navigator.clipboard.writeText(text).then(() => {
        showEditorToast('Text copied to clipboard', 'success');
    }).catch(() => {
        showEditorToast('Failed to copy', 'error');
    });
}

function clearEditor() {
    if (confirm('Clear all content?')) {
        editor.innerHTML = '';
        updateStats();
        editor.focus();
    }
}

function goBack() {
    // Save formatted content back to main page
    const html = editor.innerHTML;
    localStorage.setItem('plagiashield_editor_text', html);
    window.location.href = '/';
}

// --- Table Insertion ---
function insertTable() {
    const overlay = document.createElement('div');
    overlay.className = 'table-dialog-overlay';
    overlay.innerHTML = `
        <div class="table-dialog">
            <h3><i class="fas fa-table"></i> Insert Table</h3>
            <div class="table-form">
                <label>Rows <input type="number" id="tableRows" value="3" min="1" max="20"></label>
                <label>Columns <input type="number" id="tableCols" value="3" min="1" max="20"></label>
                <label style="margin-top:4px;">
                    <span style="font-size:11px;">Header row</span>
                    <input type="checkbox" id="tableHeader" checked style="width:auto;">
                </label>
            </div>
            <div class="table-actions">
                <button class="btn btn-secondary" onclick="this.closest('.table-dialog-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="createTableFromDialog(this)">Insert</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
    editor.focus();
}

function createTableFromDialog(btn) {
    const dialog = btn.closest('.table-dialog');
    const rows = parseInt(document.getElementById('tableRows').value) || 3;
    const cols = parseInt(document.getElementById('tableCols').value) || 3;
    const hasHeader = document.getElementById('tableHeader').checked;

    let html = '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;margin:8px 0;border:1px solid var(--border);">';
    for (let r = 0; r < rows; r++) {
        html += '<tr>';
        for (let c = 0; c < cols; c++) {
            const tag = r === 0 && hasHeader ? 'th' : 'td';
            const style = r === 0 && hasHeader ? ' style="background:var(--bg-input);font-weight:600;text-align:center;border:1px solid var(--border);padding:8px;"' :
                                                ' style="border:1px solid var(--border);padding:8px;"';
            html += '<' + tag + style + '> </' + tag + '>';
        }
        html += '</tr>';
    }
    html += '</table>';

    editor.focus();
    document.execCommand('insertHTML', false, html);

    // Close dialog
    dialog.closest('.table-dialog-overlay').remove();
    updateStats();
}

// --- Find & Replace ---
let findReplaceVisible = false;
function toggleFindReplace() {
    const bar = document.getElementById('findReplaceBar');
    findReplaceVisible = !findReplaceVisible;
    bar.style.display = findReplaceVisible ? 'flex' : 'none';
    if (findReplaceVisible) {
        document.getElementById('findInput').focus();
        document.getElementById('findInput').value = '';
        document.getElementById('replaceInput').value = '';
        document.getElementById('findCount').textContent = '';
        clearHighlights();
    }
}

function findInEditor() {
    const query = document.getElementById('findInput').value;
    clearHighlights();
    if (!query) { document.getElementById('findCount').textContent = ''; return; }

    const body = editor;
    const treeWalker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT, null, false);
    const textNodes = [];
    while (treeWalker.nextNode()) textNodes.push(treeWalker.referenceNode);

    let count = 0;
    for (const node of textNodes) {
        const idx = node.textContent.toLowerCase().indexOf(query.toLowerCase());
        if (idx === -1) continue;
        const range = document.createRange();
        range.setStart(node, idx);
        range.setEnd(node, idx + query.length);

        const mark = document.createElement('span');
        mark.className = 'find-replace-highlight';
        range.surroundContents(mark);
        count++;
    }
    document.getElementById('findCount').textContent = count + ' match' + (count !== 1 ? 'es' : '');

    // highlight first match as current
    const first = body.querySelector('.find-replace-highlight');
    if (first) { first.className = 'find-replace-current'; }
}

function replaceOne() {
    const query = document.getElementById('findInput').value;
    const replace = document.getElementById('replaceInput').value;
    if (!query) return;

    const current = editor.querySelector('.find-replace-current');
    if (current) {
        current.replaceWith(document.createTextNode(replace));
        findInEditor();
    } else {
        findInEditor();
    }
}

function replaceAll() {
    const query = document.getElementById('findInput').value;
    const replace = document.getElementById('replaceInput').value;
    if (!query) return;

    const body = editor;
    const treeWalker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT, null, false);
    const textNodes = [];
    while (treeWalker.nextNode()) textNodes.push(treeWalker.referenceNode);

    for (const node of textNodes) {
        const lower = node.textContent.toLowerCase();
        const qLower = query.toLowerCase();
        if (lower.includes(qLower)) {
            const regex = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
            node.textContent = node.textContent.replace(regex, replace);
        }
    }
    document.getElementById('findCount').textContent = '';
    editor.normalize();
    updateStats();
    showEditorToast('Replaced all occurrences', 'success');
}

function clearHighlights() {
    const highlights = editor.querySelectorAll('.find-replace-highlight, .find-replace-current');
    for (const el of highlights) {
        const parent = el.parentNode;
        if (parent) {
            parent.replaceChild(document.createTextNode(el.textContent), el);
            parent.normalize();
        }
    }
}

// Toast notifications for editor
function showEditorToast(message, type = 'info') {
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
    }, 3000);
}

// ===== Format Tools =====
let editorFormatDetectTimeout = null;

editor.addEventListener('input', () => { updateStats(); scheduleEditorFormatDetect(); });
editor.addEventListener('keyup', () => { updateStats(); scheduleEditorFormatDetect(); });

function scheduleEditorFormatDetect() {
    if (editorFormatDetectTimeout) clearTimeout(editorFormatDetectTimeout);
    editorFormatDetectTimeout = setTimeout(autoDetectEditorFormat, 500);
}

async function autoDetectEditorFormat() {
    const text = editor.innerText || '';
    const badge = document.getElementById('editor-format-detect');
    if (!badge) return;
    if (!text.trim()) { badge.innerHTML = ''; return; }
    try {
        const resp = await apiCallEditor('/api/format/detect', { text });
        const d = resp.detected_structure;
        if (d.type === 'empty') { badge.innerHTML = ''; return; }
        badge.innerHTML = '<i class="fas fa-list-tree"></i> ' + escapeHtml(d.label);
    } catch (e) { /* silent */ }
}

async function editorFormat(formatType) {
    const text = editor.innerText || '';
    if (!text.trim()) { showEditorToast('No text to format', 'error'); return; }

    const overlay = document.createElement('div');
    overlay.className = 'editor-format-overlay';
    overlay.innerHTML = '<div class="editor-format-spinner"><i class="fas fa-spinner fa-spin"></i> Formatting...</div>';
    document.body.appendChild(overlay);

    try {
        const result = await apiCallEditor('/api/format', { text, format_type: formatType });
        // Replace editor content with formatted HTML
        editor.innerHTML = result.formatted;
        updateStats();
        showEditorToast('Formatted as ' + formatType.replace(/-/g, ' '), 'success');
        // Re-run detection
        autoDetectEditorFormat();
    } catch (err) {
        showEditorToast('Format error: ' + err.message, 'error');
    } finally {
        overlay.remove();
    }
}

function apiCallEditor(endpoint, data) {
    return fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(r => {
        if (!r.ok) throw new Error('Request failed: ' + r.status);
        return r.json();
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
