# V5 資料補齊與結果反推計畫

## 1. 目標

V5 不以最低 launch-data gate 或單一資料覆蓋率宣告完成。核心問題是：

> 在資料逐步補齊後，GoodCat 的 ETF 詳細資料與 0～N 持股自動規劃，
> 是否能產生對初學者有用、可解釋且可重現的結果？

執行順序固定為：

1. 取得目前詳細資料頁實際展示所需的全部可用資料；
2. 查看一次詳細資料頁及自動規劃結果；
3. 依第一次結果的阻塞原因取得剩餘高價值資料；
4. 使用相同輸入再看一次自動規劃結果；
5. 完成資料、計算、頁面與限制的收尾驗收。

V4-8、release candidate、正式部署與 SEC-4 在 V5-5 通過前暫停。

## 2. 不變語意與工作邊界

- `ACTUAL` 正式組成、e添富 `ESTIMATED` fallback、正式 `76W`、正式 0
  與缺失資料必須分開。
- e添富已實現資本利得不得改稱正式 `76W`。
- 官方沒有提供的值維持 `UNAVAILABLE`；資料豐富不等於填入猜測值。
- 第一輪資料取得不修改配置目標函數、硬門檻或已驗收頁面，避免把資料改善
  與演算法改善混在一起。
- 每一輪使用 immutable database snapshot、exact commit 與固定 requests。
- 正式資料來源、schema、財稅或配置變更仍屬高風險工作，需要獨立 Issue、
  CODEOWNER 與至少兩位人類核准。

## 3. V5-X

### V5-0 — 規劃、欄位 manifest 與基線

產出：

- 本文件及 `docs/ROADMAP.md` 的 V5-0～V5-5；
- 詳細資料頁 visible-field manifest；
- 第一輪資料取得清單；
- 固定頁面樣本、planner requests 與比較指標；
- 第一輪 data Issue 的 claimed scope 草案。

完成條件：每個可見欄位均能追到 API、storage／derived logic、來源、目前覆蓋、
缺失語意及第一輪處理方式。

### V5-1 — 第一輪：詳細資料頁資料取得

只補目前頁面會實際使用的資料：ETF 身分與主資料、歷史品質所需證據、
1M／3M／6M／1Y PRICE_RETURN、最近 260 筆官方收盤、配息與殖利率、
逐次配息組成、正式 ACTUAL／76W 與 owner 單檔稅務情境所需歷史事實。

完成條件：

- 全 ETF universe 對每個欄位都有 `AVAILABLE` 或具原因的 `UNAVAILABLE`；
- 所有已取得 facts 有 source、as-of／event date、import evidence；
- pipeline rejected rows、review queue 與 coverage 可 reconciliation；
- 固定樣本頁不因缺少可取得的第一輪資料而顯示「資料抓取中」。

### V5-2 — 第一次頁面與自動規劃檢視

使用 V5-1 snapshot 檢查代表性 ETF 詳細頁及 frozen planner matrix。
此階段只記錄結果，不先調整演算法或頁面。

### V5-3 — 第二輪：由結果反推剩餘資料

依 V5-2 的實際阻塞排序，例如：

- N 持股因 constituent overlap 缺失而無解；
- 長期結果因 adjusted history 不足而 unavailable；
- 稅務結果因正式 ACTUAL 不足只能使用估算；
- 候選過少是價格、績效、配息、組成或 freshness 哪一層造成；
- 結果過度集中或方案無差異是否確實來自資料而非求解器。

V5-3 不追求「資料越多越好」的無界匯入；優先取得能解除結果阻塞、增加解釋力
或降低錯誤稅務推論的資料。

### V5-4 — 第二次自動規劃檢視

使用與 V5-2 完全相同的 requests，比較兩個 immutable snapshots。只有這次
比較完成後，才提出配置演算法、門檻、稅務口徑或結果頁層級的修改建議。

### V5-5 — 收尾

- 由主人確認詳細資料與規劃結果是否有用；
- 固定通過驗收的資料 snapshot、commit、contracts 與 tests；
- 記錄仍無法取得的官方資料與產品限制；
- 資料與配置驗收完成後才恢復 V4-8。

## 4. 詳細資料頁 visible-field manifest

盤點基準：`frontend/pages/etf_detail.py` at `2d2d5f9`。以下區分公開畫面、
owner 解鎖畫面，以及已有函式但目前未渲染的 operational data。

