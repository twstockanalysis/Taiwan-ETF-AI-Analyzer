"""V4-5 公開 ETF 歷史品質評等查詢契約。"""

from datetime import date
from typing import Literal

from pydantic import Field

from backend.app.models.public_planner import PublicPlannerBaseModel
from backend.app.models.quality_grade import ETFHistoricalQualityGrade


class ETFHistoricalQualityGradeItem(PublicPlannerBaseModel):
    etf_code: str = Field(min_length=1, max_length=10)
    historical_quality_grade: ETFHistoricalQualityGrade


class ETFHistoricalQualityGradeResponse(PublicPlannerBaseModel):
    methodology: Literal["DETERMINISTIC_QUALITY_GRADE_V4_1"] = (
        "DETERMINISTIC_QUALITY_GRADE_V4_1"
    )
    analysis_date: date
    history_years: int = Field(ge=1, le=10)
    items: list[ETFHistoricalQualityGradeItem] = Field(max_length=100)
