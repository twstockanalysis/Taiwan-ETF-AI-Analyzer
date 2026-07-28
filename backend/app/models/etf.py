"""ETF API 資料模型。"""

from datetime import date

from pydantic import BaseModel, Field


class ETFResponse(BaseModel):
    """ETF 主資料 API 回應模型。"""

    code: str = Field(
        description="ETF 證券代號",
        examples=["00918"],
    )

    name: str = Field(
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
        description="上市日期",
    )

    fund_size: float | None = Field(
        default=None,
        description="基金規模，單位為新台幣億元",
    )

    expense_ratio: float | None = Field(
        default=None,
        description="總費用率，單位為百分比",
    )