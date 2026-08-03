"""正式收益分配通知書的結構化輸入模型。"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Self
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class ActualDividendInformationBasis(
    StrEnum
):
    """正式配息組成的資訊性質。"""

    ACTUAL = "ACTUAL"


class ActualDividendNoticeBaseModel(
    BaseModel
):
    """正式配息通知書輸入共用設定。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class ActualDividendComponentInput(
    ActualDividendNoticeBaseModel
):
    """正式通知書中的單一所得組成。"""

    component_code: str = Field(
        min_length=1,
        max_length=40,
        pattern=r"^[0-9A-Z_-]+$",
        description="正式所得代碼，例如 76W、54C",
    )

    component_name: str | None = Field(
        default=None,
        max_length=150,
    )

    amount_per_unit: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=20,
        decimal_places=8,
    )

    ratio_pct: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=9,
        decimal_places=6,
    )

    @field_validator(
        "component_code",
        mode="before",
    )
    @classmethod
    def normalize_component_code(
        cls,
        value: object,
    ) -> str:
        """將所得代碼正規化為大寫。"""

        if not isinstance(value, str):
            raise TypeError(
                "所得代碼必須是文字"
            )

        normalized_value = (
            value.strip().upper()
        )

        if normalized_value.startswith(
            "EST_"
        ):
            raise ValueError(
                "正式通知書不得使用 EST_ 預估代碼"
            )

        return normalized_value

    @model_validator(
        mode="after",
    )
    def validate_component_values(
        self,
    ) -> Self:
        """確認組成至少具有金額或比例。"""

        if (
            self.amount_per_unit is None
            and self.ratio_pct is None
        ):
            raise ValueError(
                "正式配息組成至少必須提供"
                "每單位金額或比例"
            )

        return self


class ActualDividendNoticeInput(
    ActualDividendNoticeBaseModel
):
    """單一 ETF 正式收益分配通知書。"""

    source_id: str = Field(
        min_length=1,
        max_length=50,
        description="正式資料來源識別碼",
    )

    source_document_id: str = Field(
        min_length=1,
        max_length=150,
        description="來源文件穩定識別碼",
    )

    source_document_url: str = Field(
        min_length=1,
        max_length=1000,
    )

    source_document_date: date

    information_basis: (
        ActualDividendInformationBasis
    ) = Field(
        default=(
            ActualDividendInformationBasis
            .ACTUAL
        )
    )

    etf_code: str = Field(
        min_length=4,
        max_length=10,
        pattern=r"^[0-9A-Z]+$",
    )

    announcement_date: date | None = None

    ex_dividend_date: date

    record_date: date | None = None

    payment_date: date | None = None

    amount_per_unit: Decimal = Field(
        ge=0,
        max_digits=20,
        decimal_places=8,
    )

    distribution_period: str | None = Field(
        default=None,
        pattern=r"^[0-9]{4}Q[1-4]$",
        description="官方收益所屬年季",
    )

    official_yield_pct: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=6,
        description="正式文件揭露的單次殖利率",
    )

    currency: str = Field(
        default="TWD",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    components: list[
        ActualDividendComponentInput
    ] = Field(
        min_length=1,
    )

    @field_validator(
        "source_id",
        mode="before",
    )
    @classmethod
    def normalize_source_id(
        cls,
        value: object,
    ) -> str:
        """將來源識別碼正規化為小寫。"""

        if not isinstance(value, str):
            raise TypeError(
                "資料來源識別碼必須是文字"
            )

        return value.strip().lower()

    @field_validator(
        "etf_code",
        "currency",
        mode="before",
    )
    @classmethod
    def normalize_uppercase_values(
        cls,
        value: object,
    ) -> str:
        """將 ETF 代號與幣別正規化為大寫。"""

        if not isinstance(value, str):
            raise TypeError(
                "ETF 代號與幣別必須是文字"
            )

        return value.strip().upper()

    @field_validator(
        "distribution_period",
        mode="before",
    )
    @classmethod
    def normalize_distribution_period(
        cls,
        value: object,
    ) -> object:
        """將官方收益所屬年季正規化。"""

        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                "收益所屬年季必須是文字"
            )

        return value.strip().upper()

    @field_validator(
        "source_document_url",
    )
    @classmethod
    def validate_document_url(
        cls,
        value: str,
    ) -> str:
        """僅接受 HTTP 或 HTTPS 官方文件網址。"""

        parsed = urlparse(value)

        if (
            parsed.scheme not in {
                "http",
                "https",
            }
            or not parsed.netloc
        ):
            raise ValueError(
                "來源文件網址必須是有效的"
                " HTTP 或 HTTPS URL"
            )

        return value

    @model_validator(
        mode="after",
    )
    def validate_notice(
        self,
    ) -> Self:
        """驗證日期、重複代碼及組成合計。"""

        if (
            self.payment_date is not None
            and self.payment_date
            < self.ex_dividend_date
        ):
            raise ValueError(
                "配息發放日不可早於除息日"
            )

        component_codes = [
            component.component_code
            for component in self.components
        ]

        if len(component_codes) != len(
            set(component_codes)
        ):
            raise ValueError(
                "同一通知書不得重複所得代碼"
            )

        ratio_values = [
            component.ratio_pct
            for component in self.components
        ]

        if all(
            value is not None
            for value in ratio_values
        ):
            ratio_total = sum(
                (
                    value
                    or Decimal("0")
                )
                for value in ratio_values
            )

            if not (
                Decimal("99")
                <= ratio_total
                <= Decimal("101")
            ):
                raise ValueError(
                    "正式配息組成比例合計異常："
                    f"{ratio_total}%"
                )

        amount_values = [
            component.amount_per_unit
            for component in self.components
        ]

        if all(
            value is not None
            for value in amount_values
        ):
            amount_total = sum(
                (
                    value
                    or Decimal("0")
                )
                for value in amount_values
            )

            tolerance = max(
                Decimal("0.0001"),
                self.amount_per_unit
                * Decimal("0.005"),
            )

            if abs(
                amount_total
                - self.amount_per_unit
            ) > tolerance:
                raise ValueError(
                    "正式配息組成金額合計與"
                    "每單位配息不一致："
                    f"{amount_total} / "
                    f"{self.amount_per_unit}"
                )

        return self
