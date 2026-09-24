const state = { data: null, tab: 'overview' };

const fmt = (n, digits=1) => n == null || Number.isNaN(Number(n)) ? '—' : Number(n).toLocaleString('zh-TW', { maximumFractionDigits: digits });
const money = (n) => n == null ? '—' : `NT$ ${fmt(n, 1)}`;
const pct = (n) => n == null ? '—' : `${Number(n) >= 0 ? '+' : ''}${fmt(n, 1)}%`;
const cls = (n) => n > 0 ? 'positive' : n < 0 ? 'negative' : 'neutral';
const esc = (s='') => String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));

function badge(text, tone='blue') { return `<span class="badge ${tone}">${esc(text)}</span>`; }
function sourceBadge(level) { return level === 'official' ? badge('✅ 官方','good') : level === 'rumor' ? badge('⚠️ 待驗證','warn') : badge('🟦 次級來源','blue'); }

function sparkline(values=[]) {
  const v = values.filter(x => Number.isFinite(Number(x))).map(Number);
  if (v.length < 2) return '<div class="spark"></div>';
  const w=320,h=62,p=4, min=Math.min(...v), max=Math.max(...v), r=Math.max(1,max-min);
  const pts=v.map((x,i)=>`${p+(w-p*2)*i/(v.length-1)},${p+(h-p*2)*(1-(x-min)/r)}`).join(' ');
  const area=`${p},${h-p} ${pts} ${w-p},${h-p}`;
  return `<div class="spark"><svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><polygon class="area" points="${area}"/><polyline class="line" points="${pts}"/></svg></div>`;
}

function companyCard(c) {
  const actionTone = c.decision.action === 'ADD' ? 'good' : c.decision.action === 'TRIM' ? 'warn' : c.decision.action === 'EXIT REVIEW' ? 'bad' : 'blue';
  return `<section class="card">
    <div class="company-head">
      <div><h2>${esc(c.name)}</h2><div class="ticker">${c.id} · ${esc(c.role)}</div></div>
      <div><div class="price">${fmt(c.market.price,1)}</div><div class="delta ${cls(c.market.change_pct)}">${pct(c.market.change_pct)}</div></div>
    </div>
    ${sparkline(c.market.history.map(x=>x.close))}
    <div class="status-row">
      ${badge(c.valuation.label, c.valuation.tone)}
      ${badge(c.fundamental.label, c.fundamental.tone)}
      ${badge(c.decision.action, actionTone)}
    </div>
    <div class="metric-grid">
      <div class="metric"><div class="metric-label">合理價 Base</div><div class="metric-value">${fmt(c.valuation.base_fair,0)}</div></div>
      <div class="metric"><div class="metric-label">距 Base</div><div class="metric-value ${cls(c.valuation.base_upside_pct)}">${pct(c.valuation.base_upside_pct)}</div></div>
      <div class="metric"><div class="metric-label">最新月營收 YoY</div><div class="metric-value ${cls(c.revenue.yoy)}">${pct(c.revenue.yoy)}</div></div>
      <div class="metric"><div class="metric-label">下一驗證</div><div class="metric-value">${esc(c.next_verification)}</div></div>
    </div>
  </section>`;
}

function overview() {
  const d=state.data;
  return `
    <div class="grid grid-3">${d.companies.map(companyCard).join('')}</div>
    <div class="section-title"><h2>現在最值得注意</h2><div class="hint">不是新聞最多，而是最可能改變估值的訊號</div></div>
    <div class="grid grid-3">
      ${d.companies.map(c=>`<section class="card"><h3>${c.name}</h3><div class="callout" style="margin-top:10px">${esc(c.thesis)}</div><ul class="list">${c.alerts.slice(0,3).map(a=>`<li><div><div class="title">${esc(a.text)}</div><div class="meta">${esc(a.why)}</div></div>${badge(a.level,a.level==='正面'?'good':a.level==='風險'?'bad':'warn')}</li>`).join('')}</ul></section>`).join('')}
    </div>
    <div class="section-title"><h2>最新事件</h2><div class="hint">已區分官方、次級來源與待驗證傳聞</div></div>
    <section class="card"><ul class="list">${d.news.slice(0,10).map(n=>`<li><div><div class="title">${esc(n.company)}｜${esc(n.title)}</div><div class="meta">${esc(n.date)} · ${esc(n.source)}</div></div>${sourceBadge(n.confidence)}</li>`).join('')}</ul></section>`;
}

