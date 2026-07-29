"""ETF 每日市場價格資料模型。"""

from datetime import date
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class ETFDailyCloseRecord(BaseModel):
    """ETF 單日收盤價。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    etf_code: str = Field(
        min_length=4,
        max_length=10,
        pattern=r"^[0-9A-Z]+$",
    )

    trade_date: date

    close_price: Decimal = Field(
        gt=0,
        max_digits=20,
        decimal_places=6,
    )

    source_id: str = Field(
        default="twse_stock_day",
        min_length=1,
        max_length=50,
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
        """正規化資料來源代號。"""

        if not isinstance(value, str):
            raise TypeError(
                "資料來源代號必須是文字"
            )

        return value.strip().lower()