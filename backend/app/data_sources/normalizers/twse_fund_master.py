"""TWSE 基金基本資料正規化器。"""

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Any

from pydantic import ValidationError

from backend.app.data_sources.registry import Market
from backend.app.models.etf_import import ETFImportRecord


CODE_FIELDS = (
    "基金代號",
    "證券代號",
    "代號",
)

NAME_FIELDS = (
    "基金簡稱",
    "基金中文名稱",
    "基金名稱",
    "中文名稱",
)

FUND_TYPE_FIELDS = (
    "基金類型",
    "基金型態",
    "基金種類",
)

LISTING_DATE_FIELDS = (
    "上市日期",
    "上櫃日期",
    "掛牌日期",
)

SOURCE_UPDATED_FIELDS = (
    "出表日期",
)

ETF_KEYWORDS = (
    "ETF",
    "指數股票型基金",
    "交易所交易基金",
)

ACTIVE_KEYWORDS = (
    "主動式",
    "主動型",
    "主動",
)

BOND_KEYWORDS = (
    "債券",
    "公債",
    "公司債",
    "金融債",
    "美債",
    "投資級債",
    "非投資級債",
    "固定收益",
    "BOND",
)


@dataclass(
    frozen=True,
    slots=True,
)
class RejectedRecord:
    """正規化失敗的原始紀錄。"""

    index: int
    reason: str
    record: dict[str, Any]


@dataclass(
    frozen=True,
    slots=True,
)
class NormalizationResult:
    """一批原始資料的正規化結果。"""

    accepted: list[ETFImportRecord]
    rejected: list[RejectedRecord]


def get_first_value(
    record: dict[str, Any],
    field_names: tuple[str, ...],
) -> Any | None:
    """依候選欄位名稱取得第一個有效值。

    Args:
        record:
            官方 API 原始紀錄。
        field_names:
            可接受的來源欄位名稱。

    Returns:
        Any | None:
            第一個非空值，找不到時回傳 None。
    """

    for field_name in field_names:
        value = record.get(field_name)

        if value is None:
            continue

        if isinstance(value, str):
            value = value.strip()

            if not value:
                continue

        return value

    return None


def build_searchable_text(
    record: dict[str, Any],
) -> str:
    """建立 ETF 分類用的搜尋文字。"""

    values = [
        get_first_value(
            record,
            NAME_FIELDS,
        ),
        get_first_value(
            record,
            FUND_TYPE_FIELDS,
        ),
    ]

    return " ".join(
        str(value)
        for value in values
        if value is not None
    ).upper()


def is_etf_record(
    record: dict[str, Any],
) -> bool:
    """判斷原始紀錄是否屬於 ETF。"""

    searchable_text = build_searchable_text(
        record
    )

    return any(
        keyword.upper() in searchable_text
        for keyword in ETF_KEYWORDS
    )


def classify_is_active(
    record: dict[str, Any],
) -> bool:
    """判斷是否為主動式 ETF。"""

    searchable_text = build_searchable_text(
        record
    )

    return any(
        keyword.upper() in searchable_text
        for keyword in ACTIVE_KEYWORDS
    )


def classify_is_bond(
    record: dict[str, Any],
) -> bool:
    """判斷是否為債券 ETF。"""

    searchable_text = build_searchable_text(
        record
    )

    return any(
        keyword.upper() in searchable_text
        for keyword in BOND_KEYWORDS
    )


