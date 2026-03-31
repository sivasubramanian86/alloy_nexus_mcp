/**
 * QuerySage — Frontend Application Logic
 * Handles API calls, UI state, table rendering, and CSV export.
 */

// ── Config ────────────────────────────────────────────────────────────────
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8080'
  : 'https://querysage-agent-967518492968.us-central1.run.app';

// ── DOM refs ──────────────────────────────────────────────────────────────
const nlInput       = document.getElementById('nl-input');
const btnQuery      = document.getElementById('btn-query');
const resultsPanel  = document.getElementById('results-panel');
const loadingState  = document.getElementById('loading-state');
const errorState    = document.getElementById('error-state');
const errorMessage  = document.getElementById('error-message');
const resultContent = document.getElementById('result-content');
const sourceBadge   = document.getElementById('source-badge');
const latencyBadge  = document.getElementById('latency-badge');
const rowCountBadge = document.getElementById('row-count-badge');
const aiSummary     = document.getElementById('ai-summary');
const generatedSql  = document.getElementById('generated-sql');
const tableHead     = document.getElementById('table-head');
const tableBody     = document.getElementById('table-body');
const btnExport     = document.getElementById('btn-export');
const statusDot     = document.getElementById('status-dot');
const exampleChips  = document.getElementById('example-chips');
const kpiGrid       = document.getElementById('kpi-grid');

// ── Global state ──────────────────────────────────────────────────────────
let lastRows = [];
let lastQuery = '';

// ── Utility: show / hide panels ───────────────────────────────────────────
function showPanel(panel) {
  [loadingState, errorState, resultContent].forEach(el => el.classList.add('hidden'));
  panel.classList.remove('hidden');
  resultsPanel.classList.remove('hidden');
}

function resetPanels() {
  resultsPanel.classList.add('hidden');
  [loadingState, errorState, resultContent].forEach(el => el.classList.add('hidden'));
}

// ── API calls ─────────────────────────────────────────────────────────────
async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    statusDot.className = `status-dot ${data.alloydb_ok ? 'ok' : 'warn'}`;
    statusDot.title = `AlloyDB: ${data.alloydb_ok ? 'Connected' : 'Degraded'} · ${data.environment}`;
  } catch {
    statusDot.className = 'status-dot err';
    statusDot.title = 'API unreachable';
  }
}

async function fetchExamples() {
  try {
    const res = await fetch(`${API_BASE}/queries/examples`);
    const data = await res.json();
    renderChips(data.examples || []);
  } catch {
    // Silent fail — chips are optional
  }
}

async function fetchDashboard() {
  try {
    const res = await fetch(`${API_BASE}/inventory/dashboard`);
    const kpis = await res.json();
    animateKpi('val-total-drugs',    kpis.total_drugs          ?? '—');
    animateKpi('val-below-reorder',  kpis.below_reorder        ?? '—');
    animateKpi('val-pending-orders', kpis.pending_orders        ?? '—');
    animateKpi('val-controlled',     kpis.controlled_substances ?? '—');
    animateKpi('val-expiring',       kpis.expiring_soon         ?? '—');
  } catch {
    // Use placeholder dashes — no crash
  }
}

async function executeQuery(question) {
  if (!question.trim()) return;

  lastQuery = question;
  btnQuery.disabled = true;
  showPanel(loadingState);

  try {
    const res = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    renderResults(data);
  } catch (err) {
    errorMessage.textContent = err.message || 'Failed to reach the QuerySage API.';
    showPanel(errorState);
  } finally {
    btnQuery.disabled = false;
  }
}

// ── Render functions ──────────────────────────────────────────────────────

