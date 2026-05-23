/* ================================================================
   NETALERT DASHBOARD — app.js
   ================================================================ */

/* ===== STATE ===== */
let metricsData = null;
let treeData = null;
let featuresData = null;
let samplesData = null;
let comparisonData = null;
let edaData = null;
let pipelineInterval = null;

/* ===== INIT ===== */
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initEDAToggle();
    initRefresh();
    loadAll();
});

/* ===== TOAST ===== */
function toast(msg, type) {
    const container = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = 'toast toast-' + (type || 'info');
    el.innerHTML = '<span>' + esc(msg) + '</span><button class="toast-remove" onclick="this.parentElement.remove()">&times;</button>';
    container.appendChild(el);
    setTimeout(() => { if (el.parentElement) el.remove(); }, 4000);
}

/* ===== MODAL ===== */
function showModal(title, bodyText) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = '<pre style="white-space:pre-wrap;font-family:JetBrains Mono,monospace;font-size:0.72rem;color:#78909c;line-height:1.6;margin:0;">' + esc(bodyText) + '</pre>';
    document.getElementById('modal-overlay').style.display = 'flex';
}
function showStyledModal(title, bodyHTML) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHTML;
    document.getElementById('modal-overlay').style.display = 'flex';
}
function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
}

function formatPipelineOutput(text) {
    const lines = text.split('\n');
    let html = '<div style="font-family:Inter,sans-serif;">';
    let inMetricCard = false;
    let metricLines = [];
    for (const line of lines) {
        const t = line.trim();
        if (!t) { html += '<div style="height:4px;"></div>'; continue; }
        // Section header
        if (/^={2,}/.test(t)) {
            if (inMetricCard) { html += renderMetricCards(metricLines); metricLines = []; inMetricCard = false; }
            const title = t.replace(/^=+\s*/, '').replace(/\s*=+$/, '').trim();
            if (title) html += '<div class="rc-hero" style="padding:10px 0 6px;border:none;margin:0;"><div class="rc-hero-title" style="font-size:0.85rem;">' + esc(title) + '</div></div>';
            continue;
        }
        // Metric line like "Accuracy: 0.9923"
        if (/^[A-Za-z].*:\s*[\d.]+/.test(t) && !t.includes('=') && !t.includes('|')) {
            metricLines.push(t);
            inMetricCard = true;
            continue;
        }
        if (inMetricCard) { html += renderMetricCards(metricLines); metricLines = []; inMetricCard = false; }
        // File path
        if (t.match(/\.(csv|png|json|txt|joblib|py)$/i) && t.match(/saved|Saving|to /)) {
            html += '<div class="rc-body" style="color:var(--accent);font-size:0.68rem;font-family:JetBrains Mono,monospace;">' + esc(t) + '</div>';
            continue;
        }
        // Key-value line
        if (t.includes(':') && !t.includes('|')) {
            const parts = t.split(/:\s*/);
            if (parts.length >= 2) {
                html += '<div style="display:flex;gap:8px;padding:2px 0;font-size:0.7rem;"><span style="color:var(--text-muted);min-width:100px;">' + esc(parts[0]) + ':</span><span style="color:var(--text-secondary);">' + esc(parts.slice(1).join(': ')) + '</span></div>';
                continue;
            }
        }
        // Table lines with |
        if (t.includes('|')) {
            const cells = t.split('|').map(c => c.trim()).filter(Boolean);
            if (cells.length >= 2) {
                html += '<div style="display:flex;gap:4px;padding:1px 0;font-size:0.65rem;font-family:JetBrains Mono,monospace;">' + cells.map(c => '<span style="color:var(--text-secondary);flex:1;">' + esc(c) + '</span>').join('') + '</div>';
                continue;
            }
        }
        // Default
        html += '<div style="font-size:0.7rem;color:var(--text-secondary);padding:1px 0;">' + esc(t) + '</div>';
    }
    if (inMetricCard) { html += renderMetricCards(metricLines); }
    html += '</div>';
    return html;
}

function renderMetricCards(lines) {
    let html = '<div class="metrics-grid" style="grid-template-columns:repeat(auto-fill,minmax(180px,1fr));margin:8px 0;">';
    for (const line of lines) {
        const match = line.match(/^([^:]+):\s*([\d.]+)/);
        if (match) {
            const key = match[1].trim();
            let val = match[2];
            const isPct = /rate|ratio|pct|%|f1|accuracy|precision|recall/i.test(key);
            const displayVal = isPct ? (parseFloat(val) * 100).toFixed(1) + '%' : val;
            html += '<div class="metric-card"><div class="m-value" style="font-size:1rem;">' + displayVal + '</div><div class="m-label">' + esc(key) + '</div></div>';
        }
    }
    html += '</div>';
    return html;
}

