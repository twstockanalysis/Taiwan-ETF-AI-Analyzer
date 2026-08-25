"""V3-4 推薦、平衡與集中配置結果。"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from itertools import combinations
from pathlib import Path

from backend.app.models.allocation_results import (
    AllocationExcludedCandidate,
    AllocationResultsRequest,
    AllocationResultsResponse,
    AllocationStrategy,
    AllocationStrategyPlan,
)
from backend.app.models.public_planner import PublicPlannerIssue
from backend.app.services.constituent_overlap import calculate_gated_pair_overlap
from backend.app.services.integer_allocation import build_integer_allocation
from backend.app.services.market_eligibility_index import (
    InternalMarketCandidate,
    build_market_eligibility_index,
)


_MAX_STYLE_CANDIDATES = 10


def _issue(code: str, message: str) -> PublicPlannerIssue:
    return PublicPlannerIssue(code=code, message=message)


def _signature(plan: AllocationStrategyPlan) -> tuple[tuple[str, int], ...]:
    return tuple(
        (item.etf_code, item.additional_shares)
        for item in plan.result.additions
    )


def _pair_overlap_averages(
    candidates: tuple[InternalMarketCandidate, ...],
    database_path: str | Path,
    analysis_date: date,
) -> dict[str, Decimal]:
    selected = candidates[:_MAX_STYLE_CANDIDATES]
    totals = {item.public_item.etf_code: Decimal("0") for item in selected}
    counts = {item.public_item.etf_code: 0 for item in selected}
    for left, right in combinations(selected, 2):
        left_code = left.public_item.etf_code
        right_code = right.public_item.etf_code
        overlap = calculate_gated_pair_overlap(
            left_code,
            right_code,
            database_path,
            evaluated_on=analysis_date,
        )
        if overlap.overlap_pct is None:
            continue
        totals[left_code] += overlap.overlap_pct
        totals[right_code] += overlap.overlap_pct
        counts[left_code] += 1
        counts[right_code] += 1
    return {
        code: totals[code] / counts[code]
        for code in totals
        if counts[code] > 0
    }


def _style_order(
    candidates: tuple[InternalMarketCandidate, ...],
    overlap_averages: dict[str, Decimal],
    strategy: AllocationStrategy,
) -> tuple[str, ...]:
    def total_return(candidate: InternalMarketCandidate) -> Decimal:
        value = candidate.public_item.estimated_after_tax_total_return_pct
        return value if value is not None else Decimal("-100")

    if strategy == AllocationStrategy.BALANCED:
        ordered = sorted(
            candidates,
            key=lambda item: (
                overlap_averages.get(
                    item.public_item.etf_code, Decimal("101")
                ),
                -total_return(item),
                item.public_item.etf_code,
            ),
        )
    else:
        ordered = sorted(
            candidates,
            key=lambda item: (
                item.public_item.etf_code not in overlap_averages,
                -total_return(item),
                -overlap_averages.get(
                    item.public_item.etf_code, Decimal("-1")
                ),
                item.public_item.etf_code,
            ),
        )
    return tuple(item.public_item.etf_code for item in ordered)


def build_allocation_results(
    request: AllocationResultsRequest,
    database_path: str | Path,
    *,
    as_of_date: date | None = None,
) -> AllocationResultsResponse:
    analysis_date = as_of_date or date.today()
    built_index = build_market_eligibility_index(
        request,
        database_path,
        as_of_date=analysis_date,
    )
    recommended_result = build_integer_allocation(
        request,
        database_path,
        as_of_date=analysis_date,
    )
    plans = [
        AllocationStrategyPlan(
            strategy=AllocationStrategy.RECOMMENDED,
            label="推薦配置",
            simple_explanation="依現金流缺口、所需資金與風險門檻依序產生。",
            result=recommended_result,
        )
    ]
    strategy_issues: list[PublicPlannerIssue] = []
    candidates = built_index.ranked_eligible_candidates
    if not recommended_result.additions:
        strategy_issues.append(
            _issue(
                "ALTERNATIVE_UNAVAILABLE_WITHOUT_PRIMARY_ALLOCATION",
                "推薦配置目前沒有新增標的，因此不產生重複的其他配置。",
            )
        )
    else:
        overlap_averages = _pair_overlap_averages(
            candidates,
            database_path,
            analysis_date,
        )
        if len(overlap_averages) < 2:
            strategy_issues.append(
                _issue(
                    "ALTERNATIVE_OVERLAP_DATA_UNAVAILABLE",
                    "正式成分股資料不足，暫時無法產生可信的平衡或集中配置。",
                )
            )
            overlap_averages = {}
        definitions = () if not overlap_averages else (
            (
                AllocationStrategy.BALANCED,
                "平衡配置",
                "降低 ETF 之間的成分股重疊，避免資金過度集中在相同股票。",
            ),
            (
                AllocationStrategy.FOCUSED,
                "集中配置",
                "集中於近期總報酬較強且成分股較相近的 ETF，波動風險可能較高。",
            ),
        )
        signatures = {_signature(plans[0])}
        for strategy, label, explanation in definitions:
            result = build_integer_allocation(
                request,
                database_path,
                as_of_date=analysis_date,
                preferred_candidate_order=_style_order(
                    candidates,
                    overlap_averages,
                    strategy,
                ),
                preference_first=True,
            )
            plan = AllocationStrategyPlan(
                strategy=strategy,
                label=label,
                simple_explanation=explanation,
                result=result,
            )
            signature = _signature(plan)
            if signature in signatures:
                strategy_issues.append(
                    _issue(
                        f"{strategy.value}_NOT_MATERIALLY_DIFFERENT",
                        f"{label}與既有結果沒有明顯差異，因此不重複顯示。",
                    )
                )
                continue
            if not result.additions:
                strategy_issues.append(
                    _issue(
                        f"{strategy.value}_UNAVAILABLE",
                        f"目前資料無法產生可執行的{label}。",
                    )
                )
                continue
            signatures.add(signature)
            plans.append(plan)

    excluded = [
        AllocationExcludedCandidate(
            etf_code=item.etf_code,
            name=item.name,
            reasons=item.reasons,
        )
        for item in built_index.response.candidates
        if not item.eligible_for_addition
    ]
    return AllocationResultsResponse(
        snapshot_id=built_index.response.snapshot_id,
        plans=plans,
        excluded_candidates=excluded,
        strategy_issues=strategy_issues,
    )
