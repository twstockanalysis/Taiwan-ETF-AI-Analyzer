"""TWSE ETF 配息事件與預估組成正規化。"""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from pydantic import ValidationError

from backend.app.data_sources.twse_etf_dividend import (
    SOURCE_ID,
    TWSEDividendPageRow,
    extract_twse_dividend_rows,
)
from backend.app.models.etf_analysis import (
    DividendComponentBasis,
    ETFDividendComponentImportRecord,
    ETFDividendImportRecord,
    EstimatedDividendComponent,
)


COMPONENT_DEFINITIONS: tuple[
    tuple[
        EstimatedDividendComponent,
        str,
    ],
    ...,
] = (
    (
        EstimatedDividendComponent.DIVIDEND,
        "股利所得",
    ),
    (
        EstimatedDividendComponent.INTEREST,
        "利息所得",
    ),
    (
        EstimatedDividendComponent.EQUALIZATION,
        "收益平準金",
    ),
    (
        EstimatedDividendComponent.REALIZED_CAPITAL_GAIN,
        "已實現資本利得",
    ),
    (
        EstimatedDividendComponent.OTHER,
        "其他所得",
    ),
)


@dataclass(
    frozen=True,
    slots=True,
)
class DividendNormalizationIssue:
    """單筆配息資料拒絕原因。"""

    row_number: int
    etf_code: str
    reason: str


@dataclass(
    frozen=True,
    slots=True,
)
class DividendNormalizationResult:
    """配息正規化結果。"""

    dividends: list[
        ETFDividendImportRecord
    ]

    components: list[
        ETFDividendComponentImportRecord
    ]

    rejected: list[
        DividendNormalizationIssue
    ]


def parse_roc_date(
    value: str,
) -> date:
    """將民國日期轉為西元日期。"""

    normalized_value = (
        value.strip()
        .replace("年", "/")
        .replace("月", "/")
        .replace("日", "")
        .replace(".", "/")
        .replace("-", "/")
    )

    match = re.fullmatch(
        r"(\d{2,3})/(\d{1,2})/(\d{1,2})",
        normalized_value,
    )

    if match is None:
        raise ValueError(
            f"無法解析民國日期：{value}"
        )

    roc_year, month, day = (
        int(part)
        for part in match.groups()
    )

    return date(
        roc_year + 1911,
        month,
        day,
    )


def parse_amount(
    value: str,
) -> Decimal:
    """解析每單位配息金額。"""

    normalized_value = (
        value.strip()
        .replace(",", "")
    )

    if not normalized_value:
        raise ValueError(
            "配息金額尚未公告"
        )

    try:
        amount = Decimal(
            normalized_value
        )

    except InvalidOperation as error:
        raise ValueError(
            f"配息金額格式錯誤：{value}"
        ) from error

    if amount < 0:
        raise ValueError(
            "配息金額不得小於 0"
        )

    return amount


def build_source_event_id(
    etf_code: str,
    ex_dividend_date: date,
) -> str:
    """建立穩定的來源事件識別碼。"""

    return (
        f"{SOURCE_ID}:"
        f"{etf_code.strip().upper()}:"
        f"{ex_dividend_date.isoformat()}"
    )


def extract_estimated_components(
    row: TWSEDividendPageRow,
    source_event_id: str,
) -> list[
    ETFDividendComponentImportRecord
]:
    """擷取五大預估收益分配組成。"""

    component_records: list[
        ETFDividendComponentImportRecord
    ] = []

    for component_code, display_name in (
        COMPONENT_DEFINITIONS
    ):
        match = re.search(
            (
                re.escape(display_name)
                + r"占比\s*"
                + r"([0-9]+(?:\.[0-9]+)?)"
                + r"\s*%"
            ),
            row.detail_text,
        )

        if match is None:
            continue

        component_records.append(
            ETFDividendComponentImportRecord(
                etf_code=row.etf_code,
                dividend_source_event_id=(
                    source_event_id
                ),
                component_code=(
                    component_code.value
                ),
                component_basis=(
                    DividendComponentBasis.ESTIMATED
                ),
                component_name=display_name,
                ratio_pct=Decimal(
                    match.group(1)
                ),
                source_id=SOURCE_ID,
            )
        )

    if component_records:
        if len(component_records) != len(
            COMPONENT_DEFINITIONS
        ):
            raise ValueError(
                "預估配息組成欄位不完整"
            )

        ratio_total = sum(
            (
                record.ratio_pct
                or Decimal("0")
            )
            for record in component_records
        )

        if not (
            Decimal("99.5")
            <= ratio_total
            <= Decimal("100.5")
        ):
            raise ValueError(
                "預估配息組成比例合計異常："
                f"{ratio_total}%"
            )

    return component_records


def normalize_twse_dividend_rows(
    rows: list[TWSEDividendPageRow],
) -> DividendNormalizationResult:
    """將 TWSE 頁面列轉成 Pydantic 模型。"""

    dividends: list[
        ETFDividendImportRecord
    ] = []

    components: list[
        ETFDividendComponentImportRecord
    ] = []

    rejected: list[
        DividendNormalizationIssue
    ] = []

    for row_number, row in enumerate(
        rows,
        start=1,
    ):
        try:
            ex_dividend_date = parse_roc_date(
                row.ex_dividend_date_text
            )

            record_date = parse_roc_date(
                row.record_date_text
            )

            payment_date = parse_roc_date(
                row.payment_date_text
            )

            amount_per_unit = parse_amount(
                row.amount_per_unit_text
            )

            source_event_id = (
                build_source_event_id(
                    row.etf_code,
                    ex_dividend_date,
                )
            )

            dividend_record = (
                ETFDividendImportRecord(
                    etf_code=row.etf_code,
                    source_event_id=(
                        source_event_id
                    ),
                    ex_dividend_date=(
                        ex_dividend_date
                    ),
                    record_date=record_date,
                    payment_date=payment_date,
                    amount_per_unit=(
                        amount_per_unit
                    ),
                    currency="TWD",
                    source_id=SOURCE_ID,
                )
            )

            component_records = (
                extract_estimated_components(
                    row=row,
                    source_event_id=(
                        source_event_id
                    ),
                )
            )

        except (
            ValueError,
            ValidationError,
        ) as error:
            rejected.append(
                DividendNormalizationIssue(
                    row_number=row_number,
                    etf_code=row.etf_code,
                    reason=str(error),
                )
            )

            continue

        dividends.append(
            dividend_record
        )

        components.extend(
            component_records
        )

    return DividendNormalizationResult(
        dividends=dividends,
        components=components,
        rejected=rejected,
    )


def normalize_twse_dividend_html(
    html_text: str,
) -> DividendNormalizationResult:
    """解析並正規化完整 TWSE 配息頁面。"""

    return normalize_twse_dividend_rows(
        extract_twse_dividend_rows(
            html_text
        )
    )
