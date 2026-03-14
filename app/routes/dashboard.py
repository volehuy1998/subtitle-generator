"""Built-in performance monitoring dashboard."""

import logging
import time

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app import state
from app.config import OUTPUT_DIR, UPLOAD_DIR

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Analytics"])

_start_time = time.time()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Built-in monitoring dashboard with auto-refresh."""
    return HTMLResponse(content=DASHBOARD_HTML)


@router.get("/dashboard/data")
async def dashboard_data():
    """JSON data endpoint for the dashboard."""
    import psutil

    # Task stats
    status_counts = {}
    for t in state.tasks.values():
        s = t.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    active_tasks = []
    for tid, t in state.tasks.items():
        if t.get("status") not in ("done", "error", "cancelled"):
            active_tasks.append(
                {
                    "id": tid[:8],
                    "status": t.get("status", "unknown"),
                    "percent": t.get("percent", 0),
                    "message": t.get("message", ""),
                    "filename": t.get("filename", ""),
                }
            )

    recent_tasks = []
    for tid, t in list(state.tasks.items())[-20:]:
        recent_tasks.append(
            {
                "id": tid[:8],
                "status": t.get("status", "unknown"),
                "filename": t.get("filename", ""),
                "language": t.get("language", ""),
                "segments": t.get("segments", 0),
                "device": t.get("device", ""),
                "model": t.get("model_size", ""),
            }
        )

    # System stats
    cpu_percent = psutil.cpu_percent()
    mem = psutil.virtual_memory()

    try:
        upload_files = sum(1 for f in UPLOAD_DIR.iterdir() if f.is_file())
        output_files = sum(1 for f in OUTPUT_DIR.iterdir() if f.is_file())
    except Exception:
        upload_files = output_files = 0

    return {
        "uptime_sec": round(time.time() - _start_time, 1),
        "total_tasks": len(state.tasks),
        "status_counts": status_counts,
        "active_tasks": active_tasks,
        "recent_tasks": recent_tasks,
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": mem.percent,
            "memory_used_gb": round(mem.used / 1024**3, 1),
            "memory_total_gb": round(mem.total / 1024**3, 1),
        },
        "files": {
            "uploads": upload_files,
            "outputs": output_files,
        },
        "shutting_down": state.shutting_down,
    }


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Subtitle Generator - Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }
  .header { background: #1e293b; padding: 16px 24px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { font-size: 18px; color: #38bdf8; }
  .header .uptime { font-size: 13px; color: #94a3b8; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; padding: 24px; }
  .card { background: #1e293b; border-radius: 8px; padding: 20px; border: 1px solid #334155; }
  .card h3 { font-size: 13px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
  .card .value { font-size: 32px; font-weight: 700; color: #f8fafc; }
  .card .sub { font-size: 12px; color: #64748b; margin-top: 4px; }
  .bar { height: 8px; background: #334155; border-radius: 4px; margin-top: 12px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
  .bar-fill.cpu { background: #38bdf8; }
  .bar-fill.mem { background: #a78bfa; }
  .table-wrap { padding: 0 24px 24px; }
  table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; border: 1px solid #334155; }
  th { background: #334155; padding: 10px 14px; text-align: left; font-size: 12px; color: #94a3b8; text-transform: uppercase; }
  td { padding: 10px 14px; border-top: 1px solid #1e293b; font-size: 13px; }
  .status { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .status.done { background: #065f46; color: #6ee7b7; }
  .status.error { background: #7f1d1d; color: #fca5a5; }
  .status.transcribing { background: #1e3a5f; color: #7dd3fc; }
  .status.extracting { background: #713f12; color: #fde68a; }
  .status.queued { background: #374151; color: #d1d5db; }
  .status.cancelled { background: #44403c; color: #a8a29e; }
  .refresh { font-size: 11px; color: #475569; padding: 4px 24px; }
</style>
</head>
<body>
  <div class="header">
    <h1>Subtitle Generator Dashboard</h1>
    <span class="uptime" id="uptime">Loading...</span>
  </div>
  <div class="grid" id="cards"></div>
  <div class="refresh">Auto-refreshes every 3 seconds</div>
  <div class="table-wrap">
    <h3 style="color:#94a3b8;margin-bottom:12px;font-size:14px">Recent Tasks</h3>
    <table>
      <thead><tr><th>ID</th><th>File</th><th>Status</th><th>Lang</th><th>Segments</th><th>Device</th><th>Model</th></tr></thead>
      <tbody id="tasks"></tbody>
    </table>
  </div>
<script>
function formatUptime(sec) {
  const h = Math.floor(sec/3600), m = Math.floor((sec%3600)/60), s = Math.floor(sec%60);
  return `Uptime: ${h}h ${m}m ${s}s`;
}
function refresh() {
  fetch('/dashboard/data').then(r=>r.json()).then(d=>{
    document.getElementById('uptime').textContent = formatUptime(d.uptime_sec);
    const done = d.status_counts.done||0, err = d.status_counts.error||0;
    const active = d.active_tasks.length;
    document.getElementById('cards').innerHTML = `
      <div class="card"><h3>Total Tasks</h3><div class="value">${d.total_tasks}</div><div class="sub">${done} done, ${err} errors</div></div>
      <div class="card"><h3>Active Now</h3><div class="value">${active}</div><div class="sub">${d.shutting_down?'SHUTTING DOWN':'Accepting tasks'}</div></div>
      <div class="card"><h3>CPU Usage</h3><div class="value">${d.system.cpu_percent}%</div><div class="bar"><div class="bar-fill cpu" style="width:${d.system.cpu_percent}%"></div></div></div>
      <div class="card"><h3>Memory</h3><div class="value">${d.system.memory_used_gb}/${d.system.memory_total_gb} GB</div><div class="bar"><div class="bar-fill mem" style="width:${d.system.memory_percent}%"></div></div><div class="sub">${d.system.memory_percent}% used</div></div>
      <div class="card"><h3>Files</h3><div class="value">${d.files.uploads+d.files.outputs}</div><div class="sub">Uploads: ${d.files.uploads}, Outputs: ${d.files.outputs}</div></div>
    `;
    const rows = d.recent_tasks.reverse().map(t=>`<tr>
      <td><code>${t.id}</code></td><td>${t.filename||'-'}</td>
      <td><span class="status ${t.status}">${t.status}</span></td>
      <td>${t.language||'-'}</td><td>${t.segments||'-'}</td>
      <td>${t.device||'-'}</td><td>${t.model||'-'}</td></tr>`).join('');
    document.getElementById('tasks').innerHTML = rows || '<tr><td colspan=7 style="text-align:center;color:#475569">No tasks yet</td></tr>';
  }).catch(()=>{});
}
refresh();
setInterval(refresh, 3000);
</script>
</body>
</html>"""
