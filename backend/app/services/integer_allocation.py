"""V3-3 確定性整數股數配置求解器。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from pathlib import Path

from backend.app.models.integer_allocation import (
    IntegerAllocationAddition,
    IntegerAllocationAssumptions,
    IntegerAllocationHoldingResult,
    IntegerAllocationMonthResult,
    IntegerAllocationOptimality,
    IntegerAllocationRequest,
    IntegerAllocationResponse,
    IntegerAllocationStatus,
)
from backend.app.models.public_planner import (
    PublicPlannerIssue,
    PublicPlannerResponse,
)
from backend.app.services.market_eligibility_index import (
    InternalMarketCandidate,
    build_market_eligibility_index,
)
from backend.app.services.public_planner import analyze_public_planner_baseline


_MONEY = Decimal("0.01")
_PCT = Decimal("0.01")
_MAX_REPAIR_STEPS = 10_000


def _money(value: Decimal) -> Decimal:
    return value.quantize(_MONEY, rounding=ROUND_HALF_UP)


def _ceil_shares(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_CEILING))


def _issue(code: str, message: str, field: str | None = None) -> PublicPlannerIssue:
    return PublicPlannerIssue(code=code, message=message, field=field)


@dataclass(slots=True)
class _SolveState:
    shares: dict[str, int]
    current_values: dict[str, Decimal]
    prices: dict[str, Decimal]


def _resulting_holdings(
    baseline: PublicPlannerResponse,
    request: IntegerAllocationRequest,
    added_shares: dict[str, int],
    added_prices: dict[str, Decimal],
) -> list[IntegerAllocationHoldingResult]:
    existing_units = {
        holding.etf_code: holding.held_units for holding in request.existing_holdings
    }
    values = {
        holding.etf_code: holding.current_value
        for holding in baseline.holdings
        if holding.current_value is not None
    }
    for code, shares in added_shares.items():
        if shares > 0:
            values[code] = values.get(code, Decimal("0")) + added_prices[code] * shares
    total = sum(values.values(), Decimal("0"))
    results = []
    for code in sorted(values):
        fact = next(
            (holding for holding in baseline.holdings if holding.etf_code == code),
            None,
        )
        price = added_prices.get(code) or (fact.unit_price if fact else None)
        if price is None or total <= 0:
            continue
        existing = existing_units.get(code, 0)
        additional = added_shares.get(code, 0)
        results.append(
            IntegerAllocationHoldingResult(
                etf_code=code,
                existing_shares=existing,
                additional_shares=additional,
                resulting_shares=existing + additional,
                reference_price=price,
                resulting_value=_money(values[code]),
                allocation_pct=(
                    values[code] / total * Decimal("100")
                ).quantize(_PCT, rounding=ROUND_HALF_UP),
            )
        )
    return results


def _cash_gain(
    candidate: InternalMarketCandidate,
    selected_months: tuple[int, ...],
    remaining: dict[int, Decimal],
) -> Decimal:
    return sum(
        min(
            remaining[month],
            candidate.monthly_after_tax_cash_per_share[month - 1],
        )
        for month in selected_months
    )


def _add_cash_covering_shares(
    candidates: tuple[InternalMarketCandidate, ...],
    selected_months: tuple[int, ...],
    current_cash: dict[int, Decimal],
    target: Decimal,
    state: _SolveState,
    preference_rank: dict[str, int] | None = None,
    preference_first: bool = False,
) -> bool:
    """以整數批次逐步縮小短缺；不經過小數股求解再進位。"""

    for _ in range(len(selected_months) * max(len(candidates), 1) + 1):
        remaining = {
            month: max(target - current_cash[month], Decimal("0"))
            for month in selected_months
        }
        if not any(remaining.values()):
            return True
        ranked = []
        for candidate in candidates:
            price = candidate.public_item.reference_price
            if price is None:
                continue
            gain = _cash_gain(candidate, selected_months, remaining)
            if gain <= 0:
                continue
            code = candidate.public_item.etf_code
            preference = (preference_rank or {}).get(code, len(candidates))
            if preference_first:
                key = (
                    preference,
                    -(gain / price),
                    -(candidate.quality_score or Decimal("0")),
                    code,
                )
            else:
                key = (
                    -(gain / price),
                    -(candidate.quality_score or Decimal("0")),
                    preference,
                    code,
                )
            ranked.append((*key, candidate))
        if not ranked:
            return False
        candidate = min(ranked)[-1]
        positive_needs = [
            _ceil_shares(
                remaining[month]
                / candidate.monthly_after_tax_cash_per_share[month - 1]
            )
            for month in selected_months
            if remaining[month] > 0
            and candidate.monthly_after_tax_cash_per_share[month - 1] > 0
        ]
        quantity = max(1, min(positive_needs))
        code = candidate.public_item.etf_code
        state.shares[code] = state.shares.get(code, 0) + quantity
        for month in selected_months:
            current_cash[month] += (
                candidate.monthly_after_tax_cash_per_share[month - 1] * quantity
            )
    return not any(current_cash[month] < target for month in selected_months)


def _repair_concentration(
    candidates_by_code: dict[str, InternalMarketCandidate],
    state: _SolveState,
    max_pct: Decimal,
    preference_rank: dict[str, int] | None = None,
) -> bool:
    """以整數股增加低權重候選，直到所有單一 ETF 市值不超過上限。"""

    limit = max_pct / Decimal("100")
    if limit <= 0:
        return False
    for _ in range(_MAX_REPAIR_STEPS):
        values = dict(state.current_values)
        for code, shares in state.shares.items():
            values[code] = values.get(code, Decimal("0")) + state.prices[code] * shares
        total = sum(values.values(), Decimal("0"))
        if total <= 0:
            return not state.shares
        dominant_value = max(values.values())
        if dominant_value <= total * limit:
            return True

        required_total = dominant_value / limit
        deficit = required_total - total
        choices = []
        for code, candidate in candidates_by_code.items():
            price = state.prices[code]
            value = values.get(code, Decimal("0"))
            if value >= dominant_value:
                continue
            choices.append((value, code, price, candidate))
        if not choices:
            return False
        value, code, price, _ = min(
            choices,
            key=lambda row: (
                row[0],
                (preference_rank or {}).get(row[1], len(candidates_by_code)),
                row[1],
            ),
        )
        room = max(dominant_value - value, price)
        quantity = max(1, min(_ceil_shares(deficit / price), _ceil_shares(room / price)))
        state.shares[code] = state.shares.get(code, 0) + quantity
    return False


def build_integer_allocation(
    request: IntegerAllocationRequest,
    database_path: str | Path,
    *,
    as_of_date: date | None = None,
    preferred_candidate_order: tuple[str, ...] | None = None,
    preference_first: bool = False,
) -> IntegerAllocationResponse:
    analysis_date = as_of_date or date.today()
    baseline = analyze_public_planner_baseline(
        request, database_path, as_of_date=analysis_date
    )
    built_index = build_market_eligibility_index(
        request, database_path, as_of_date=analysis_date
    )
    index = built_index.response
    assumptions = IntegerAllocationAssumptions(
        cash_deduction_rate_pct=request.cash_deduction_rate_pct,
        max_candidate_allocation_pct=index.rules.max_candidate_allocation_pct,
    )
    selected = tuple(request.target_months)
    current_cash: dict[int, Decimal] = {}
    unavailable_months = []
    for month in selected:
        row = baseline.monthly_cash_flow[month - 1]
        if row.after_tax_cash is None:
            unavailable_months.append(month)
        else:
            current_cash[month] = row.after_tax_cash

    empty_months = [
        IntegerAllocationMonthResult(
            month=month,
            current_after_tax_cash=current_cash.get(month, Decimal("0")),
            added_after_tax_cash=Decimal("0"),
            modeled_after_tax_cash=current_cash.get(month, Decimal("0")),
            target_after_tax_cash=request.target_after_tax_cash_twd,
            shortfall=max(
                request.target_after_tax_cash_twd
                - current_cash.get(month, Decimal("0")),
                Decimal("0"),
            ),
        )
        for month in selected
    ]
    common = dict(
        analysis_date=analysis_date,
        snapshot_id=index.snapshot_id,
        target_after_tax_cash_twd=request.target_after_tax_cash_twd,
        target_months=list(selected),
        assumptions=assumptions,
        universe_count=index.universe_count,
        eligible_count=index.eligible_count,
    )
    missing_holding_values = [
        holding.etf_code
        for holding in baseline.holdings
        if holding.current_value is None
    ]
    if unavailable_months or missing_holding_values:
        unavailable_issues = list(baseline.issues)
        if unavailable_months:
            unavailable_issues.append(
                _issue(
                    "CURRENT_CASH_UNAVAILABLE",
                    "現有持股在部分目標月份缺少可計算的歷史現金流。",
                    "existing_holdings",
                )
            )
        if missing_holding_values:
            unavailable_issues.append(
                _issue(
                    "CURRENT_VALUE_UNAVAILABLE",
                    "現有持股缺少參考價格，無法驗證配置後集中度與所需資金。",
                    "existing_holdings",
                )
            )
        return IntegerAllocationResponse(
            **common,
            status=IntegerAllocationStatus.UNAVAILABLE,
            optimality=IntegerAllocationOptimality.NOT_APPLICABLE,
            total_required_additional_capital=Decimal("0"),
            monthly_results=empty_months,
            issues=unavailable_issues,
        )

    target = request.target_after_tax_cash_twd
    already_met = all(current_cash[month] >= target for month in selected)
    candidates = built_index.ranked_eligible_candidates
    if already_met:
        return IntegerAllocationResponse(
            **common,
            status=IntegerAllocationStatus.TARGET_MET,
            optimality=IntegerAllocationOptimality.PROVED_OPTIMAL,
            total_required_additional_capital=Decimal("0"),
            monthly_results=empty_months,
            resulting_holdings=_resulting_holdings(
                baseline, request, {}, {}
            ),
            issues=baseline.issues,
        )
    if not candidates:
        return IntegerAllocationResponse(
            **common,
            status=IntegerAllocationStatus.NO_ELIGIBLE_ALLOCATION,
            optimality=IntegerAllocationOptimality.NOT_APPLICABLE,
            total_required_additional_capital=Decimal("0"),
            monthly_results=empty_months,
            issues=[
                *baseline.issues,
                _issue(
                    "NO_ELIGIBLE_CANDIDATE",
                    "目前沒有通過全市場資料與風險門檻的可新增 ETF。",
                )
            ],
        )

    candidates_by_code = {
        item.public_item.etf_code: item for item in candidates
    }
    prices = {
        code: candidate.public_item.reference_price
        for code, candidate in candidates_by_code.items()
        if candidate.public_item.reference_price is not None
    }
    current_values = {
        holding.etf_code: holding.current_value
        for holding in baseline.holdings
        if holding.current_value is not None
    }
    state = _SolveState(shares={}, current_values=current_values, prices=prices)
    solve_cash = dict(current_cash)
    preference_rank = {
        code: rank for rank, code in enumerate(preferred_candidate_order or ())
    }
    _add_cash_covering_shares(
        candidates,
        selected,
        solve_cash,
        target,
        state,
        preference_rank,
        preference_first,
    )
    concentration_ok = _repair_concentration(
        candidates_by_code,
        state,
        index.rules.max_candidate_allocation_pct,
        preference_rank,
    )
    if not concentration_ok:
        return IntegerAllocationResponse(
            **common,
            status=IntegerAllocationStatus.NO_ELIGIBLE_ALLOCATION,
            optimality=IntegerAllocationOptimality.NOT_APPLICABLE,
            total_required_additional_capital=Decimal("0"),
            monthly_results=empty_months,
            issues=[
                *baseline.issues,
                _issue(
                    "CONCENTRATION_CONSTRAINT_INFEASIBLE",
                    "通過資格門檻的 ETF 結構不足以同時符合單一 ETF 20% 市值上限。",
                )
            ],
        )

    added_cash = {month: Decimal("0") for month in selected}
    additions = []
    for code in sorted(state.shares):
        quantity = state.shares[code]
        if quantity <= 0:
            continue
        candidate = candidates_by_code[code]
        price = prices[code]
        for month in selected:
            added_cash[month] += (
                candidate.monthly_after_tax_cash_per_share[month - 1] * quantity
            )
        supported = [
            month
            for month in selected
            if candidate.monthly_after_tax_cash_per_share[month - 1] > 0
        ]
        risks = [reason.message for reason in candidate.public_item.reasons]
        additions.append(
            IntegerAllocationAddition(
                etf_code=code,
                name=candidate.public_item.name,
                additional_shares=quantity,
                reference_price=price,
                reference_price_as_of=candidate.public_item.reference_price_as_of,
                reference_price_source_id=(
                    candidate.public_item.reference_price_source_id or "UNKNOWN"
                ),
                estimated_transaction_cost=Decimal("0"),
                required_capital=_money(price * quantity),
                supported_target_months=supported,
                holding_overlap_pct=candidate.public_item.holding_overlap_pct,
                constituent_snapshot_dates=(
                    candidate.public_item.constituent_snapshot_dates
                ),
                reasons=["通過全市場資料門檻，並用於縮小目標月份現金流缺口。"],
                risks=risks,
            )
        )

    total_capital = sum(
        (item.required_capital for item in additions), Decimal("0")
    )
    holdings = _resulting_holdings(baseline, request, state.shares, prices)

    month_results = []
    total_shortfall = Decimal("0")
    for month in selected:
        modeled = current_cash[month] + added_cash[month]
        shortfall = max(target - modeled, Decimal("0"))
        total_shortfall += shortfall
        month_results.append(
            IntegerAllocationMonthResult(
                month=month,
                current_after_tax_cash=_money(current_cash[month]),
                added_after_tax_cash=_money(added_cash[month]),
                modeled_after_tax_cash=_money(modeled),
                target_after_tax_cash=target,
                shortfall=_money(shortfall),
            )
        )
    status = (
        IntegerAllocationStatus.TARGET_MET
        if total_shortfall <= 0
        else IntegerAllocationStatus.PARTIAL
    )
    issues = list(baseline.issues)
    if status == IntegerAllocationStatus.PARTIAL:
        issues.append(
            _issue(
                "TARGET_MONTH_COVERAGE_INCOMPLETE",
                "通過門檻的候選 ETF 無法涵蓋所有目標月份。",
            )
        )
    return IntegerAllocationResponse(
        **common,
        status=status,
        optimality=IntegerAllocationOptimality.BOUNDED_BEST_EFFORT,
        additions=additions,
        total_required_additional_capital=_money(total_capital),
        monthly_results=month_results,
        resulting_holdings=holdings,
        issues=issues,
    )
