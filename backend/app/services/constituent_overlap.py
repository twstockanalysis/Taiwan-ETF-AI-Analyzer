"""以 ETF 揭露權重計算可追溯的成分股重疊率。"""

from decimal import Decimal, ROUND_HALF_UP

from backend.app.models.etf_constituent import (
    ETFConstituentPosition,
    ETFConstituentSnapshot,
    ETFWeightedOverlapResult,
)


_PERCENT_QUANTUM = Decimal("0.000001")


def calculate_weighted_overlap(
    left: ETFConstituentSnapshot,
    right: ETFConstituentSnapshot,
) -> ETFWeightedOverlapResult:
    """逐一相同識別碼加總兩邊較小的已揭露權重。"""

    left_by_id = {item.constituent_id: item for item in left.positions}
    right_by_id = {item.constituent_id: item for item in right.positions}
    shared: list[ETFConstituentPosition] = []
    for identifier in sorted(left_by_id.keys() & right_by_id.keys()):
        left_item = left_by_id[identifier]
        right_item = right_by_id[identifier]
        shared.append(
            ETFConstituentPosition(
                constituent_id=identifier,
                constituent_name=left_item.constituent_name,
                weight_pct=min(left_item.weight_pct, right_item.weight_pct),
            )
        )
    shared.sort(key=lambda item: (-item.weight_pct, item.constituent_id))
    overlap = sum(item.weight_pct for item in shared).quantize(
        _PERCENT_QUANTUM,
        rounding=ROUND_HALF_UP,
    )
    return ETFWeightedOverlapResult(
        left_etf_code=left.etf_code,
        right_etf_code=right.etf_code,
        left_as_of_date=left.as_of_date,
        right_as_of_date=right.as_of_date,
        left_total_weight_pct=left.total_weight_pct,
        right_total_weight_pct=right.total_weight_pct,
        overlap_pct=overlap,
        shared_constituent_count=len(shared),
        shared_constituents=shared,
    )
