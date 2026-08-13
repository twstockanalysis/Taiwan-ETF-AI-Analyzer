"""正式 ETF 配息組成資料來源 Registry。"""

from dataclasses import dataclass
from enum import StrEnum

from backend.app.data_sources.issuer_dividend_landing_pages import (
    ISSUER_DIVIDEND_LANDING_PAGES,
)


class ActualDividendSourceMode(StrEnum):
    """正式配息來源目前的導入狀態。"""

    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    MANUAL_IMPORT = "MANUAL_IMPORT"
    VERIFIED_ADAPTER = "VERIFIED_ADAPTER"
    DISABLED = "DISABLED"


class SourceRetrievalPolicy(StrEnum):
    """官方來源文件取得政策。"""

    MANUAL_ONLY = "MANUAL_ONLY"
    EXPLICIT_NETWORK = "EXPLICIT_NETWORK"


class SourceDiscoveryKind(StrEnum):
    """官方文件候選的自動發現方式。"""

    NONE = "NONE"
    JSON_API = "JSON_API"
    DETERMINISTIC_URL = "DETERMINISTIC_URL"
    HTML_LIST = "HTML_LIST"
    OFFICIAL_LANDING_PAGE = "OFFICIAL_LANDING_PAGE"
    RESTRICTED_OFFICIAL_SOURCE = "RESTRICTED_OFFICIAL_SOURCE"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


@dataclass(
    frozen=True,
    slots=True,
)
class ActualDividendSource:
    """正式收益分配組成來源設定。"""

    source_id: str
    issuer_name: str
    official_domains: tuple[str, ...]
    mode: ActualDividendSourceMode
    retrieval_policy: SourceRetrievalPolicy
    priority: int
    adapter_name: str | None = None
    discovery_kind: SourceDiscoveryKind = SourceDiscoveryKind.NONE
    enabled: bool = True
    notes: str = ""
    issuer_key: str | None = None


# TWSE e添富「投資篩選器」目前列出的 ETF 發行人全集。
# 這份清單是來源覆蓋的驗收基準；新增發行人時，測試會要求同步補上
# 一筆 issuer_key 相符的正式配息來源設定。
TWSE_ETF_ISSUERS: dict[str, str] = {
    "yuanta": "元大",
    "fubon": "富邦",
    "sinopac": "永豐",
    "mega": "兆豐",
    "cathay": "國泰",
    "first": "第一金",
    "fuh_hwa": "復華",
    "capital": "群益",
    "taishin": "台新",
    "ctbc": "中國信託",
    "upam": "統一",
    "jko": "街口",
    "franklin": "富蘭克林",
    "kgi": "凱基",
    "uob": "大華銀",
    "nomura": "野村",
    "esun": "玉山",
    "union": "聯邦",
    "hnh": "華南永昌",
    "allianz": "安聯",
    "blackrock": "貝萊德投信",
    "jpmorgan": "摩根",
    "alliancebernstein": "聯博",
}


