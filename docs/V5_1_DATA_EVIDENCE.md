# V5-1 第一輪資料與規劃結果證據

## 結論

V5-1 已建立一份不覆寫來源資料庫的第一輪候選快照，並完成詳細資料頁與
固定規劃案例覆核。這份資料比 V5-0 基線更豐富，但仍不是「完整資料庫」，
也不構成上線資料驗收：價格與短期績效覆蓋顯著提高，正式 ACTUAL／76W、
基金規模、費用率、distribution period、成分股 overlap 與長期總報酬仍是
主要缺口。

## 可重現快照

- Code base：`2d2d5f95fba52bac8b5cc191ed99fdf9291bf219`
- Analysis date：`2026-08-30`
- Source database SHA-256：
  `6a817e10ff4daeb09c9612490b3ff624a523780d46e3dc629210e80084712a76`
- Candidate database SHA-256：
  `64a4ab5f947777b39e38edf90146db597512a2dad42f7a31edcab894331b10e5`
- Candidate size：`13,963,264` bytes
- SQLite integrity：`ok`
- Foreign-key violations：`0`
- Completed at：`2026-08-30T20:05:16.471490+00:00`

資料庫、raw snapshots、rejected rows 與本機報告均位於 git-ignored 的
`reports/v5-1-20260830/`，不提交到 repository。版本控制只保留建立候選、
覆蓋 ledger 與 frozen replay 的程式及這份摘要。

重建候選時必須指定新的、不存在的 database 與 artifacts 路徑，並顯式允許
官方資料網路存取：

```powershell
python -m deployment.detail_data_candidate `
  --source <source.db> `
  --database <new-candidate.db> `
  --artifacts <new-artifact-directory> `
  --evaluated-on 2026-08-30 `
  --allow-network

python -m deployment.v5_planner_replay `
  --database <new-candidate.db> `
  --evaluated-on 2026-08-30 `
  --output <new-planner-replay.json>
```

## 第一輪資料覆蓋

### ETF universe 與主資料

- 官方 master raw 269 筆，接受 261 筆、拒絕 8 筆；拒絕項目是目前產品
  範圍外的期貨信託產品，並保留 rejected evidence。
- 261／261 具有代號、名稱、主動／被動、股票／債券分類與上市日期。
- 官方出表日期 `1150829` 已解析為資料集來源日期 `2026-08-29`，保存在
  processed artifact／import evidence；不偽裝成每一 ETF 的個別更新日。
- 基金規模與費用率仍為 0／261，原因分別為尚未驗證官方 AUM 來源及總費用率
  口徑，不以猜測值補齊。

### 價格與績效

- 全市場候選 260 檔，網路失敗 0；另 1 檔主檔沒有形成可用價格歷史。
- 有官方日收盤價 231／261。
- 1M：230／261；3M：223／261；6M：210／261；1Y：190／261。
- 期間不足分別為 30、37、50、70 檔；這是可解釋的上市歷史限制，不回填 0。
- 詳細頁抽查 `0050`、`0056`、`0051` 均顯示截至 `2026-08-28` 的價格與
  1M／3M／6M／1Y 績效；`0051` 已由基線「缺參考價格」改善為有價格。

### 配息、殖利率與組成

- 當次官方配息 raw 338 筆，接受 331 個事件與 1,640 筆組成，拒絕 8 筆；
  候選資料庫累積 1,519 個配息事件、121 檔 ETF 有配息歷史。
- estimated component coverage 為 106／261；估算已實現資本利得仍標為
  `ESTIMATED`，不得稱為正式 `76W`。
- 正式 ACTUAL component 與正式 ACTUAL 76W 均只有 1／1,519 事件，ETF
  coverage 1／261；review queue 3,036 筆。此覆蓋不可描述為完整。
- 殖利率有值 113／261。1,231 個待補事件中成功計算 347、失敗 884；
  失敗分類為最大 redirect 次數 607、HTTP 307 274、未來除息日 2、
  除息日前無可用收盤價 1。既有 client 已啟用 redirect follow，不能把這批
  結果簡化成單一程式開關缺陷；V5-3 應改採可斷點、節流與批次重試策略。
- distribution period、股票股利正式欄位仍為 0／261；缺失維持 unavailable。

