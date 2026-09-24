#!/usr/bin/env python3
"""Update the static dashboard JSON.

Data policy:
- Market prices: Yahoo chart endpoint (secondary/unofficial).
- Monthly revenue / financials: FinMind when a token is configured.
- Broker branch: FinMind Sponsor endpoint when FINMIND_SPONSOR_TOKEN exists.
- News: Google News RSS discovery; confidence is keyword-based and should not replace official filings.
- On any provider error, keep the previous known-good data instead of writing blanks.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import pathlib
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "site" / "data"
DASHBOARD = SITE_DATA / "dashboard.json"
WATCHLIST = ROOT / "config" / "watchlist.json"
VALUATION = ROOT / "config" / "valuation.json"
SIGNALS = ROOT / "config" / "signals.json"
MANUAL_BROKER = SITE_DATA / "manual_broker.json"

TZ = dt.timezone(dt.timedelta(hours=8))
UA = "Mozilla/5.0 (compatible; tw-stock-signal-dashboard/1.0; +https://github.com/)"


def load(path: pathlib.Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path: pathlib.Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def http_json(url: str, params=None, headers=None, timeout=20):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def yahoo_history(symbol: str, days=90):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}"
    payload = http_json(url, {"range": "3mo", "interval": "1d", "events": "div,splits"})
    result = payload["chart"]["result"][0]
    stamps = result.get("timestamp", [])
    closes = result["indicators"]["quote"][0].get("close", [])
    rows = []
    for ts, close in zip(stamps, closes):
        if close is None:
            continue
        day = dt.datetime.fromtimestamp(ts, TZ).date().isoformat()
        rows.append({"date": day, "close": round(float(close), 3)})
    rows = rows[-days:]
    if not rows:
        raise RuntimeError("Yahoo returned no price rows")
    latest = rows[-1]["close"]
    prev = rows[-2]["close"] if len(rows) >= 2 else latest
    change = ((latest / prev) - 1) * 100 if prev else 0
    return latest, round(change, 3), rows


def finmind(dataset: str, stock_id: str | None = None, start_date: str | None = None, token: str | None = None):
    params = {"dataset": dataset}
    if stock_id:
        params["data_id"] = stock_id
    if start_date:
        params["start_date"] = start_date
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        params["token"] = token
    payload = http_json("https://api.finmindtrade.com/api/v4/data", params, headers)
    if payload.get("status") not in (200, None) and not payload.get("data"):
        raise RuntimeError(payload.get("msg") or f"FinMind error: {payload.get('status')}")
    return payload.get("data", [])


def update_revenue(company: dict, token: str | None):
    if not token:
        return
    start = (dt.date.today().replace(day=1) - dt.timedelta(days=500)).isoformat()
    rows = finmind("TaiwanStockMonthRevenue", company["id"], start, token)
    if not rows:
        return
    def key(r):
        if r.get("revenue_year") and r.get("revenue_month"):
            return int(r["revenue_year"]), int(r["revenue_month"])
        return (r.get("date") or "")
    rows = sorted(rows, key=key)
    cur = rows[-1]
    revenue = float(cur.get("revenue", 0) or 0)
    yoy = cur.get("revenue_year_on_year")
    mom = cur.get("revenue_month_on_month")
    if yoy is None and len(rows) >= 13:
        old = float(rows[-13].get("revenue", 0) or 0)
        yoy = (revenue / old - 1) * 100 if old else None
    if mom is None and len(rows) >= 2:
        old = float(rows[-2].get("revenue", 0) or 0)
        mom = (revenue / old - 1) * 100 if old else None
    ym = f"{cur.get('revenue_year','')}-{int(cur.get('revenue_month',0) or 0):02d}" if cur.get("revenue_year") else (cur.get("date") or "")[:7]
    company["revenue"].update({"period": ym, "value_twd": round(revenue, 0), "yoy": round(float(yoy), 2) if yoy is not None else None, "mom": round(float(mom), 2) if mom is not None else None, "source": "FinMind / company filings"})


def google_news(company: dict, max_items=5):
    q = urllib.parse.quote_plus(f'{company["name"]} {company["id"]}')
    url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    out = []
    for item in root.findall(".//item")[:max_items]:
        title = (item.findtext("title") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        source = item.find("source")
        source_text = source.text.strip() if source is not None and source.text else "Google News"
        link = (item.findtext("link") or "").strip()
        try:
            date = dt.datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z").date().isoformat()
        except Exception:
            date = pub[:16]
        out.append({"company": company["name"], "company_id": company["id"], "title": title, "date": date, "source": source_text, "url": link, "confidence": "secondary"})
    return out


def classify_news(items, signals):
    official = [x.lower() for x in signals["keywords"]["confirmed"]]
    rumor = [x.lower() for x in signals["keywords"]["rumor"]]
    for n in items:
        t = n["title"].lower()
        if any(k in t for k in rumor):
            n["confidence"] = "rumor"
        elif any(k in t for k in official) and any(x in n["source"] for x in ["中央社", "MoneyDJ", "鉅亨", "經濟日報", "工商時報"]):
            n["confidence"] = "secondary"
    return items


def valuation_fair(cfg):
    out = {}
    for name, s in cfg["scenarios"].items():
        if cfg["model"] == "forward_eps":
            fair = float(s["eps"]) * float(s["pe"])
            desc = f"EPS {s['eps']} × P/E {s['pe']}x"
        else:
            fair = float(s["forward_revenue_m"]) * float(s["ps"]) / float(cfg["shares_m"])
            desc = f"Forward revenue {s['forward_revenue_m']}M × P/S {s['ps']}x ÷ {cfg['shares_m']}M shares"
        out[name] = {"fair_value": round(fair, 1), "description": desc}
    return out


def apply_valuation(company: dict, cfg: dict, rules: dict):
    sc = valuation_fair(cfg)
    price = float(company["market"].get("price") or 0)
    base = sc["base"]["fair_value"]
    upside = (base / price - 1) * 100 if price else None
    if upside is None:
        label, tone = "無價格", "warn"
    elif upside >= 15:
        label, tone = "偏便宜", "good"
    elif upside <= -15:
        label, tone = "偏貴", "bad"
    else:
        label, tone = "合理區間", "blue"
    company["valuation"] = {"label": label, "tone": tone, "base_fair": base, "base_upside_pct": round(upside, 1) if upside is not None else None, "scenarios": sc, "notes": cfg.get("notes", "")}

    red_count = int(company.get("fundamental", {}).get("red_flag_count", 0))
    if red_count >= rules["exit_review_red_flags"]:
        action = "EXIT REVIEW"
        reason = "重大基本面紅旗達到門檻；先重新驗證投資論點，不因下跌自動攤平。"
    elif upside is not None and upside >= abs(rules["add_below_base_pct"]):
        action = "ADD"
        reason = "價格相對 Base fair value 留有安全邊際，且目前紅旗未達退出門檻。"
    elif upside is not None and upside <= -abs(rules["trim_above_base_pct"]):
        action = "TRIM"
        reason = "現價已高於 Base fair value 約15%以上；除非新基本面足以同步上修合理價，否則降低追價風險。"
    else:
        action = "HOLD"
        reason = "價格接近 Base 情境；等待下一個可驗證的營收、訂單、毛利或現金流訊號。"
    company["decision"].update({"action": action, "reason": reason})


def weekdays_back(n=25):
    d = dt.date.today()
    out=[]
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= dt.timedelta(days=1)
    return list(reversed(out))


def finmind_broker_by_stock(stock_id: str, day: dt.date, token: str):
    url = "https://api.finmindtrade.com/api/v4/taiwan_stock_trading_daily_report"
    params = {"data_id": stock_id, "date": day.isoformat()}
    payload = http_json(url, params, {"Authorization": f"Bearer {token}"}, timeout=30)
    return payload.get("data", [])


def finmind_broker_by_branch(branch_id: str, day: dt.date, token: str):
    url = "https://api.finmindtrade.com/api/v4/taiwan_stock_trading_daily_report"
    params = {"securities_trader_id": branch_id, "date": day.isoformat()}
    payload = http_json(url, params, {"Authorization": f"Bearer {token}"}, timeout=30)
    return payload.get("data", [])


def broker_from_manual(existing: dict):
    manual = load(MANUAL_BROKER, {}) or {}
    rows = manual.get("target_history", [])
    cum=0
    hist=[]
    for r in rows:
        cum += float(r.get("net", 0))
        hist.append({**r, "cum": round(cum, 2)})
    net5 = sum(float(r.get("net",0)) for r in rows[-5:]) if rows else 0
    net20 = sum(float(r.get("net",0)) for r in rows[-20:]) if rows else 0
    pattern = "建倉觀察" if net5 > 0 and net20 >= 0 else "出貨觀察" if net5 < 0 else "中性"
    existing.update({
        "branch_id": "9887", "branch_name": "元大經紀", "source": "manual fallback",
        "target": {"stock_id": "7853", "as_of": rows[-1]["date"] if rows else "—", "net_5d": round(net5,1), "net_20d": round(net20,1), "pattern": pattern, "pattern_note": "手動備援資料；有 Sponsor token 時會改用自動分點資料。", "history": hist},
        "cross_stock": manual.get("cross_stock", []),
        "data_note": "分點資料只代表該券商營業據點的客戶交易彙總，不代表單一大戶。自動逐分點資料需要 FinMind Sponsor 方案；未設定時使用 manual_broker.json。"
    })


def update_broker(existing: dict, token: str | None, market_hist: dict[str, list]):
    if not token:
        broker_from_manual(existing)
        return
    branch_id="9887"
    days=weekdays_back(22)
    hist=[]
    close_by_date={r["date"]:r["close"] for r in market_hist.get("7853",[])}
    for day in days:
        try:
            rows=finmind_broker_by_stock("7853", day, token)
        except Exception:
            continue
        f=[r for r in rows if str(r.get("securities_trader_id"))==branch_id]
        if not f:
            continue
        buy=sum(float(r.get("buy",0) or 0) for r in f)/1000
        sell=sum(float(r.get("sell",0) or 0) for r in f)/1000
        total=sum(float(r.get("buy",0) or 0)+float(r.get("sell",0) or 0) for r in rows)/1000
        net=buy-sell
        hist.append({"date":day.isoformat(),"stock_id":"7853","close":close_by_date.get(day.isoformat()),"net":round(net,2),"volume_share_pct":round((buy+sell)/total*100,2) if total else 0})
    cum=0
    for r in hist:
        cum += r["net"]
        r["cum"] = round(cum,2)
    net5=sum(r["net"] for r in hist[-5:])
    net20=sum(r["net"] for r in hist[-20:])
    pattern="建倉" if net5>0 and net20>0 else "出貨" if net5<0 and net20<0 else "反轉/中性"

    cross={}
    for day in days[-5:]:
        try:
            rows=finmind_broker_by_branch(branch_id, day, token)
        except Exception:
            continue
        for r in rows:
            sid=str(r.get("stock_id",""))
            if not sid:
                continue
            x=cross.setdefault(sid,{"buy":0.0,"sell":0.0})
            x["buy"] += float(r.get("buy",0) or 0)/1000
            x["sell"] += float(r.get("sell",0) or 0)/1000
    ranked=sorted(((sid,v["buy"]-v["sell"]) for sid,v in cross.items()), key=lambda x:abs(x[1]), reverse=True)[:12]
    cross_rows=[{"id":sid,"name":sid,"net_5d":round(net,1),"net_20d":None,"share_pct":None,"estimated_value_m":None,"pattern":"大額淨買" if net>0 else "大額淨賣"} for sid,net in ranked]
    existing.update({"branch_id":branch_id,"branch_name":"元大經紀","source":"FinMind Sponsor","target":{"stock_id":"7853","as_of":hist[-1]["date"] if hist else "—","net_5d":round(net5,1),"net_20d":round(net20,1),"pattern":pattern,"pattern_note":"自動逐日彙總。仍不可把同一分點視為單一投資人。","history":hist},"cross_stock":cross_rows,"data_note":"資料由 FinMind Sponsor 分點資料彙整。分點是券商營業據點，不代表單一帳戶。"})


def main():
    watch=load(WATCHLIST,{})
    valuation=load(VALUATION,{})
    signals=load(SIGNALS,{})
    data=load(DASHBOARD,{}) or {}
    by_id={c["id"]:c for c in data.get("companies",[])}
    market_hist={}

    for w in watch.get("companies",[]):
        c=by_id.get(w["id"])
        if not c:
            continue
        try:
            price,chg,hist=yahoo_history(w["yahoo_symbol"])
            c["market"].update({"price":price,"change_pct":chg,"as_of":hist[-1]["date"],"history":hist})
            market_hist[w["id"]]=hist
        except Exception as e:
            print(f"WARN price {w['id']}: {e}")
            market_hist[w["id"]]=c.get("market",{}).get("history",[])
        try:
            update_revenue(c, os.getenv("FINMIND_TOKEN"))
        except Exception as e:
            print(f"WARN revenue {w['id']}: {e}")
        try:
            items=google_news(w,5)
            data.setdefault("news",[])
            data["news"]=[n for n in data["news"] if n.get("company_id")!=w["id"]]
            data["news"].extend(classify_news(items,signals))
        except Exception as e:
            print(f"WARN news {w['id']}: {e}")
        apply_valuation(c, valuation[w["id"]], signals["decision"])

    try:
        update_broker(data.setdefault("broker",{}), os.getenv("FINMIND_SPONSOR_TOKEN"), market_hist)
    except Exception as e:
        print(f"WARN broker: {e}")
        broker_from_manual(data.setdefault("broker",{}))

    data["news"] = sorted(data.get("news",[]), key=lambda x:x.get("date",""), reverse=True)[:30]
    data["generated_at"] = dt.datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    data["mode"] = "自動更新" + ("＋分點Sponsor" if os.getenv("FINMIND_SPONSOR_TOKEN") else "（分點手動備援）")
    data["companies"]=[by_id[w["id"]] for w in watch.get("companies",[]) if w["id"] in by_id]
    save(DASHBOARD,data)
    print(f"Updated {DASHBOARD}")

if __name__ == "__main__":
    main()
