"""現金流與稅後總報酬純計算服務。"""

from decimal import Decimal, ROUND_HALF_UP

from backend.app.models.cash_flow_analysis import (
    CalculationIssue,
    CalculationUnavailableReason,
    CashFlowCalculationInput,
    CashFlowCalculationResult,
    NoReinvestmentTotalReturnCalculationInput,
    TotalReturnCalculationInput,
    TotalReturnCalculationResult,
)


MONEY_QUANTUM = Decimal("0.01")
PERCENT_QUANTUM = Decimal("0.000001")
HUNDRED = Decimal("100")
MONTHS_PER_YEAR = Decimal("12")


def _round_money(value: Decimal) -> Decimal:
    """將公開金額結果四捨五入至小數點後兩位。"""

    return value.quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _round_percentage(value: Decimal) -> Decimal:
    """將公開百分比四捨五入至小數點後六位。"""

    return value.quantize(
        PERCENT_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _issue(
    field: str,
    reason: CalculationUnavailableReason,
) -> CalculationIssue:
    """建立穩定的不可計算原因。"""

    return CalculationIssue(
        field=field,
        reason=reason,
    )


def _projection_issues(
    reason: CalculationUnavailableReason,
) -> list[CalculationIssue]:
    """建立固定現金流推算欄位的原因。"""

    return [
        _issue("target_coverage_pct", reason),
        _issue("required_capital", reason),
        _issue("funding_shortfall", reason),
    ]


def _cash_result(
    *,
    value: CashFlowCalculationInput,
    annual_target: Decimal,
    after_tax_usable_cash: Decimal | None,
    target_coverage_pct: Decimal | None,
    required_capital: Decimal | None,
    funding_shortfall: Decimal | None,
    issues: list[CalculationIssue],
) -> CashFlowCalculationResult:
    """建立固定現金流結果並統一金額格式。"""

    return CashFlowCalculationResult(
        currency=value.context.currency,
        annual_after_tax_target=annual_target,
        gross_distribution_cash=(
            _round_money(value.gross_distribution_cash)
            if value.gross_distribution_cash is not None
            else None
        ),
        after_tax_usable_cash=after_tax_usable_cash,
        target_coverage_pct=target_coverage_pct,
        required_capital=required_capital,
        funding_shortfall=funding_shortfall,
        issues=issues,
    )


def calculate_cash_flow_target(
    value: CashFlowCalculationInput,
) -> CashFlowCalculationResult:
    """計算固定稅後現金流目標與所需本金。"""

    annual_target_raw = (
        value.monthly_after_tax_target
        * MONTHS_PER_YEAR
    )
    annual_target = _round_money(
        annual_target_raw
    )
    deduction_values = (
        value.distribution_tax,
        value.supplementary_premium,
        value.other_distribution_costs,
    )
    cash_inputs_complete = (
        value.gross_distribution_cash
        is not None
        and all(
            item is not None
            for item in deduction_values
        )
    )

    after_tax_raw: Decimal | None = None
    after_tax_usable_cash: Decimal | None = None
    issues: list[CalculationIssue] = []

    if cash_inputs_complete:
        assert value.gross_distribution_cash is not None
        assert value.distribution_tax is not None
        assert value.supplementary_premium is not None
        assert value.other_distribution_costs is not None
        after_tax_raw = (
            value.gross_distribution_cash
            - value.distribution_tax
            - value.supplementary_premium
            - value.other_distribution_costs
        )
        after_tax_usable_cash = _round_money(
            after_tax_raw
        )
    else:
        issues.append(
            _issue(
                "after_tax_usable_cash",
                CalculationUnavailableReason.MISSING_INPUT,
            )
        )

    if annual_target_raw == 0:
        return _cash_result(
            value=value,
            annual_target=annual_target,
            after_tax_usable_cash=after_tax_usable_cash,
            target_coverage_pct=Decimal("100.000000"),
            required_capital=Decimal("0.00"),
            funding_shortfall=Decimal("0.00"),
            issues=issues,
        )

    if after_tax_raw is None:
        issues.extend(
            _projection_issues(
                CalculationUnavailableReason.MISSING_INPUT
            )
        )
        return _cash_result(
            value=value,
            annual_target=annual_target,
            after_tax_usable_cash=None,
            target_coverage_pct=None,
            required_capital=None,
            funding_shortfall=None,
            issues=issues,
        )

    if after_tax_raw < 0:
        issues.extend(
            _projection_issues(
                CalculationUnavailableReason
                .NEGATIVE_AFTER_TAX_USABLE_CASH
            )
        )
        return _cash_result(
            value=value,
            annual_target=annual_target,
            after_tax_usable_cash=after_tax_usable_cash,
            target_coverage_pct=None,
            required_capital=None,
            funding_shortfall=None,
            issues=issues,
        )

    if value.reference_capital is None:
        issues.extend(
            _projection_issues(
                CalculationUnavailableReason.MISSING_INPUT
            )
        )
        return _cash_result(
            value=value,
            annual_target=annual_target,
            after_tax_usable_cash=after_tax_usable_cash,
            target_coverage_pct=None,
            required_capital=None,
            funding_shortfall=None,
            issues=issues,
        )

    if (
        value.reference_capital <= 0
        or after_tax_raw <= 0
    ):
        issues.extend(
            _projection_issues(
                CalculationUnavailableReason
                .NON_POSITIVE_AFTER_TAX_CASH_RATE
            )
        )
        return _cash_result(
            value=value,
            annual_target=annual_target,
            after_tax_usable_cash=after_tax_usable_cash,
            target_coverage_pct=None,
            required_capital=None,
            funding_shortfall=None,
            issues=issues,
        )

    cash_rate = (
        after_tax_raw
        / value.reference_capital
    )
    projected_cash = (
        cash_rate
        * value.available_capital
    )
    coverage_pct = (
        projected_cash
        / annual_target_raw
        * HUNDRED
    )
    required_capital_raw = (
        annual_target_raw
        / cash_rate
    )
    shortfall_raw = max(
        required_capital_raw
        - value.available_capital,
        Decimal("0"),
    )

    return _cash_result(
        value=value,
        annual_target=annual_target,
        after_tax_usable_cash=after_tax_usable_cash,
        target_coverage_pct=_round_percentage(
            coverage_pct
        ),
        required_capital=_round_money(
            required_capital_raw
        ),
        funding_shortfall=_round_money(
            shortfall_raw
        ),
        issues=issues,
    )


def _calculate_total_return_result(
    *,
    currency: str,
    initial_capital: Decimal | None,
    ending_holding_value: Decimal | None,
    total_gain_loss_raw: Decimal | None,
) -> TotalReturnCalculationResult:
    """由共同結果組件建立總報酬結果。"""

    issues: list[CalculationIssue] = []

    if (
        initial_capital is None
        or ending_holding_value is None
    ):
        market_value_gain_loss = None
        issues.append(
            _issue(
                "market_value_gain_loss",
                CalculationUnavailableReason.MISSING_INPUT,
            )
        )
    else:
        market_value_gain_loss = _round_money(
            ending_holding_value
            - initial_capital
        )

    if total_gain_loss_raw is None:
        after_tax_total_gain_loss = None
        after_tax_total_return_pct = None
        issues.extend(
            [
                _issue(
                    "after_tax_total_gain_loss",
                    CalculationUnavailableReason.MISSING_INPUT,
                ),
                _issue(
                    "after_tax_total_return_pct",
                    CalculationUnavailableReason.MISSING_INPUT,
                ),
            ]
        )
    else:
        after_tax_total_gain_loss = _round_money(
            total_gain_loss_raw
        )
        if initial_capital is None:
            after_tax_total_return_pct = None
            issues.append(
                _issue(
                    "after_tax_total_return_pct",
                    CalculationUnavailableReason.MISSING_INPUT,
                )
            )
        elif initial_capital <= 0:
            after_tax_total_return_pct = None
            issues.append(
                _issue(
                    "after_tax_total_return_pct",
                    CalculationUnavailableReason
                    .NON_POSITIVE_INITIAL_CAPITAL,
                )
            )
        else:
            after_tax_total_return_pct = (
                _round_percentage(
                    total_gain_loss_raw
                    / initial_capital
                    * HUNDRED
                )
            )

    return TotalReturnCalculationResult(
        currency=currency,
        market_value_gain_loss=market_value_gain_loss,
        after_tax_total_gain_loss=after_tax_total_gain_loss,
        after_tax_total_return_pct=(
            after_tax_total_return_pct
        ),
        issues=issues,
    )


def calculate_total_return(
    value: TotalReturnCalculationInput,
) -> TotalReturnCalculationResult:
    """依投資組合帳本恆等式計算稅後總報酬。"""

    required_values = (
        value.initial_capital,
        value.ending_holding_value,
        value.net_withdrawn_cash,
    )
    total_gain_loss_raw = (
        value.ending_holding_value
        + value.net_withdrawn_cash
        - value.initial_capital
        - value.later_external_contributions
        - value.externally_paid_costs
        if all(
            item is not None
            for item in required_values
        )
        else None
    )

    return _calculate_total_return_result(
        currency=value.context.currency,
        initial_capital=value.initial_capital,
        ending_holding_value=value.ending_holding_value,
        total_gain_loss_raw=total_gain_loss_raw,
    )


def calculate_no_reinvestment_total_return(
    value: NoReinvestmentTotalReturnCalculationInput,
) -> TotalReturnCalculationResult:
    """依未再投入配息拆解計算稅後總報酬。"""

    required_values = (
        value.initial_capital,
        value.ending_holding_value,
        value.gross_distributions,
        value.distribution_tax,
        value.supplementary_premium,
        value.transaction_costs,
        value.other_externally_paid_costs,
    )
    total_gain_loss_raw = (
        value.ending_holding_value
        - value.initial_capital
        + value.gross_distributions
        - value.distribution_tax
        - value.supplementary_premium
        - value.transaction_costs
        - value.other_externally_paid_costs
        if all(
            item is not None
            for item in required_values
        )
        else None
    )

    return _calculate_total_return_result(
        currency=value.context.currency,
        initial_capital=value.initial_capital,
        ending_holding_value=value.ending_holding_value,
        total_gain_loss_raw=total_gain_loss_raw,
    )
