const state = { data: null, tab: 'overview' };

const fmt = (n, digits=1) => n == null || Number.isNaN(Number(n)) ? '—' : Number(n).toLocaleString('zh-TW', { maximumFractionDigits: digits });
const money = (n) => n == null ? '—' : `NT$ ${fmt(n, 1)}`;
const pct = (n) => n == null ? '—' : `${Number(n) >= 0 ? '+' : ''}${fmt(n, 1)}%`;
const cls = (n) => n > 0 ? 'positive' : n < 0 ? 'negative' : 'neutral';
const esc = (s='') => String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));

function badge(text, tone='blue') { return `<span class="badge ${tone}">${esc(text)}</span>`; }
function sourceBadge(level) { return level === 'official' ? badge('✅ 官方','good') : level === 'rumor' ? badge('⚠️ 待驗證','warn') : badge('🟦 次級來源','blue'); }

function actionZh(action='') {
  return ({
    'ADD':'加碼觀察',
    'HOLD':'續抱觀察',
    'TRIM':'減碼',
    'EXIT REVIEW':'重新檢視／退出'
  })[action] || action;
}

function safeUrl(url='') {
  try { const u=new URL(url); return ['http:','https:'].includes(u.protocol)?u.href:''; } catch { return ''; }
}
function newsLink(n, includeCompany=false) {
  const url=safeUrl(n.url||'');
  const title=`${includeCompany?esc(n.company)+'｜':''}${esc(n.title)}`;
  const body=url
    ? `<a class="news-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer"><span>${title}</span><span class="news-arrow">↗</span></a>`
    : `<div class="title">${title}</div>`;
  const when=esc(n.published_at||n.date||'');
  return `<li class="news-item"><div><div class="title">${body}</div><div class="meta">${when} · ${esc(n.source)}</div></div>${sourceBadge(n.confidence)}</li>`;
}