ACTUAL_DIVIDEND_SOURCES: dict[
    str,
    ActualDividendSource,
] = {
    "manual_actual_dividend_notice": (
        ActualDividendSource(
            source_id=(
                "manual_actual_dividend_notice"
            ),
            issuer_name="人工核對正式通知書",
            official_domains=(),
            mode=(
                ActualDividendSourceMode
                .MANUAL_IMPORT
            ),
            retrieval_policy=(
                SourceRetrievalPolicy
                .MANUAL_ONLY
            ),
            priority=1,
            notes=(
                "M8-4A 人工核對 JSON 匯入；"
                "不執行 OCR 或所得代碼推論。"
            ),
        )
    ),
    "cathay_actual_dividend_announcement": (
        ActualDividendSource(
            source_id=(
                "cathay_actual_dividend_announcement"
            ),
            issuer_name="國泰證券投資信託股份有限公司",
            official_domains=(
                "cathaysite.com.tw",
                "www.cathaysite.com.tw",
                "cwapi.cathaysite.com.tw",
            ),
            mode=(
                ActualDividendSourceMode
                .VERIFIED_ADAPTER
            ),
            retrieval_policy=(
                SourceRetrievalPolicy
                .EXPLICIT_NETWORK
            ),
            priority=1,
            adapter_name=(
                "cathay_actual_dividend_adapter"
            ),
            discovery_kind=(
                SourceDiscoveryKind.JSON_API
            ),
            notes=(
                "只接受明確標示實際配發組成"
                "的國泰投信官方公告。"
            ),
            issuer_key="cathay",
        )
    ),
    "ctbc_latest_etf_dividend_pdf": (
        ActualDividendSource(
            source_id="ctbc_latest_etf_dividend_pdf",
            issuer_name="中國信託證券投資信託股份有限公司",
            official_domains=(
                "ctbcinvestments.com",
                "www.ctbcinvestments.com",
                "ctbcinvestments.com.tw",
                "www.ctbcinvestments.com.tw",
            ),
            mode=ActualDividendSourceMode.DISCOVERY_ONLY,
            retrieval_policy=SourceRetrievalPolicy.EXPLICIT_NETWORK,
            priority=2,
            discovery_kind=SourceDiscoveryKind.DETERMINISTIC_URL,
            notes=(
                "依 ETF 代號探測官方 ETFLatestDividend PDF；"
                "文件內容尚須區分預估與實際組成。"
            ),
            issuer_key="ctbc",
        )
    ),
    "kgi_etf_dividend_announcement": (
        ActualDividendSource(
            source_id="kgi_etf_dividend_announcement",
            issuer_name="凱基證券投資信託股份有限公司",
            official_domains=(
                "kgifund.com.tw",
                "www.kgifund.com.tw",
            ),
            mode=ActualDividendSourceMode.DISCOVERY_ONLY,
            retrieval_policy=SourceRetrievalPolicy.EXPLICIT_NETWORK,
            priority=3,
            discovery_kind=SourceDiscoveryKind.HTML_LIST,
            notes=(
                "官方 ETF 公告頁可發現 PDF；"
                "已驗證依 ETF 代號查詢與期後／期前公告分流；"
                "PDF 內容 Parser 尚未完成。"
            ),
            issuer_key="kgi",
        )
    ),
    "upam_etf_dividend_document": (
        ActualDividendSource(
            source_id="upam_etf_dividend_document",
            issuer_name="統一證券投資信託股份有限公司",
            official_domains=(
                "ezmoney.com.tw",
                "www.ezmoney.com.tw",
            ),
            mode=ActualDividendSourceMode.DISCOVERY_ONLY,
            retrieval_policy=SourceRetrievalPolicy.EXPLICIT_NETWORK,
            priority=4,
            discovery_kind=SourceDiscoveryKind.PENDING_VERIFICATION,
            notes=(
                "已確認官方文件網域；"
                "尚未確認可依 ETF 代號穩定查詢的公開入口。"
            ),
            issuer_key="upam",
        )
    ),
    "twse_etfortune_dividend": (
        ActualDividendSource(
            source_id="twse_etfortune_dividend",
            issuer_name="臺灣證券交易所",
            official_domains=(
                "twse.com.tw",
                "www.twse.com.tw",
            ),
            mode=(
                ActualDividendSourceMode
                .DISCOVERY_ONLY
            ),
            retrieval_policy=(
                SourceRetrievalPolicy
                .MANUAL_ONLY
            ),
            priority=99,
            enabled=False,
            notes=(
                "現有組成屬 ESTIMATED；"
                "不得作為 ACTUAL 76W 來源。"
            ),
        )
    ),
}