function companyPage(id) {
  const c=state.data.companies.find(x=>x.id===id);
  const actionTone = c.decision.action === 'ADD' ? 'good' : c.decision.action === 'TRIM' ? 'warn' : c.decision.action === 'EXIT REVIEW' ? 'bad' : 'blue';
  return `
    <div class="grid grid-2">
      <section class="card">
        <div class="company-head"><div><h2>${c.name} ${c.id}</h2><div class="ticker">${c.role}</div></div><div><div class="price">${fmt(c.market.price,1)}</div><div class="delta ${cls(c.market.change_pct)}">${pct(c.market.change_pct)}</div></div></div>
        ${sparkline(c.market.history.map(x=>x.close))}
        <div class="status-row">${badge(c.valuation.label,c.valuation.tone)} ${badge(c.fundamental.label,c.fundamental.tone)} ${badge(c.decision.action,actionTone)}</div>
      </section>
      <section class="action-box">
        <div class="metric-label">目前操作判斷</div>
        <div class="action ${actionTone==='good'?'positive':actionTone==='bad'?'negative':''}">${c.decision.action}</div>
        <p>${esc(c.decision.reason)}</p>
        <p><strong>改變判斷的條件：</strong>${esc(c.decision.change_condition)}</p>
      </section>
    </div>

    <div class="section-title"><h2>關鍵數字</h2><div class="hint">只放會改變投資論點的欄位</div></div>
    <div class="grid grid-4">
      ${c.kpis.map(k=>`<div class="card kpi"><div class="metric-label">${esc(k.label)}</div><div class="big ${k.tone||''}">${esc(String(k.value))}</div><div class="small">${esc(k.note||'')}</div></div>`).join('')}
    </div>

    <div class="section-title"><h2>故事驗證 Pipeline</h2><div class="hint">從題材走到現金流</div></div>
    <section class="card"><div class="pipeline">${c.pipeline.map(s=>`<div class="stage ${s.status}"><strong>${s.status==='ok'?'✅':s.status==='partial'?'🟡':'⬜'} ${esc(s.name)}</strong><p>${esc(s.note)}</p></div>`).join('')}</div></section>

    <div class="section-title"><h2>估值情境</h2><div class="hint">假設可在 config/valuation.json 修改</div></div>
    <section class="card"><div class="scenarios">${Object.entries(c.valuation.scenarios).map(([name,s])=>`<div class="scenario"><div class="name">${name.toUpperCase()}</div><div class="fair">${fmt(s.fair_value,0)}</div><div class="details">${esc(s.description)}</div></div>`).join('')}</div></section>

    <div class="section-title"><h2>紅旗與催化劑</h2></div>
    <div class="grid grid-2">
      <section class="card"><h3>催化劑</h3><ul class="list">${c.catalysts.map(x=>`<li><div class="title">${esc(x)}</div>${badge('Catalyst','good')}</li>`).join('')}</ul></section>
      <section class="card"><h3>紅旗</h3><ul class="list">${c.red_flags.map(x=>`<li><div class="title">${esc(x)}</div>${badge('Risk','bad')}</li>`).join('')}</ul></section>
    </div>

    <div class="section-title"><h2>最近新聞</h2></div>
    <section class="card"><ul class="list">${state.data.news.filter(n=>n.company_id===id).slice(0,10).map(n=>`<li><div><div class="title">${esc(n.title)}</div><div class="meta">${esc(n.date)} · ${esc(n.source)}</div></div>${sourceBadge(n.confidence)}</li>`).join('') || '<li><div class="title">暫無資料</div></li>'}</ul></section>`;
}

function brokerPage() {
  const b=state.data.broker;
  const t=b.target||{};
  const shortDays=t.short_window_days||5;
  const longDays=t.long_window_days||20;
  const snaps=t.summary_history||[];
  const signed=(n)=> n==null?'—':`${n>=0?'+':''}${fmt(n,0)}`;
  return `
    <div class="grid grid-4">
      <div class="card kpi"><div class="metric-label">分點</div><div class="big">${esc(b.branch_name)}</div><div class="small">代碼 ${b.branch_id}；同一分點不代表同一投資人。</div></div>
      <div class="card kpi"><div class="metric-label">政美近${shortDays}日</div><div class="big ${cls(t.net_5d)}">${signed(t.net_5d)} 張</div><div class="small">Top 3 排名 ${t.rank||'—'}；占區間成交量 ${t.share_pct==null?'—':fmt(t.share_pct,2)+'%'}</div></div>
      <div class="card kpi"><div class="metric-label">政美近${longDays}日</div><div class="big ${cls(t.net_20d)}">${signed(t.net_20d)} 張</div><div class="small">來源實際提供幾日，就顯示幾日，不硬補成20日。</div></div>
      <div class="card kpi"><div class="metric-label">CR15 / 型態</div><div class="big">${t.cr15_latest==null?'—':fmt(t.cr15_latest,2)}</div><div class="small">${esc(t.pattern)} · 資料日 ${t.as_of||'—'}</div></div>
    </div>
    <div class="section-title"><h2>政美 9887 公開摘要歷史</h2><div class="hint">${esc(b.source||'公開分點摘要')}；每天晚間更新後記錄一筆</div></div>
    <section class="card"><div class="table-wrap"><table><thead><tr><th>資料日</th><th>短區間</th><th>9887淨買賣</th><th>排名</th><th>占成交量</th><th>長區間</th><th>長區間淨買賣</th><th>CR15</th><th>分點數</th></tr></thead><tbody>${snaps.length?snaps.slice().reverse().map(r=>`<tr><td>${r.source_date||'—'}</td><td>近${r.window_days||'—'}日</td><td class="${cls(r.net)}">${signed(r.net)}</td><td>${r.rank||'—'}</td><td>${r.share_pct==null?'—':fmt(r.share_pct,2)+'%'}</td><td>${r.long_window_days?'近'+r.long_window_days+'日':'—'}</td><td class="${cls(r.long_net)}">${signed(r.long_net)}</td><td>${r.cr15_latest==null?'—':fmt(r.cr15_latest,2)}</td><td>${r.branches_count==null?'—':fmt(r.branches_count,0)}</td></tr>`).join(''):'<tr><td colspan="9">尚未累積公開摘要歷史。</td></tr>'}</tbody></table></div></section>
    <div class="section-title"><h2>9887 跨股票雷達</h2><div class="hint">目前掃描 config/public_broker_watchlist.json 內的股票</div></div>
    <section class="card"><div class="table-wrap"><table><thead><tr><th>股票</th><th>短區間</th><th>排名</th><th>短區間淨買賣</th><th>占成交量</th><th>長區間</th><th>長區間淨買賣</th><th>CR15</th><th>型態</th></tr></thead><tbody>${(b.cross_stock||[]).map(r=>`<tr><td>${esc(r.name)} ${r.id}</td><td>近${r.short_window_days||'—'}日</td><td>${r.rank||'—'}</td><td class="${cls(r.net_5d)}">${signed(r.net_5d)}</td><td>${r.share_pct==null?'—':fmt(r.share_pct,2)+'%'}</td><td>${r.long_window_days?'近'+r.long_window_days+'日':'—'}</td><td class="${cls(r.net_20d)}">${signed(r.net_20d)}</td><td>${r.cr15_latest==null?'—':fmt(r.cr15_latest,2)}</td><td>${esc(r.pattern)}</td></tr>`).join('')}</tbody></table></div></section>
    <div class="section-title"><h2>資料限制</h2></div>
    <div class="callout">${esc(b.data_note)}</div>`;
}

