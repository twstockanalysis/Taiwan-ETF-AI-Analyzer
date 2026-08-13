"""ETF 成分股快照與加權重疊契約。"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ConstituentBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ETFConstituentPosition(ConstituentBaseModel):
    constituent_id: str = Field(min_length=1, max_length=80)
    constituent_name: str = Field(min_length=1, max_length=200)
    weight_pct: Decimal = Field(ge=0, le=100)
    rank: int | None = Field(default=None, gt=0)

    @field_validator("constituent_id")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        return value.upper()


class ETFConstituentSnapshotCreate(ConstituentBaseModel):
    etf_code: str = Field(min_length=4, max_length=10)
    as_of_date: date
    source_id: str = Field(min_length=1, max_length=100)
    source_url: str | None = Field(default=None, min_length=1, max_length=2000)
    fetched_at: datetime
    positions: list[ETFConstituentPosition] = Field(min_length=1)

    @field_validator("etf_code")
    @classmethod
    def normalize_etf_code(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_positions(self):
        identifiers = [item.constituent_id for item in self.positions]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("同一快照不可包含重複成分股識別碼")
        total = sum(item.weight_pct for item in self.positions)
        if total > Decimal("100.5"):
            raise ValueError("成分股權重合計不可超過 100.5%")
        return self


class ETFConstituentSnapshot(ConstituentBaseModel):
    id: int = Field(gt=0)
    etf_code: str
    as_of_date: date
    source_id: str
    source_url: str | None
    fetched_at: datetime
    total_weight_pct: Decimal = Field(ge=0, le=Decimal("100.5"))
    constituent_count: int = Field(ge=0)
    positions: list[ETFConstituentPosition]


class ETFWeightedOverlapResult(ConstituentBaseModel):
    left_etf_code: str
    right_etf_code: str
    left_as_of_date: date
    right_as_of_date: date
    left_total_weight_pct: Decimal = Field(ge=0, le=Decimal("100.5"))
    right_total_weight_pct: Decimal = Field(ge=0, le=Decimal("100.5"))
    overlap_pct: Decimal = Field(ge=0, le=100)
    shared_constituent_count: int = Field(ge=0)
    shared_constituents: list[ETFConstituentPosition]
    method: str = "SUM_MIN_DISCLOSED_WEIGHTS_V1"