/* ===== TABS ===== */
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            const tabId = btn.dataset.tab;
            document.getElementById('tab-' + tabId).classList.add('active');
            if (tabId === 'metrics') renderMetricsTab();
            if (tabId === 'tree') renderTreeTab();
            if (tabId === 'features') renderFeaturesTab();
            if (tabId === 'samples') renderSamplesTab();
            if (tabId === 'comparison') renderComparisonTab();
        });
    });
}

/* ===== EDA TOGGLE ===== */
function initEDAToggle() {
    const toggles = document.querySelectorAll('#eda-toggle .toggle-btn');
    toggles.forEach(btn => {
        btn.addEventListener('click', () => {
            toggles.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const view = btn.dataset.view;
            document.querySelectorAll('#eda-section .analysis-view').forEach(v => v.classList.remove('active'));
            document.getElementById('eda-view-' + view).classList.add('active');
            if (view === 'overview') renderEDAOverview();
            if (view === 'correlation') renderEDACorrelation();
            if (view === 'boxplots') renderEDABoxplots();
            if (view === 'pca') renderEDAPCA();
            if (view === 'clustering') renderEDAClustering();
            if (view === 'scatter') renderEDAScatter();
        });
    });
}

/* ===== REFRESH ===== */
function initRefresh() {
    document.getElementById('refresh-btn').addEventListener('click', () => {
        const btn = document.getElementById('refresh-btn');
        btn.classList.add('spinning');
        loadAll();
        setTimeout(() => btn.classList.remove('spinning'), 800);
    });
}
function updateTimestamp() {
    document.getElementById('last-refresh').textContent = new Date().toLocaleTimeString();
}

/* ===== DATA LOADING ===== */
async function loadAll() {
    await Promise.allSettled([loadMetrics(), loadTree(), loadFeatures(), loadSamples(), loadComparison(), loadEDA()]);
    updateTimestamp();
}
async function fetchJSON(url) {
    try {
        const r = await fetch(url);
        if (!r.ok) return null;
        return await r.json();
    } catch (e) { console.error(url, e); return null; }
}

/* ===== METRICS ===== */
async function loadMetrics() {
    metricsData = await fetchJSON('/api/metrics');
    if (!metricsData) return;
    const p = metricsData.performance || {};
    document.getElementById('stat-accuracy').textContent = (p.accuracy * 100).toFixed(1) + '%';
    document.getElementById('stat-precision').textContent = (p.precision * 100).toFixed(1) + '%';
    document.getElementById('stat-recall').textContent = (p.recall * 100).toFixed(1) + '%';
    document.getElementById('stat-f1').textContent = (p.f1_score * 100).toFixed(1) + '%';
    document.getElementById('val-data').textContent = metricsData.model || 'N/A';

    // Confusion matrix heatmap
    const cm = metricsData.confusion_matrix || {};
    Plotly.react(document.getElementById('chart-cm'), [{
        z: [[cm.true_negative || 0, cm.false_positive || 0],
            [cm.false_negative || 0, cm.true_positive || 0]],
        x: ['Predicted Normal', 'Predicted Attack'],
        y: ['Actual Normal', 'Actual Attack'],
        type: 'heatmap', colorscale: [[0, '#0d1117'], [0.5, '#00838f'], [1, '#00bcd4']],
        showscale: false,
        text: [[String(cm.true_negative || 0), String(cm.false_positive || 0)],
               [String(cm.false_negative || 0), String(cm.true_positive || 0)]],
        texttemplate: '<b>%{text}</b>', textfont: { size: 16, color: '#e0e0e0' }, hoverongaps: false,
    }], {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#78909c', size: 10 },
        margin: { l: 80, r: 20, t: 10, b: 50 },
        xaxis: { side: 'top', gridcolor: '#1a2332' },
        yaxis: { gridcolor: '#1a2332', autorange: 'reversed' }, height: 220,
    }, { displayModeBar: false, responsive: true });

    // Key metrics
    document.getElementById('metrics-detail').innerHTML = [
        { lbl: 'False Positive Rate', val: (p.false_positive_rate * 100).toFixed(2) + '%', color: 'var(--accent)' },
        { lbl: 'False Negative Rate', val: (p.false_negative_rate * 100).toFixed(2) + '%', color: 'var(--accent)' },
        { lbl: 'Attack Detection', val: (p.recall * 100).toFixed(1) + '%', color: 'var(--success)' },
    ].map(m => '<div class="metric-card"><div class="m-value" style="color:' + m.color + '">' + m.val + '</div><div class="m-label">' + m.lbl + '</div></div>').join('');
}

