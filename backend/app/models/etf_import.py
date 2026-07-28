"""ETF 資料匯入模型。"""

from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from backend.app.data_sources.registry import Market


class ETFImportRecord(BaseModel):
    """已正規化、準備寫入資料庫的 ETF 資料。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    code: str = Field(
        min_length=4,
        max_length=10,
        pattern=r"^[0-9A-Z]+$",
        description="ETF 證券代號",
    )

    name: str = Field(
        min_length=1,
        max_length=100,
        description="ETF 中文名稱",
    )

    is_active: bool = Field(
        description="是否為主動式 ETF",
    )

    is_bond: bool = Field(
        description="是否為債券 ETF",
    )

    listing_date: date | None = Field(
        default=None,
        description="上市或上櫃日期",
    )

    fund_size: float | None = Field(
        default=None,
        ge=0,
        description="基金規模，單位為新台幣億元",
    )

    expense_ratio: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="總費用率，單位為百分比",
    )

    market: Market = Field(
        description="掛牌市場",
    )

    source_id: str = Field(
        min_length=1,
        max_length=50,
        description="資料來源識別碼",
    )

    source_updated_at: datetime | None = Field(
        default=None,
        description="來源資料更新時間",
    )

    @field_validator(
        "code",
        mode="before",
    )
    @classmethod
    def normalize_code(
        cls,
        value: object,
    ) -> str:
        """正規化 ETF 證券代號。"""

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