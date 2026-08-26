"""V4-1 評等覆蓋、門檻敏感度與候選因子決策報告。"""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field

from backend.app.models.public_planner import PublicPlannerBaseModel


class CalibrationFactorStatus(StrEnum):
    RETAINED = "RETAINED"
    DEFERRED = "DEFERRED"
    RISK_EVIDENCE_ONLY = "RISK_EVIDENCE_ONLY"
    NOT_ADOPTED = "NOT_ADOPTED"


class CalibrationFactorDecision(PublicPlannerBaseModel):
    code: str = Field(min_length=1)
    status: CalibrationFactorStatus
    reason: str = Field(min_length=1)


class CalibrationScoreSummary(PublicPlannerBaseModel):
    available_count: int = Field(ge=0)
    minimum: Decimal | None = Field(default=None, ge=0, le=100)
    median: Decimal | None = Field(default=None, ge=0, le=100)
    maximum: Decimal | None = Field(default=None, ge=0, le=100)
    observed_minimum: Decimal | None = None
    observed_median: Decimal | None = None
    observed_maximum: Decimal | None = None


class AssessmentCalibrationReport(PublicPlannerBaseModel):
    methodology: Literal["ASSESSMENT_CALIBRATION_V4_1"] = (
        "ASSESSMENT_CALIBRATION_V4_1"
    )
    score_methodology: Literal["DETERMINISTIC_MULTI_SCORE_V2"] = (
        "DETERMINISTIC_MULTI_SCORE_V2"
    )
    grade_methodology: Literal["DETERMINISTIC_QUALITY_GRADE_V4_1"] = (
        "DETERMINISTIC_QUALITY_GRADE_V4_1"
    )
    analysis_date: date
    snapshot_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    universe_count: int = Field(ge=0)
    supported_product_count: int = Field(ge=0)
    publication_ready: bool
    publication_blockers: list[str]
    provisional_rated_count: int = Field(ge=0)
    published_rated_count: int = Field(ge=0)
    provisional_grade_counts: dict[str, int]
    boundary_sensitivity_points: str = "2.5"
    boundary_sensitive_count: int = Field(ge=0)
    rated_score_min: Decimal | None = Field(default=None, ge=0, le=100)
    rated_score_median: Decimal | None = Field(default=None, ge=0, le=100)
    rated_score_max: Decimal | None = Field(default=None, ge=0, le=100)
    factor_available_counts: dict[str, int]
    factor_score_summaries: dict[str, CalibrationScoreSummary]
    factor_decisions: list[CalibrationFactorDecision]
    conclusion: str = Field(min_length=1)
