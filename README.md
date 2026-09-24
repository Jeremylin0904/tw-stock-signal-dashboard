# 台股驗證儀表板：政美 × 由田 × 南亞

這是一個可以直接放到 **GitHub Pages** 的零前端依賴儀表板。目的不是做一般看盤，而是持續回答四個問題：

1. 公司故事有沒有被 **營收、毛利、訂單、現金流** 驗證？
2. 政美的 **9887 元大經紀** 是持續建倉、短線交易，還是開始出貨？
3. 現價相對 Bear / Base / Bull 情境，已經 price-in 多少成長？
4. 目前研究訊號偏向 **ADD / HOLD / TRIM / EXIT REVIEW** 哪一種？

> 這是研究與決策輔助工具，不會自動下單。

## 已完成的頁面

- **總覽**：三檔現價、估值、基本面狀態、操作訊號、下一個驗證點。
- **政美 7853**：TSMC/先進封裝 Story Verification Pipeline、月營收、毛利、虧損、repeat order、存貨/現金流紅旗。
- **由田 3455**：矽品累積 14.6535 億元設備採購 → 營收 → 毛利 → EPS 的驗證鏈，以及私募風險。
- **南亞 1303**：電子材料、本業毛利、M9/M10，以及南亞科等權益法投資的拆分思維。
- **9887 分點**：政美近期累積、5/20日淨買賣、跨股票雷達。
- **估值與訊號**：Bear/Base/Bull fair value，並依規則產生 ADD/HOLD/TRIM/EXIT REVIEW。

## 專案結構

```text
site/                       # GitHub Pages 網站
  index.html
  app.js
  styles.css
  data/
    dashboard.json          # 儀表板唯一主要資料檔
    manual_broker.json      # 沒有分點付費 API 時的手動備援
config/
  watchlist.json
  valuation.json            # 三檔 Bear/Base/Bull 假設，可直接修改
  signals.json              # 決策規則、新聞關鍵字
scripts/
  update_data.py            # 自動抓價、營收、新聞、分點並重算估值
  backfill_broker.py        # 回補歷史分點，例如政美 2026/3–4 月暴漲期
.github/workflows/
  update-data.yml           # 台灣時間 14:40 / 21:40 自動更新
  deploy-pages.yml          # 自動部署 Pages
```

## 1. 本機預覽

完全不需要 npm。

```bash
cd tw-stock-signal-dashboard
python -m http.server 8000 -d site
```

瀏覽 `http://localhost:8000`。

## 2. 放到 GitHub

建立一個 repository，例如 `tw-stock-signal-dashboard`，把整個資料夾 push 上去。

GitHub repository → **Settings → Pages → Build and deployment → Source: GitHub Actions**。

之後 `deploy-pages.yml` 會自動部署 `site/`。

## 3. GitHub Actions Secrets

Repository → **Settings → Secrets and variables → Actions**。

### `FINMIND_TOKEN`（建議）

用來更新月營收等 FinMind 資料。未設定時，程式會保留 `dashboard.json` 上一次的有效資料，不會寫成空白。

### `FINMIND_SPONSOR_TOKEN`（要自動追 9887 才需要）

FinMind 的逐分點 `TaiwanStockTradingDailyReport` 是 Sponsor 資料。設定後，21:40 的 workflow 會自動追：

- 政美 7853 × 9887 每日淨買賣
- 近5日、近20日累積
- 分點交易占比
- 9887 其他股票的大額動作

若沒有 Sponsor token，Dashboard 會使用 `site/data/manual_broker.json`，其他功能仍可正常使用。

## 4. 回補「政美 2026/3–4 月暴漲期」9887 歷史

如果有 Sponsor token：

```bash
export FINMIND_SPONSOR_TOKEN='你的token'
python scripts/backfill_broker.py \
  --stock 7853 \
  --branch 9887 \
  --start 2026-03-01 \
  --end 2026-04-30
```

會產生：

```text
site/data/broker_history_7853_9887_2026-03-01_2026-04-30.json
```

這份資料可用來真正驗證：「4月暴漲前是否也是 9887 提前建倉」。

## 5. 修改合理價假設

編輯 `config/valuation.json`。

目前預設：

- **政美**：因獲利未穩定，用 `Forward Revenue × P/S ÷ Shares`。
- **由田**：用 `2027 EPS × P/E`。
- **南亞**：用 `Forward EPS × P/E`，但研究時必須另外拆本業與轉投資。

這些不是永遠不變的目標價。每次基本面驗證後，應修改假設再讓 Dashboard 重算。

## 6. 決策訊號邏輯

預設規則在 `config/signals.json`：

- Base fair value 比現價高 **15% 以上** → `ADD`
- 現價在 Base 附近 → `HOLD`
- 現價比 Base fair value高 **15% 以上** → `TRIM`
- 基本面重大紅旗達門檻 → `EXIT REVIEW`

`EXIT REVIEW` 優先於價格訊號，避免因為股票跌很多就自動判定「便宜」。

## 7. 三家公司各自真正該驗證什麼

### 政美 7853

不要只搜尋「台積電」。重點順序是：

`驗證 → Qualification → Tool Matching → 量產導入 → Repeat order → 多台設備 → 營收 → 營益轉正 → 現金流`

### 由田 3455

核心是：

`矽品 14.6535 億採購 → 交機 → 月營收階梯上升 → 毛利維持 → EPS / 營業現金流`

### 南亞 1303

核心是：

`電子材料營收與毛利 → M9/M10 認證/量產 → 本業 EPS`，同時把 `南亞科 / 南電 / 台塑石化` 的權益法貢獻拆開。

## 資料來源與限制

- 股價：Yahoo chart endpoint（次級、非官方，失敗時保留舊值）。
- 月營收/財報：FinMind，底層多來自公開市場資料；依帳號方案可用資料不同。
- 券商分點：FinMind Sponsor 才能自動化逐分點資料；同一分點**不等於同一投資人**。
- 新聞：Google News RSS 用來發現事件；真正影響估值前仍應回到 MOPS / TPEx / TWSE / 公司 IR 驗證。