_PENDING_ISSUER_SOURCE_SPECS: dict[
    str,
    tuple[str, str],
] = {
    "yuanta": ("元大投信", "yuanta_etf_dividend_document"),
    "sinopac": ("永豐投信", "sinopac_etf_dividend_document"),
    "mega": ("兆豐投信", "mega_etf_dividend_document"),
    "first": ("第一金投信", "first_etf_dividend_document"),
    "fuh_hwa": ("復華投信", "fuh_hwa_etf_dividend_document"),
    "taishin": ("台新投信", "taishin_etf_dividend_document"),
    "jko": ("街口投信", "jko_etf_dividend_document"),
    "franklin": ("富蘭克林投信", "franklin_etf_dividend_document"),
    "uob": ("大華銀投信", "uob_etf_dividend_document"),
    "nomura": ("野村投信", "nomura_etf_dividend_document"),
    "esun": ("玉山投信", "esun_etf_dividend_document"),
    "union": ("聯邦投信", "union_etf_dividend_document"),
    "hnh": ("華南永昌投信", "hnh_etf_dividend_document"),
    "allianz": ("安聯投信", "allianz_etf_dividend_document"),
    "blackrock": ("貝萊德投信", "blackrock_etf_dividend_document"),
    "jpmorgan": ("摩根投信", "jpmorgan_etf_dividend_document"),
    "alliancebernstein": (
        "聯博投信",
        "alliancebernstein_etf_dividend_document",
    ),
}


# 已以代表 ETF 對官方入口完成即時驗證，可使用共用 HTML 公告探索器。
_HTML_LIST_ISSUER_KEYS = frozenset({
    "yuanta", "upam", "franklin", "jpmorgan", "taishin", "uob", "allianz", "mega",
    "first",
    "sinopac",
    "fuh_hwa",
    "jko",
    "union",
})
_JSON_API_ISSUER_KEYS = frozenset({"alliancebernstein", "esun", "nomura"})
_RESTRICTED_ISSUER_KEYS = frozenset({"blackrock", "hnh"})


ACTUAL_DIVIDEND_SOURCES["capital_etf_dividend_document"] = (
    ActualDividendSource(
        source_id="capital_etf_dividend_document",
        issuer_name="群益證券投資信託股份有限公司",
        official_domains=(
            "capitalfund.com.tw",
            "www.capitalfund.com.tw",
        ),
        mode=ActualDividendSourceMode.DISCOVERY_ONLY,
        retrieval_policy=SourceRetrievalPolicy.EXPLICIT_NETWORK,
        priority=5,
        discovery_kind=SourceDiscoveryKind.HTML_LIST,
        notes=(
            "以官方 DividendInfo API 對應 ETF 名稱，並從最新配息公告頁"
            "篩選期後實際配發公告及 PDF；目前僅覆蓋最新一頁。"
        ),
        issuer_key="capital",
    )
)


ACTUAL_DIVIDEND_SOURCES["fubon_etf_dividend_document"] = (
    ActualDividendSource(
        source_id="fubon_etf_dividend_document",
        issuer_name="富邦證券投資信託股份有限公司",
        official_domains=(
            "fubon.com",
            "www.fubon.com",
            "etrade.fsit.com.tw",
        ),
        mode=ActualDividendSourceMode.DISCOVERY_ONLY,
        retrieval_policy=SourceRetrievalPolicy.EXPLICIT_NETWORK,
        priority=6,
        discovery_kind=SourceDiscoveryKind.HTML_LIST,
        notes=(
            "從官方基金總覽映射證券代號與 Fd，再發現基金頁中的"
            "收益分配 PDF；公告標題不足以判定期前或期後。"
        ),
        issuer_key="fubon",
    )
)


for _issuer_key, (
    _issuer_name,
    _source_id,
) in _PENDING_ISSUER_SOURCE_SPECS.items():
    ACTUAL_DIVIDEND_SOURCES[_source_id] = ActualDividendSource(
        source_id=_source_id,
        issuer_name=_issuer_name,
        official_domains=(),
        mode=ActualDividendSourceMode.DISCOVERY_ONLY,
        retrieval_policy=SourceRetrievalPolicy.EXPLICIT_NETWORK,
        priority=10,
        discovery_kind=SourceDiscoveryKind.PENDING_VERIFICATION,
        notes=(
            "已納入 TWSE ETF 發行人覆蓋基準；"
            "官方查詢入口與文件格式尚待逐家驗證。"
        ),
        issuer_key=_issuer_key,
    )


