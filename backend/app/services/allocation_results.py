"""V5-4 完整組合的主配置結果。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from backend.app.models.allocation_results import (
    AllocationExcludedCandidate,
    AllocationResultsRequest,
    AllocationResultsResponse,
    AllocationStrategy,
    AllocationStrategyPlan,
)
from backend.app.models.public_planner import PublicPlannerIssue
from backend.app.services.integer_allocation import build_integer_allocation
from backend.app.services.market_eligibility_index import (
    build_market_eligibility_index,
)


def _issue(code: str, message: str) -> PublicPlannerIssue:
    return PublicPlannerIssue(code=code, message=message)


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
            simple_explanation=(
                "依現金流缺口、所需資金、溢出與新增檔數依序產生。"
            ),
            result=recommended_result,
        )
    ]
    strategy_issues: list[PublicPlannerIssue] = []
    if not recommended_result.additions:
        strategy_issues.append(
            _issue(
                "ALTERNATIVE_UNAVAILABLE_WITHOUT_PRIMARY_ALLOCATION",
                "推薦配置目前沒有新增標的，因此不產生重複的其他配置。",
            )
        )
    else:
        strategy_issues.append(
            _issue(
                "POST_FEASIBILITY_ALTERNATIVE_SELECTION_DEFERRED",
                "V5-4 先回傳資金效率主方案；品質、風險、集中度與重疊"
                "只能在可行後比較，尚未完成公開替代方案命名。",
            )
        )

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