def parse_listing_date(
    value: Any | None,
) -> date | None:
    """將來源日期轉換成西元 date。

    支援格式：

    - 西元YYYY-MM-DD
    - 西元YYYY/MM/DD
    - 西元YYYYMMDD
    - 民國 YYY/MM/DD
    - 民國 YYYMMDD
    - 民國 YYMMDD

    Args:
        value:
            來源日期值。

    Returns:
        date | None:
            轉換完成的西元日期。

    Raises:
        ValueError:
            日期格式無法辨識。
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()

    if not text:
        return None

    # 處理有分隔符號的格式。
    normalized_text = text.replace("-", "/")
    parts = normalized_text.split("/")

    if len(parts) == 3:
        year_text, month_text, day_text = parts

        if not all(
            part.isdigit()
            for part in parts
        ):
            raise ValueError(
                f"無法辨識上市日期：{text}"
            )

        year = int(year_text)
        month = int(month_text)
        day = int(day_text)

        # 三位數以下視為民國年。
        if len(year_text) <= 3:
            year += 1911

        return date(
            year,
            month,
            day,
        )

    if not text.isdigit():
        raise ValueError(
            f"無法辨識上市日期：{text}"
        )

    # 西元 YYYYMMDD，必須明確為 8 位數。
    if len(text) == 8:
        year = int(text[:4])
        month = int(text[4:6])
        day = int(text[6:8])

        return date(
            year,
            month,
            day,
        )

    # 民國 YYYMMDD，例如 0920630。
    if len(text) == 7:
        roc_year = int(text[:3])
        month = int(text[3:5])
        day = int(text[5:7])

        return date(
            roc_year + 1911,
            month,
            day,
        )

    # 民國 YYMMDD，例如 920630。
    if len(text) == 6:
        roc_year = int(text[:2])
        month = int(text[2:4])
        day = int(text[4:6])

        return date(
            roc_year + 1911,
            month,
            day,
        )

    raise ValueError(
        f"無法辨識上市日期：{text}"
    )


def normalize_twse_fund_record(
    record: dict[str, Any],
) -> ETFImportRecord:
    """將一筆 TWSE 原始資料轉換為 ETFImportRecord。

    Args:
        record:
            TWSE 官方原始紀錄。

    Returns:
        ETFImportRecord:
            驗證完成的 ETF 資料。

    Raises:
        ValueError:
            非 ETF 或缺少必要欄位。
        ValidationError:
            Pydantic 驗證失敗。
    """

    if not is_etf_record(record):
        raise ValueError(
            "來源紀錄不是 ETF"
        )

    code = get_first_value(
        record,
        CODE_FIELDS,
    )

    if code is None:
        raise ValueError(
            "來源紀錄缺少 ETF 代號"
        )

    name = get_first_value(
        record,
        NAME_FIELDS,
    )

    if name is None:
        raise ValueError(
            "來源紀錄缺少 ETF 名稱"
        )

    listing_date_value = get_first_value(
        record,
        LISTING_DATE_FIELDS,
    )

    source_updated_value = get_first_value(
        record,
        SOURCE_UPDATED_FIELDS,
    )
    source_updated_date = parse_listing_date(
        source_updated_value
    )

    return ETFImportRecord.model_validate(
        {
            "code": str(code),
            "name": str(name),
            "is_active": classify_is_active(
                record
            ),
            "is_bond": classify_is_bond(
                record
            ),
            "listing_date": parse_listing_date(
                listing_date_value
            ),
            "fund_size": None,
            "expense_ratio": None,
            "market": Market.TWSE,
            "source_id": "twse_openapi",
            "source_updated_at": (
                datetime.combine(
                    source_updated_date,
                    time.min,
                    tzinfo=timezone.utc,
                )
                if source_updated_date
                else None
            ),
        }
    )


def normalize_twse_fund_records(
    records: list[dict[str, Any]],
) -> NormalizationResult:
    """正規化一批 TWSE 基金基本資料。"""

    accepted: list[ETFImportRecord] = []
    rejected: list[RejectedRecord] = []

    for index, record in enumerate(
        records,
        start=1,
    ):
        try:
            normalized_record = (
                normalize_twse_fund_record(
                    record
                )
            )

        except (
            ValueError,
            TypeError,
            ValidationError,
        ) as error:
            rejected.append(
                RejectedRecord(
                    index=index,
                    reason=str(error),
                    record=record,
                )
            )
            continue

        accepted.append(
            normalized_record
        )

    return NormalizationResult(
        accepted=accepted,
        rejected=rejected,
    )
