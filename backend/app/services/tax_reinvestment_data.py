"""M10-4 配息組成資料選擇與估算降階。"""

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
class CalculationComponentSelection:
    """計算使用的最新完整組成與來源層級。"""

    dividend_id: int
    source_event_id: str
    source_date: date | None
    basis: str
    mix: list[OfficialComponentAllocation]


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
    """選出最新、比例齊全且合計合理的 ACTUAL 事件。"""

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


def select_calculation_component_mix(
    rows: list[dict],
) -> CalculationComponentSelection | None:
    """優先選 ACTUAL；缺少時以完整 ESTIMATED 組成降階。"""

    for source_basis, calculation_basis in (
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
            return CalculationComponentSelection(
                dividend_id=selection.dividend_id,
                source_event_id=selection.source_event_id,
                source_date=selection.source_date,
                basis=calculation_basis,
                mix=selection.mix,
            )
    return None
