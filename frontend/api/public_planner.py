"""V3-1 公開現金流試算 API client。"""

from typing import Any

from frontend.api.errors import APIResponseError
from frontend.api.transport import post_json


def validate_public_planner_result(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise APIResponseError("公開試算回應必須是 JSON 物件")
    if payload.get("profile_scope") != "PUBLIC_STATELESS":
        raise APIResponseError("公開試算 profile_scope 格式不正確")
    if payload.get("request_persisted") is not False:
        raise APIResponseError("公開試算不得標示為已儲存")
    if payload.get("status") not in {"AVAILABLE", "PARTIAL", "UNAVAILABLE"}:
        raise APIResponseError("公開試算 status 格式不正確")
    months = payload.get("monthly_cash_flow")
    if (
        not isinstance(months, list)
        or len(months) != 12
        or [item.get("month") for item in months if isinstance(item, dict)]
        != list(range(1, 13))
    ):
        raise APIResponseError("公開試算必須包含依序排列的 1 至 12 月")
    if not isinstance(payload.get("holdings"), list):
        raise APIResponseError("公開試算缺少現有持股資料")
    forbidden = {"etf_quality_score", "assessment_confidence", "confidence"}
    if forbidden.intersection(payload):
        raise APIResponseError("公開試算不得包含內部評分或可信度欄位")
    return payload


def fetch_public_planner_baseline(
    api_base_url: str,
    payload: dict[str, Any],
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    result = post_json(
        api_base_url=api_base_url,
        endpoint_path="/api/v1/allocation-plans/baseline",
        operation_name="公開現金流試算",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    return validate_public_planner_result(result)