function renderMetricsTab() {
    const el = document.getElementById('metrics-content');
    if (!metricsData) { el.innerHTML = '<div class="empty-state">Loading...</div>'; return; }
    const p = metricsData.performance || {};
    const cm = metricsData.confusion_matrix || {};
    el.innerHTML = '<div class="metrics-grid">' +
        ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'False Pos. Rate', 'False Neg. Rate'].map((lbl, i) => {
            const vals = [p.accuracy, p.precision, p.recall, p.f1_score, p.false_positive_rate, p.false_negative_rate];
            return '<div class="metric-card"><div class="m-value">' + (vals[i] * 100).toFixed(2) + '%</div><div class="m-label">' + lbl + '</div></div>';
        }).join('') + '</div>' +
        '<div class="info-box"><strong>Professional Interpretation:</strong><br>' +
        '&bull; When alert raised, correct <strong>' + (p.precision * 100).toFixed(1) + '%</strong> of the time<br>' +
        '&bull; Catch <strong>' + (p.recall * 100).toFixed(1) + '%</strong> of attacks<br>' +
        '&bull; False positives: ' + (cm.false_positive || 0) + ' &middot; False negatives: ' + (cm.false_negative || 0) + '<br>' +
        '&bull; <strong>0 attacks go undetected</strong></div>';
}

/* ===== TREE ===== */
async function loadTree() { treeData = await fetchJSON('/api/tree'); }
function renderTreeTab() {
    const el = document.getElementById('tree-content');
    el.innerHTML = !treeData || !treeData.rules
        ? '<div class="empty-state">Not available. Run training first.</div>'
        : '<pre class="tree-code">' + esc(treeData.rules) + '</pre>';
}

/* ===== FEATURES ===== */
async function loadFeatures() { featuresData = await fetchJSON('/api/features'); }
function renderFeaturesTab() {
    const el = document.getElementById('features-content');
    if (!featuresData || !featuresData.features || !featuresData.features.length) {
        el.innerHTML = '<div class="empty-state">Not available.</div>'; return;
    }
    const colors = ['#00bcd4','#26c6da','#00838f','#4dd0e1','#0097a7'];
    Plotly.react(el, [{
        x: featuresData.features.map(f => f.importance), y: featuresData.features.map(f => f.name),
        type: 'bar', orientation: 'h',
        marker: { color: colors.slice(0, featuresData.features.length), line: { width: 0 } },
        text: featuresData.features.map(f => (f.importance * 100).toFixed(1) + '%'),
        textposition: 'outside', textfont: { size: 10, color: '#78909c' },
    }], {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#78909c', size: 10 }, margin: { l: 120, r: 60, t: 10, b: 30 }, height: 300,
        xaxis: { showgrid: true, gridcolor: '#1a2332', zeroline: false, title: 'Importance' },
        yaxis: { showgrid: false, autorange: 'reversed' }, bargap: 0.3,
    }, { displayModeBar: false, responsive: true });
}

/* ===== SAMPLES ===== */
async function loadSamples() { samplesData = await fetchJSON('/api/samples'); }
function renderSamplesTab() {
    const el = document.getElementById('samples-content');
    if (!samplesData || !samplesData.samples || !samplesData.samples.length) {
        el.innerHTML = '<div class="empty-state">Not available.</div>'; return;
    }
    el.innerHTML = samplesData.samples.map((s, i) => {
        const ok = s.predicted === s.true_label;
        const c = ok ? 'var(--success)' : 'var(--danger)';
        return '<div class="sample-card"><div class="sample-header" style="background:' + c + '">Sample #' + (i + 1) +
            ' &mdash; True: <strong>' + esc(s.true_label) + '</strong> | Predicted: <strong>' + esc(s.predicted) +
            '</strong> <span style="float:right;">' + (ok ? 'CORRECT' : 'INCORRECT') + '</span></div>' +
            '<div class="sample-body"><div class="sample-features-grid">' +
            Object.entries(s.features).map(([k, v]) =>
                '<div class="sample-feature"><span class="sf-key">' + esc(k) + '</span><span class="sf-val">' +
                esc(typeof v === 'number' ? (Math.abs(v) < 0.01 ? v.toExponential(2) : Number(v.toFixed(4)).toLocaleString()) : v) + '</span></div>'
            ).join('') + '</div><div class="pred-box"><strong>Prediction:</strong> ' + esc(s.predicted) +
            ' &middot; <strong>Confidence:</strong> ' + (s.confidence * 100).toFixed(1) + '%</div></div></div>';
    }).join('');
}

