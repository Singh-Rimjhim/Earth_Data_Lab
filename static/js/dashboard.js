/**
 * Earth Data Lab — Interactive Dashboard & Assistant Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    datasetId: 'nasa_gistemp',
    records: [],
    metadata: {},
    summary: {},
    trend: {},
    insights: {},
    chart: null,
    currentPage: 1,
    rowsPerPage: 15,
    filterStartYear: null,
    filterEndYear: null,
    tableSearchTerm: ''
  };

  // DOM Elements
  const datasetSelect = document.getElementById('datasetSelect');
  const datasetBadge = document.getElementById('datasetBadge');
  const badgeText = document.getElementById('badgeText');
  const syntheticAlert = document.getElementById('syntheticAlert');

  // Metadata Banner Elements
  const metaSource = document.getElementById('metaSource');
  const metaBaseline = document.getElementById('metaBaseline');
  const metaUnits = document.getElementById('metaUnits');
  const metaPeriod = document.getElementById('metaPeriod');

  // KPI Elements
  const kpiLatestAnomaly = document.getElementById('kpiLatestAnomaly');
  const kpiLatestYear = document.getElementById('kpiLatestYear');
  const kpiWarmingRate = document.getElementById('kpiWarmingRate');
  const kpiTrendStatus = document.getElementById('kpiTrendStatus');
  const kpiWarmestYear = document.getElementById('kpiWarmestYear');
  const kpiWarmestAnomaly = document.getElementById('kpiWarmestAnomaly');
  const kpiRSquared = document.getElementById('kpiRSquared');
  const kpiTotalRecords = document.getElementById('kpiTotalRecords');

  // Chart & Filter Elements
  const chartCanvas = document.getElementById('temperatureChart');
  const chartLoading = document.getElementById('chartLoading');
  const startYearInput = document.getElementById('startYearInput');
  const endYearInput = document.getElementById('endYearInput');
  const toggleSmoothing = document.getElementById('toggleSmoothing');
  const toggleTrendline = document.getElementById('toggleTrendline');
  const applyFilterBtn = document.getElementById('applyFilterBtn');
  const resetFilterBtn = document.getElementById('resetFilterBtn');
  const exportCsvBtn = document.getElementById('exportCsvBtn');

  // Assistant Elements
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  const sendSpinner = document.getElementById('sendSpinner');
  const chatHistory = document.getElementById('chatHistory');
  const promptChips = document.querySelectorAll('.chip-btn');

  // Table Elements
  const tableBody = document.getElementById('tableBody');
  const tableSearchInput = document.getElementById('tableSearchInput');
  const tableRecordCount = document.getElementById('tableRecordCount');
  const prevPageBtn = document.getElementById('prevPageBtn');
  const nextPageBtn = document.getElementById('nextPageBtn');
  const pageIndicator = document.getElementById('pageIndicator');
  const insightsContainer = document.getElementById('insightsContainer');
  const limitationsList = document.getElementById('limitationsList');

  // --- 1. DATA FETCHING ---
  async function loadDashboardData() {
    chartLoading.classList.remove('hidden');
    try {
      let url = `/api/data?dataset_id=${encodeURIComponent(state.datasetId)}`;
      if (state.filterStartYear !== null && state.filterEndYear !== null) {
        url += `&start_year=${state.filterStartYear}&end_year=${state.filterEndYear}`;
      }

      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      state.records = data.records || [];
      state.metadata = data.metadata || {};
      state.summary = data.summary || {};
      state.trend = data.trend || {};
      state.insights = data.insights || {};

      updateHeaderAndMetadata();
      updateKPIs();
      renderChart();
      renderResearchInsights();
      renderTable();
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      showAssistantMessage(
        'System Notice',
        `⚠️ Error loading dataset: ${err.message}. Please check connection or select another dataset.`
      );
    } finally {
      chartLoading.classList.add('hidden');
    }
  }

  // --- 2. HEADER & METADATA ---
  function updateHeaderAndMetadata() {
    const meta = state.metadata;
    const isSynth = meta.is_synthetic || false;

    // Badge
    if (isSynth) {
      datasetBadge.className = 'badge badge-synthetic';
      badgeText.textContent = `${meta.name || 'Synthetic Demo'} (SIMULATED)`;
      syntheticAlert.classList.remove('hidden');
    } else {
      datasetBadge.className = 'badge badge-observed';
      badgeText.textContent = `${meta.name || 'Observed'} (OBSERVED)`;
      syntheticAlert.classList.add('hidden');
    }

    // Metadata Banner
    metaSource.textContent = meta.source_name || 'N/A';
    metaBaseline.textContent = meta.baseline_period || 'N/A';
    metaUnits.textContent = meta.units || 'Degrees Celsius (°C)';
    metaPeriod.textContent = `${meta.query_start_year || meta.min_available_year}–${meta.query_end_year || meta.max_available_year} (${state.records.length} records)`;

    // Year inputs min/max bounds
    if (state.filterStartYear === null) {
      startYearInput.min = meta.min_available_year;
      startYearInput.max = meta.max_available_year;
      startYearInput.value = meta.min_available_year;

      endYearInput.min = meta.min_available_year;
      endYearInput.max = meta.max_available_year;
      endYearInput.value = meta.max_available_year;
    }

    // Limitations list
    if (meta.limitations && meta.limitations.length > 0) {
      limitationsList.innerHTML = meta.limitations.map(lim => `<li>${lim}</li>`).join('');
    }
  }

  // --- 3. SUMMARY KPIS ---
  function updateKPIs() {
    const sum = state.summary;
    const tr = state.trend;
    const records = state.records;

    if (!records || records.length === 0) return;

    // Latest Record
    const latest = records[records.length - 1];
    const sign = latest.annual_anomaly > 0 ? '+' : '';
    kpiLatestAnomaly.textContent = `${sign}${latest.annual_anomaly.toFixed(2)} °C`;
    kpiLatestAnomaly.style.color = latest.annual_anomaly >= 0 ? '#dc2626' : '#2563eb';
    kpiLatestYear.textContent = `Year ${latest.year} (±${latest.uncertainty || 0.05}°C unc)`;

    // Warming Rate
    const rateSign = tr.warming_rate_per_decade > 0 ? '+' : '';
    kpiWarmingRate.textContent = `${rateSign}${(tr.warming_rate_per_decade || 0).toFixed(3)} °C/dec`;
    kpiWarmingRate.style.color = tr.warming_rate_per_decade > 0 ? '#dc2626' : '#2563eb';
    kpiTrendStatus.textContent = tr.trend_direction || 'OLS Trend';

    // Warmest Year
    kpiWarmestYear.textContent = sum.max_year || '--';
    const maxSign = sum.max_anomaly > 0 ? '+' : '';
    kpiWarmestAnomaly.textContent = `Peak: ${maxSign}${(sum.max_anomaly || 0).toFixed(2)} °C`;

    // Variance Explained (R2)
    kpiRSquared.textContent = tr.r_squared !== undefined ? tr.r_squared.toFixed(3) : '--';
    kpiTotalRecords.textContent = `${records.length} Annual Observations`;
  }

  // --- 4. CHART.JS RENDERING ---
  function renderChart() {
    if (!chartCanvas) return;
    const ctx = chartCanvas.getContext('2d');

    const years = state.records.map(r => r.year);
    const anomalies = state.records.map(r => r.annual_anomaly);
    const smooths = state.records.map(r => r.five_year_smooth);

    // Compute linear regression trend points for the chart
    const tr = state.trend;
    let trendlineData = [];
    if (years.length >= 2 && tr.slope_per_year !== undefined) {
      const slope = tr.slope_per_year;
      const intercept = tr.intercept;
      trendlineData = years.map(yr => (slope * yr + intercept));
    }

    // Color bars: warm red for positive anomaly, cool blue for negative anomaly
    const barColors = anomalies.map(val => val >= 0 ? 'rgba(220, 38, 38, 0.75)' : 'rgba(37, 99, 235, 0.75)');
    const barBorders = anomalies.map(val => val >= 0 ? '#b91c1c' : '#1d4ed8');

    if (state.chart) {
      state.chart.destroy();
    }

    const datasets = [
      {
        type: 'bar',
        label: 'Annual Anomaly (°C)',
        data: anomalies,
        backgroundColor: barColors,
        borderColor: barBorders,
        borderWidth: 1,
        borderRadius: 2,
        order: 3
      }
    ];

    if (toggleSmoothing.checked) {
      datasets.push({
        type: 'line',
        label: '5-Year Smooth (°C)',
        data: smooths,
        borderColor: '#991b1b',
        borderWidth: 2.5,
        pointRadius: 0,
        fill: false,
        tension: 0.25,
        order: 1
      });
    }

    if (toggleTrendline.checked && trendlineData.length > 0) {
      datasets.push({
        type: 'line',
        label: `Linear Trend (+${(tr.warming_rate_per_decade || 0).toFixed(3)}°C/dec)`,
        data: trendlineData,
        borderColor: '#059669',
        borderWidth: 2,
        borderDash: [6, 4],
        pointRadius: 0,
        fill: false,
        order: 2
      });
    }

    state.chart = new Chart(ctx, {
      data: {
        labels: years,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                const val = context.parsed.y;
                const sign = val > 0 ? '+' : '';
                return ` ${context.dataset.label}: ${sign}${val.toFixed(3)} °C`;
              }
            }
          },
          legend: {
            position: 'top',
            labels: {
              boxWidth: 14,
              font: { size: 12, family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto' }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { maxTicksLimit: 14 }
          },
          y: {
            title: {
              display: true,
              text: 'Temperature Anomaly (°C)',
              font: { weight: 'bold', size: 12 }
            },
            grid: {
              color: function(context) {
                if (context.tick.value === 0) {
                  return '#0f172a'; // Bold zero baseline
                }
                return '#e2e8f0';
              },
              lineWidth: function(context) {
                return context.tick.value === 0 ? 1.5 : 1;
              }
            }
          }
        }
      }
    });
  }

  // --- 5. RESEARCH INSIGHTS PANEL ---
  function renderResearchInsights() {
    if (!insightsContainer) return;
    const insights = state.insights.insights || [];

    if (insights.length === 0) {
      insightsContainer.innerHTML = '<p class="text-muted">No insights available for current selection.</p>';
      return;
    }

    insightsContainer.innerHTML = insights.map(item => {
      const cardType = item.type || 'standard';
      return `
        <div class="insight-card ${cardType}">
          <div class="insight-card-header">
            <span class="insight-card-title">${item.title}</span>
            <span class="insight-confidence">${item.confidence_level}</span>
          </div>
          <div class="insight-section">
            <span class="insight-pattern"><strong>Observed Empirical Pattern:</strong> ${item.observed_pattern}</span>
          </div>
          <div class="insight-section">
            <div class="insight-causal"><strong>Physical / Causal Attribution:</strong> ${item.causal_explanation}</div>
          </div>
        </div>
      `;
    }).join('');
  }

  // --- 6. DATA TABLE & PAGINATION ---
  function renderTable() {
    if (!tableBody) return;

    let filtered = state.records;
    if (state.tableSearchTerm) {
      filtered = filtered.filter(r => r.year.toString().includes(state.tableSearchTerm));
    }

    const total = filtered.length;
    tableRecordCount.textContent = `Showing ${total} records`;

    const totalPages = Math.ceil(total / state.rowsPerPage) || 1;
    if (state.currentPage > totalPages) state.currentPage = totalPages;
    if (state.currentPage < 1) state.currentPage = 1;

    pageIndicator.textContent = `Page ${state.currentPage} of ${totalPages}`;
    prevPageBtn.disabled = state.currentPage <= 1;
    nextPageBtn.disabled = state.currentPage >= totalPages;

    const startIdx = (state.currentPage - 1) * state.rowsPerPage;
    const pageRecords = filtered.slice(startIdx, startIdx + state.rowsPerPage);

    if (pageRecords.length === 0) {
      tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:1.5rem; color:#64748b;">No matching records found.</td></tr>';
      return;
    }

    tableBody.innerHTML = pageRecords.map(r => {
      const sign = r.annual_anomaly > 0 ? '+' : '';
      const cls = r.annual_anomaly >= 0 ? 'badge-warm-val' : 'badge-cool-val';
      const devText = r.annual_anomaly >= 0 ? `${sign}${r.annual_anomaly.toFixed(2)}°C Warmer` : `${r.annual_anomaly.toFixed(2)}°C Cooler`;
      return `
        <tr>
          <td><strong>${r.year}</strong></td>
          <td class="${cls}">${sign}${r.annual_anomaly.toFixed(3)}</td>
          <td>${r.five_year_smooth !== undefined ? r.five_year_smooth.toFixed(3) : '--'}</td>
          <td>±${(r.uncertainty || 0.05).toFixed(2)}</td>
          <td><span class="${cls}">${devText}</span></td>
        </tr>
      `;
    }).join('');
  }

  // --- 7. ASSISTANT CHAT ---
  async function submitQuery(queryText) {
    if (!queryText || !queryText.trim()) return;
    const cleanQuery = queryText.trim();

    // 1. Append User Message Bubble
    appendMessage('User', cleanQuery, 'user-message');
    chatInput.value = '';

    // Show loading
    sendBtn.disabled = true;
    sendSpinner.classList.remove('hidden');

    try {
      const payload = {
        query: cleanQuery,
        dataset_id: state.datasetId,
        start_year: state.filterStartYear,
        end_year: state.filterEndYear
      };

      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      const formattedHtml = parseMarkdownToHtml(data.answer || data.error);
      appendMessage('Climate Intelligence Assistant', formattedHtml, 'assistant-message', true);
    } catch (err) {
      console.error('Chat error:', err);
      appendMessage(
        'Climate Intelligence Assistant',
        `⚠️ Failed to process question: ${err.message}. Please try again.`,
        'assistant-message'
      );
    } finally {
      sendBtn.disabled = false;
      sendSpinner.classList.add('hidden');
    }
  }

  function appendMessage(sender, textOrHtml, cssClass, isHtml = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${cssClass}`;

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const avatar = cssClass.includes('user') ? '👤' : '🤖';

    msgDiv.innerHTML = `
      <div class="message-sender">
        <span class="sender-avatar">${avatar}</span>
        <strong>${sender}</strong>
        <span class="message-time">${now}</span>
      </div>
      <div class="message-body">${isHtml ? textOrHtml : `<p>${escapeHtml(textOrHtml)}</p>`}</div>
    `;

    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  // Lightweight safe Markdown to HTML parser
  function parseMarkdownToHtml(md) {
    if (!md) return '';

    // Escape raw HTML first
    let text = escapeHtml(md);

    // Headers
    text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    text = text.replace(/^#### (.*$)/gim, '<h4>$1</h4>');

    // Bold & Italics
    text = text.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/gim, '<em>$1</em>');

    // Code blocks & Inline Code
    text = text.replace(/`([^`]+)`/gim, '<code>$1</code>');

    // Blockquotes
    text = text.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

    // Lists
    text = text.replace(/^\- (.*$)/gim, '<li>$1</li>');

    // Links [Text](URL)
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    // Tables
    const lines = text.split('\n');
    let inTable = false;
    let tableHtml = '<table>';
    let outputLines = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith('|') && line.endsWith('|')) {
        if (!inTable) {
          inTable = true;
          tableHtml = '<table>';
        }
        if (line.includes('---')) continue; // Divider row

        const cells = line.split('|').slice(1, -1);
        const tag = (tableHtml === '<table>') ? 'th' : 'td';
        tableHtml += '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
      } else {
        if (inTable) {
          inTable = false;
          tableHtml += '</table>';
          outputLines.push(tableHtml);
        }
        if (line.length > 0) {
          outputLines.push(`<p>${line}</p>`);
        }
      }
    }
    if (inTable) {
      tableHtml += '</table>';
      outputLines.push(tableHtml);
    }

    return outputLines.join('');
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // --- 8. EVENT HANDLERS ---

  // Dataset Switcher
  datasetSelect.addEventListener('change', (e) => {
    state.datasetId = e.target.value;
    state.filterStartYear = null;
    state.filterEndYear = null;
    state.currentPage = 1;
    loadDashboardData();
  });

  // Apply Year Filters
  applyFilterBtn.addEventListener('click', () => {
    const s = parseInt(startYearInput.value, 10);
    const e = parseInt(endYearInput.value, 10);
    if (!isNaN(s) && !isNaN(e)) {
      state.filterStartYear = s;
      state.filterEndYear = e;
      state.currentPage = 1;
      loadDashboardData();
    }
  });

  // Reset Filters
  resetFilterBtn.addEventListener('click', () => {
    state.filterStartYear = null;
    state.filterEndYear = null;
    state.currentPage = 1;
    loadDashboardData();
  });

  // Toggle smoothing / trendline
  toggleSmoothing.addEventListener('change', () => renderChart());
  toggleTrendline.addEventListener('change', () => renderChart());

  // Export CSV
  exportCsvBtn.addEventListener('click', () => {
    let url = `/api/export?dataset_id=${encodeURIComponent(state.datasetId)}`;
    if (state.filterStartYear !== null && state.filterEndYear !== null) {
      url += `&start_year=${state.filterStartYear}&end_year=${state.filterEndYear}`;
    }
    window.location.href = url;
  });

  // Prompt Chips
  promptChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const query = chip.getAttribute('data-query');
      submitQuery(query);
    });
  });

  // Chat Form Submit
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    submitQuery(chatInput.value);
  });

  // Table Search
  tableSearchInput.addEventListener('input', (e) => {
    state.tableSearchTerm = e.target.value.trim();
    state.currentPage = 1;
    renderTable();
  });

  // Table Pagination
  prevPageBtn.addEventListener('click', () => {
    if (state.currentPage > 1) {
      state.currentPage--;
      renderTable();
    }
  });

  nextPageBtn.addEventListener('click', () => {
    state.currentPage++;
    renderTable();
  });

  // Initialize
  loadDashboardData();
});