function sparkline(history=[]) {
  const rows=(history||[]).filter(x=>Number.isFinite(Number(x.close))).map((x,i,a)=>{
    const close=Number(x.close);
    const prev=i>0?Number(a[i-1].close):null;
    const open=Number.isFinite(Number(x.open))?Number(x.open):close;
    const high=Number.isFinite(Number(x.high))?Number(x.high):Math.max(open,close);
    const low=Number.isFinite(Number(x.low))?Number(x.low):Math.min(open,close);
    return {...x,open,high,low,close,day_pct:prev?((close/prev)-1)*100:null};
  });
  if (rows.length < 2) return '<div class="price-chart"></div>';

  const w=560,h=232,left=48,right=54,top=16,priceBottom=162,volTop=180,volBottom=216;
  const rawMin=Math.min(...rows.map(x=>x.low));
  const rawMax=Math.max(...rows.map(x=>x.high));
  const rawRange=Math.max(1,rawMax-rawMin);
  const min=rawMin-rawRange*.06, max=rawMax+rawRange*.06, range=Math.max(1,max-min);
  const maxVol=Math.max(1,...rows.map(x=>Number(x.volume)||0));
  const xAt=i=>left+(w-left-right)*i/(rows.length-1);
  const yAt=v=>top+(priceBottom-top)*(1-(v-min)/range);
  const vAt=v=>volBottom-(volBottom-volTop)*(v/maxVol);
  const step=(w-left-right)/Math.max(1,rows.length-1);
  const bodyW=Math.max(2.2,Math.min(7,step*.62));

  const ma=rows.map((x,i)=> i<19 ? null : rows.slice(i-19,i+1).reduce((s,r)=>s+r.close,0)/20);
  const points=rows.map((x,i)=>({...x,sx:xAt(i),sy:yAt(x.close),ma20:ma[i]}));

  const priceTicks=[0,1,2,3,4].map(i=>{
    const value=max-(range*i/4);
    const y=yAt(value);
    return `<g class="axis-tick price-tick">
      <line x1="${left}" x2="${w-right}" y1="${y}" y2="${y}" class="chart-gridline"></line>
      <text x="${w-4}" y="${y+3}" text-anchor="end">${fmt(value,1)}</text>
    </g>`;
  }).join('');

  const volTicks=[0,.5,1].map(t=>{
    const value=maxVol*t;
    const y=vAt(value);
    const lots=value/1000;
    const label=lots>=1000 ? `${fmt(lots/1000,1)}K張` : `${fmt(lots,0)}張`;
    return `<g class="axis-tick volume-tick">
      <line x1="${left}" x2="${w-right}" y1="${y}" y2="${y}" class="volume-gridline"></line>
      <text x="4" y="${y+3}" text-anchor="start">${label}</text>
    </g>`;
  }).join('');

  const candles=points.map(x=>{
    const up=x.close>=x.open;
    const topY=yAt(Math.max(x.open,x.close));
    const bottomY=yAt(Math.min(x.open,x.close));
    const bodyH=Math.max(1.2,bottomY-topY);
    const klass=up?'candle-up':'candle-down';
    return `<g class="candle ${klass}">
      <line class="wick" x1="${x.sx}" x2="${x.sx}" y1="${yAt(x.high)}" y2="${yAt(x.low)}"></line>
      <rect class="body" x="${x.sx-bodyW/2}" y="${topY}" width="${bodyW}" height="${bodyH}" rx=".5"></rect>
    </g>`;
  }).join('');

  const volumes=points.map(x=>{
    const v=Number(x.volume)||0, y=vAt(v);
    const klass=x.close>=x.open?'vol-up':'vol-down';
    return `<rect class="volume-candle ${klass}" x="${x.sx-bodyW/2}" y="${y}" width="${bodyW}" height="${Math.max(.8,volBottom-y)}" rx=".5"></rect>`;
  }).join('');

  const maPts=points.filter(x=>x.ma20!=null).map(x=>`${x.sx},${yAt(x.ma20)}`).join(' ');
  const latest=points[points.length-1];
  const rangePct=((latest.close/rows[0].close)-1)*100;

  const zones=points.map((x,i)=>{
    const zx=Math.max(left,x.sx-step/2), zw=Math.min(w-right,zx+step)-zx;
    const meta=encodeURIComponent(JSON.stringify({
      date:x.date,close:x.close,open:x.open,high:x.high,low:x.low,volume:x.volume,
      day_pct:x.day_pct,ma20:x.ma20
    }));
    return `<rect class="chart-zone" x="${zx}" y="${top}" width="${Math.max(5,zw)}" height="${volBottom-top}" data-x="${x.sx}" data-y="${x.sy}" data-meta="${meta}"></rect>`;
  }).join('');

  return `<div class="price-chart">
    <div class="chart-header">
      <div class="chart-legend">
        <span class="legend-candle up"></span>上漲
        <span class="legend-candle down"></span>下跌
        <span class="legend-ma"></span>MA20
        <span class="chart-period">3M</span>
      </div>
      <div class="chart-stats"><span class="${cls(rangePct)}">${pct(rangePct)}</span><span>高 ${fmt(rawMax,1)} · 低 ${fmt(rawMin,1)}</span></div>
    </div>
    <div class="chart-canvas candle-canvas">
      <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid meet" aria-label="近三個月K線與成交量">
        <text class="axis-title price-axis-title" x="${w-4}" y="10" text-anchor="end">股價</text>
        <text class="axis-title volume-axis-title" x="4" y="${volTop-5}" text-anchor="start">成交量</text>
        ${priceTicks}
        ${volTicks}
        ${volumes}
        ${candles}
        <polyline class="ma-line" points="${maPts}"></polyline>
        <line class="latest-line" x1="${left}" x2="${w-right}" y1="${latest.sy}" y2="${latest.sy}"></line>
        <line class="chart-guide-x" x1="0" x2="0" y1="${top}" y2="${volBottom}"></line>
        <line class="chart-guide-y" x1="${left}" x2="${w-right}" y1="0" y2="0"></line>
        <circle class="chart-focus" cx="0" cy="0" r="3.8"></circle>
        ${zones}
      </svg>
      <div class="chart-tooltip" role="status"></div>
    </div>
    <div class="chart-footer"><span>${esc(rows[0].date)}</span><span>K線 · 成交量</span><span>${esc(latest.date)}</span></div>
  </div>`;
}