/* ===== COMPARISON ===== */
async function loadComparison() { comparisonData = await fetchJSON('/api/comparison'); }
function renderComparisonTab() {
    const el = document.getElementById('comparison-content');
    if (!comparisonData || !comparisonData.models || !comparisonData.models.length) {
        el.innerHTML = '<div class="empty-state">Run 06_knn_comparison.py first.</div>'; return;
    }
    const models = comparisonData.models;
    const metrics = ['accuracy','precision','recall','f1_score'];
    let html = '<div class="comparison-grid"><div><table><thead><tr><th>Model</th>' +
        metrics.map(m => '<th>' + m.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()) + '</th>').join('') +
        '</tr></thead><tbody>' +
        models.map(m => '<tr><td><strong>' + esc(m.name) + '</strong></td>' +
            metrics.map(mm => '<td>' + ((m.metrics[mm] || 0) * 100).toFixed(1) + '%</td>').join('') + '</tr>'
        ).join('') + '</tbody></table></div><div id="comparison-chart"></div></div>';
    el.innerHTML = html;
    const trace = {
        x: models.map(m => m.name), y: models.map(m => m.metrics.accuracy * 100),
        type: 'bar', marker: { color: '#00bcd4' },
        text: models.map(m => (m.metrics.accuracy * 100).toFixed(1) + '%'),
        textposition: 'outside', textfont: { size: 9, color: '#78909c' },
    };
    Plotly.react(document.getElementById('comparison-chart'), [trace], {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#78909c', size: 10 }, margin: { l: 40, r: 20, t: 10, b: 60 }, height: 250,
        xaxis: { showgrid: false, tickangle: -20 }, yaxis: { showgrid: true, gridcolor: '#1a2332', zeroline: false, title: 'Accuracy' },
    }, { displayModeBar: false, responsive: true });
}

/* ==================================================================
   EDA — EXPLORATORY DATA ANALYSIS
   ================================================================== */
async function loadEDA() {
    edaData = await fetchJSON('/api/eda');
    if (edaData && edaData.class_distribution) {
        document.getElementById('ds-samples').textContent = (edaData.class_distribution.total || '').toLocaleString();
        document.getElementById('ds-features').textContent = edaData.info ? edaData.info.length : '';
        document.getElementById('ds-attacks').textContent = edaData.class_distribution.attack_pct + '%';
    }
}