function animateKpi(id, target) {
  const el = document.getElementById(id);
  if (!el || target === '—') { if (el) el.textContent = target; return; }
  const end = parseInt(target, 10);
  if (isNaN(end)) { el.textContent = target; return; }
  const duration = 800;
  const start = performance.now();
  const step = (ts) => {
    const progress = Math.min((ts - start) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);  // ease-out-cubic
    el.textContent = Math.round(ease * end);
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function renderChips(examples) {
  exampleChips.innerHTML = '';
  examples.forEach(ex => {
    const chip = document.createElement('button');
    chip.className = 'chip';
    chip.textContent = ex.question.length > 60 ? ex.question.slice(0, 58) + '…' : ex.question;
    chip.title = ex.question;
    chip.setAttribute('data-category', ex.category);
    chip.addEventListener('click', () => {
      nlInput.value = ex.question;
      nlInput.focus();
    });
    exampleChips.appendChild(chip);
  });
}

function renderResults(data) {
  lastRows = data.rows || [];

  // ── Meta row ──
  const sourceKey = (data.source || 'no_match').replace(/_/g, ' ');
  sourceBadge.textContent = data.source === 'alloydb_ai' ? 'AlloyDB AI' : data.source === 'curated_fallback' ? 'Curated SQL' : 'No Match';
  sourceBadge.className   = `source-badge ${data.source}`;
  latencyBadge.textContent = `${data.latency_ms} ms`;
  rowCountBadge.textContent = `${data.row_count} row${data.row_count !== 1 ? 's' : ''}`;

  // ── AI Summary ──
  aiSummary.innerHTML = formatSummary(data.summary || 'No summary available.');

  // ── SQL ──
  generatedSql.textContent = data.generated_sql
    ? formatSql(data.generated_sql)
    : '-- No SQL generated (curated fallback or no-match)';

  // ── Table ──
  renderTable(lastRows);

  showPanel(resultContent);
}

function formatSummary(text) {
  // Convert **bold** markdown to <strong>, bullet points to <li>
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^[\-\*] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
}

function formatSql(sql) {
  return sql
    .replace(/\bSELECT\b/g, 'SELECT')
    .replace(/\bFROM\b/g, '\nFROM')
    .replace(/\bJOIN\b/g, '\n  JOIN')
    .replace(/\bWHERE\b/g, '\nWHERE')
    .replace(/\bGROUP BY\b/g, '\nGROUP BY')
    .replace(/\bORDER BY\b/g, '\nORDER BY')
    .replace(/\bLIMIT\b/g, '\nLIMIT')
    .trim();
}

function renderTable(rows) {
  tableHead.innerHTML = '';
  tableBody.innerHTML = '';

  if (!rows || rows.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 99;
    td.textContent = 'No results returned.';
    td.style.cssText = 'text-align:center;color:var(--c-text-faint);padding:2rem';
    tr.appendChild(td);
    tableBody.appendChild(tr);
    return;
  }

  // Header
  const headRow = document.createElement('tr');
  Object.keys(rows[0]).forEach(col => {
    const th = document.createElement('th');
    th.textContent = col.replace(/_/g, ' ');
    headRow.appendChild(th);
  });
  tableHead.appendChild(headRow);

  // Body
  rows.forEach(row => {
    const tr = document.createElement('tr');
    Object.entries(row).forEach(([key, val]) => {
      const td = document.createElement('td');
      const formatted = formatCell(key, val);
      td.innerHTML = formatted.html;
      td.className = formatted.cls;
      tr.appendChild(td);
    });
    tableBody.appendChild(tr);
  });
}

function formatCell(key, val) {
  if (val === null || val === undefined) return { html: '<span style="color:var(--c-text-faint)">—</span>', cls: '' };

  const lk = key.toLowerCase();
  const sval = String(val);

  // Numeric formatting
  if (typeof val === 'number') {
    if (lk.includes('usd') || lk.includes('cost') || lk.includes('value') || lk.includes('price')) {
      return { html: `$${parseFloat(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, cls: 'cell-code' };
    }
    if (lk.includes('shortage') && val > 0) return { html: sval, cls: 'cell-alert' };
    if (lk === 'days_to_expiry' && val < 30) return { html: sval, cls: 'cell-alert' };
    if (lk === 'days_to_expiry' && val < 60) return { html: sval, cls: 'cell-warn' };
    return { html: val.toLocaleString(), cls: '' };
  }

  // Boolean
  if (typeof val === 'boolean') {
    return val
      ? { html: '<span style="color:var(--c-red);font-weight:600">YES</span>', cls: '' }
      : { html: '<span style="color:var(--c-text-faint)">No</span>', cls: '' };
  }

  // Dates
  if (lk.includes('date') || lk.includes('expiry')) {
    try {
      const d = new Date(val);
      const today = new Date();
      const diffDays = Math.ceil((d - today) / 86400000);
      const formatted2 = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
      if (diffDays < 30)  return { html: formatted2, cls: 'cell-alert' };
      if (diffDays < 60)  return { html: formatted2, cls: 'cell-warn' };
    } catch {}
  }

  // Status badges
  if (lk === 'status') {
    const map = { DELIVERED: 'ok', PENDING: 'warn', PARTIAL: 'warn', CANCELLED: 'alert' };
    const cls = map[sval.toUpperCase()] || '';
    return { html: sval, cls: `cell-${cls}` };
  }

  // Controlled
  if (lk === 'is_controlled' && sval === 'true') {
    return { html: '<span style="color:var(--c-red);font-weight:600">CONTROLLED</span>', cls: '' };
  }

  return { html: sval, cls: '' };
}

// ── CSV Export ────────────────────────────────────────────────────────────
function exportCsv() {
  if (!lastRows.length) return;
  const cols = Object.keys(lastRows[0]);
  const csvContent = [
    cols.join(','),
    ...lastRows.map(row =>
      cols.map(c => {
        const v = row[c];
        if (v === null || v === undefined) return '';
        const s = String(v).replace(/"/g, '""');
        return s.includes(',') || s.includes('"') || s.includes('\n') ? `"${s}"` : s;
      }).join(',')
    ),
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `querysage_${Date.now()}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── Event listeners ───────────────────────────────────────────────────────
btnQuery.addEventListener('click', () => executeQuery(nlInput.value.trim()));

nlInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    executeQuery(nlInput.value.trim());
  }
});

btnExport.addEventListener('click', exportCsv);

// ── Init ──────────────────────────────────────────────────────────────────
(async () => {
  await Promise.allSettled([fetchHealth(), fetchExamples(), fetchDashboard()]);
  // Auto-refresh health every 30s
  setInterval(fetchHealth, 30_000);
})();