function bindSparkTooltips() {
  document.querySelectorAll('.price-chart').forEach(chart=>{
    const tip=chart.querySelector('.chart-tooltip');
    const guideX=chart.querySelector('.chart-guide-x');
    const guideY=chart.querySelector('.chart-guide-y');
    const focus=chart.querySelector('.chart-focus');
    chart.querySelectorAll('.chart-zone').forEach(zone=>{
      zone.addEventListener('pointerenter',show);
      zone.addEventListener('pointermove',show);
      zone.addEventListener('pointerleave',hide);
      function show(){
        const m=JSON.parse(decodeURIComponent(zone.dataset.meta));
        const x=Number(zone.dataset.x), y=Number(zone.dataset.y);
        const vb=zone.ownerSVGElement.viewBox.baseVal;
        const left=(x/vb.width)*100, top=(y/vb.height)*100;
        guideX.setAttribute('x1',x); guideX.setAttribute('x2',x);
        guideY.setAttribute('y1',y); guideY.setAttribute('y2',y);
        guideX.classList.add('show'); guideY.classList.add('show');
        focus.setAttribute('cx',x); focus.setAttribute('cy',y); focus.classList.add('show');
        const lots=m.volume==null?'—':fmt(Number(m.volume)/1000,0)+' 張';
        const ma=m.ma20==null?'—':fmt(m.ma20,1);
        tip.innerHTML=`<strong>${esc(m.date||'')}</strong>
          <span>開 ${fmt(m.open,1)}　高 ${fmt(m.high,1)}</span>
          <span>低 ${fmt(m.low,1)}　收 <b>${fmt(m.close,1)}</b></span>
          <span>漲跌 <b class="${cls(m.day_pct)}">${pct(m.day_pct)}</b>　MA20 ${ma}</span>
          <span>成交量 ${lots}</span>`;
        tip.style.left=`${Math.min(84,Math.max(16,left))}%`;
        tip.style.top=`${Math.max(10,top-7)}%`;
        tip.classList.add('show');
      }
      function hide(){
        tip.classList.remove('show');
        guideX.classList.remove('show'); guideY.classList.remove('show'); focus.classList.remove('show');
      }
    });
  });
}

function companyCard(c) {
  const actionTone = c.decision.action === 'ADD' ? 'good' : c.decision.action === 'TRIM' ? 'warn' : c.decision.action === 'EXIT REVIEW' ? 'bad' : 'blue';
  return `<section class="card">
    <div class="company-head">
      <div><h2>${esc(c.name)}</h2><div class="ticker">${c.id} · ${esc(c.role)}</div></div>
      <div><div class="price">${fmt(c.market.price,1)}</div><div class="delta ${cls(c.market.change_pct)}">${pct(c.market.change_pct)}</div></div>
    </div>
    ${sparkline(c.market.history)}
    <div class="status-row">
      ${badge(c.valuation.label, c.valuation.tone)}
      ${badge(c.fundamental.label, c.fundamental.tone)}
      ${badge(actionZh(c.decision.action), actionTone)}
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
    <div class="section-title"><h2>最新事件</h2><div class="hint">每30分鐘更新 · ${esc(d.news_updated_at||d.generated_at||"—")} · 點標題開原文</div></div>
    <section class="card"><ul class="list">${d.news.slice(0,12).map(n=>newsLink(n,true)).join('')}</ul></section>`;
}

