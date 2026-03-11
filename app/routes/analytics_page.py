"""Analytics dashboard page with Chart.js visualizations."""

import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Analytics"])


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page():
    """Full-page analytics dashboard with interactive charts."""
    return HTMLResponse(content=ANALYTICS_HTML)


ANALYTICS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Subtitle Generator - Analytics</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }
  .header { background: #1e293b; padding: 16px 24px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { font-size: 18px; color: #38bdf8; }
  .header-right { display: flex; align-items: center; gap: 16px; }
  .header a { color: #94a3b8; text-decoration: none; font-size: 13px; }
  .header a:hover { color: #e2e8f0; }
  .refresh-select { background: #334155; border: 1px solid #475569; color: #e2e8f0; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
  .last-updated { font-size: 11px; color: #475569; }

  .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; padding: 20px 24px 0; }
  .kpi { background: #1e293b; border-radius: 8px; padding: 16px; border: 1px solid #334155; }
  .kpi h3 { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
  .kpi .val { font-size: 28px; font-weight: 700; color: #f8fafc; }
  .kpi .sub { font-size: 11px; color: #64748b; margin-top: 2px; }
  .kpi .val.green { color: #4ade80; }
  .kpi .val.red { color: #f87171; }
  .kpi .val.blue { color: #38bdf8; }

  .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 20px 24px; }
  .chart-card { background: #1e293b; border-radius: 8px; padding: 16px; border: 1px solid #334155; }
  .chart-card h3 { font-size: 13px; color: #94a3b8; margin-bottom: 12px; font-weight: 600; }
  .chart-card canvas { max-height: 280px; }
  .chart-card.full-width { grid-column: 1 / -1; }

  .range-bar { display: flex; gap: 6px; padding: 0 24px; margin-top: 12px; }
  .range-btn { background: #334155; border: 1px solid #475569; color: #94a3b8; padding: 4px 12px; border-radius: 4px; font-size: 12px; cursor: pointer; }
  .range-btn:hover { border-color: #64748b; color: #e2e8f0; }
  .range-btn.active { background: #38bdf8; color: #0f172a; border-color: #38bdf8; }

  @media (max-width: 800px) {
    .charts { grid-template-columns: 1fr; }
    .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  }
  @media (max-width: 480px) {
    .kpi-grid { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
  <div class="header">
    <h1>Analytics Dashboard</h1>
    <div class="header-right">
      <a href="/">Home</a>
      <a href="/dashboard">System Dashboard</a>
      <select class="refresh-select" id="refreshInterval" onchange="setRefreshInterval()">
        <option value="5">5s refresh</option>
        <option value="10" selected>10s refresh</option>
        <option value="30">30s refresh</option>
        <option value="60">60s refresh</option>
      </select>
      <span class="last-updated" id="lastUpdated">Loading...</span>
    </div>
  </div>

  <div class="kpi-grid" id="kpis"></div>

  <div class="range-bar">
    <button class="range-btn active" data-minutes="60" onclick="setRange(this, 60)">1 Hour</button>
    <button class="range-btn" data-minutes="360" onclick="setRange(this, 360)">6 Hours</button>
    <button class="range-btn" data-minutes="720" onclick="setRange(this, 720)">12 Hours</button>
    <button class="range-btn" data-minutes="1440" onclick="setRange(this, 1440)">24 Hours</button>
  </div>

  <div class="charts">
    <div class="chart-card full-width">
      <h3>Processing Volume (tasks per interval)</h3>
      <canvas id="volumeChart"></canvas>
    </div>
    <div class="chart-card">
      <h3>Success / Error Rate</h3>
      <canvas id="rateChart"></canvas>
    </div>
    <div class="chart-card">
      <h3>Top Languages</h3>
      <canvas id="langChart"></canvas>
    </div>
    <div class="chart-card">
      <h3>Average Processing Time by Model</h3>
      <canvas id="modelChart"></canvas>
    </div>
    <div class="chart-card">
      <h3>Device Distribution</h3>
      <canvas id="deviceChart"></canvas>
    </div>
  </div>

<script>
  const chartDefaults = {
    color: '#94a3b8',
    borderColor: '#334155',
  };
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.borderColor = '#334155';
  Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

  let currentMinutes = 60;
  let refreshTimer = null;
  let volumeChart, rateChart, langChart, modelChart, deviceChart;

  function setRange(btn, minutes) {
    currentMinutes = minutes;
    document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    refresh();
  }

  function setRefreshInterval() {
    const sec = parseInt(document.getElementById('refreshInterval').value);
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(refresh, sec * 1000);
  }

  function formatTime(isoStr) {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function initCharts() {
    volumeChart = new Chart(document.getElementById('volumeChart'), {
      type: 'line',
      data: { labels: [], datasets: [
        { label: 'Uploads', data: [], borderColor: '#38bdf8', backgroundColor: '#38bdf822', fill: true, tension: 0.3 },
        { label: 'Completed', data: [], borderColor: '#4ade80', backgroundColor: '#4ade8022', fill: true, tension: 0.3 },
        { label: 'Failed', data: [], borderColor: '#f87171', backgroundColor: '#f8717122', fill: true, tension: 0.3 },
      ]},
      options: { responsive: true, scales: { y: { beginAtZero: true } }, plugins: { legend: { position: 'top' } } }
    });

    rateChart = new Chart(document.getElementById('rateChart'), {
      type: 'doughnut',
      data: { labels: ['Success', 'Failed', 'Cancelled'], datasets: [{
        data: [0, 0, 0],
        backgroundColor: ['#4ade80', '#f87171', '#fbbf24'],
        borderWidth: 0,
      }]},
      options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
    });

    langChart = new Chart(document.getElementById('langChart'), {
      type: 'bar',
      data: { labels: [], datasets: [{ label: 'Tasks', data: [], backgroundColor: '#38bdf8', borderRadius: 4 }] },
      options: { responsive: true, indexAxis: 'y', scales: { x: { beginAtZero: true } }, plugins: { legend: { display: false } } }
    });

    modelChart = new Chart(document.getElementById('modelChart'), {
      type: 'bar',
      data: { labels: [], datasets: [{ label: 'Avg Time (sec)', data: [], backgroundColor: '#a78bfa', borderRadius: 4 }] },
      options: { responsive: true, scales: { y: { beginAtZero: true } }, plugins: { legend: { display: false } } }
    });

    deviceChart = new Chart(document.getElementById('deviceChart'), {
      type: 'doughnut',
      data: { labels: [], datasets: [{ data: [], backgroundColor: ['#4ade80', '#38bdf8', '#fbbf24', '#f87171'], borderWidth: 0 }] },
      options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
    });
  }

  async function refresh() {
    try {
      const [summaryRes, tsRes] = await Promise.all([
        fetch('/analytics/summary'),
        fetch(`/analytics/timeseries?minutes=${currentMinutes}`)
      ]);
      const summary = await summaryRes.json();
      const ts = await tsRes.json();

      // KPIs
      const c = summary.counters;
      const r = summary.rates;
      document.getElementById('kpis').innerHTML = `
        <div class="kpi"><h3>Total Uploads</h3><div class="val blue">${c.uploads_total}</div><div class="sub">${r.uploads_per_hour}/hr</div></div>
        <div class="kpi"><h3>Completed</h3><div class="val green">${c.completed_total}</div><div class="sub">${r.completions_per_hour}/hr</div></div>
        <div class="kpi"><h3>Failed</h3><div class="val red">${c.failed_total}</div><div class="sub">${r.error_rate}% error rate</div></div>
        <div class="kpi"><h3>Cancelled</h3><div class="val">${c.cancelled_total}</div></div>
        <div class="kpi"><h3>Success Rate</h3><div class="val green">${r.success_rate}%</div></div>
        <div class="kpi"><h3>Avg Processing</h3><div class="val">${summary.processing.avg_sec}s</div><div class="sub">P95: ${summary.processing.p95_sec}s</div></div>
      `;

      // Volume chart
      const points = ts.points;
      volumeChart.data.labels = points.map(p => formatTime(p.time));
      volumeChart.data.datasets[0].data = points.map(p => p.uploads);
      volumeChart.data.datasets[1].data = points.map(p => p.completed);
      volumeChart.data.datasets[2].data = points.map(p => p.failed);
      volumeChart.update('none');

      // Rate chart
      rateChart.data.datasets[0].data = [c.completed_total, c.failed_total, c.cancelled_total];
      rateChart.update('none');

      // Language chart
      const langs = summary.distributions.top_languages;
      const langEntries = Object.entries(langs).sort((a, b) => b[1] - a[1]).slice(0, 10);
      langChart.data.labels = langEntries.map(e => e[0]);
      langChart.data.datasets[0].data = langEntries.map(e => e[1]);
      langChart.update('none');

      // Model chart
      const models = summary.processing.by_model;
      const modelOrder = ['tiny', 'base', 'small', 'medium', 'large'];
      const modelEntries = Object.entries(models).sort((a, b) => modelOrder.indexOf(a[0]) - modelOrder.indexOf(b[0]));
      modelChart.data.labels = modelEntries.map(e => e[0]);
      modelChart.data.datasets[0].data = modelEntries.map(e => e[1]);
      modelChart.update('none');

      // Device chart
      const devices = summary.distributions.devices;
      deviceChart.data.labels = Object.keys(devices);
      deviceChart.data.datasets[0].data = Object.values(devices);
      deviceChart.update('none');

      document.getElementById('lastUpdated').textContent = 'Updated: ' + new Date().toLocaleTimeString();
    } catch (e) {
      console.error('Analytics refresh failed:', e);
    }
  }

  initCharts();
  refresh();
  refreshTimer = setInterval(refresh, 10000);
</script>
</body>
</html>"""
