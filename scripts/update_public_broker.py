#!/usr/bin/env python3
"""Refresh broker-branch summary from publicly visible Signova stock pages.

This intentionally records only what the public page exposes:
- recent-window Top 3 broker branches and their share of interval volume
- longer-window Top 3 when the page exposes one
- latest CR15, recent average CR15, branch count
It does NOT pretend these Top-3 summaries are a complete broker ledger.
"""
from __future__ import annotations
import datetime as dt
import html
from html.parser import HTMLParser
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "site" / "data" / "dashboard.json"
HISTORY = ROOT / "site" / "data" / "public_broker_history.json"
CONFIG = ROOT / "config" / "public_broker_watchlist.json"
UA = "Mozilla/5.0 (compatible; tw-stock-signal-dashboard/1.0; public-summary-bot)"
TZ = dt.timezone(dt.timedelta(hours=8))

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
    def handle_data(self, data):
        t=data.strip()
        if t: self.parts.append(t)

def fetch_text(stock_id: str) -> str:
    url=f"https://signova.tw/stock/{stock_id}"
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=25) as r:
        raw=r.read().decode("utf-8",errors="replace")
    p=TextParser(); p.feed(raw)
    return re.sub(r"\s+"," ",html.unescape(" ".join(p.parts)))

def num(s):
    return float(s.replace(",",""))

def entries(segment: str, side: str):
    # Examples: 9887（買超 154 張）, 9887 買超 154 張（占區間成交量 3.47%）
    out=[]
    pat1=rf"([^、；。]+?)（{side}\s*([\d,]+)\s*張(?:，[^）]*)?）"
    for name,n in re.findall(pat1,segment):
        out.append({"name":name.strip(),"net":num(n)*(1 if side=="買超" else -1)})
    pat2=rf"([^、；。]+?)\s+{side}\s*([\d,]+)\s*張(?:（占區間成交量\s*([\d.]+)%）)?"
    for name,n,share in re.findall(pat2,segment):
        clean=name.strip()
        if not any(x["name"]==clean for x in out):
            out.append({"name":clean,"net":num(n)*(1 if side=="買超" else -1),"share_pct":float(share) if share else None})
    return out

def find_branch(items, branch_id):
    for rank,x in enumerate(items,1):
        if branch_id in x["name"]:
            return {**x,"rank":rank}
    return None

def parse_page(text: str, branch_id: str):
    m=re.search(r"近\s*(\d+)\s*個交易日（([^）]+)），買超張數最多的券商分點是(.*?)；同期賣超最多的是(.*?)(?:。|拉長到近)",text)
    if not m:
        # Some very new stocks expose "近 4 個交易日" but same wording; allow end before latest-day sentence.
        m=re.search(r"近\s*(\d+)\s*個交易日（([^）]+)），買超張數最多的券商分點是(.*?)；同期賣超最多的是(.*?)(?:。|\d{1,2}/\d{1,2}\s*當天)",text)
    window_days=int(m.group(1)) if m else None
    range_label=m.group(2) if m else None
    buyers=entries(m.group(3),"買超") if m else []
    sellers=entries(m.group(4),"賣超") if m else []

    # Table-style text usually includes interval share; use it to enrich Top 3.
    table_buy=re.search(r"買超前\s*3\s*分點\s*\|?\s*(.*?)\s*賣超前\s*3\s*分點",text)
    if table_buy:
        tb=entries(table_buy.group(1),"買超")
        if tb: buyers=tb
    table_sell=re.search(r"賣超前\s*3\s*分點\s*\|?\s*(.*?)\s*最新交易日\s*CR15",text)
    if table_sell:
        ts=entries(table_sell.group(1),"賣超")
        if ts: sellers=ts

    branch=find_branch(buyers,branch_id) or find_branch(sellers,branch_id)

    long_days=None; long_branch=None
    lm=re.search(r"拉長到近\s*(\d+)\s*個交易日，買超最多的是(.*?)(?:。|\d{1,2}/\d{1,2}\s*當天)",text)
    if lm:
        long_days=int(lm.group(1))
        long_items=entries(lm.group(2),"買超")
        long_branch=find_branch(long_items,branch_id)

    cr=re.search(r"最新交易日\s*CR15\s*集中度\s*\|?\s*([\d.]+)",text)
    if not cr:
        cr=re.search(r"籌碼集中度\s*CR15\s*為\s*([\d.]+)",text)
    avg=re.search(r"近\s*(\d+)\s*日平均\s*CR15\s*\|?\s*([\d.]+)",text)
    count=re.search(r"最新交易日進出分點數\s*\|?\s*([\d,]+)\s*個",text)
    date=re.search(r"分點資料日\s*(\d{4}-\d{2}-\d{2})",text)
    if not date:
        date=re.search(r"資料日範圍\s*\|?\s*(\d{4}-\d{2}-\d{2})\s*[～~]\s*(\d{4}-\d{2}-\d{2})",text)
    source_date=(date.group(2) if date and date.lastindex==2 else date.group(1)) if date else None

    return {
        "source_date":source_date,
        "window_days":window_days,
        "range_label":range_label,
        "branch":branch,
        "long_window_days":long_days,
        "long_branch":long_branch,
        "cr15_latest":float(cr.group(1)) if cr else None,
        "cr15_avg":float(avg.group(2)) if avg else None,
        "branches_count":int(count.group(1).replace(",","")) if count else None,
        "top_buyers":buyers,
        "top_sellers":sellers,
    }