function chipSection(c) {
  const ch=c.chips;
  if(!ch) {
    return `<div class="section-title"><h2>籌碼・分點</h2><div class="hint">等待盤後分點摘要更新</div></div>
      <section class="card"><div class="callout">目前尚未取得這檔股票的公開分點摘要；資料通常在交易日晚間更新。</div></section>`;
  }
  const signed=n=>n==null?'—':`${n>=0?'+':''}${fmt(n,0)} 張`;
  const buyer0=ch.top_buyers?.[0];
  const seller0=ch.top_sellers?.[0];
  const source=safeUrl(ch.source_url||'');
  const branchRows=(items,side)=> (items||[]).map((r,i)=>`<div class="chip-row">
    <div class="chip-rank">${i+1}</div>
    <div class="chip-name">${esc(r.name)}</div>
    <div class="chip-net ${cls(r.net)}">${signed(r.net)}</div>
    <div class="chip-share">${r.share_pct==null?'—':fmt(r.share_pct,2)+'%'}</div>
  </div>`).join('');
  return `
    <div class="section-title"><h2>籌碼・分點</h2><div class="hint">資料日 ${esc(ch.as_of||'—')} · ${source?`<a class="inline-source" href="${esc(source)}" target="_blank" rel="noopener noreferrer">公開來源 ↗</a>`:esc(ch.source||'')}</div></div>
    <div class="grid grid-4">
      <div class="card kpi"><div class="metric-label">近${ch.window_days||'—'}日最大買方</div><div class="big chip-big positive">${buyer0?esc(buyer0.name):'—'}</div><div class="small">${buyer0?signed(buyer0.net):'—'}${buyer0?.share_pct!=null?` · 占成交量 ${fmt(buyer0.share_pct,2)}%`:''}</div></div>
      <div class="card kpi"><div class="metric-label">近${ch.window_days||'—'}日最大賣方</div><div class="big chip-big negative">${seller0?esc(seller0.name):'—'}</div><div class="small">${seller0?signed(seller0.net):'—'}${seller0?.share_pct!=null?` · 占成交量 ${fmt(Math.abs(seller0.share_pct),2)}%`:''}</div></div>
      <div class="card kpi"><div class="metric-label">最新 CR15</div><div class="big">${ch.cr15_latest==null?'—':fmt(ch.cr15_latest,2)}</div><div class="small">近${ch.window_days||'—'}日平均 ${ch.cr15_avg==null?'—':fmt(ch.cr15_avg,2)}；值域 0–2</div></div>
      <div class="card kpi"><div class="metric-label">進出分點數</div><div class="big">${ch.branches_count==null?'—':fmt(ch.branches_count,0)}</div><div class="small">分點越多，通常代表參與來源越分散。</div></div>
    </div>

    <div class="grid grid-2 chip-columns">
      <section class="card chip-card">
        <div class="chip-card-head"><h3>近${ch.window_days||'—'}日買超 Top 3</h3><span>淨買超 / 區間成交占比</span></div>
        <div class="chip-table">${branchRows(ch.top_buyers,'buy') || '<div class="chip-empty">暫無資料</div>'}</div>
      </section>
      <section class="card chip-card">
        <div class="chip-card-head"><h3>近${ch.window_days||'—'}日賣超 Top 3</h3><span>淨賣超 / 區間成交占比</span></div>
        <div class="chip-table">${branchRows(ch.top_sellers,'sell') || '<div class="chip-empty">暫無資料</div>'}</div>
      </section>
    </div>

    ${ch.long_buyers?.length ? `<section class="card chip-long">
      <div class="chip-card-head"><h3>拉長到近${ch.long_window_days}日的主要買方</h3><span>觀察是否只是短線買盤，或有較長時間累積</span></div>
      <div class="chip-long-grid">${ch.long_buyers.map((r,i)=>`<div class="chip-long-item"><span>#${i+1} ${esc(r.name)}</span><strong class="${cls(r.net)}">${signed(r.net)}</strong></div>`).join('')}</div>
    </section>` : ''}

    <div class="chip-note">${esc(ch.note||'')}</div>`;
}

