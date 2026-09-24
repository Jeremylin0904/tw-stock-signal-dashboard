#!/usr/bin/env python3
import json, pathlib, datetime as dt
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'site'/'data'/'dashboard.json'

def company(id,name,role,price,chg,history,revenue,fundamental,thesis,next_verification,kpis,pipeline,catalysts,red_flags,alerts,decision):
    return {"id":id,"name":name,"role":role,"market":{"price":price,"change_pct":chg,"as_of":"2026-09-24" if id=='7853' else "2026-09-23","history":history},"revenue":revenue,"fundamental":fundamental,"thesis":thesis,"next_verification":next_verification,"kpis":kpis,"pipeline":pipeline,"catalysts":catalysts,"red_flags":red_flags,"alerts":alerts,"decision":decision,"valuation":{}}

data={
  "generated_at":"2026-09-24 14:30",
  "mode":"Seed snapshot；執行 scripts/update_data.py 後改為自動更新",
  "companies":[
    company("7853","政美應用","3D Metrology / RDL / Bump / CoWoS 量測",376.5,5.8,[{"date":"2026-09-23","close":356.0},{"date":"2026-09-24","close":376.5}],{"period":"2026-08","value_twd":30300000,"yoy":10.87,"mom":-68.1,"source":"公開月營收"},{"label":"尚待驗證","tone":"warn","red_flag_count":1},"技術與先進封裝題材強，但市場真正需要驗證的是新一波設備能否從驗證機變成 repeat order 與多台量產機。","repeat order / 多台量產 / 存貨轉營收",[
      {"label":"H1 毛利率","value":"46.6%","note":"高毛利不是主要問題，規模與固定成本吸收才是。"},
      {"label":"H1 EPS","value":"-1.08","note":"營收放大後應看到 Operating Leverage。"},
      {"label":"9887 近5日","value":"+160 張","note":"目前是值得追的籌碼線索，不等於單一大戶。"},
      {"label":"8月營收 MoM","value":"-68.1%","note":"月營收仍高度跳動，尚未證明穩定量產。"}
    ],[
      {"name":"歷史 TSMC 合作","status":"ok","note":"既有合作/客群基礎不是本輪需要驗證的核心。"},
      {"name":"新設備驗證","status":"partial","note":"市場有相關報導，但需官方/財報交叉驗證。"},
      {"name":"Qualification","status":"partial","note":"等待更明確的正式認證訊號。"},
      {"name":"量產導入","status":"partial","note":"需要連續季度營收而非單月爆發。"},
      {"name":"Repeat order","status":"no","note":"尚缺可公開驗證的大量追加訂單。"},
      {"name":"營益轉正","status":"no","note":"H1仍虧損。"},
      {"name":"現金流驗證","status":"no","note":"要看存貨→營收→應收→現金的轉換。"}
    ],["新客戶 qualification / Tool Matching 完成","量產導入與 repeat order","連續兩季營收放大且毛利維持高檔","存貨下降、營業現金流改善"],["媒體接單消息曾由公司澄清為自行推估","2025營運預估曾大幅落空","高存貨若無法轉成營收可能代表驗收延後","仍虧損但市值已反映高成長"],[
      {"level":"觀察","text":"9887近期集中買超","why":"需等9/24後續是否持續累積或反轉。"},
      {"level":"風險","text":"8月營收月減幅大","why":"量產收入仍不像穩定流水。"},
      {"level":"正面","text":"H1毛利率維持46%上下","why":"若營收放大，具營運槓桿條件。"}
    ],{"action":"HOLD","reason":"由估值引擎於更新時重新計算。","change_condition":"若 repeat order、多台量產與營益轉正得到驗證，可上修 Base；若存貨續升但營收/現金流不動，下修。"}),
    company("3455","由田","AOI / 先進封裝缺陷檢測",244.0,0.0,[{"date":"2026-09-23","close":244.0}],{"period":"2026-08","value_twd":206000000,"yoy":22.4,"mom":None,"source":"公開月營收"},{"label":"轉型驗證中","tone":"blue","red_flag_count":0},"矽品累積14.6535億元設備採購提供硬證據；接下來不是問有沒有訂單，而是訂單何時轉成營收、毛利與EPS。","矽品採購認列速度 / 月營收階梯",[
      {"label":"矽品累積採購","value":"14.6535 億","note":"已確認採購，不直接等於同期間營收。"},
      {"label":"H1 EPS","value":"-0.44","note":"2026上半年仍未把轉型完整反映到獲利。"},
      {"label":"2025 毛利率","value":"約54%","note":"營收放大時若能維持，是關鍵優勢。"},
      {"label":"私募額度","value":"最多1,200萬股","note":"需追策略投資人與稀釋風險。"}
    ],[
      {"name":"半導體轉型","status":"ok","note":"公司明確轉型且已有大型OSAT採購。"},
      {"name":"矽品大額採購","status":"ok","note":"累積14.6535億元設備採購已由客戶公告。"},
      {"name":"營收認列","status":"partial","note":"8月轉強，但累計營收仍需驗證。"},
      {"name":"高毛利維持","status":"partial","note":"等待半導體放量後的產品組合毛利。"},
      {"name":"EPS爆發","status":"no","note":"H1仍虧損。"},
      {"name":"新客戶複製","status":"partial","note":"需看更多OSAT/Fab的 repeat order。"}
    ],["矽品14.65億開始密集認列","半導體營收占比持續提高","新OSAT/Fab repeat order","私募引進真正策略投資人"],["採購認列延遲","營收放大但毛利率明顯下滑","私募低價造成稀釋","2025 EPS含較多一次性業外收益"],[
      {"level":"正面","text":"矽品14.6535億元採購是硬證據","why":"轉型不是只有法說故事。"},
      {"level":"觀察","text":"8月營收已轉強","why":"需要連續數月/數季延續。"},
      {"level":"風險","text":"現價已提前交易2027成長","why":"若EPS認列不夠快，估值易壓縮。"}
    ],{"action":"HOLD","reason":"由估值引擎於更新時重新計算。","change_condition":"若月營收與營益率同步階梯式上升，上修 Base；若交機延遲且存貨堆高，下修。"}),
    company("1303","南亞","AI電子材料 / CCL / 銅箔 / 玻纖布 / 環氧樹脂",227.5,0.0,[{"date":"2026-09-23","close":227.5}],{"period":"2026-08","value_twd":30600000000,"yoy":46.7,"mom":None,"source":"公開月營收"},{"label":"基本面已兌現","tone":"good","red_flag_count":0},"AI電子材料成長已反映在營收與毛利，但EPS很大一部分來自南亞科等轉投資；估值需拆分本業與景氣循環。","Q3毛利 / M9-M10認證 / 南亞科貢獻",[
      {"label":"Q2 毛利率","value":"18.9%","note":"較去年同期大幅改善，重點是能否成為新常態。"},
      {"label":"H1 EPS","value":"5.17","note":"不可直接年化，轉投資貢獻很大。"},
      {"label":"南亞科 H1貢獻","value":"EPS 2.68","note":"記憶體景氣是南亞EPS的重要變數。"},
      {"label":"電子材料","value":"營收占比 >50%","note":"公司估值框架正從塑化往電子材料重估。"}
    ],[
      {"name":"AI材料需求","status":"ok","note":"營收與毛利已有財報驗證。"},
      {"name":"M8量產","status":"ok","note":"高階材料已有實際出貨基礎。"},
      {"name":"M9認證","status":"partial","note":"持續追認證與實際營收貢獻。"},
      {"name":"M10認證","status":"partial","note":"市場已有期待，正式量產仍待驗證。"},
      {"name":"毛利20%+常態","status":"partial","note":"Q2達18.9%，需跨季度確認。"},
      {"name":"轉投資景氣","status":"partial","note":"南亞科/台塑石化波動會放大EPS。"}
    ],["M9/M10正式認證與量產","CCL/銅箔/玻纖布持續漲價與滿載","電子材料占營益比持續提高","南亞科景氣維持強勢"],["毛利率回落至15%以下","M9/M10認證延後","記憶體循環反轉造成權益法收益下滑","石化產能過剩拖累本業"],[
      {"level":"正面","text":"Q2毛利率18.9%","why":"電子材料mix與漲價已真正反映在財報。"},
      {"level":"觀察","text":"M9/M10仍需正式認證/量產","why":"市場已提前交易部分高階材料故事。"},
      {"level":"風險","text":"H1 EPS大量來自轉投資","why":"不能把5.17直接年化當本業盈利能力。"}
    ],{"action":"HOLD","reason":"由估值引擎於更新時重新計算。","change_condition":"若電子材料毛利持續上升且M9/M10量產，上修；若轉投資景氣反轉且本業毛利走弱，下修。"})
  ],
  "broker":{},
  "news":[
    {"company":"政美應用","company_id":"7853","title":"9/24盤中出現集中買盤；尚未見正式新訂單重大訊息","date":"2026-09-24","source":"盤中觀察","confidence":"secondary"},
    {"company":"由田","company_id":"3455","title":"日月光投控旗下矽品累積向由田採購14批設備，總額14.6535億元","date":"2026-07-06","source":"客戶重大訊息","confidence":"official"},
    {"company":"南亞","company_id":"1303","title":"電子材料占比提升，Q2毛利率與獲利明顯改善","date":"2026-07-09","source":"財報/法說摘要","confidence":"official"}
  ]
}

