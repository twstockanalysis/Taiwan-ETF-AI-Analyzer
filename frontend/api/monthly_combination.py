"""M10-5 月配缺口組合 API client。"""

from typing import Any
from urllib.parse import quote

from frontend.api.errors import APIResponseError
from frontend.api.transport import post_json


def validate_monthly_combination_result(payload: object) -> dict[str, Any]:
    """驗證月配組合回應的必要公開欄位。"""

    if not isinstance(payload, dict):
        raise APIResponseError("月配組合回應必須是 JSON 物件")
    facts = payload.get("historical_facts")
    calculation = payload.get("calculation")
    if not isinstance(facts, dict) or not isinstance(calculation, dict):
        raise APIResponseError("月配組合缺少歷史事實或計算結果")
    if calculation.get("status") not in {
        "AVAILABLE", "PARTIAL", "UNAVAILABLE"
    }:
        raise APIResponseError("月配組合 status 格式不正確")
    for field in ("selected_candidates", "rejected_candidates"):
        candidates = calculation.get(field)
        if not isinstance(candidates, list):
            raise APIResponseError(f"月配組合缺少 {field}")
        if any(
            not isinstance(item, dict)
            or not isinstance(item.get("reasons"), list)
            for item in candidates
        ):
            raise APIResponseError("月配候選缺少納入或排除理由")
    if not isinstance(calculation.get("base_etf_code"), str):
        raise APIResponseError("月配組合缺少基準 ETF")
    target_months = calculation.get("target_payment_months")
    if (
        not isinstance(target_months, list)
        or not target_months
        or target_months != sorted(set(target_months))
        or any(not isinstance(month, int) or month < 1 or month > 12
               for month in target_months)
    ):
        raise APIResponseError("月配組合 target_payment_months 格式不正確")
    return payload


def fetch_monthly_payment_combination(
    api_base_url: str,
    code: str,
    payload: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得以指定 ETF 為錨點的月配缺口組合。"""

    normalized_code = code.strip().upper()
    if not normalized_code:
        raise ValueError("ETF 代號不可為空白")
    result = post_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/etfs/{quote(normalized_code, safe='')}"
            "/monthly-payment-combination"
        ),
        operation_name=f"ETF {normalized_code} 月配組合分析",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    return validate_monthly_combination_result(result)
