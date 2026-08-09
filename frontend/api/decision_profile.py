"""M11-1 單一使用者條件與手動持有部位 API client。"""

from typing import Any
from urllib.parse import quote

from frontend.api.errors import APIResponseError
from frontend.api.transport import delete_json, get_json, put_json


def validate_user_conditions(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise APIResponseError("使用者條件回應必須是 JSON 物件")
    required = {
        "monthly_after_tax_target",
        "analysis_years",
        "history_years",
        "cash_deduction_rate_pct",
        "currency",
        "updated_at",
    }
    if required - payload.keys():
        raise APIResponseError("使用者條件回應缺少必要欄位")
    if payload["currency"] != "TWD":
        raise APIResponseError("使用者條件幣別必須為 TWD")
    return payload


def validate_manual_holding(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise APIResponseError("手動持有部位回應必須是 JSON 物件")
    required = {
        "etf_code",
        "name",
        "is_active",
        "is_bond",
        "held_units",
        "unit_price",
        "price_as_of_date",
        "currency",
        "updated_at",
    }
    if required - payload.keys():
        raise APIResponseError("手動持有部位回應缺少必要欄位")
    if payload["currency"] != "TWD":
        raise APIResponseError("手動持有部位幣別必須為 TWD")
    return payload


def validate_decision_profile(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise APIResponseError("決策條件回應必須是 JSON 物件")
    if payload.get("profile_scope") != "SINGLE_USER":
        raise APIResponseError("決策條件 scope 格式不正確")
    if payload.get("broker_connected") is not False:
        raise APIResponseError("M11-1 不可宣稱已連接券商")
    conditions = payload.get("conditions")
    if conditions is not None:
        validate_user_conditions(conditions)
    holdings = payload.get("holdings")
    if not isinstance(holdings, list):
        raise APIResponseError("決策條件 holdings 格式不正確")
    for item in holdings:
        validate_manual_holding(item)
    return payload


def fetch_decision_profile(
    api_base_url: str,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    result = get_json(
        api_base_url=api_base_url,
        endpoint_path="/api/v1/decision-profile",
        operation_name="決策條件查詢",
        timeout_seconds=timeout_seconds,
    )
    return validate_decision_profile(result)


def save_user_conditions(
    api_base_url: str,
    payload: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    result = put_json(
        api_base_url=api_base_url,
        endpoint_path="/api/v1/decision-profile/conditions",
        operation_name="使用者條件儲存",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    return validate_user_conditions(result)


def save_manual_holding(
    api_base_url: str,
    etf_code: str,
    payload: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    normalized_code = etf_code.strip().upper()
    if not normalized_code:
        raise ValueError("ETF 代號不可為空白")
    result = put_json(
        api_base_url=api_base_url,
        endpoint_path=(
            "/api/v1/decision-profile/holdings/"
            f"{quote(normalized_code, safe='')}"
        ),
        operation_name=f"ETF {normalized_code} 持有部位儲存",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    return validate_manual_holding(result)


def delete_manual_holding(
    api_base_url: str,
    etf_code: str,
    timeout_seconds: float = 10.0,
) -> None:
    normalized_code = etf_code.strip().upper()
    if not normalized_code:
        raise ValueError("ETF 代號不可為空白")
    delete_json(
        api_base_url=api_base_url,
        endpoint_path=(
            "/api/v1/decision-profile/holdings/"
            f"{quote(normalized_code, safe='')}"
        ),
        operation_name=f"ETF {normalized_code} 持有部位刪除",
        timeout_seconds=timeout_seconds,
    )