val=json.loads((ROOT/'config'/'valuation.json').read_text(encoding='utf-8'))
rules=json.loads((ROOT/'config'/'signals.json').read_text(encoding='utf-8'))['decision']
for c in data['companies']:
    cfg=val[c['id']]
    sc={}
    for name,s in cfg['scenarios'].items():
        if cfg['model']=='forward_eps':
            fair=s['eps']*s['pe']; desc=f"EPS {s['eps']} × P/E {s['pe']}x"
        else:
            fair=s['forward_revenue_m']*s['ps']/cfg['shares_m']; desc=f"Forward revenue {s['forward_revenue_m']}M × P/S {s['ps']}x ÷ {cfg['shares_m']}M shares"
        sc[name]={"fair_value":round(fair,1),"description":desc}
    p=c['market']['price']; base=sc['base']['fair_value']; up=(base/p-1)*100
    label,tone=("偏便宜","good") if up>=15 else (("偏貴","bad") if up<=-15 else ("合理區間","blue"))
    c['valuation']={"label":label,"tone":tone,"base_fair":base,"base_upside_pct":round(up,1),"scenarios":sc,"notes":cfg['notes']}
    if c['fundamental']['red_flag_count']>=rules['exit_review_red_flags']:
        action='EXIT REVIEW'; reason='重大基本面紅旗達到門檻；先重新驗證投資論點。'
    elif up>=15:
        action='ADD'; reason='價格相對 Base fair value 留有約15%以上安全邊際，且重大紅旗未達退出門檻。'
    elif up<=-15:
        action='TRIM'; reason='現價高於 Base fair value 約15%以上；除非新基本面同步上修合理價，否則降低追價風險。'
    else:
        action='HOLD'; reason='價格接近 Base 情境；等待下一個可驗證的基本面訊號。'
    c['decision']['action']=action; c['decision']['reason']=reason

manual=json.loads((ROOT/'site'/'data'/'manual_broker.json').read_text(encoding='utf-8'))
cum=0; hist=[]
for r in manual['target_history']:
    cum += r['net']; hist.append({**r,'cum':cum})
data['broker']={"branch_id":"9887","branch_name":"元大經紀","source":"manual fallback","target":{"stock_id":"7853","as_of":hist[-1]['date'],"net_5d":sum(x['net'] for x in hist[-5:]),"net_20d":sum(x['net'] for x in hist[-20:]),"pattern":"建倉觀察","pattern_note":"目前近5日為正累積；等待9/24後資料確認是否延續。","history":hist},"cross_stock":manual['cross_stock'],"data_note":"分點資料只代表該券商營業據點客戶交易彙總，不代表單一大戶。自動逐分點資料需 FinMind Sponsor；未設定時使用 manual_broker.json。"}
OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT)
