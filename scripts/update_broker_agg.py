#!/usr/bin/env python3
"""Refresh 7853 × 9887 with FinMind's sponsor aggregate endpoint.

Uses TaiwanStockTradingDailyReportSecIdAgg, which is designed for querying
one stock + one broker branch across a date range.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import pathlib
import urllib.parse
import urllib.request
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "site" / "data" / "dashboard.json"
UA = "Mozilla/5.0 (compatible; tw-stock-signal-dashboard/1.0)"
TZ = dt.timezone(dt.timedelta(hours=8))

def get_json(url, params, token):
    req = urllib.request.Request(
        url + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": UA, "Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"FinMind broker API error {e.code}: {body[:1000]}")
        raise

def main():
    token = os.getenv("FINMIND_SPONSOR_TOKEN")
    if not token:
        print("No FINMIND_SPONSOR_TOKEN; keep existing broker data.")
        return

    data = json.loads(DASHBOARD.read_text(encoding="utf-8"))
    end = dt.datetime.now(TZ).date()
    start = end - dt.timedelta(days=45)

    payload = get_json(
        "https://api.finmindtrade.com/api/v4/taiwan_stock_trading_daily_report_secid_agg",
        {
            "data_id": "7853",
            "securities_trader_id": "9887",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
        token,
    )
    rows = payload.get("data", [])
    if not rows:
        print("Sponsor token works, but SecIdAgg returned no 7853 × 9887 rows. Keeping current broker data.")
        return

    close_map = {}
    for c in data.get("companies", []):
        if c.get("id") == "7853":
            close_map = {x.get("date"): x.get("close") for x in c.get("market", {}).get("history", [])}

    hist = []
    cum = 0.0
    for r in sorted(rows, key=lambda x: x.get("date", "")):
        buy = float(r.get("buy_volume", 0) or 0) / 1000.0
        sell = float(r.get("sell_volume", 0) or 0) / 1000.0
        net = buy - sell
        cum += net
        hist.append({
            "date": r.get("date"),
            "stock_id": "7853",
            "close": close_map.get(r.get("date")),
            "buy_lots": round(buy, 2),
            "sell_lots": round(sell, 2),
            "net": round(net, 2),
            "cum": round(cum, 2),
            "buy_price": r.get("buy_price"),
            "sell_price": r.get("sell_price"),
            "volume_share_pct": None,
        })

    net5 = sum(x["net"] for x in hist[-5:])
    net20 = sum(x["net"] for x in hist[-20:])
    if net5 > 0 and net20 > 0:
        pattern = "持續建倉"
    elif net5 < 0 and net20 < 0:
        pattern = "持續出貨"
    elif net5 > 0 >= net20:
        pattern = "近期轉買"
    elif net5 < 0 <= net20:
        pattern = "近期轉賣"
    else:
        pattern = "中性"

    b = data.setdefault("broker", {})
    # Keep manually curated cross-stock radar until we add a full branch-wide scanner.
    cross = b.get("cross_stock", [])
    b.update({
        "branch_id": "9887",
        "branch_name": "元大經紀",
        "source": "FinMind Sponsor / SecIdAgg",
        "target": {
            "stock_id": "7853",
            "as_of": hist[-1]["date"],
            "net_5d": round(net5, 2),
            "net_20d": round(net20, 2),
            "pattern": pattern,
            "pattern_note": "以 FinMind Sponsor 的 TaiwanStockTradingDailyReportSecIdAgg 直接查詢 7853 × 9887。",
            "history": hist,
        },
        "cross_stock": cross,
        "data_note": "分點是券商經紀部客戶交易彙總，不等於單一投資人。分點資料通常於交易日晚間更新。",
    })

    DASHBOARD.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated broker: {len(hist)} dates, latest={hist[-1]['date']}, net5={net5:.2f}, net20={net20:.2f}")

if __name__ == "__main__":
    main()