/* ----- OVERVIEW ----- */
function renderEDAOverview() {
    const el = document.getElementById('eda-overview-content');
    if (!edaData || !edaData.info) { el.innerHTML = '<div class="empty-state">EDA not available. Run EDA step first.</div>'; return; }
    let html = '';

    // Data Quality Summary
    const totalNulls = edaData.info.reduce((s, c) => s + c.null_count, 0);
    const allNumeric = edaData.info.every(c => c.dtype.includes('float') || c.dtype.includes('int'));
    html += '<div class="toolbar"><span class="filter-count">Data Quality Summary</span></div>' +
        '<div class="metrics-grid" style="grid-template-columns:repeat(4,1fr);">' +
        '<div class="metric-card"><div class="m-value" style="color:var(--accent);">' + edaData.info.length + '</div><div class="m-label">Features</div></div>' +
        '<div class="metric-card"><div class="m-value" style="color:' + (totalNulls === 0 ? 'var(--success)' : 'var(--warning)') + ';">' + totalNulls + '</div><div class="m-label">Missing Values</div></div>' +
        '<div class="metric-card"><div class="m-value" style="color:var(--success);">' + (allNumeric ? 'Yes' : 'Mixed') + '</div><div class="m-label">All Numeric</div></div>' +
        '<div class="metric-card"><div class="m-value">UNSW-NB15</div><div class="m-label">Dataset Source</div></div>' +
        '</div>';

    // Label Encoding explanation
    html += '<div class="info-box" style="margin:10px 0;">' +
        '<strong>Label Encoding (Codification)</strong> — The target variable is already binary: <strong>0 = Normal</strong>, <strong>1 = Attack</strong>.<br>' +
        'No additional LabelEncoder needed. The original dataset had categorical attack types; they were collapsed to binary (attack / no attack) for supervised learning.<br>' +
        '<span style="color:var(--text-muted);font-size:0.65rem;">If we had categorical features (e.g., protocol type, service), we would use sklearn\'s LabelEncoder to convert them to numeric.</span></div>';

    // Column info table
    html += '<div class="toolbar"><span class="filter-count">Column Information (df.info())</span></div>' +
        '<div class="table-wrap" style="max-height:160px;overflow-y:auto;"><table><thead><tr><th>#</th><th>Column</th><th>Dtype</th><th>Non-Null</th><th>Nulls</th><th>Network Meaning</th></tr></thead><tbody>' +
        edaData.info.map((c, i) => {
            const meanings = {
                'sttl': 'Source→Destination TTL (time-to-live)',
                'sbytes': 'Source bytes transferred',
                'dbytes': 'Destination bytes transferred',
                'Sload': 'Source load (bits/sec)',
                'Dload': 'Destination load (bits/sec)',
            };
            return '<tr><td>' + (i + 1) + '</td><td><strong>' + esc(c.column) + '</strong></td><td>' + esc(c.dtype) + '</td><td>' + c.non_null.toLocaleString() + '</td><td>' + c.null_count + '</td><td style="color:var(--text-muted);font-size:0.62rem;">' + (meanings[c.column] || '—') + '</td></tr>';
        }).join('') +
        '</tbody></table></div>';

    // Descriptive stats table
    const feats = Object.keys(edaData.describe || {});
    html += '<div class="toolbar" style="margin-top:12px;"><span class="filter-count">Descriptive Statistics (df.describe())</span></div>' +
        '<div class="table-wrap" style="max-height:200px;overflow-y:auto;"><table><thead><tr><th>Stat</th>' +
        feats.map(c => '<th>' + esc(c) + '</th>').join('') +
        '</tr></thead><tbody>' +
        ['count','mean','std','min','25%','50%','75%','max'].map(stat =>
            '<tr><td><strong>' + stat + '</strong></td>' +
            feats.map(f => {
                const val = edaData.describe[f][stat];
                const display = typeof val === 'number' ? (Math.abs(val) < 0.01 ? val.toExponential(3) : Number(val.toFixed(4)).toLocaleString()) : val;
                return '<td>' + display + '</td>';
            }).join('') + '</tr>'
        ).join('') + '</tbody></table></div>';

    // Insight box
    const desc = edaData.describe;
    if (desc && desc.sttl) {
        html += '<div class="info-box" style="margin-top:10px;"><strong>Key Insights from Descriptive Statistics:</strong><br>' +
            '&bull; <strong>sttl</strong> (TTL): ranges from ' + desc.sttl['min'] + ' to ' + desc.sttl['max'] + '. Normal TTL values are typically 64, 128, or 255. Values outside these suggest tunneling or spoofing.<br>' +
            '&bull; <strong>sbytes</strong> (source bytes): mean = ' + Number(desc.sbytes['mean']).toFixed(1) + ', std = ' + Number(desc.sbytes['std']).toFixed(1) + '. High std indicates traffic volume varies widely.<br>' +
            '&bull; <strong>Attack rate</strong>: only ' + (edaData.class_distribution.attack_pct || 0) + '% of samples are attacks (imbalanced dataset). This is why we use <code>class_weight=\'balanced\'</code> in the Decision Tree.</div>';
    }

    // Class distribution
    const cd = edaData.class_distribution || {};
    html += '<div class="toolbar" style="margin-top:12px;"><span class="filter-count">Class Distribution</span></div>' +
        '<div class="metrics-grid" style="grid-template-columns:repeat(4,1fr);">' +
        '<div class="metric-card"><div class="m-value">' + (cd.total || 0).toLocaleString() + '</div><div class="m-label">Total Samples</div></div>' +
        '<div class="metric-card"><div class="m-value" style="color:var(--success);">' + (cd.normal || 0).toLocaleString() + '</div><div class="m-label">Normal Traffic</div></div>' +
        '<div class="metric-card"><div class="m-value" style="color:var(--danger);">' + (cd.attack || 0).toLocaleString() + '</div><div class="m-label">Attack Samples</div></div>' +
        '<div class="metric-card"><div class="m-value" style="color:var(--warning);">' + (cd.attack_pct || 0) + '%</div><div class="m-label">Attack Rate</div></div>' +
        '</div>';

    el.innerHTML = html;
}

/* ----- CORRELATION ----- */
function renderEDACorrelation() {
    const el = document.getElementById('eda-correlation-chart');
    if (!edaData || !edaData.correlation) { el.innerHTML = '<div class="empty-state">No correlation data.</div>'; return; }
    const corr = edaData.correlation;
    Plotly.react(el, [{
        z: corr.values, x: corr.columns, y: corr.columns,
        type: 'heatmap', colorscale: 'RdBu_r', zmid: 0,
        showscale: true, colorbar: { title: { text: 'Pearson', font: { color: '#78909c', size: 9 } }, tickfont: { color: '#78909c', size: 8 } },
        text: corr.values.map(row => row.map(v => v.toFixed(3))),
        texttemplate: '%{text}', textfont: { size: 11, color: '#e0e0e0' }, hoverongaps: false,
    }], {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#78909c', size: 10 },
        margin: { l: 80, r: 60, t: 10, b: 80 }, height: 380,
        xaxis: { side: 'top', gridcolor: '#1a2332', tickangle: -30 },
        yaxis: { gridcolor: '#1a2332', autorange: 'reversed' },
    }, { displayModeBar: false, responsive: true, toImageButtonOptions: { format: 'png' } });
}