### 4.1 ETF 身分與歷史品質

| 可見資料 | API／計算 | DB／依賴 | 2026-08-30 基線 | V5-1 行動 |
| --- | --- | --- | --- | --- |
| 代號、名稱 | `GET /api/v1/etfs/{code}` | `etf_master.code/name` | 256／256 | 與最新官方 universe 全量 reconciliation |
| 主動／被動、股票／債券 | ETF response label | `is_active/is_bond` | 256／256 有值 | 驗證分類語意與正式產品類型來源 |
| 上市日期 | ETF response | `listing_date` | 256／256 | 重新與官方 master 對帳 |
| 基金規模 | ETF response | `fund_size` | 0／256 | 尋找正式來源；不可取得者記錄 unavailable reason |
| 費用率 | ETF response | `expense_ratio` | 0／256 | 尋找正式來源及資料口徑／日期 |
| 喵喵評等與證據 | quality-grade catalog | 價格績效、配息、ACTUAL 76W 等 derived facts | 256／256 `UNRATED` | 先補輸入事實，不直接放寬 publication gate |

### 4.2 績效與價格走勢

| 可見資料 | API／計算 | DB／依賴 | 2026-08-30 基線 | V5-1 行動 |
| --- | --- | --- | --- | --- |
| 1M／3M／6M／1Y PRICE_RETURN | `/performance` | `etf_performance` | 1M／3M／1Y 各 8 檔；6M 199 檔 | 對支援 universe 取得足夠官方收盤後一致重算 |
| 最近 260 筆股價走勢 | `/price-history` | `etf_daily_close` | 8 檔、2,256 筆；2025-07-01～2026-08-25 | 全量取得最近至少 260 個可用交易日或上市後全部日期 |
| 資料日期與證交所來源說明 | performance／price history response | `as_of_date/source_id` | 有資料的 8 檔可顯示 | 每檔保留 source、trade date 與 import evidence |

### 4.3 配息、殖利率與逐次組成

| 可見資料 | API／計算 | DB／依賴 | 2026-08-30 基線 | V5-1 行動 |
| --- | --- | --- | --- | --- |
| 最新除息日、每單位現金股利、發放日 | `/dividends` | `etf_dividend` | 1,517 事件、121 檔；日期與金額完整 | 全量對帳；未來公告與已付款歷史分層 |
| 股票股利 | 頁面讀取 `stock_dividend_per_unit` | 目前 API／schema 沒有此欄 | 0／1,517，永遠顯示尚未取得 | 確認正式來源後另立 schema/data Issue，不以 0 代替 |
| 年／季 | dividend response | `distribution_period` summary metric | 0／1,517 | 取得或可追溯推導 distribution period |
| 殖利率趨勢 | dividend response | `yield_pct/basis/reference_close` | 288／1,517，全部為 calculated | 以官方值優先；缺少時保留公式、參考價與日期 |
| 現金／股票股利圖 | page-derived annual rows | 配息事件與股票股利 | 現金可用；股票不可用 | 股票資料未取得前保持 missing disclosure |
| 逐次配息列表 | `/dividends` | period、amount、yield、ex/payment date | 最多顯示最近 20 筆 | 保證每一列 source/event identity 可追溯 |
| 現金股利組成名稱、比例、金額 | `/dividends/{id}` | `etf_dividend_component` | estimated 972 事件／106 檔；ACTUAL 1 事件／1 檔 | 擴充完整 estimated coverage 並以正式 ACTUAL 優先 |
| 組成 basis | composite selector | ACTUAL／ESTIMATED | 語意已分開 | 維持 fallback label，不升格估算 |

### 4.4 資本利得組成摘要

| 可見資料 | API／計算 | DB／依賴 | 2026-08-30 基線 | V5-1 行動 |
| --- | --- | --- | --- | --- |
| 可分析配息次數 | `/actual-76w` composite summary | 完整 ACTUAL 或 estimated event | 972 estimated＋1 ACTUAL event | 顯示 analysis basis，正式與估算分母分開 |
| 100% 資本利得次數 | composite summary | realized-capital-gain ratio | 依 estimated 為主 | 禁止描述為正式免稅 76W |
| 最新／平均資本利得比例 | composite summary | selected component history | 主要為 estimated fallback | 同時呈現 basis coverage，避免只看單一比例 |
| 正式 ACTUAL／76W | actual summary | 正式通知書與 source document | 1／1,517 = 0.06592% | 依發行商分批擴充 discovery、parse、review |

