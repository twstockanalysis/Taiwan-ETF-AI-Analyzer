"""V3-1 公開現金流試算 API client。"""

import json
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


def validate_allocation_results(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise APIResponseError("配置結果回應必須是 JSON 物件")
    if payload.get("profile_scope") != "PUBLIC_STATELESS":
        raise APIResponseError("配置結果 profile_scope 格式不正確")
    if payload.get("request_persisted") is not False:
        raise APIResponseError("公開配置結果不得標示為已儲存")
    plans = payload.get("plans")
    if not isinstance(plans, list) or not 1 <= len(plans) <= 3:
        raise APIResponseError("配置結果必須包含一至三種方案")
    allowed_strategies = {"RECOMMENDED", "BALANCED", "FOCUSED"}
    strategies = []
    for plan in plans:
        if not isinstance(plan, dict) or plan.get("strategy") not in allowed_strategies:
            raise APIResponseError("配置方案類型不正確")
        strategies.append(plan["strategy"])
        result = plan.get("result")
        if not isinstance(result, dict) or result.get("status") not in {
            "TARGET_MET",
            "PARTIAL",
            "NO_ELIGIBLE_ALLOCATION",
            "UNAVAILABLE",
        }:
            raise APIResponseError("配置方案結果格式不正確")
        if not isinstance(result.get("additions"), list):
            raise APIResponseError("配置方案缺少新增股數資料")
        if not isinstance(result.get("monthly_results"), list):
            raise APIResponseError("配置方案缺少逐月現金流資料")
    if strategies[0] != "RECOMMENDED" or len(strategies) != len(set(strategies)):
        raise APIResponseError("配置方案順序或唯一性不正確")
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    for forbidden in ("quality_score", "confidence"):
        if forbidden in serialized:
            raise APIResponseError("配置結果不得包含內部評分或可信度欄位")
    return payload


def fetch_allocation_results(
    api_base_url: str,
    payload: dict[str, Any],
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    result = post_json(
        api_base_url=api_base_url,
        endpoint_path="/api/v1/allocation-plans/allocation-results",
        operation_name="ETF 配置結果",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    return validate_allocation_results(result)


def validate_long_term_scenarios(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise APIResponseError("長期情境回應必須是 JSON 物件")
    if payload.get("profile_scope") != "PUBLIC_STATELESS":
        raise APIResponseError("長期情境 profile_scope 格式不正確")
    if payload.get("request_persisted") is not False:
        raise APIResponseError("長期情境不得標示為已儲存")
    allocation_results = validate_allocation_results(
        payload.get("allocation_results")
    )
    evidence = payload.get("plan_evidence")
    if not isinstance(evidence, list) or len(evidence) != len(
        allocation_results["plans"]
    ):
        raise APIResponseError("長期情境必須對應每一種配置")
    expected_strategies = [
        item["strategy"] for item in allocation_results["plans"]
    ]
    for index, item in enumerate(evidence):
        if not isinstance(item, dict) or item.get("strategy") != expected_strategies[index]:
            raise APIResponseError("長期情境與配置方案順序不一致")
        periods = item.get("historical_periods")
        if not isinstance(periods, list) or [
            period.get("period") for period in periods if isinstance(period, dict)
        ] != ["AVAILABLE_HISTORY", "3Y", "5Y", "10Y"]:
            raise APIResponseError("長期情境必須包含最長、3、5 與 10 年歷史")
        scenarios = item.get("scenarios")
        if not isinstance(scenarios, list) or len(scenarios) not in {0, 3}:
            raise APIResponseError("長期情境必須無情境或包含三種情境")
        for scenario in scenarios:
            points = scenario.get("index_points") if isinstance(scenario, dict) else None
            if not isinstance(points, list) or [
                point.get("year") for point in points if isinstance(point, dict)
            ] != list(range(11)):
                raise APIResponseError("十年情境必須包含第 0 至 10 年")
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    for forbidden in ("quality_score", "confidence"):
        if forbidden in serialized:
            raise APIResponseError("長期情境不得包含內部評分或可信度欄位")
    return payload


def fetch_long_term_scenarios(
    api_base_url: str,
    payload: dict[str, Any],
    timeout_seconds: float = 90.0,
) -> dict[str, Any]:
    result = post_json(
        api_base_url=api_base_url,
        endpoint_path="/api/v1/allocation-plans/long-term-scenarios",
        operation_name="ETF 長期歷史與情境",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    return validate_long_term_scenarios(result)