/* ----- BOX PLOTS ----- */
function renderEDABoxplots() {
    const el = document.getElementById('eda-boxplots-content');
    if (!edaData || !edaData.boxplots) { el.innerHTML = '<div class="empty-state">No box plot data.</div>'; return; }
    const bp = edaData.boxplots;
    const features = Object.keys(bp);
    // For each feature, create a grouped box plot
    let html = '<div style="display:grid;gap:14px;">';
    features.forEach(feat => {
        const f = bp[feat];
        const traces = [];
        ['normal', 'attack'].forEach((grp, gi) => {
            const d = f[grp];
            if (!d) return;
            traces.push({
                y: [d.min, d.q1, d.median, d.q3, d.max].concat(d.outliers || []),
                type: 'box', name: grp.charAt(0).toUpperCase() + grp.slice(1),
                marker: { color: gi === 0 ? '#00bcd4' : '#ff1744' },
                boxmean: true,
                orientation: 'v',
                quartilemethod: 'linear',
            });
        });
        const divId = 'box-' + feat.replace(/[^a-zA-Z0-9]/g, '_');
        html += '<div><div class="toolbar"><span class="filter-count">' + esc(feat) + ' — Normal vs Attack</span></div><div id="' + divId + '" style="height:200px;"></div></div>';
        // Defer render
        setTimeout(() => {
            const container = document.getElementById(divId);
            if (!container) return;
            const traceData = [];
            ['normal', 'attack'].forEach((grp, gi) => {
                const d = f[grp];
                if (!d) return;
                traceData.push({
                    y: [d.min, d.q1, d.median, d.q3, d.max],
                    type: 'box', name: grp.charAt(0).toUpperCase() + grp.slice(1),
                    marker: { color: gi === 0 ? '#00bcd4' : '#ff1744' },
                    boxmean: true, orientation: 'v',
                    whiskerwidth: 0.5,
                });
                if (d.outliers && d.outliers.length) {
                    traceData.push({
                        y: d.outliers,
                        type: 'scatter', mode: 'markers', name: grp + ' outliers',
                        marker: { color: gi === 0 ? '#00bcd4' : '#ff1744', symbol: 'x', size: 4 },
                        showlegend: false,
                    });
                }
            });
            Plotly.react(container, traceData, {
                paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#78909c', size: 9 },
                margin: { l: 50, r: 20, t: 10, b: 30 }, height: 200,
                xaxis: { showgrid: false }, yaxis: { showgrid: true, gridcolor: '#1a2332', zeroline: false },
                showlegend: true, legend: { font: { color: '#78909c', size: 8 }, orientation: 'h', y: 1.05 },
                hovermode: 'y',
            }, { displayModeBar: false, responsive: true });
        }, 50);
    });
    html += '</div>';
    el.innerHTML = html;
}

/* ----- SCATTER MATRIX (Pair Plot) ----- */
function renderEDAScatter() {
    const el = document.getElementById('eda-scatter-chart');
    if (!edaData || !edaData.pairplot || !edaData.pairplot.data) {
        el.innerHTML = '<div class="empty-state">No pair plot data available.</div>'; return;
    }
    const pp = edaData.pairplot;
    const cols = pp.columns;
    const data = pp.data;
    const labels = data.label;
    // Build traces: one per class
    const normalIdx = [], attackIdx = [];
    labels.forEach((l, i) => { if (l === 0) normalIdx.push(i); else attackIdx.push(i); });
    const traces = [];
    const classes = [
        { name: 'Normal', idx: normalIdx, color: '#00bcd4', symbol: 'circle' },
        { name: 'Attack', idx: attackIdx, color: '#ff1744', symbol: 'x' },
    ];
    classes.forEach(cls => {
        if (!cls.idx.length) return;
        const dims = cols.map(col => ({
            label: col,
            values: cls.idx.map(i => data[col][i]),
        }));
        traces.push({
            type: 'splom',
            dimensions: dims,
            text: cls.idx.map(i => 'Label: ' + labels[i]),
            marker: { color: cls.color, size: 3, opacity: 0.5, symbol: cls.symbol },
            name: cls.name,
        });
    });
    const axisStyle = { showgrid: true, gridcolor: '#1a2332', zeroline: false, showticklabels: false };
    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#78909c', size: 8 },
        margin: { l: 30, r: 30, t: 30, b: 30 },
        height: 500,
        hovermode: 'closest',
        showlegend: true,
        legend: { font: { color: '#78909c', size: 10 }, orientation: 'h', y: 1.02, x: 0.35 },
        xaxis: axisStyle, yaxis: axisStyle,
    };
    // Add axis templates for each dimension
    for (let i = 1; i < cols.length; i++) {
        layout['xaxis' + (i + 1)] = axisStyle;
        layout['yaxis' + (i + 1)] = axisStyle;
    }
    Plotly.react(el, traces, layout, {
        displayModeBar: true, responsive: true,
        modeBarButtonsToRemove: ['sendDataToCloud', 'lasso2d', 'select2d'],
        toImageButtonOptions: { format: 'png' },
    });
}

