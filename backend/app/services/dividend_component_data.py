"""配息綜合組成的完整性驗證與單一來源選擇。"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from backend.app.models.tax_reinvestment import (
    OfficialComponentAllocation,
)


@dataclass(frozen=True, slots=True)
class ActualComponentSelection:
    """最新且比例完整的 ACTUAL 配息事件。"""

    dividend_id: int
    source_event_id: str
    source_date: date | None
    mix: list[OfficialComponentAllocation]


@dataclass(frozen=True, slots=True)
class CompositeComponentSelection:
    """綜合數據系統選出的單一完整組成與來源層級。"""

    dividend_id: int
    source_event_id: str
    source_date: date | None
    basis: str
    mix: list[OfficialComponentAllocation]


@dataclass(frozen=True, slots=True)
class CompositeRealizedGainRecord:
    """單次配息經綜合選擇後的資本利得資料。"""

    dividend_id: int
    source_event_id: str
    source_date: date | None
    basis: str
    component_code: str
    ratio_pct: Decimal


def _to_date(value) -> date | None:
    if isinstance(value, date):
        return value
    if value:
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None
    return None


def select_latest_complete_actual_mix(
    rows: list[dict],
) -> ActualComponentSelection | None:
    """選出最新、比例齊全且合計約為 100% 的同一事件。"""

    grouped: dict[int, list[dict]] = {}
    order: list[int] = []
    for row in rows:
        dividend_id = int(row["dividend_id"])
        if dividend_id not in grouped:
            grouped[dividend_id] = []
            order.append(dividend_id)
        grouped[dividend_id].append(row)

    for dividend_id in order:
        event_rows = grouped[dividend_id]
        if any(row.get("ratio_pct") is None for row in event_rows):
            continue
        total = sum(
            (Decimal(str(row["ratio_pct"])) for row in event_rows),
            Decimal("0"),
        )
        if total < Decimal("99") or total > Decimal("101"):
            continue

        first = event_rows[0]
        source_date = next(
            (
                parsed
                for field in (
                    "payment_date",
                    "ex_dividend_date",
                    "record_date",
                    "announcement_date",
                )
                if (parsed := _to_date(first.get(field))) is not None
            ),
            None,
        )
        return ActualComponentSelection(
            dividend_id=dividend_id,
            source_event_id=str(first["source_event_id"]),
            source_date=source_date,
            mix=[
                OfficialComponentAllocation(
                    component_code=str(row["component_code"]),
                    component_name=row.get("component_name"),
                    ratio_pct=Decimal(str(row["ratio_pct"])),
                )
                for row in event_rows
            ],
        )
    return None


def select_composite_component_mix(
    rows: list[dict],
) -> CompositeComponentSelection | None:
    """完整 ACTUAL 優先，否則選完整 e添富；不同基礎絕不混用。"""

    for source_basis, output_basis in (
        ("ACTUAL", "ACTUAL"),
        ("ESTIMATED", "ESTIMATED_FALLBACK"),
    ):
        basis_rows = [
            row
            for row in rows
            if str(row.get("component_basis", "ACTUAL")).upper()
            == source_basis
        ]
        selection = select_latest_complete_actual_mix(basis_rows)
        if selection is not None:
            return CompositeComponentSelection(
                dividend_id=selection.dividend_id,
                source_event_id=selection.source_event_id,
                source_date=selection.source_date,
                basis=output_basis,
                mix=selection.mix,
            )
    return None


def select_composite_realized_gain_history(
    rows: list[dict],
) -> list[CompositeRealizedGainRecord]:
    """逐次配息選擇完整組成，再取得正式或替代資本利得比例。"""

    grouped: dict[int, list[dict]] = {}
    for row in rows:
        dividend_id = int(row["dividend_id"])
        grouped.setdefault(dividend_id, []).append(row)

    records: list[CompositeRealizedGainRecord] = []
    for event_rows in grouped.values():
        selection = select_composite_component_mix(event_rows)
        if selection is None:
            continue

        target_code = (
            "76W"
            if selection.basis == "ACTUAL"
            else "EST_REALIZED_CAPITAL_GAIN"
        )
        component = next(
            (
                item
                for item in selection.mix
                if item.component_code == target_code
            ),
            None,
        )
        if component is None:
            continue

        records.append(
            CompositeRealizedGainRecord(
                dividend_id=selection.dividend_id,
                source_event_id=selection.source_event_id,
                source_date=selection.source_date,
                basis=selection.basis,
                component_code=target_code,
                ratio_pct=component.ratio_pct,
            )
        )

    return sorted(
        records,
        key=lambda item: (
            item.source_date or date.min,
            item.dividend_id,
        ),
        reverse=True,
    )
