"""舊稅務模組的配息組成選擇相容介面。"""

from backend.app.services.dividend_component_data import (
    ActualComponentSelection,
    CompositeComponentSelection,
    select_composite_component_mix,
    select_latest_complete_actual_mix,
)


CalculationComponentSelection = CompositeComponentSelection


def select_calculation_component_mix(
    rows: list[dict],
) -> CompositeComponentSelection | None:
    """相容舊呼叫名稱，轉交共用綜合組成選擇器。"""

    return select_composite_component_mix(rows)
