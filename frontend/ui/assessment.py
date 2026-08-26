"""V4 公開安全的歷史品質與主人目標適配呈現語意。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


BadgeColor = Literal["blue", "green", "orange", "red", "gray"]


@dataclass(frozen=True)
class AssessmentPresentation:
    """不含原始分數、排名或可信度的前台呈現資料。"""

    label: str
    explanation: str
    color: BadgeColor


def historical_quality_presentation(
    grade_payload: object,
) -> AssessmentPresentation:
    """將公開評等物件轉成字母評等或明確的暫不評等。"""

    payload = grade_payload if isinstance(grade_payload, dict) else {}
    status = str(payload.get("status", "UNRATED")).strip().upper()
    grade = payload.get("grade")
    explanation = str(payload.get("explanation") or "").strip()

    if status == "RATED" and grade in {"A+", "A", "B", "C", "D", "E", "F"}:
        color: BadgeColor = (
            "green"
            if grade in {"A+", "A", "B"}
            else "orange"
            if grade in {"C", "D"}
            else "red"
        )
        return AssessmentPresentation(
            label=f"歷史品質 {grade}",
            explanation=explanation or "依目前可用歷史資料與固定門檻評定。",
            color=color,
        )

    return AssessmentPresentation(
        label="歷史品質暫不評等",
        explanation=(
            explanation
            or "核心歷史證據或市場校準尚不足，因此不以低分代替缺少資料。"
        ),
        color="gray",
    )


def allocation_fit_presentation(
    result: dict[str, Any],
) -> AssessmentPresentation:
    """將配置結果轉成只描述本次主人條件的適配狀態。"""

    status = str(result.get("status", "UNAVAILABLE")).strip().upper()
    presentations = {
        "TARGET_MET": AssessmentPresentation(
            label="符合主人設定",
            explanation="依本次月份、現金目標與庫存條件，目標月份皆已覆蓋。",
            color="green",
        ),
        "PARTIAL": AssessmentPresentation(
            label="部分符合主人設定",
            explanation="目前配置已縮小缺口，但仍有目標月份尚未完全覆蓋。",
            color="orange",
        ),
        "NO_ELIGIBLE_ALLOCATION": AssessmentPresentation(
            label="目前沒有合適配置",
            explanation="現有資料與風險門檻下，沒有可安全加入的整股配置。",
            color="red",
        ),
        "UNAVAILABLE": AssessmentPresentation(
            label="必要資料不足",
            explanation="缺少完成本次主人條件判斷所需的核心資料。",
            color="gray",
        ),
    }
    return presentations.get(status, presentations["UNAVAILABLE"])
