# V5-1B 殖利率實頁核對

## 結論

V5-1B 確認殖利率圖表缺點位不是 Vega／Streamlit 彙總錯誤，而是部分配息
事件雖已有官方日收盤價，殖利率批次仍重複發出網路請求，導致可計算事件
維持缺失。修正後，批次會先在與既有兩個月下載範圍相同的日期窗內重用
已保存官方價格；只有該窗沒有價格時才下載。

這份核對不宣告全市場殖利率完整，也不構成正式部署或 SEC-4 驗收。沒有
除息前可用官方收盤價的事件仍維持缺失，不回填 0。

## 程式修正

- 每檔 ETF 的已保存日收盤價在單次批次中只讀取一次。
- 快取候選限制於原本兩個月下載窗，避免過舊價格冒充除息前一交易日。
- 當有效快取存在時不載入或呼叫網路 client。
- 有效快取不存在時仍使用既有 TWSE 官方價格下載流程。
- `yield_basis`、`yield_source_id`、`reference_trade_date` 與
  `reference_close_price` 的追溯語意不變。

## 全 ETF reconciliation

核對資料庫：本機 `database/tw_etf.db`，不是正式部署資料庫。

- 核對日期：`2026-08-31`
- 核對後 SHA-256：
  `4c2cabb98b4df0be79700d99a138d2d11d95da1e153733112945d0f4c513e2fc`
- 配息事件：1,517，分布於 121 檔 ETF。
- 核對前殖利率：312 個事件、95 檔 ETF。
- 全市場 cached-price sweep 新增：20 個事件，分布於 0056、00713、
  00878、00915、00918、00919、00929。
- 五檔代表 ETF 官方歷史價格補算新增：87 個事件；0051 15、0056 20、
  00878 19、00918 9、00929 24，失敗 0。
- 核對後殖利率：419／1,517 個事件、96／121 檔 ETF。
- 仍缺殖利率：1,098 個事件；缺少有效官方價格者維持 `NULL`。
- 所有 calculated yield 的來源／參考日／參考價完整性錯誤：0。
- SQLite integrity：`ok`；foreign-key violations：0。

## 實際頁面樣本

以下詳細頁均以本機 FastAPI + Streamlit 實際渲染核對，不只檢查 0050：

| ETF | 配息事件 | 有殖利率 | 最新 20 筆缺值 | 結果 |
| --- | ---: | ---: | ---: | --- |
| 0050 | 26 | 26 | 0 | 五年圖 2022–2026 點位完整 |
| 0051 | 15 | 15 | 0 | 單年配息歷史逐年皆有殖利率 |
| 0056 | 25 | 25 | 0 | 五年圖 2022–2026 點位完整 |
| 00878 | 24 | 24 | 0 | 最新 20 筆皆有殖利率 |
| 00918 | 13 | 13 | 0 | 最新 13 筆皆有殖利率 |
| 00929 | 38 | 38 | 0 | 最新 20 筆皆有殖利率 |

頁面仍可能顯示基金規模、費用率或價格歷史等其他 V5 缺口；這些不屬於本次
殖利率修正，不能因配息圖完整而宣告詳細頁所有資料完整。

## 驗證邊界

- 本機 SQLite 資料庫不進入 Git；協作者使用下列經白名單匯出的可攜式
  殖利率資料包重建相同的 419 筆結果。
- 正式資料庫仍需由人類 sponsor 依候選快照與部署程序審核後匯入。
- Draft PR 不代表作者核准、正式資料驗收、部署或 READY。

## 協作者資料同步

版本控制保留兩個不含 SQLite 自增 ID、本機路徑、raw snapshot 或其他資料表
內容的檔案：

- `data/collaboration/v5-1b/dividend-yields.json`
- `data/collaboration/v5-1b/dividend-yields.manifest.json`

manifest 固定記錄資料包 SHA-256、來源資料庫 SHA-256／容量、SQLite 完整性、
外鍵結果、筆數及 `yield_basis` 分布。資料包只保留重建殖利率所需的事件穩定
鍵、事件指紋、殖利率、來源與參考價格欄位。

協作者必須先以 V5-1 候選流程建立含相同配息事件的本機資料庫，再執行：

```powershell
.venv\Scripts\python.exe -m deployment.dividend_yield_bundle import `
  --database <collaborator-candidate.db> `
  --bundle data\collaboration\v5-1b\dividend-yields.json `
  --manifest data\collaboration\v5-1b\dividend-yields.manifest.json
```

匯入前會驗證資料包 SHA-256 與筆數，並以 `source_id + source_event_id` 尋找
事件，再比對 ETF 代號、除息日、每單位金額與幣別。任何事件缺少、重複、
指紋不一致、SQLite integrity 失敗或外鍵錯誤都會在寫入前停止。既有 repository
規則仍會阻止 calculated yield 覆蓋正式 `OFFICIAL` yield。

需要重新產生資料包時，輸出路徑必須尚不存在：

```powershell
.venv\Scripts\python.exe -m deployment.dividend_yield_bundle export `
  --database <verified-source.db> `
  --bundle <new-dividend-yields.json> `
  --manifest <new-dividend-yields.manifest.json>
```