function companyPage(id) {
  const c=state.data.companies.find(x=>x.id===id);
  const actionTone = c.decision.action === 'ADD' ? 'good' : c.decision.action === 'TRIM' ? 'warn' : c.decision.action === 'EXIT REVIEW' ? 'bad' : 'blue';
  return `
    <div class="grid grid-2">
      <section class="card">
        <div class="company-head"><div><h2>${c.name} ${c.id}</h2><div class="ticker">${c.role}</div></div><div><div class="price">${fmt(c.market.price,1)}</div><div class="delta ${cls(c.market.change_pct)}">${pct(c.market.change_pct)}</div></div></div>
        ${sparkline(c.market.history)}
        <div class="status-row">${badge(c.valuation.label,c.valuation.tone)} ${badge(c.fundamental.label,c.fundamental.tone)} ${badge(actionZh(c.decision.action),actionTone)}</div>
      </section>
      <section class="action-box">
        <div class="metric-label">目前操作判斷</div>
        <div class="action ${actionTone==='good'?'positive':actionTone==='bad'?'negative':''}">${actionZh(c.decision.action)}</div>
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

    ${chipSection(c)}

    <div class="section-title"><h2>估值情境</h2><div class="hint">假設可在 config/valuation.json 修改</div></div>
    <section class="card"><div class="scenarios">${Object.entries(c.valuation.scenarios).map(([name,s])=>`<div class="scenario"><div class="name">${name.toUpperCase()}</div><div class="fair">${fmt(s.fair_value,0)}</div><div class="details">${esc(s.description)}</div></div>`).join('')}</div></section>

    <div class="section-title"><h2>紅旗與催化劑</h2></div>
    <div class="grid grid-2">
      <section class="card"><h3>催化劑</h3><ul class="list">${c.catalysts.map(x=>`<li><div class="title">${esc(x)}</div>${badge('Catalyst','good')}</li>`).join('')}</ul></section>
      <section class="card"><h3>紅旗</h3><ul class="list">${c.red_flags.map(x=>`<li><div class="title">${esc(x)}</div>${badge('Risk','bad')}</li>`).join('')}</ul></section>
    </div>

    <div class="section-title"><h2>最近新聞</h2><div class="hint">每30分鐘更新 · ${esc(state.data.news_updated_at||state.data.generated_at||"—")} · 點標題開原文</div></div>
    <section class="card"><ul class="list">${state.data.news.filter(n=>n.company_id===id).slice(0,12).map(n=>newsLink(n,false)).join('') || '<li><div class="title">暫無資料</div></li>'}</ul></section>`;
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
        ${state.data.companies.map(c=>`<tr><td>${c.name} ${c.id}</td><td>${fmt(c.market.price,1)}</td><td>${fmt(c.valuation.scenarios.bear.fair_value,0)}</td><td>${fmt(c.valuation.scenarios.base.fair_value,0)}</td><td>${fmt(c.valuation.scenarios.bull.fair_value,0)}</td><td class="${cls(c.valuation.base_upside_pct)}">${pct(c.valuation.base_upside_pct)}</td><td>${actionZh(c.decision.action)}</td></tr>`).join('')}
      </tbody></table></div>
    </section>
    <div class="section-title"><h2>決策規則</h2></div>
    <div class="grid grid-2">
      <section class="card"><h3>價格規則</h3><ul class="list"><li><div class="title">加碼觀察：價格低於 Base fair value 約 15% 以上，且基本面沒有紅旗。</div></li><li><div class="title">續抱觀察：價格落在 Base 附近，等待下一個基本面驗證。</div></li><li><div class="title">減碼：價格高於 Base 約 15% 以上，但新資訊沒有同步上修合理價。</div></li><li><div class="title">重新檢視／退出：基本面出現兩項以上重大紅旗，不因股價便宜自動加碼。</div></li></ul></section>
      <section class="card"><h3>重要原則</h3><ul class="list"><li><div class="title">政美：未證實的台積電量產訂單不納入 Base case。</div></li><li><div class="title">由田：14.6535 億採購額不直接等於同期營收。</div></li><li><div class="title">南亞：拆分本業 EPS 與南亞科／南電／台塑石化等轉投資貢獻。</div></li></ul></section>
    </div>`;
}

function render() {
  if (!state.data) return;
  const app=document.getElementById('app');
  app.innerHTML = state.tab==='overview' ? overview() : state.tab==='broker' ? brokerPage() : state.tab==='valuation' ? valuationPage() : companyPage(state.tab);
  document.querySelectorAll('#tabs button').forEach(b=>b.classList.toggle('active',b.dataset.tab===state.tab));
  bindSparkTooltips();
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
