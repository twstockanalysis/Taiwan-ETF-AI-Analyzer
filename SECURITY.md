# Security policy

## 私密通報

請勿用公開 Issue 回報漏洞、token／cookie、認證繞過、個資或資料外洩。請使用 GitHub repository 的 **Security → Advisories → Report a vulnerability** 私密通報：

https://github.com/twstockanalysis/Taiwan-ETF-AI-Analyzer/security/advisories/new

通報時提供最小可重現資訊、受影響版本／commit、影響與建議緩解方式；不要附真實憑證、未匿名化資料或不必要的本機檔案。

## AI 處理限制

AI 可以在維護者授權下進行只讀分類、測試建議或本地修正，但不得：

- 將私密通報內容複製到公開 Issue、PR、log 或第三方服務；
- 使用、驗證或傳送真實 token、cookie、帳號或正式資料；
- 自行公開漏洞、merge、release、deploy 或修改 repository secrets；
- 把沒有經過人類安全審查的結果標記為已修復。

安全修正需要獨立 `security/<sec-id>-<slug>` branch／PR、CODEOWNER 及至少兩位人類核准，並通過 required security checks。