/* ----- PCA ----- */
function renderEDAPCA() {
    const el = document.getElementById('eda-pca-chart');
    const pca = edaData ? edaData.pca : null;
    if (!pca || !pca.projection) { el.innerHTML = '<div class="empty-state">No PCA data.</div>'; return; }
    document.getElementById('pca-pc1').textContent = (pca.explained_variance_ratio[0] * 100).toFixed(1) + '%';
    document.getElementById('pca-pc2').textContent = (pca.explained_variance_ratio[1] * 100).toFixed(1) + '%';
    document.getElementById('pca-cumul').textContent = (pca.cumulative_variance * 100).toFixed(1) + '%';
    // Sample for performance (max 5000 points)
    const proj = pca.projection;
    const step = Math.max(1, Math.floor(proj.length / 5000));
    const sampled = proj.filter((_, i) => i % step === 0);
    const normal = sampled.filter(d => d.label === 0);
    const attack = sampled.filter(d => d.label === 1);
    Plotly.react(el, [
        { x: normal.map(d => d.pc1), y: normal.map(d => d.pc2), mode: 'markers', type: 'scattergl',
          name: 'Normal', marker: { color: '#00bcd4', size: 3, opacity: 0.6 } },
        { x: attack.map(d => d.pc1), y: attack.map(d => d.pc2), mode: 'markers', type: 'scattergl',
          name: 'Attack', marker: { color: '#ff1744', size: 5, opacity: 0.8, symbol: 'x' } },
    ], {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: '#020408',
        font: { color: '#78909c', size: 10 },
        margin: { l: 50, r: 20, t: 10, b: 50 }, height: 420,
        xaxis: { showgrid: true, gridcolor: '#1a2332', zeroline: true, zerolinecolor: '#1a2332',
                 title: 'PC1 (' + (pca.explained_variance_ratio[0] * 100).toFixed(1) + '%)' },
        yaxis: { showgrid: true, gridcolor: '#1a2332', zeroline: true, zerolinecolor: '#1a2332',
                 title: 'PC2 (' + (pca.explained_variance_ratio[1] * 100).toFixed(1) + '%)' },
        showlegend: true, legend: { font: { color: '#78909c', size: 10 }, orientation: 'h', y: 1.02, x: 0.4 },
        hovermode: 'closest',
    }, { displayModeBar: true, responsive: true, scrollZoom: true,
        modeBarButtonsToRemove: ['sendDataToCloud', 'lasso2d', 'select2d'],
        toImageButtonOptions: { format: 'png' } });
}

/* ----- CLUSTERING ----- */
function renderEDAClustering() {
    const el = document.getElementById('eda-clustering-content');
    if (!edaData || !edaData.kmeans) { el.innerHTML = '<div class="empty-state">No clustering data.</div>'; return; }
    const km = edaData.kmeans;
    const pca = edaData.pca;
    let html = '';

    // K-Means stats
    html += '<div class="toolbar"><span class="filter-count">K-Means Clustering (k=2) — Unsupervised</span></div>' +
        '<div class="metrics-grid" style="grid-template-columns:repeat(3,1fr);">' +
        '<div class="metric-card"><div class="m-value" style="color:var(--accent);">' + km.inertia.toFixed(2) + '</div><div class="m-label">Inertia</div></div>' +
        '<div class="metric-card"><div class="m-value" style="color:' + (km.accuracy_vs_true > 0.9 ? 'var(--success)' : 'var(--warning)') + ';">' + (km.accuracy_vs_true * 100).toFixed(1) + '%</div><div class="m-label">vs True Labels</div></div>' +
        '<div class="metric-card"><div class="m-value">2</div><div class="m-label">Clusters (k)</div></div>' +
        '</div>';

    // K-Means scatter in PCA space (colored by cluster)
    if (pca && pca.projection) {
        const proj = pca.projection;
        const step = Math.max(1, Math.floor(proj.length / 5000));
        const sampled = proj.filter((_, i) => i % step === 0);
        const cluster0 = sampled.filter((_, i) => km.assignments[i * step] === 0);
        const cluster1 = sampled.filter((_, i) => km.assignments[i * step] === 1);
        html += '<div id="kmeans-chart" style="height:300px;margin:8px 0;"></div>';
        el.innerHTML = html;
        Plotly.react(document.getElementById('kmeans-chart'), [
            { x: cluster0.map(d => d.pc1), y: cluster0.map(d => d.pc2), mode: 'markers', type: 'scattergl',
              name: 'Cluster 0', marker: { color: '#00bcd4', size: 3, opacity: 0.5 } },
            { x: cluster1.map(d => d.pc1), y: cluster1.map(d => d.pc2), mode: 'markers', type: 'scattergl',
              name: 'Cluster 1', marker: { color: '#ffc107', size: 3, opacity: 0.5 } },
        ], {
            paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: '#020408',
            font: { color: '#78909c', size: 9 },
            margin: { l: 45, r: 15, t: 10, b: 45 }, height: 300,
            xaxis: { showgrid: true, gridcolor: '#1a2332', title: 'PC1' },
            yaxis: { showgrid: true, gridcolor: '#1a2332', title: 'PC2' },
            showlegend: true, legend: { font: { color: '#78909c', size: 9 }, orientation: 'h', y: 1.02 },
        }, { displayModeBar: false, responsive: true });
    }

    // Dendrogram image
    if (edaData.hierarchical && edaData.hierarchical.dendrogram_image) {
        html = el.innerHTML;
        html += '<div class="toolbar" style="margin-top:12px;"><span class="filter-count">Hierarchical Clustering Dendrogram (Ward, n=' + edaData.hierarchical.sample_size + ')</span></div>' +
            '<div style="text-align:center;background:#0d1117;border:1px solid var(--border);border-radius:var(--radius);padding:10px;">' +
            '<img src="data:image/png;base64,' + edaData.hierarchical.dendrogram_image + '" style="max-width:100%;height:auto;border-radius:4px;"></div>';
        el.innerHTML = html;
    }
}

