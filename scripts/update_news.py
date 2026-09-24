#!/usr/bin/env python3
"""Refresh only the news feed for the static dashboard."""
from __future__ import annotations
import datetime as dt
import pathlib
import sys

HERE=pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0,str(HERE))

from update_data import DASHBOARD, WATCHLIST, SIGNALS, TZ, load, save, google_news, classify_news

def main():
    data=load(DASHBOARD,{}) or {}
    watch=load(WATCHLIST,{}) or {}
    signals=load(SIGNALS,{}) or {}
    items=[]
    for company in watch.get("companies",[]):
        try:
            items.extend(classify_news(google_news(company,10),signals))
        except Exception as e:
            print(f"WARN news {company.get('id')}: {e}")

    # Dedupe by URL when available, otherwise title/company.
    seen=set()
    dedup=[]
    for n in sorted(items,key=lambda x:x.get("published_at") or x.get("date") or "",reverse=True):
        key=n.get("url") or (n.get("company_id"),n.get("title"))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(n)

    # If all providers fail, preserve the last good feed.
    if dedup:
        data["news"]=dedup[:50]
    now=dt.datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    data["news_updated_at"]=now
    save(DASHBOARD,data)
    print(f"News refreshed at {now}: {len(dedup)} items")

if __name__=="__main__":
    main()