function valuationPage() {
  return `
    <section class="card">
      <h2>三檔估值總表</h2>
      <div class="table-wrap" style="margin-top:12px"><table><thead><tr><th>公司</th><th>現價</th><th>Bear</th><th>Base</th><th>Bull</th><th>距 Base</th><th>操作</th></tr></thead><tbody>
        ${state.data.companies.map(c=>`<tr><td>${c.name} ${c.id}</td><td>${fmt(c.market.price,1)}</td><td>${fmt(c.valuation.scenarios.bear.fair_value,0)}</td><td>${fmt(c.valuation.scenarios.base.fair_value,0)}</td><td>${fmt(c.valuation.scenarios.bull.fair_value,0)}</td><td class="${cls(c.valuation.base_upside_pct)}">${pct(c.valuation.base_upside_pct)}</td><td>${c.decision.action}</td></tr>`).join('')}
      </tbody></table></div>
    </section>
    <div class="section-title"><h2>決策規則</h2></div>
    <div class="grid grid-2">
      <section class="card"><h3>價格規則</h3><ul class="list"><li><div class="title">ADD：價格低於 Base fair value 約 15% 以上，且基本面沒有紅旗。</div></li><li><div class="title">HOLD：價格落在 Base 附近，等待下一個基本面驗證。</div></li><li><div class="title">TRIM：價格高於 Base 約 15% 以上，但新資訊沒有同步上修合理價。</div></li><li><div class="title">EXIT REVIEW：基本面出現兩項以上重大紅旗，不因股價便宜自動加碼。</div></li></ul></section>
      <section class="card"><h3>重要原則</h3><ul class="list"><li><div class="title">政美：未證實的台積電量產訂單不納入 Base case。</div></li><li><div class="title">由田：14.6535 億採購額不直接等於同期營收。</div></li><li><div class="title">南亞：拆分本業 EPS 與南亞科／南電／台塑石化等轉投資貢獻。</div></li></ul></section>
    </div>`;
}

function render() {
  if (!state.data) return;
  const app=document.getElementById('app');
  app.innerHTML = state.tab==='overview' ? overview() : state.tab==='broker' ? brokerPage() : state.tab==='valuation' ? valuationPage() : companyPage(state.tab);
  document.querySelectorAll('#tabs button').forEach(b=>b.classList.toggle('active',b.dataset.tab===state.tab));
}

async function init() {
  try {
    const res=await fetch('./data/dashboard.json',{cache:'no-store'});
    if(!res.ok) throw new Error(`HTTP ${res.status}`);
    state.data=await res.json();
    const f=document.getElementById('freshness');
    f.textContent=`資料更新：${state.data.generated_at} · ${state.data.mode}`;
    document.getElementById('tabs').addEventListener('click',e=>{const b=e.target.closest('button[data-tab]'); if(!b)return; state.tab=b.dataset.tab; render();});
    render();
  } catch(err) {
    document.getElementById('app').innerHTML=`<div class="error">資料載入失敗：${esc(err.message)}</div>`;
  }
}
init();