def label_pattern(short_net, long_net):
    if short_net is None: return "未進 Top 3"
    if long_net is None: return "近期買超" if short_net>0 else "近期賣超"
    if short_net>0 and long_net>0: return "持續累積"
    if short_net<0 and long_net<0: return "持續賣出"
    if short_net>0>=long_net: return "近期轉買"
    if short_net<0<=long_net: return "近期轉賣"
    return "中性"

def main():
    cfg=json.loads(CONFIG.read_text(encoding="utf-8"))
    data=json.loads(DASHBOARD.read_text(encoding="utf-8"))
    history=json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else {"snapshots":[]}
    branch_id=cfg["branch_id"]
    parsed={}
    for item in cfg["radar"]:
        try:
            text=fetch_text(item["id"])
            parsed[item["id"]]=parse_page(text,branch_id)
            print(item["id"],parsed[item["id"]])
        except Exception as e:
            print("WARN public broker",item["id"],repr(e))

    target_id=cfg["target"]["id"]
    t=parsed.get(target_id)
    if not t:
        print("No public target summary; keeping existing broker block.")
        return

    short=t.get("branch")
    longb=t.get("long_branch")
    short_net=short.get("net") if short else None
    long_net=longb.get("net") if longb else None
    short_share=short.get("share_pct") if short else None
    pattern=label_pattern(short_net,long_net)

    snap={
        "observed_at":dt.datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
        "source_date":t.get("source_date"),
        "stock_id":target_id,
        "window_days":t.get("window_days"),
        "net":short_net,
        "rank":short.get("rank") if short else None,
        "share_pct":short_share,
        "long_window_days":t.get("long_window_days"),
        "long_net":long_net,
        "long_rank":longb.get("rank") if longb else None,
        "cr15_latest":t.get("cr15_latest"),
        "cr15_avg":t.get("cr15_avg"),
        "branches_count":t.get("branches_count"),
    }
    snaps=history.setdefault("snapshots",[])
    # One snapshot per source data date; replace if the source revised it.
    key=(snap["stock_id"],snap["source_date"])
    snaps[:]=[x for x in snaps if (x.get("stock_id"),x.get("source_date"))!=key]
    snaps.append(snap)
    snaps.sort(key=lambda x:(x.get("source_date") or "",x.get("observed_at") or ""))
    history["source"]="Signova public stock pages (summary only)"
    HISTORY.write_text(json.dumps(history,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    cross=[]
    names={x["id"]:x["name"] for x in cfg["radar"]}
    for sid,p in parsed.items():
        b=p.get("branch"); lb=p.get("long_branch")
        n=b.get("net") if b else None
        ln=lb.get("net") if lb else None
        cross.append({
            "id":sid,
            "name":names.get(sid,sid),
            "net_5d":n,
            "short_window_days":p.get("window_days"),
            "net_20d":ln,
            "long_window_days":p.get("long_window_days"),
            "share_pct":b.get("share_pct") if b else None,
            "estimated_value_m":None,
            "pattern":label_pattern(n,ln),
            "rank":b.get("rank") if b else None,
            "cr15_latest":p.get("cr15_latest"),
            "source_date":p.get("source_date"),
        })

    b=data.setdefault("broker",{})
    # Keep any genuine daily ledger in history; public source does not provide it.
    old_daily=b.get("target",{}).get("history",[])
    b.update({
        "branch_id":branch_id,
        "branch_name":cfg["branch_name"],
        "source":"Signova 公開分點摘要",
        "target":{
            "stock_id":target_id,
            "as_of":t.get("source_date") or "—",
            "net_5d":short_net,
            "short_window_days":t.get("window_days"),
            "net_20d":long_net,
            "long_window_days":t.get("long_window_days"),
            "rank":short.get("rank") if short else None,
            "share_pct":short_share,
            "cr15_latest":t.get("cr15_latest"),
            "cr15_avg":t.get("cr15_avg"),
            "branches_count":t.get("branches_count"),
            "pattern":pattern,
            "pattern_note":f"公開頁僅提供 Top 3 摘要；{branch_id} 若未進 Top 3，不代表當日/區間沒有交易。",
            "history":old_daily,
            "summary_history":snaps[-30:],
        },
        "cross_stock":cross,
        "data_note":"來源為 Signova 公開個股頁的分點籌碼摘要；其排名只統計公開頁呈現的 Top 3/上榜資訊，不是完整券商帳本。CR15 的母體與 Top 分點排名不同。同一分點也不代表單一投資人。",
    })
    DASHBOARD.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Public broker summary updated:",target_id,t.get("source_date"),short_net,long_net)

if __name__=="__main__":
    main()