## Frozen planner 比較

共同輸入為 1／4／7／10 月各 100 TWD、3 年歷史、generic deduction 0%。

### 無持股

- Funnel：256 universe／6 eligible → 261 universe／47 eligible。
- 結果仍為 `TARGET_MET`／`BOUNDED_BEST_EFFORT`。
- 所需資金：22,218.51 → 24,382.11 TWD；候選增加不代表資金更省。
- 第一輪新增整數股數：0050 43、0051 32、0053 20、0055 108、0056 12、
  00712 522、00922 4。
- 1／4／7／10 月 added after-tax cash 分別為 100.05、100.24、166.17、
  100.92 TWD，shortfall 均為 0。
- 主要排除仍包含 stale data 133、unstable distributions 116、missing total
  return 104、missing complete components 100、missing after-tax cash 96。

### 一檔與多檔既有持股

- `0050` 10 股及 `0050 + 00878` 各 10 股均仍為 0 eligible，原因核心是
  既有持股與候選的 constituent overlap 無資料，資料增加沒有解除 N 持股阻塞。
- `0051` 10 股已不再因缺價格回 `UNAVAILABLE`，但仍因 overlap 缺失成為
  `NO_ELIGIBLE_ALLOCATION`。
- 所有案例只產生 `RECOMMENDED` strategy；alternative 仍因 overlap evidence
  unavailable。這是 V5-3 的最高優先資料缺口。

## 實頁覆核

本機 FastAPI 與 Streamlit 使用 candidate SHA 啟動，沒有修改前端或配置引擎。

### 已符合

- 詳細頁能清楚顯示 ETF 身分、分類、上市日期、價格日期、四期間績效、配息
  事件與部分殖利率；缺值以破折號或「資料抓取中」呈現，沒有被當成 0。
- 規劃結果呈現整數股數、資金、支援月份、納入理由、主要風險、月份達標、
  assumptions 與 exclusions 的 disclosure 入口。
- 頁尾聲明不構成投資建議或下單指示。

### 需調整（留待 V5-2／V5-3 決策）

- 基金規模與費用率仍顯示「資料抓取中」；這是資料來源缺口，不是畫面故障。
- `0056` 的 76W 統計主要來自 estimated fallback，必須持續讓 basis 與正式
  ACTUAL coverage 可見，不能只讓使用者看到比例。
- 規劃頁仍使用「使用AI預測長期表現」「推薦配置」「咪建議增加」等文案；
  容易被理解為 opaque AI 或個人化買進建議，與產品解釋性邊界有衝突。
- 實頁預設全年每月 3,000 TWD、無持股案例產生 14 檔、約 6,221,466.52 TWD
  新增資金。雖然有逐檔理由與風險，但結果過長且資金巨大，需檢驗使用者是否
  能理解缺口形成、估算 basis、集中度與求解 tradeoff。

### 建議延後

- 不在 V5-1 修改演算法、硬門檻、稅務公式或 V4 已驗收頁面。
- 不因 47 eligible 或單一 `TARGET_MET` 宣告資料完整、結果可用或可上線。
- V4-8、正式部署與 SEC-4 繼續暫停至 V5-5 owner acceptance。

## V5-3 建議優先序與驗收指標

1. 成分股與 overlap：讓 frozen 一檔／多檔持股案例不再因
   `HOLDING_OVERLAP_UNAVAILABLE` 全數歸零，並保留 snapshot/source date。
2. Adjusted total-return 與 downside history：降低 `MISSING_TOTAL_RETURN`、
   `MISSING_DOWNSIDE_RISK`，使 3Y／5Y／10Y 情境有足夠歷史證據。
3. 配息可靠性：建立可恢復的殖利率批次、補 distribution period，並以發行商
   為單位增加 reviewed ACTUAL notices；estimated 與 ACTUAL 分別量測。
4. 詳細頁剩餘欄位：只在找到可驗證的官方口徑後補 fund size、expense ratio、
   stock dividend；否則保留明確 unavailable reason。
5. 使用完全相同的 database SHA、commit、requests 與指標重跑 V5-4，再決定
   是否調整 objective、排除門檻、輸出層級與推薦語言。
