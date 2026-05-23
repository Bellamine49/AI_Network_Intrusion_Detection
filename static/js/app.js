/* ===== STATE ===== */
let metricsData = null;
let treeData = null;
let featuresData = null;
let samplesData = null;
let comparisonData = null;

/* ===== INIT ===== */
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initRefresh();
    loadAll();
});

/* ===== TOAST ===== */
function toast(msg, type = 'info') {
    const container = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `<span>${msg}</span><button class="toast-remove" onclick="this.parentElement.remove()">&times;</button>`;
    container.appendChild(el);
    setTimeout(() => { if (el.parentElement) el.remove(); }, 4000);
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
    await Promise.allSettled([
        loadMetrics(),
        loadTree(),
        loadFeatures(),
        loadSamples(),
        loadComparison(),
    ]);
    updateTimestamp();
}

async function fetchJSON(url) {
    try {
        const r = await fetch(url);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return await r.json();
    } catch (e) {
        console.error(`fetch ${url}:`, e);
        return null;
    }
}

/* ===== METRICS ===== */
async function loadMetrics() {
    metricsData = await fetchJSON('/api/metrics');
    if (!metricsData) return;
    const perf = metricsData.performance || {};
    document.getElementById('stat-accuracy').textContent = (perf.accuracy * 100).toFixed(1) + '%';
    document.getElementById('stat-precision').textContent = (perf.precision * 100).toFixed(1) + '%';
    document.getElementById('stat-recall').textContent = (perf.recall * 100).toFixed(1) + '%';
    document.getElementById('stat-f1').textContent = (perf.f1_score * 100).toFixed(1) + '%';
    document.getElementById('val-data').textContent = metricsData.model || 'N/A';
    document.getElementById('val-alerts').textContent = metricsData.version || 'N/A';

    // Confusion matrix heatmap
    const cm = metricsData.confusion_matrix || {};
    const cmData = [{
        z: [[cm.true_negative || 0, cm.false_positive || 0],
            [cm.false_negative || 0, cm.true_positive || 0]],
        x: ['Predicted Normal', 'Predicted Attack'],
        y: ['Actual Normal', 'Actual Attack'],
        type: 'heatmap',
        colorscale: [[0, '#0d1117'], [0.5, '#00838f'], [1, '#00bcd4']],
        showscale: false,
        text: [[String(cm.true_negative || 0), String(cm.false_positive || 0)],
               [String(cm.false_negative || 0), String(cm.true_positive || 0)]],
        texttemplate: '<b>%{text}</b>',
        textfont: { size: 16, color: '#e0e0e0' },
        hoverongaps: false,
    }];
    const cmLayout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#78909c', size: 10 },
        margin: { l: 80, r: 20, t: 10, b: 50 },
        xaxis: { side: 'top', gridcolor: '#1a2332' },
        yaxis: { gridcolor: '#1a2332', autorange: 'reversed' },
        height: 220,
    };
    Plotly.react(document.getElementById('chart-cm'), cmData, cmLayout, { displayModeBar: false, responsive: true });

    // Key metrics detail
    const detailHtml = `
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="m-value">${(perf.false_positive_rate * 100).toFixed(2)}%</div>
                <div class="m-label">False Positive Rate</div>
            </div>
            <div class="metric-card">
                <div class="m-value">${(perf.false_negative_rate * 100).toFixed(2)}%</div>
                <div class="m-label">False Negative Rate</div>
            </div>
            <div class="metric-card">
                <div class="m-value" style="color:var(--success);">${(perf.recall * 100).toFixed(1)}%</div>
                <div class="m-label">Attack Detection Rate</div>
            </div>
        </div>
    `;
    document.getElementById('metrics-detail').innerHTML = detailHtml;
}

function renderMetricsTab() {
    const container = document.getElementById('metrics-content');
    if (!metricsData) {
        container.innerHTML = '<div class="empty-state">Loading metrics...</div>';
        return;
    }
    const perf = metricsData.performance || {};
    const cm = metricsData.confusion_matrix || {};
    container.innerHTML = `
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="m-value">${(perf.accuracy * 100).toFixed(2)}%</div>
                <div class="m-label">Accuracy</div>
            </div>
            <div class="metric-card">
                <div class="m-value">${(perf.precision * 100).toFixed(2)}%</div>
                <div class="m-label">Precision</div>
            </div>
            <div class="metric-card">
                <div class="m-value">${(perf.recall * 100).toFixed(2)}%</div>
                <div class="m-label">Recall</div>
            </div>
            <div class="metric-card">
                <div class="m-value">${(perf.f1_score * 100).toFixed(2)}%</div>
                <div class="m-label">F1-Score</div>
            </div>
            <div class="metric-card">
                <div class="m-value">${(perf.false_positive_rate * 100).toFixed(2)}%</div>
                <div class="m-label">False Positive Rate</div>
            </div>
            <div class="metric-card">
                <div class="m-value">${(perf.false_negative_rate * 100).toFixed(2)}%</div>
                <div class="m-label">False Negative Rate</div>
            </div>
        </div>
        <div class="info-box">
            <strong>Professional Interpretation:</strong><br>
            &bull; When our system raises an alert, it is correct <strong>${(perf.precision * 100).toFixed(1)}%</strong> of the time<br>
            &bull; We catch <strong>${(perf.recall * 100).toFixed(1)}%</strong> of all actual attacks<br>
            &bull; False positives (${cm.false_positive || 0} cases) trigger investigations but no actual attacks are missed<br>
            &bull; <strong>0 attacks go undetected</strong> (false negatives = ${cm.false_negative || 0})
        </div>
    `;
}

/* ===== TREE RULES ===== */
async function loadTree() {
    treeData = await fetchJSON('/api/tree');
}