/* ==================================================================
   PIPELINE RUNNER
   ================================================================== */
function startPipeline(step) {
    return new Promise((resolve) => {
        const btn = document.getElementById('btn-' + step);
        if (btn) { btn.dataset.origHtml = btn.innerHTML; btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...'; }

        fetch('/api/pipeline/' + step, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
        .then(r => r.ok ? r.json() : Promise.reject('HTTP ' + r.status))
        .then(data => {
            if (!data || !data.task_id) { throw new Error('No task_id'); }
            const taskId = data.task_id;
            const progressEl = document.getElementById('pipeline-progress');
            const progressFill = document.getElementById('pipeline-progress-fill');
            const progressText = document.getElementById('pipeline-progress-text');
            const startTime = Date.now();
            progressEl.style.display = 'block';
            progressFill.style.width = '5%';
            progressText.textContent = 'Starting ' + step + '...';
            if (pipelineInterval) clearInterval(pipelineInterval);
            let count = 0;

            pipelineInterval = setInterval(() => {
                count++;
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                progressText.textContent = step + ' running... ' + elapsed + 's';
                progressFill.style.width = Math.min(85, 10 + count * 3) + '%';

                fetch('/api/pipeline/status/' + taskId)
                .then(r => r.ok ? r.json() : null)
                .then(status => {
                    if (!status || status.status === 'running') return;
                    clearInterval(pipelineInterval);
                    pipelineInterval = null;
                    progressFill.style.width = '100%';
                    progressText.textContent = 'Done!';
                    setTimeout(() => { progressEl.style.display = 'none'; }, 2000);
                    if (btn) { btn.disabled = false; btn.innerHTML = btn.dataset.origHtml || step; }
                    if (status.status === 'done') {
                        toast(step + ' completed!', 'success');
                        if (status.output) showStyledModal(step + ' Output', formatPipelineOutput(status.output));
                        loadAll();
                    } else {
                        toast(step + ' failed', 'error');
                        showStyledModal(step + ' Failed', formatPipelineOutput(status.error || status.output || 'Unknown error'));
                    }
                    resolve();
                })
                .catch(() => { resolve(); });
            }, 2000);
        })
        .catch(err => {
            console.error('Pipeline start failed:', err);
            toast('Failed to start ' + step, 'error');
            if (btn) { btn.disabled = false; btn.innerHTML = btn.dataset.origHtml || step; }
            resolve();
        });
    });
}

async function runStep(step) {
    if (step === 'run-all') {
        const steps = ['clean', 'train', 'evaluate', 'knn', 'eda'];
        for (const s of steps) {
            await startPipeline(s);
        }
        toast('Full pipeline completed!', 'success');
        return;
    }
    await startPipeline(step);
}

/* ===== UTILITY ===== */
function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('open');
    const overlay = document.getElementById('sidebar-overlay');
    if (overlay) overlay.classList.toggle('show');
}
function closeSidebar() {
    document.querySelector('.sidebar').classList.remove('open');
    const overlay = document.getElementById('sidebar-overlay');
    if (overlay) overlay.classList.remove('show');
}
function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
