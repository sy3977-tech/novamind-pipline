"""
NovaMind Dashboard
==================
Run with: /opt/anaconda3/bin/python dashboard.py
Then open: http://127.0.0.1:8080
"""

import json
import glob
import os
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

pipeline_status = {"running": False, "step": "", "done": False, "error": ""}

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NovaMind Dashboard</title>
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#0f0f13; color:#e2e2e8; min-height:100vh; }
    .topbar { background:#1a1a24; border-bottom:1px solid #2a2a3a; padding:16px 32px; display:flex; align-items:center; gap:12px; }
    .logo { width:32px; height:32px; background:linear-gradient(135deg,#7c6af7,#4facfe); border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:14px; color:#fff; }
    .topbar h1 { font-size:18px; font-weight:600; }
    .last-updated { color:#666; font-size:13px; margin-left:auto; }
    .run-area { background:#1a1a24; border-bottom:1px solid #2a2a3a; padding:20px 32px; display:flex; align-items:center; gap:16px; }
    .topic-input { flex:1; max-width:400px; background:#0f0f13; border:1px solid #2a2a3a; border-radius:8px; padding:10px 16px; color:#fff; font-size:14px; outline:none; }
    .topic-input:focus { border-color:#7c6af7; }
    .run-btn { background:linear-gradient(135deg,#7c6af7,#4facfe); color:#fff; border:none; padding:10px 24px; border-radius:8px; font-size:14px; font-weight:600; cursor:pointer; }
    .run-btn:disabled { opacity:0.5; cursor:not-allowed; }
    .status-msg { font-size:13px; color:#4facfe; }
    .tabs { display:flex; border-bottom:1px solid #2a2a3a; padding:0 32px; background:#1a1a24; }
    .tab { padding:14px 20px; font-size:13px; font-weight:500; color:#666; cursor:pointer; border-bottom:2px solid transparent; }
    .tab.active { color:#fff; border-bottom-color:#7c6af7; }
    .container { max-width:1200px; margin:0 auto; padding:32px; }
    .tab-content { display:none; }
    .tab-content.active { display:block; }
    .section-title { font-size:11px; font-weight:600; letter-spacing:0.1em; text-transform:uppercase; color:#666; margin-bottom:16px; }
    .cards-row { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:32px; }
    .card { background:#1a1a24; border:1px solid #2a2a3a; border-radius:12px; padding:20px; }
    .card .label { font-size:12px; color:#666; margin-bottom:8px; }
    .card .value { font-size:28px; font-weight:700; color:#fff; }
    .card .sub { font-size:12px; color:#4facfe; margin-top:4px; }
    .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:32px; }
    .panel { background:#1a1a24; border:1px solid #2a2a3a; border-radius:12px; padding:24px; }
    .panel h3 { font-size:14px; font-weight:600; margin-bottom:20px; color:#ccc; }
    .persona-row { display:flex; align-items:center; gap:12px; margin-bottom:16px; }
    .persona-badge { font-size:11px; padding:3px 10px; border-radius:20px; font-weight:500; white-space:nowrap; }
    .badge-creative { background:#2d1f6e; color:#a78bfa; }
    .badge-startup { background:#1a3a2a; color:#4ade80; }
    .badge-marketing { background:#3a1f1a; color:#fb923c; }
    .bar-wrap { flex:1; background:#0f0f13; border-radius:4px; height:8px; overflow:hidden; }
    .bar { height:100%; border-radius:4px; }
    .bar-open { background:#7c6af7; }
    .bar-click { background:#4facfe; }
    .stat-val { font-size:13px; font-weight:600; min-width:40px; text-align:right; }
    .blog-card { background:#1a1a24; border:1px solid #2a2a3a; border-radius:12px; padding:24px; margin-bottom:32px; }
    .blog-title { font-size:20px; font-weight:700; margin-bottom:8px; }
    .blog-meta { font-size:12px; color:#666; margin-bottom:16px; }
    .blog-outline { list-style:none; }
    .blog-outline li { padding:8px 0; border-bottom:1px solid #2a2a3a; font-size:14px; color:#aaa; display:flex; gap:10px; }
    .blog-outline li:last-child { border-bottom:none; }
    .outline-num { color:#7c6af7; font-weight:600; min-width:20px; }
    .newsletters { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:32px; }
    .newsletter-card { background:#1a1a24; border:1px solid #2a2a3a; border-radius:12px; padding:20px; }
    .newsletter-card .subject { font-size:13px; font-weight:600; margin-bottom:12px; color:#fff; line-height:1.4; }
    .newsletter-card .body-text { font-size:12px; color:#888; line-height:1.6; }
    .ai-summary { background:#1a1a24; border:1px solid #2a2a3a; border-left:3px solid #7c6af7; border-radius:12px; padding:24px; margin-bottom:32px; }
    .ai-summary h3 { font-size:14px; font-weight:600; margin-bottom:12px; color:#a78bfa; }
    .ai-summary p { font-size:14px; color:#aaa; line-height:1.7; }
    .topic-item { background:#1a1a24; border:1px solid #2a2a3a; border-radius:10px; padding:16px 20px; margin-bottom:12px; display:flex; align-items:flex-start; gap:16px; }
    .topic-num { background:#2d1f6e; color:#a78bfa; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; flex-shrink:0; margin-top:2px; }
    .topic-text { font-size:14px; font-weight:600; color:#fff; margin-bottom:4px; }
    .topic-reason { font-size:12px; color:#666; line-height:1.5; }
    .use-btn { margin-left:auto; background:#2d1f6e; color:#a78bfa; border:none; padding:6px 14px; border-radius:6px; font-size:12px; cursor:pointer; flex-shrink:0; }
    .headline-item { background:#1a1a24; border:1px solid #2a2a3a; border-radius:10px; padding:16px 20px; margin-bottom:12px; }
    .headline-style { font-size:11px; color:#4facfe; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px; }
    .headline-text { font-size:15px; font-weight:600; color:#fff; }
    .revision-card { background:#1a1a24; border:1px solid #2a2a3a; border-radius:12px; padding:24px; margin-bottom:16px; }
    .revision-card h3 { font-size:14px; font-weight:600; margin-bottom:16px; color:#ccc; }
    .diagnosis { background:#0f0f13; border-radius:8px; padding:14px; margin-bottom:20px; font-size:13px; color:#aaa; line-height:1.6; }
    .revision-item { border-bottom:1px solid #2a2a3a; padding:12px 0; }
    .revision-item:last-child { border-bottom:none; }
    .revision-element { font-size:11px; color:#fb923c; font-weight:600; text-transform:uppercase; margin-bottom:4px; }
    .revision-issue { font-size:12px; color:#f87171; margin-bottom:4px; }
    .revision-suggestion { font-size:13px; color:#4ade80; }
    .revised-body { background:#0f0f13; border-radius:8px; padding:16px; font-size:13px; color:#aaa; line-height:1.7; white-space:pre-wrap; margin-top:16px; }
    .empty { text-align:center; padding:80px; color:#444; }
    .empty h2 { font-size:20px; margin-bottom:8px; }
  </style>
</head>
<body>
  <div class="topbar">
    <div class="logo">N</div>
    <h1>NovaMind Pipeline Dashboard</h1>
    <span class="last-updated" id="last-updated">—</span>
  </div>

  <div class="run-area">
    <input class="topic-input" id="topic-input" type="text" placeholder="Enter a blog topic..." value="AI in creative automation">
    <button class="run-btn" id="run-btn" onclick="runPipeline()">▶ Run Pipeline</button>
    <span class="status-msg" id="status-msg"></span>
  </div>

  <div class="tabs">
    <div class="tab active" onclick="showTab('overview')">Overview</div>
    <div class="tab" onclick="showTab('content')">Content</div>
    <div class="tab" onclick="showTab('performance')">Performance</div>
    <div class="tab" onclick="showTab('optimization')">AI Optimization</div>
  </div>

  <div class="container">
    <div id="tab-overview" class="tab-content active"><div class="empty"><h2>Loading...</h2></div></div>
    <div id="tab-content" class="tab-content"></div>
    <div id="tab-performance" class="tab-content"></div>
    <div id="tab-optimization" class="tab-content"></div>
  </div>

<script>
  const badgeClass = {creative_professional:'badge-creative',startup_founder:'badge-startup',marketing_manager:'badge-marketing'};
  const badgeLabel = {creative_professional:'Creative Pro',startup_founder:'Startup Founder',marketing_manager:'Mktg Manager'};
  function pct(v){return(v*100).toFixed(1)+'%';}
  function showTab(name){
    ['overview','content','performance','optimization'].forEach((t,i)=>{
      document.querySelectorAll('.tab')[i].classList.toggle('active',t===name);
      document.getElementById('tab-'+t).classList.toggle('active',t===name);
    });
  }

  async function loadData(){
    const res=await fetch('/api/latest');
    const data=await res.json();
    if(!data.content){
      ['overview','content','performance','optimization'].forEach(t=>{
        document.getElementById('tab-'+t).innerHTML='<div class="empty"><h2>No data yet</h2><p>Enter a topic above and click Run Pipeline</p></div>';
      });
      return;
    }
    document.getElementById('last-updated').textContent='Last run: '+new Date(data.content.generated_at).toLocaleString();
    renderOverview(data.content,data.performance);
    renderContent(data.content);
    renderPerformance(data.performance);
    renderOptimization(data.optimization);
  }

  function renderOverview(content,performance){
    const metrics=performance?performance.metrics_by_persona:null;
    const avgOpen=metrics?Object.values(metrics).reduce((s,m)=>s+m.open_rate,0)/3:0;
    const avgClick=metrics?Object.values(metrics).reduce((s,m)=>s+m.click_rate,0)/3:0;
    const total=metrics?Object.values(metrics).reduce((s,m)=>s+m.contacts_sent,0):0;
    const personas=Object.keys(content.newsletters);
    document.getElementById('tab-overview').innerHTML=`
      <div class="section-title" style="margin-top:0">Campaign Overview</div>
      <div class="cards-row">
        <div class="card"><div class="label">Avg Open Rate</div><div class="value">${pct(avgOpen)}</div><div class="sub">across 3 personas</div></div>
        <div class="card"><div class="label">Avg Click Rate</div><div class="value">${pct(avgClick)}</div><div class="sub">across 3 personas</div></div>
        <div class="card"><div class="label">Contacts Reached</div><div class="value">${total}</div><div class="sub">mock contacts</div></div>
        <div class="card"><div class="label">Campaigns Sent</div><div class="value">3</div><div class="sub">personas targeted</div></div>
      </div>
      ${metrics?`<div class="section-title">Performance by Persona</div><div class="grid-2">
        <div class="panel"><h3>Open Rate</h3>${personas.map(p=>`<div class="persona-row"><span class="persona-badge ${badgeClass[p]}">${badgeLabel[p]}</span><div class="bar-wrap"><div class="bar bar-open" style="width:${metrics[p].open_rate*100}%"></div></div><span class="stat-val">${pct(metrics[p].open_rate)}</span></div>`).join('')}</div>
        <div class="panel"><h3>Click Rate</h3>${personas.map(p=>`<div class="persona-row"><span class="persona-badge ${badgeClass[p]}">${badgeLabel[p]}</span><div class="bar-wrap"><div class="bar bar-click" style="width:${metrics[p].click_rate*500}%"></div></div><span class="stat-val">${pct(metrics[p].click_rate)}</span></div>`).join('')}</div>
      </div>`:''}
      ${performance&&performance.ai_summary?`<div class="ai-summary"><h3>✦ AI Performance Summary</h3><p>${performance.ai_summary}</p></div>`:''}`;
  }

  function renderContent(content){
    const personas=Object.keys(content.newsletters);
    document.getElementById('tab-content').innerHTML=`
      <div class="blog-card">
        <div class="section-title">Generated Blog Post</div>
        <div class="blog-title">${content.blog.title}</div>
        <div class="blog-meta">Topic: ${content.topic} · ${content.blog.draft.split(' ').length} words</div>
        <ul class="blog-outline">${content.blog.outline.map((p,i)=>`<li><span class="outline-num">${i+1}</span>${p}</li>`).join('')}</ul>
      </div>
      <div class="section-title">Newsletter Versions by Persona</div>
      <div class="newsletters">${personas.map(p=>`<div class="newsletter-card">
        <div class="persona-badge ${badgeClass[p]}" style="display:inline-block;margin-bottom:12px">${badgeLabel[p]}</div>
        <div class="subject">${content.newsletters[p].subject}</div>
        <div class="body-text">${content.newsletters[p].body}</div>
      </div>`).join('')}</div>`;
  }

  function renderPerformance(performance){
    if(!performance){document.getElementById('tab-performance').innerHTML='<div class="empty"><h2>No performance data yet</h2></div>';return;}
    const m=performance.metrics_by_persona;
    const personas=Object.keys(m);
    document.getElementById('tab-performance').innerHTML=`
      <div class="section-title">Detailed Metrics</div>
      <div class="cards-row" style="grid-template-columns:repeat(3,1fr)">
        ${personas.map(p=>`<div class="card">
          <div class="label"><span class="persona-badge ${badgeClass[p]}">${badgeLabel[p]}</span></div>
          <div style="margin-top:12px;font-size:13px;color:#aaa">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px"><span>Open rate</span><strong style="color:#fff">${pct(m[p].open_rate)}</strong></div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px"><span>Click rate</span><strong style="color:#fff">${pct(m[p].click_rate)}</strong></div>
            <div style="display:flex;justify-content:space-between"><span>Unsubscribe</span><strong style="color:#f87171">${pct(m[p].unsubscribe_rate)}</strong></div>
          </div>
        </div>`).join('')}
      </div>
      <div class="ai-summary"><h3>✦ AI Performance Summary</h3><p>${performance.ai_summary}</p></div>`;
  }

  function renderOptimization(opt){
    if(!opt){document.getElementById('tab-optimization').innerHTML='<div class="empty"><h2>No optimization data yet</h2><p>Run the full pipeline to get AI suggestions</p></div>';return;}
    const topics=opt.suggested_topics||[];
    const headlines=opt.alternative_headlines||[];
    const rev=opt.newsletter_revision;
    document.getElementById('tab-optimization').innerHTML=`
      <div class="section-title">Suggested Next Blog Topics</div>
      ${topics.map((t,i)=>`<div class="topic-item">
        <div class="topic-num">${i+1}</div>
        <div style="flex:1"><div class="topic-text">${t.topic}</div><div class="topic-reason">${t.reason}</div></div>
        <button class="use-btn" onclick="document.getElementById('topic-input').value='${t.topic.replace(/'/g,"\\'")}';window.scrollTo(0,0)">Use this ↑</button>
      </div>`).join('')}
      <div class="section-title" style="margin-top:32px">Alternative Headlines for A/B Testing</div>
      ${headlines.map(h=>`<div class="headline-item"><div class="headline-style">${h.style}</div><div class="headline-text">${h.headline}</div></div>`).join('')}
      ${rev?`<div class="section-title" style="margin-top:32px">Newsletter Revision Suggestions</div>
      <div class="revision-card">
        <h3>Revisions for: <span class="persona-badge ${badgeClass[rev.persona]||'badge-creative'}">${badgeLabel[rev.persona]||rev.persona}</span></h3>
        <div class="diagnosis">${rev.diagnosis||''}</div>
        ${(rev.revisions||[]).map(r=>`<div class="revision-item">
          <div class="revision-element">${r.element}</div>
          <div class="revision-issue">Issue: ${r.issue}</div>
          <div class="revision-suggestion">→ ${r.suggestion}</div>
        </div>`).join('')}
        ${rev.revised_version?`<div class="section-title" style="margin-top:20px">Revised Newsletter</div><div class="revised-body">${rev.revised_version}</div>`:''}
      </div>`:''}`;
  }

  async function runPipeline(){
    const topic=document.getElementById('topic-input').value.trim();
    if(!topic)return;
    const btn=document.getElementById('run-btn');
    const msg=document.getElementById('status-msg');
    btn.disabled=true;
    msg.textContent='Starting...';
    const res=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic})});
    const {ok}=await res.json();
    if(!ok){msg.textContent='Already running!';btn.disabled=false;return;}
    const poll=setInterval(async()=>{
      const s=await fetch('/api/status');
      const st=await s.json();
      msg.textContent=st.step||'Running...';
      if(st.done){clearInterval(poll);btn.disabled=false;msg.textContent='✅ Done!';setTimeout(()=>{msg.textContent='';loadData();},1500);}
      if(st.error){clearInterval(poll);btn.disabled=false;msg.textContent='❌ '+st.error;}
    },1500);
  }

  loadData();
</script>
</body>
</html>
"""


def load_latest(pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        return None
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/latest")
def api_latest():
    content = load_latest("output/campaigns/content_*.json")
    perf_raw = load_latest("output/campaigns/performance_*.json")
    opt_raw = load_latest("output/campaigns/optimization_*.json")
    performance = None
    if perf_raw:
        performance = {"ai_summary": perf_raw.get("ai_summary"), "metrics_by_persona": perf_raw.get("metrics_by_persona")}
    return jsonify({"content": content, "performance": performance, "optimization": opt_raw})


@app.route("/api/run", methods=["POST"])
def api_run():
    global pipeline_status
    if pipeline_status["running"]:
        return jsonify({"ok": False})
    topic = request.json.get("topic", "AI in creative automation")
    pipeline_status = {"running": True, "step": "Starting...", "done": False, "error": ""}

    def run_bg():
        global pipeline_status
        try:
            import content_generator, performance_tracker, optimizer, crm_manager
            pipeline_status["step"] = "[Step 1] Generating blog + newsletters..."
            content, _ = content_generator.run(topic)
            pipeline_status["step"] = "[Step 2] Pushing to HubSpot..."
            try:
                campaigns = crm_manager.run(content)
            except Exception:
                campaigns = {p: {"campaign_id": f"NM-MOCK-{p[:4].upper()}", "newsletter_subject": content["newsletters"][p]["subject"], "contact_count": 2, "sent_at": datetime.now().isoformat()} for p in content["newsletters"]}
            pipeline_status["step"] = "[Step 3] Analyzing performance..."
            report = performance_tracker.run(content["blog"]["title"], campaigns)
            pipeline_status["step"] = "[Step 4] Running AI optimization..."
            optimizer.run(content, report)
            pipeline_status.update({"running": False, "done": True, "step": "Complete!"})
        except Exception as e:
            pipeline_status.update({"running": False, "error": str(e)})

    threading.Thread(target=run_bg, daemon=True).start()
    return jsonify({"ok": True})


@app.route("/api/status")
def api_status():
    return jsonify(pipeline_status)


if __name__ == "__main__":
    os.makedirs("output/campaigns", exist_ok=True)
    print("\n🚀 NovaMind Dashboard running at http://127.0.0.1:8080\n")
    app.run(debug=False, port=8080, host="0.0.0.0")