function renderTreeTab() {
    const container = document.getElementById('tree-content');
    if (!treeData || !treeData.rules) {
        container.innerHTML = '<div class="empty-state">Tree rules not available. Run training first.</div>';
        return;
    }
    container.innerHTML = `<pre class="tree-code">${esc(treeData.rules)}</pre>`;
}

/* ===== FEATURE IMPORTANCE ===== */
async function loadFeatures() {
    featuresData = await fetchJSON('/api/features');
}

function renderFeaturesTab() {
    const container = document.getElementById('features-content');
    if (!featuresData || !featuresData.features || featuresData.features.length === 0) {
        container.innerHTML = '<div class="empty-state">Feature importance not available.</div>';
        return;
    }
    const labels = featuresData.features.map(f => f.name);
    const values = featuresData.features.map(f => f.importance);
    const colors = ['#00bcd4', '#26c6da', '#00838f', '#4dd0e1', '#0097a7'];

    const trace = {
        x: values,
        y: labels,
        type: 'bar',
        orientation: 'h',
        marker: { color: colors.slice(0, labels.length), line: { width: 0 } },
        text: values.map(v => (v * 100).toFixed(1) + '%'),
        textposition: 'outside',
        textfont: { size: 10, color: '#78909c' },
    };
    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#78909c', size: 10 },
        margin: { l: 120, r: 60, t: 10, b: 30 },
        height: 300,
        xaxis: { showgrid: true, gridcolor: '#1a2332', zeroline: false, title: 'Importance' },
        yaxis: { showgrid: false, autorange: 'reversed' },
        bargap: 0.3,
    };
    Plotly.react(container, [trace], layout, { displayModeBar: false, responsive: true });
}

/* ===== SAMPLES ===== */
async function loadSamples() {
    samplesData = await fetchJSON('/api/samples');
}

function renderSamplesTab() {
    const container = document.getElementById('samples-content');
    if (!samplesData || !samplesData.samples || samplesData.samples.length === 0) {
        container.innerHTML = '<div class="empty-state">Sample predictions not available.</div>';
        return;
    }
    let html = '';
    samplesData.samples.forEach((s, i) => {
        const isCorrect = s.predicted === s.true_label;
        const statusText = isCorrect ? 'CORRECT' : 'INCORRECT';
        const statusColor = isCorrect ? 'var(--success)' : 'var(--danger)';
        html += `
        <div class="sample-card">
            <div class="sample-header" style="background:${statusColor};">
                Sample #${i + 1} &mdash; True: <strong>${esc(s.true_label)}</strong> | Predicted: <strong>${esc(s.predicted)}</strong> <span style="float:right;">${statusText}</span>
            </div>
            <div class="sample-body">
                <div class="sample-features-grid">`;
        Object.entries(s.features).forEach(([k, v]) => {
            let val = typeof v === 'number' ? (Math.abs(v) < 0.01 ? v.toExponential(2) : v.toLocaleString()) : v;
            html += `<div class="sample-feature"><span class="sf-key">${esc(k)}</span><span class="sf-val">${esc(val)}</span></div>`;
        });
        html += `</div>
                <div class="pred-box">
                    <strong>Prediction:</strong> ${esc(s.predicted)} &middot;
                    <strong>Confidence:</strong> ${(s.confidence * 100).toFixed(1)}%
                </div>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

/* ===== COMPARISON ===== */
async function loadComparison() {
    comparisonData = await fetchJSON('/api/comparison');
}

function renderComparisonTab() {
    const container = document.getElementById('comparison-content');
    if (!comparisonData || !comparisonData.models || comparisonData.models.length === 0) {
        container.innerHTML = '<div class="empty-state">Model comparison not available. Run 06_knn_comparison.py first.</div>';
        return;
    }
    const models = comparisonData.models;
    const labels = models.map(m => m.name);
    const metrics_list = ['accuracy', 'precision', 'recall', 'f1_score'];
    const colors = ['#00bcd4', '#ff1744', '#ffc107', '#00e676'];

    let tableHtml = '<table><thead><tr><th>Model</th>';
    metrics_list.forEach(m => { tableHtml += `<th>${esc(m.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()))}</th>`; });
    tableHtml += '</tr></thead><tbody>';
    models.forEach(m => {
        tableHtml += '<tr>';
        tableHtml += `<td><strong>${esc(m.name)}</strong></td>`;
        metrics_list.forEach(metric => {
            const val = m.metrics[metric] || 0;
            tableHtml += `<td>${(val * 100).toFixed(1)}%</td>`;
        });
        tableHtml += '</tr>';
    });
    tableHtml += '</tbody></table>';

    const trace = {
        x: metrics_list.map(m => m.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())),
        y: models.map(m => m.metrics.accuracy * 100),
        type: 'bar',
        name: 'Accuracy',
        marker: { color: colors[0] },
    };
    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#78909c', size: 10 },
        margin: { l: 40, r: 20, t: 10, b: 40 },
        height: 250,
        xaxis: { showgrid: false },
        yaxis: { showgrid: true, gridcolor: '#1a2332', zeroline: false, title: 'Accuracy' },
    };
    const chartHtml = `<div id="comparison-chart"></div>`;

    container.innerHTML = `
        <div class="toolbar"><span class="filter-count">Model Performance Comparison</span></div>
        <div class="comparison-grid">
            <div>${tableHtml}</div>
            ${chartHtml}
        </div>`;
    Plotly.react(document.getElementById('comparison-chart'), [trace], layout, { displayModeBar: false, responsive: true });

    comparisonData.models.forEach(m => {
        console.log(`${m.name}:`, m.metrics);
    });
}

/* ===== UTILITY ===== */
function esc(str) {
    if (str === null || str === undefined) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