for _source_id, _source in tuple(ACTUAL_DIVIDEND_SOURCES.items()):
    if (
        _source.issuer_key in ISSUER_DIVIDEND_LANDING_PAGES
        and _source.discovery_kind == SourceDiscoveryKind.PENDING_VERIFICATION
    ):
        _landing_page = ISSUER_DIVIDEND_LANDING_PAGES[_source.issuer_key]
        _supports_generic_discovery = (
            _source.issuer_key in _HTML_LIST_ISSUER_KEYS
            or _source.issuer_key in _JSON_API_ISSUER_KEYS
        )
        ACTUAL_DIVIDEND_SOURCES[_source_id] = ActualDividendSource(
            source_id=_source.source_id,
            issuer_name=_source.issuer_name,
            official_domains=_landing_page.official_domains,
            mode=_source.mode,
            retrieval_policy=(
                SourceRetrievalPolicy.MANUAL_ONLY
                if _source.issuer_key in _RESTRICTED_ISSUER_KEYS
                else _source.retrieval_policy
            ),
            priority=_source.priority,
            discovery_kind=(
                SourceDiscoveryKind.JSON_API
                if _source.issuer_key in _JSON_API_ISSUER_KEYS
                else SourceDiscoveryKind.HTML_LIST
                if _source.issuer_key in _HTML_LIST_ISSUER_KEYS
                else SourceDiscoveryKind.RESTRICTED_OFFICIAL_SOURCE
                if _source.issuer_key in _RESTRICTED_ISSUER_KEYS
                else SourceDiscoveryKind.OFFICIAL_LANDING_PAGE
            ),
            notes=(
                f"已驗證官方 {_landing_page.page_kind} 入口："
                f"{_landing_page.url}；"
                + (
                    (
                        "已實測可依 ETF 代號解析官方歷史配息金額、日期與"
                        "股息利息、資本利得、其他所得及收益平準金比例。"
                        if _source.issuer_key == "taishin"
                        else (
                            "已驗證官方 distributions JSON API；尚未首次配息"
                            "時允許回傳空歷史資料與下次預定日。"
                            if _source.issuer_key == "alliancebernstein"
                            else (
                                "已驗證官方 GetETFOverview 與 "
                                "GetETFFundYieldList JSON API；可對照上市代號並"
                                "取得歷史配息金額及日期。"
                                if _source.issuer_key == "esun"
                                else (
                                "已驗證官方 GetFundYield JSON API；可依 ETF 代號"
                                "取得歷史配息金額、評價日、除息日及發放日。"
                                if _source.issuer_key == "nomura"
                            else (
                                "已實測可依 ETF 代號解析官方基金 ID、基金名稱與"
                                "實際配息金額及日期；組成比例仍待其他官方揭露。"
                                if _source.issuer_key == "uob"
                                else (
                                    "已驗證官方產品公告卡片解析；只接受實際配發或"
                                    "期後收益分配公告，首次配息前允許回傳空結果。"
                                    if _source.issuer_key == "allianz"
                                    else (
                                        "已實測可用官方基金名稱連接證券代號與內部 ID，"
                                        "並解析歷史配息金額、日期、殖利率及明示所得欄位。"
                                        if _source.issuer_key == "mega"
                                        else (
                                            "已實測可用官方內嵌基金資料映射 ETF 代號與"
                                            "基金名稱，並篩選配息金額公告、拒絕期前公告。"
                                            if _source.issuer_key == "first"
                                            else (
                                                "已實測可由官方 PCF 頁解析 ETF 對應 fund ID，"
                                                "並取得配息金額、日期、可分配淨利益與本金比例。"
                                                if _source.issuer_key == "sinopac"
                                                else (
                                                    "已實測可由官方 ETF 選單映射內部 ID，"
                                                    "解析歷史配息並建立月份化組成 PDF 網址。"
                                                    if _source.issuer_key == "fuh_hwa"
                                                    else (
                                                        "已逐檔驗證現有街口期貨 ETF 官方產品頁"
                                                        "均明示收益分配為無；未知新代號不得推定。"
                                                        if _source.issuer_key == "jko"
                                else "已實測可由官方 HTML 探索器依 ETF 代號發現公告；"
                                "文件內容仍須判定正式組成。"
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                            )
                            )
                        )
                    )
                    if _supports_generic_discovery
                    else "尚待升級為可依 ETF 代號查詢的 Adapter。"
                )
            ),
            issuer_key=_source.issuer_key,
        )


for _source_id, _source in tuple(ACTUAL_DIVIDEND_SOURCES.items()):
    if _source.issuer_key not in _RESTRICTED_ISSUER_KEYS:
        continue
    _landing_page = ISSUER_DIVIDEND_LANDING_PAGES[_source.issuer_key]
    _restriction = (
        "官方 HTTPS 憑證已過期；禁止略過 TLS 驗證，待發行人更新憑證。"
        if _landing_page.network_access == "EXPIRED_TLS"
        else "官方 CDN 對後端程式回傳 403；保留瀏覽器可讀入口與手動流程。"
    )
    ACTUAL_DIVIDEND_SOURCES[_source_id] = ActualDividendSource(
        source_id=_source.source_id,
        issuer_name=_source.issuer_name,
        official_domains=_source.official_domains,
        mode=_source.mode,
        retrieval_policy=SourceRetrievalPolicy.MANUAL_ONLY,
        priority=_source.priority,
        adapter_name=_source.adapter_name,
        discovery_kind=SourceDiscoveryKind.RESTRICTED_OFFICIAL_SOURCE,
        enabled=_source.enabled,
        notes=f"已驗證官方入口：{_landing_page.url}；{_restriction}",
        issuer_key=_source.issuer_key,
    )


def list_etf_issuer_sources() -> list[ActualDividendSource]:
    """列出每家 TWSE ETF 發行人的正式配息來源設定。"""

    sources = [
        source
        for source in ACTUAL_DIVIDEND_SOURCES.values()
        if source.issuer_key is not None
    ]
    return sorted(
        sources,
        key=lambda source: source.issuer_key or "",
    )


def get_missing_etf_issuer_keys() -> tuple[str, ...]:
    """回傳尚未在正式配息 Registry 登錄的 ETF 發行人。"""

    registered_keys = {
        source.issuer_key
        for source in list_etf_issuer_sources()
    }
    return tuple(
        sorted(set(TWSE_ETF_ISSUERS) - registered_keys)
    )


def get_actual_dividend_source(
    source_id: str,
) -> ActualDividendSource:
    """依來源識別碼取得正式配息來源。"""

    normalized_source_id = (
        source_id.strip().lower()
    )

    try:
        return ACTUAL_DIVIDEND_SOURCES[
            normalized_source_id
        ]

    except KeyError as error:
        raise KeyError(
            "找不到正式配息資料來源："
            f"{normalized_source_id}"
        ) from error


def list_enabled_actual_dividend_sources(
) -> list[ActualDividendSource]:
    """列出目前啟用的正式配息來源。"""

    return sorted(
        (
            source
            for source in (
                ACTUAL_DIVIDEND_SOURCES
                .values()
            )
            if source.enabled
        ),
        key=lambda source: (
            source.priority,
            source.source_id,
        ),
    )


def list_verified_actual_dividend_adapters(
) -> list[ActualDividendSource]:
    """列出已完成格式驗證的來源 Adapter。"""

    return [
        source
        for source in (
            list_enabled_actual_dividend_sources()
        )
        if (
            source.mode
            == (
                ActualDividendSourceMode
                .VERIFIED_ADAPTER
            )
            and source.adapter_name
        )
    ]