### 4.5 Owner 解鎖後的單檔稅務與再投入

頁面提供持有單位數、目前價格、每月保留現金、估算年數、歷史年數、配息次數、
再投入比例、54C 稅率／抵減率及其他所得稅率等輸入。輸出使用：

- 年化配息率與 payments-per-year；
- 完整 ACTUAL 或明確 estimated fallback 組成；
- 1Y 等可用價格報酬；
- 稅規版本、四種配息使用情境、稅與補充保費、總報酬檢查。

V5-1 只補它所需的歷史事實。個人輸入、稅務方法與外推模型是否適合公開配置，
留到 V5-2／V5-4 根據結果再決定。

### 4.6 目前未渲染，不列入 V5-1 第一優先

- `load_etf_data_profile`／`render_data_profile` 已存在但目前頁面未呼叫；
- 單檔 `render_base_target_analysis` 已存在但目前頁面未呼叫；
- constituent overlap 不在詳細資料頁渲染，但已知會阻塞 N 持股規劃，先列入
  V5-3 候選；若 V5-2 再次證明是首要 blocker，可提前為 V5-3 第一項。

## 5. 第一輪固定頁面樣本

樣本需同時涵蓋資料完整與缺失語意，不只挑熱門 ETF：

- `0050`：有完整價格歷史的市值型代表；
- `0056`：有完整價格與季度配息的高股息代表；
- `00878`：目前唯一正式 ACTUAL／76W seed；
- `00929`：月配代表；
- `0051`：主檔與配息存在但目前缺價格的代表；
- 一檔主動式股票 ETF；
- 一檔債券 ETF（確認產品分類與非適用資料）；
- 一檔新上市、歷史年限不足 ETF（應為 N/A，不是資料錯誤）。

實際 active／bond／new-listing 代號在 V5-1 snapshot 建立時由最新 official universe
固定，不在本文件預先猜測。

## 6. Frozen planner matrix

每輪至少使用下列 requests；目標月均需逐月判定，不以年度平均替代：

1. 無持股；1／4／7／10 月，每月 100 TWD；
2. 0050 10 股；相同目標；
3. 0050 10 股＋00878 10 股；相同目標；
4. 一檔缺參考價格的既有持股；
5. 無持股；全年每月 3,000 TWD；
6. 多檔持股且含不適用於新增配置的產品；
7. 正式 0 目標；
8. 一個資料缺失應回 `UNAVAILABLE`、不得回 0 的對抗案例。

## 7. 兩次結果比較指標

- universe、supported、eligible 與每一 exclusion code 的 ETF 數；
- 0／1／N 持股 requests 的可解率與狀態；
- `ACTUAL`、estimated fallback、unavailable 的候選及配置持股數；
- 新增 ETF、整數股數、總資金、每月 current／added／shortfall；
- concentration 與 constituent-overlap 可用率；
- recommendation alternatives 是否有資料支持且實際不同；
- 3Y／5Y／10Y history 及 market-scenario 可用率；
- 稅務輸出的 component basis、正式 54C／76W 與估算占比；
- 詳細資料頁每一 visible field 的 available／unavailable ratio；
- 所有 inclusion／exclusion／risk／estimate／limitation 是否能由資料 ledger 重算。

結果比較不得只報「候選變多」或「TARGET_MET」。若新增資料使資金大幅增加、
方案更集中、稅務不確定性提高或解釋變差，也必須列為負面結果。

## 8. V5-1 data Issue（#74）

Tracking: https://github.com/twstockanalysis/goodcat-website/issues/74

### Problem

詳細資料頁大量可見欄位仍缺資料；目前價格只有 8 檔、基金規模與費用率皆為
0／256、所有公開評等為 `UNRATED`、distribution period 為 0／1,517、殖利率
只有 288／1,517，正式 ACTUAL／76W 只有 1／1,517。無法用目前資料判斷頁面與
配置是否真的有用。

### Claimed scope

- ETF master official enrichment；
- official daily closes and derived 1M／3M／6M／1Y PRICE_RETURN；
- dividend history、distribution period、yield provenance；
- complete e添富 estimated components；
- issuer ACTUAL discovery／parse／review expansion；
- coverage、freshness、rejection、queue reconciliation tests and evidence。

### Out of scope

