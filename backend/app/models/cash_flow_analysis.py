"""現金流與總報酬計算契約模型。"""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class AnalysisMode(StrEnum):
    """計算使用的資料性質。"""

    HISTORICAL_REPLAY = "HISTORICAL_REPLAY"
    SCENARIO_ESTIMATE = "SCENARIO_ESTIMATE"


class CalculationDateBasis(StrEnum):
    """金流或估值採用的日期基準。"""

    PAYMENT_DATE = "PAYMENT_DATE"
    TRADE_DATE = "TRADE_DATE"


class CalculationUnavailableReason(StrEnum):
    """結果無法計算的穩定原因代碼。"""

    MISSING_INPUT = "MISSING_INPUT"
    MIXED_CURRENCY = "MIXED_CURRENCY"
    DATE_BASIS_MISMATCH = (
        "DATE_BASIS_MISMATCH"
    )
    NON_POSITIVE_INITIAL_CAPITAL = (
        "NON_POSITIVE_INITIAL_CAPITAL"
    )
    NON_POSITIVE_AFTER_TAX_CASH_RATE = (
        "NON_POSITIVE_AFTER_TAX_CASH_RATE"
    )
    NEGATIVE_AFTER_TAX_USABLE_CASH = (
        "NEGATIVE_AFTER_TAX_USABLE_CASH"
    )


class DistributionReinvestmentPolicy(StrEnum):
    """情境估算中的配息再投入假設。"""

    NO_REINVESTMENT = "NO_REINVESTMENT"


class CalculationContractBaseModel(BaseModel):
    """計算契約模型的共同設定。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class CalculationContext(
    CalculationContractBaseModel
):
    """單次計算共用的分析範圍。"""

    mode: AnalysisMode

    currency: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        description=(
            "單次計算唯一使用的 ISO 4217 幣別"
        ),
    )

    period_start: date

    period_end: date

    cash_date_basis: CalculationDateBasis = Field(
        default=CalculationDateBasis.PAYMENT_DATE,
    )

    valuation_date_basis: (
        CalculationDateBasis
    ) = Field(
        default=CalculationDateBasis.TRADE_DATE,
    )

    @field_validator(
        "currency",
        mode="before",
    )
    @classmethod
    def normalize_currency(
        cls,
        value: object,
    ) -> str:
        """正規化幣別代碼。"""

        if not isinstance(value, str):
            raise TypeError(
                "幣別代碼必須是文字"
            )

        return value.strip().upper()

    @model_validator(mode="after")
    def validate_period(self) -> Self:
        """確認分析起日不晚於迄日。"""

        if self.period_start > self.period_end:
            raise ValueError(
                "分析起日不可晚於迄日"
            )

        if (
            self.cash_date_basis
            != CalculationDateBasis.PAYMENT_DATE
        ):
            raise ValueError(
                "現金流日期基準必須是 PAYMENT_DATE"
            )

        if (
            self.valuation_date_basis
            != CalculationDateBasis.TRADE_DATE
        ):
            raise ValueError(
                "估值日期基準必須是 TRADE_DATE"
            )

        return self


class CashFlowCalculationInput(
    CalculationContractBaseModel
):
    """固定稅後現金流目標的輸入。"""

    context: CalculationContext

    available_capital: Decimal = Field(
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    monthly_after_tax_target: Decimal = Field(
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    reference_capital: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
        description=(
            "產生參考期現金流的本金；缺少時不得推算所需本金"
        ),
    )

    gross_distribution_cash: (
        Decimal | None
    ) = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    distribution_tax: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    supplementary_premium: (
        Decimal | None
    ) = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    other_distribution_costs: (
        Decimal | None
    ) = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )


class TotalReturnCalculationInput(
    CalculationContractBaseModel
):
    """以投資組合帳本恆等式計算總報酬的輸入。"""

    context: CalculationContext

    initial_capital: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    ending_holding_value: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    net_withdrawn_cash: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
        description=(
            "已扣除內含稅費且未再投入的外部現金"
        ),
    )

    later_external_contributions: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    externally_paid_costs: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=24,
        decimal_places=6,
        description=(
            "尚未反映於期末價值或淨提領現金的外付成本"
        ),
    )


class NoReinvestmentTotalReturnCalculationInput(
    CalculationContractBaseModel
):
    """未再投入配息時的總報酬拆解輸入。"""

    context: CalculationContext

    initial_capital: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    ending_holding_value: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    gross_distributions: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    distribution_tax: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    supplementary_premium: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    transaction_costs: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    other_externally_paid_costs: (
        Decimal | None
    ) = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )


class ScenarioEstimateCalculationInput(
    CalculationContractBaseModel
):
    """不再投入配息的明示情境假設。"""

    context: CalculationContext

    initial_capital: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=24,
        decimal_places=6,
    )

    annual_gross_cash_rate_pct: (
        Decimal | None
    ) = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=6,
        description=(
            "每年依初始本金估算的稅前現金率，單位為百分點"
        ),
    )

    cash_deduction_rate_pct: (
        Decimal | None
    ) = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=9,
        decimal_places=6,
        description=(
            "稅、補充保費及其他現金扣除占稅前現金的比例"
        ),
    )

    annual_price_return_pct: Decimal | None = Field(
        default=None,
        ge=-100,
        max_digits=12,
        decimal_places=6,
        description=(
            "持有部位的假設年化價格報酬率，單位為百分點"
        ),
    )

    projection_years: int | None = Field(
        default=None,
        ge=1,
        le=50,
    )

    reinvestment_policy: (
        DistributionReinvestmentPolicy
    ) = Field(
        default=(
            DistributionReinvestmentPolicy.NO_REINVESTMENT
        ),
    )

    @model_validator(mode="after")
    def validate_scenario_mode(self) -> Self:
        """避免把情境假設標示成歷史回放。"""

        if self.context.mode != AnalysisMode.SCENARIO_ESTIMATE:
            raise ValueError(
                "情境估算必須使用 SCENARIO_ESTIMATE 模式"
            )

        return self


class CalculationIssue(
    CalculationContractBaseModel
):
    """單一不可計算欄位與原因。"""

    field: str = Field(
        min_length=1,
    )

    reason: CalculationUnavailableReason


class CashFlowCalculationResult(
    CalculationContractBaseModel
):
    """固定現金流目標的可解釋結果。"""

    currency: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    annual_after_tax_target: Decimal

    gross_distribution_cash: Decimal | None

    after_tax_usable_cash: Decimal | None

    target_coverage_pct: Decimal | None

    required_capital: Decimal | None

    funding_shortfall: Decimal | None

    issues: list[CalculationIssue] = Field(
        default_factory=list,
    )


class TotalReturnCalculationResult(
    CalculationContractBaseModel
):
    """帳本式稅後總報酬結果。"""

    currency: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    market_value_gain_loss: Decimal | None

    after_tax_total_gain_loss: Decimal | None

    after_tax_total_return_pct: Decimal | None

    issues: list[CalculationIssue] = Field(
        default_factory=list,
    )


class ScenarioEstimateCalculationResult(
    CalculationContractBaseModel
):
    """不再投入配息的情境估算結果。"""

    currency: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    projection_years: int | None

    reinvestment_policy: (
        DistributionReinvestmentPolicy
    )

    ending_holding_value: Decimal | None

    cumulative_gross_cash: Decimal | None

    cumulative_cash_deductions: Decimal | None

    cumulative_after_tax_cash: Decimal | None

    after_tax_total_gain_loss: Decimal | None

    after_tax_total_return_pct: Decimal | None

    issues: list[CalculationIssue] = Field(
        default_factory=list,
    )
