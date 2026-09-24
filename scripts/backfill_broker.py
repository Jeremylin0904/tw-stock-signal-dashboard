#!/usr/bin/env python3
"""Backfill a historical broker-branch series (requires FinMind Sponsor token).

Example:
  FINMIND_SPONSOR_TOKEN=xxx python scripts/backfill_broker.py \
    --stock 7853 --branch 9887 --start 2026-03-01 --end 2026-04-30
"""
import argparse, datetime as dt, json, os, pathlib, time, urllib.parse, urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
UA='Mozilla/5.0 (compatible; tw-stock-signal-dashboard/1.0)'

def get_json(url,params,token):
    u=url+'?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(u,headers={'User-Agent':UA,'Authorization':f'Bearer {token}'})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--stock',default='7853')
    ap.add_argument('--branch',default='9887')
    ap.add_argument('--start',required=True)
    ap.add_argument('--end',required=True)
    args=ap.parse_args()
    token=os.getenv('FINMIND_SPONSOR_TOKEN')
    if not token: raise SystemExit('FINMIND_SPONSOR_TOKEN is required')
    start=dt.date.fromisoformat(args.start); end=dt.date.fromisoformat(args.end)
    rows=[]; d=start
    while d<=end:
        if d.weekday()<5:
            try:
                p=get_json('https://api.finmindtrade.com/api/v4/taiwan_stock_trading_daily_report',{'data_id':args.stock,'date':d.isoformat()},token)
                data=[x for x in p.get('data',[]) if str(x.get('securities_trader_id'))==args.branch]
                if data:
                    buy=sum(float(x.get('buy',0) or 0) for x in data)/1000
                    sell=sum(float(x.get('sell',0) or 0) for x in data)/1000
                    rows.append({'date':d.isoformat(),'stock_id':args.stock,'branch_id':args.branch,'buy_lots':round(buy,3),'sell_lots':round(sell,3),'net_lots':round(buy-sell,3)})
            except Exception as e:
                print('WARN',d,e)
            time.sleep(.15)
        d += dt.timedelta(days=1)
    out=ROOT/'site'/'data'/f'broker_history_{args.stock}_{args.branch}_{args.start}_{args.end}.json'
    out.write_text(json.dumps({'stock_id':args.stock,'branch_id':args.branch,'start':args.start,'end':args.end,'rows':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(out)

if __name__=='__main__': main()