- 配置 objective／hard gates；
- Streamlit layout／copy；
- constituent overlap 與 adjusted 3Y／5Y／10Y total-return history；
- 正式部署、V4-8、SEC-4。

### Risk

`risk:high`：正式資料來源、財稅語意與公開評等輸入。需要 human sponsor、
CODEOWNER 及至少兩位人類核准。

## 9. V5-0 補資料前固定基線

### 9.1 程式與資料 snapshot

- Code commit：`2d2d5f95fba52bac8b5cc191ed99fdf9291bf219`
- Database role：本機 V5 audit candidate，不是正式部署資料庫
- Database SHA-256：`6a817e10ff4daeb09c9612490b3ff624a523780d46e3dc629210e80084712a76`
- Database size：`2,846,720` bytes
- Database last-write UTC：`2026-08-25T16:25:57Z`
- SQLite `integrity_check`：`ok`
- Foreign-key violations：`0`
- Analysis date：`2026-08-30`

### 9.2 Visible-field coverage

- ETF master：256 檔；code／name／listing date 256／256；fund size 0／256；
  expense ratio 0／256。
- Historical quality：256／256 `UNRATED`，沒有公開字母評等。
- Daily closes：8 檔、2,256 筆，範圍 2025-07-01～2026-08-25。
- Performance：1M／3M／1Y 各 8 檔，6M 199 檔；全部為 PRICE_RETURN。
- Dividends：1,517 事件、121 檔；amount／ex-date／payment-date 1,517／1,517；
  announcement date 與 source-updated timestamp 皆 0／1,517。
- Distribution period：0／1,517。
- Yield：288／1,517，全部為 calculated，且保留 reference close。
- Stock dividend：API／schema 無正式欄位；頁面所有事件皆為 unavailable。
- Estimated components：972 事件／106 檔、4,860 rows；ratio 皆有值，
  amount 皆由比例與配息金額顯示時計算。
- ACTUAL components：1 事件／1 檔、2 rows。
- Parsed ACTUAL source documents：1；文件日期 2023-08-15。

### 9.3 Frozen planner baseline

共同輸入：1／4／7／10 月各 100 TWD、3 年歷史、generic deduction 0%。

#### Zero holdings

- Snapshot：`sha256:283f8b3300b19ab5d7cb0af2658fa3ad92391137f69327a7a8c1ca7956db80b7`
- Funnel：256 universe → 192 supported → 6 eligible
- Result：`TARGET_MET`／`BOUNDED_BEST_EFFORT`
- Required capital：22,218.51 TWD
- Additions：0050 42、0056 84、00713 72、00915 121、00918 24、00919 140
- Selected-month shortfall：四個月份皆 0.00
- Top exclusions：STALE_DATA 186、INCOMPLETE_DATA 184、
  MISSING_TOTAL_RETURN 184、MISSING_AFTER_TAX_CASH 184、
  MISSING_REFERENCE_PRICE 184

#### Existing 0050 10 shares

- Snapshot：`sha256:e04c6fea19d2b76a528bb7241fe2d90dd7db68628f19356ee3488b1bf55c68e5`
- Funnel：256 → 192 → 0 eligible
- Result：`NO_ELIGIBLE_ALLOCATION`／`NOT_APPLICABLE`
- `HOLDING_OVERLAP_UNAVAILABLE`：192
- 每一目標月 shortfall：100.00 TWD

#### Existing 0050 10 shares and 00878 10 shares

- Snapshot：`sha256:59a5ea0ee9c9c24962dbd026777a96fbd23a193d6ba49366387763ebd1d5a4ce`
- Funnel：256 → 192 → 0 eligible
- Result：`NO_ELIGIBLE_ALLOCATION`／`NOT_APPLICABLE`
- `HOLDING_OVERLAP_UNAVAILABLE`：192

#### Existing 0051 10 shares with no saved reference price

- Snapshot：`sha256:b1fd0e942d87223dd64d4cbbb323b1b99dafae6f04241e1e73ae0e0478e87ce5`
- Funnel：256 → 192 → 0 eligible
- Result：`UNAVAILABLE`／`NOT_APPLICABLE`
- Current value and concentration cannot be verified.

以上 snapshot ID 是 eligibility facts 的 hash，不是資料庫檔案 hash。V5-2 與 V5-4
必須同時比較 database SHA、code commit、request 及 result snapshot，不能只比較
畫面上的狀態名稱。
