"""V4-1 對外安全的 ETF 歷史品質字母評等契約。"""

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from backend.app.models.public_planner import PublicPlannerBaseModel


class ETFQualityGradeStatus(StrEnum):
    RATED = "RATED"
    UNRATED = "UNRATED"


class ETFQualityGrade(StrEnum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"


class ETFHistoricalQualityGrade(PublicPlannerBaseModel):
    """只公開等級與簡短證據，不公開原始分數、排名或可信度。"""

    methodology: Literal["DETERMINISTIC_QUALITY_GRADE_V4_1"] = (
        "DETERMINISTIC_QUALITY_GRADE_V4_1"
    )
    score_methodology: Literal["DETERMINISTIC_MULTI_SCORE_V2"] = (
        "DETERMINISTIC_MULTI_SCORE_V2"
    )
    threshold_version: Literal["FIXED_THRESHOLDS_V1"] = "FIXED_THRESHOLDS_V1"
    status: ETFQualityGradeStatus
    grade: ETFQualityGrade | None = None
    evidence_period_years: int = Field(ge=1, le=10)
    strengths: list[str] = Field(default_factory=list, max_length=3)
    risks: list[str] = Field(default_factory=list, max_length=3)
    unavailable_evidence: list[str] = Field(default_factory=list)
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_status_and_grade(self):
        if self.status == ETFQualityGradeStatus.RATED and self.grade is None:
            raise ValueError("已評等狀態必須包含字母評等")
        if self.status == ETFQualityGradeStatus.UNRATED and self.grade is not None:
            raise ValueError("暫不評等狀態不可包含字母評等")
        return self

