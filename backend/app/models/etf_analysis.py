"""ETF 績效、配息及配息組成資料模型。"""

from datetime import date, datetime
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


class PerformancePeriod(StrEnum):
    """ETF 績效期間。"""

    ONE_DAY = "1D"
    ONE_WEEK = "1W"
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    THREE_YEARS = "3Y"
    FIVE_YEARS = "5Y"


class ETFAnalysisBaseModel(BaseModel):
    """ETF 分析匯入模型共用設定。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class ETFPerformanceImportRecord(
    ETFAnalysisBaseModel
):
    """ETF 單一期間績效匯入資料。"""

    etf_code: str = Field(
        min_length=4,
        max_length=10,
        pattern=r"^[0-9A-Z]+$",
        description="ETF 證券代號",
    )

    as_of_date: date = Field(
        description="績效資料基準日",
    )

    period_code: PerformancePeriod = Field(
        description="績效期間",
    )

    return_pct: Decimal = Field(
        ge=Decimal("-100"),
        max_digits=14,
        decimal_places=6,
        description="期間報酬率百分比",
    )

    source_id: str = Field(
        min_length=1,
        max_length=50,
        description="資料來源識別碼",
    )

    import_batch_id: int | None = Field(
        default=None,
        ge=1,
        description="匯入批次 ID",
    )

    source_updated_at: datetime | None = Field(
        default=None,
        description="來源資料更新時間",
    )

    @field_validator(
        "etf_code",
        mode="before",
    )
    @classmethod
    def normalize_etf_code(
        cls,
        value: object,
    ) -> str:
        """正規化 ETF 代號。"""

        if not isinstance(value, str):
            raise TypeError(
                "ETF 代號必須是文字"
            )

        return value.strip().upper()

    @field_validator(
        "source_id",
        mode="before",
    )
    @classmethod
    def normalize_source_id(
        cls,
        value: object,
    ) -> str:
        """正規化資料來源識別碼。"""

        if not isinstance(value, str):
            raise TypeError(
                "資料來源識別碼必須是文字"
            )

        return value.strip().lower()


class ETFDividendImportRecord(
    ETFAnalysisBaseModel
):
    """ETF 單次配息事件匯入資料。"""

    etf_code: str = Field(
        min_length=4,
        max_length=10,
        pattern=r"^[0-9A-Z]+$",
        description="ETF 證券代號",
    )

    source_event_id: str = Field(
        min_length=1,
        max_length=150,
        description="來源端配息事件識別碼",
    )

    announcement_date: date | None = None

    ex_dividend_date: date | None = None

    record_date: date | None = None

    payment_date: date | None = None

    amount_per_unit: Decimal = Field(
        ge=0,
        max_digits=20,
        decimal_places=8,
        description="每受益權單位配息金額",
    )

    currency: str = Field(
        default="TWD",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        description="ISO 4217 幣別代碼",
    )

    source_id: str = Field(
        min_length=1,
        max_length=50,
        description="資料來源識別碼",
    )

    import_batch_id: int | None = Field(
        default=None,
        ge=1,
    )

    source_updated_at: datetime | None = None

    @field_validator(
        "etf_code",
        mode="before",
    )
    @classmethod
    def normalize_etf_code(
        cls,
        value: object,
    ) -> str:
        """正規化 ETF 代號。"""

        if not isinstance(value, str):
            raise TypeError(
                "ETF 代號必須是文字"
            )

        return value.strip().upper()

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

    @field_validator(
        "source_id",
        mode="before",
    )
    @classmethod
    def normalize_source_id(
        cls,
        value: object,
    ) -> str:
        """正規化資料來源識別碼。"""

        if not isinstance(value, str):
            raise TypeError(
                "資料來源識別碼必須是文字"
            )

        return value.strip().lower()

    @model_validator(
        mode="after",
    )
    def validate_event_dates(
        self,
    ) -> Self:
        """確認配息事件至少具有一個日期。"""

        event_dates = (
            self.announcement_date,
            self.ex_dividend_date,
            self.record_date,
            self.payment_date,
        )

        if all(
            value is None
            for value in event_dates
        ):
            raise ValueError(
                "配息事件至少必須提供一個日期"
            )

        if (
            self.ex_dividend_date is not None
            and self.payment_date is not None
            and self.payment_date
            < self.ex_dividend_date
        ):
            raise ValueError(
                "配息發放日不可早於除息日"
            )

        return self


class ETFDividendComponentImportRecord(
    ETFAnalysisBaseModel
):
    """ETF 單一配息來源組成匯入資料。"""

    etf_code: str = Field(
        min_length=4,
        max_length=10,
        pattern=r"^[0-9A-Z]+$",
    )

    dividend_source_event_id: str = Field(
        min_length=1,
        max_length=150,
        description="所屬配息事件識別碼",
    )

    component_code: str = Field(
        min_length=1,
        max_length=20,
        pattern=r"^[0-9A-Z_-]+$",
        description="配息來源代碼，例如 76W",
    )

    component_name: str | None = Field(
        default=None,
        max_length=150,
        description="配息來源說明",
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

    source_id: str = Field(
        min_length=1,
        max_length=50,
    )

    import_batch_id: int | None = Field(
        default=None,
        ge=1,
    )

    source_updated_at: datetime | None = None

    @field_validator(
        "etf_code",
        "component_code",
        mode="before",
    )
    @classmethod
    def normalize_uppercase_values(
        cls,
        value: object,
    ) -> str:
        """將代號欄位去除空白並轉大寫。"""

        if not isinstance(value, str):
            raise TypeError(
                "代號欄位必須是文字"
            )

        return value.strip().upper()

    @field_validator(
        "source_id",
        mode="before",
    )
    @classmethod
    def normalize_source_id(
        cls,
        value: object,
    ) -> str:
        """正規化資料來源識別碼。"""

        if not isinstance(value, str):
            raise TypeError(
                "資料來源識別碼必須是文字"
            )

        return value.strip().lower()

    @model_validator(
        mode="after",
    )
    def validate_component_values(
        self,
    ) -> Self:
        """確認配息組成具有金額或比例。"""

        if (
            self.amount_per_unit is None
            and self.ratio_pct is None
        ):
            raise ValueError(
                "配息組成至少必須提供金額或比例"
            )

        return self