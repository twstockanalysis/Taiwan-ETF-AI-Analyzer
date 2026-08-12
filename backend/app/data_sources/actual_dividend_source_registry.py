"""正式 ETF 配息組成資料來源 Registry。"""

from dataclasses import dataclass
from enum import StrEnum


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
                "尚需驗證分頁與正式／期前公告分流。"
            ),
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
