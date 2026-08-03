"""正式收益分配通知書與既有配息事件匹配。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.data_sources.actual_dividend_notice import (
    ActualDividendNoticeInput,
)


AMOUNT_TOLERANCE = Decimal("0.000001")


@dataclass(
    frozen=True,
    slots=True,
)
class MatchedActualDividendNotice:
    """已唯一匹配既有配息事件的通知書。"""

    notice: ActualDividendNoticeInput
    dividend_id: int
    dividend_source_event_id: str


@dataclass(
    frozen=True,
    slots=True,
)
class ActualDividendMatchIssue:
    """通知書與配息事件匹配失敗原因。"""

    category: str
    etf_code: str
    source_document_id: str
    reason: str


@dataclass(
    frozen=True,
    slots=True,
)
class ActualDividendMatchResult:
    """正式通知書批次匹配結果。"""

    matched: list[
        MatchedActualDividendNotice
    ]

    rejected: list[
        ActualDividendMatchIssue
    ]


def match_actual_dividend_notices(
    notices: list[
        ActualDividendNoticeInput
    ],
    database_path: str | Path,
) -> ActualDividendMatchResult:
    """以 ETF、除息日與金額匹配既有事件。"""

    connection = get_connection(
        database_path
    )

    matched: list[
        MatchedActualDividendNotice
    ] = []

    rejected: list[
        ActualDividendMatchIssue
    ] = []

    try:
        for notice in notices:
            master_row = connection.execute(
                """
                SELECT code
                FROM etf_master
                WHERE code = ?;
                """,
                (notice.etf_code,),
            ).fetchone()

            if master_row is None:
                rejected.append(
                    ActualDividendMatchIssue(
                        category=(
                            "missing_etf_master"
                        ),
                        etf_code=notice.etf_code,
                        source_document_id=(
                            notice.source_document_id
                        ),
                        reason=(
                            "找不到 ETF 主資料："
                            f"{notice.etf_code}"
                        ),
                    )
                )
                continue

            rows = connection.execute(
                """
                SELECT
                    id,
                    source_event_id,
                    source_id,
                    record_date,
                    payment_date,
                    amount_per_unit
                FROM etf_dividend
                WHERE etf_code = ?
                  AND ex_dividend_date = ?
                ORDER BY id;
                """,
                (
                    notice.etf_code,
                    notice.ex_dividend_date
                    .isoformat(),
                ),
            ).fetchall()

            if not rows:
                rejected.append(
                    ActualDividendMatchIssue(
                        category=(
                            "missing_dividend_event"
                        ),
                        etf_code=notice.etf_code,
                        source_document_id=(
                            notice.source_document_id
                        ),
                        reason=(
                            "找不到相同 ETF 與除息日的"
                            "既有配息事件"
                        ),
                    )
                )
                continue

            amount_matches = [
                row
                for row in rows
                if abs(
                    Decimal(
                        str(
                            row[
                                "amount_per_unit"
                            ]
                        )
                    )
                    - notice.amount_per_unit
                )
                <= AMOUNT_TOLERANCE
            ]

            if not amount_matches:
                available_amounts = ", ".join(
                    str(
                        row[
                            "amount_per_unit"
                        ]
                    )
                    for row in rows
                )

                rejected.append(
                    ActualDividendMatchIssue(
                        category="amount_mismatch",
                        etf_code=notice.etf_code,
                        source_document_id=(
                            notice.source_document_id
                        ),
                        reason=(
                            "每單位配息金額無法匹配；"
                            "既有金額："
                            f"{available_amounts}"
                        ),
                    )
                )
                continue

            metadata_matches = (
                amount_matches
            )

            if notice.record_date is not None:
                metadata_matches = [
                    row
                    for row in metadata_matches
                    if row["record_date"]
                    == notice.record_date
                    .isoformat()
                ]

            if notice.payment_date is not None:
                metadata_matches = [
                    row
                    for row in metadata_matches
                    if row["payment_date"]
                    == notice.payment_date
                    .isoformat()
                ]

            if not metadata_matches:
                rejected.append(
                    ActualDividendMatchIssue(
                        category=(
                            "event_metadata_mismatch"
                        ),
                        etf_code=notice.etf_code,
                        source_document_id=(
                            notice.source_document_id
                        ),
                        reason=(
                            "配息金額相同，但基準日或"
                            "發放日與既有事件不一致"
                        ),
                    )
                )
                continue

            if len(metadata_matches) > 1:
                event_descriptions = ", ".join(
                    (
                        f"{row['source_id']}/"
                        f"{row['source_event_id']}"
                    )
                    for row in metadata_matches
                )

                rejected.append(
                    ActualDividendMatchIssue(
                        category=(
                            "ambiguous_dividend_event"
                        ),
                        etf_code=notice.etf_code,
                        source_document_id=(
                            notice.source_document_id
                        ),
                        reason=(
                            "正式通知書匹配到多筆"
                            "既有配息事件："
                            f"{event_descriptions}"
                        ),
                    )
                )
                continue

            row = metadata_matches[0]

            matched.append(
                MatchedActualDividendNotice(
                    notice=notice,
                    dividend_id=int(
                        row["id"]
                    ),
                    dividend_source_event_id=(
                        row["source_event_id"]
                    ),
                )
            )

    finally:
        connection.close()

    return ActualDividendMatchResult(
        matched=matched,
        rejected=rejected,
    )
