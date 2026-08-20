"""M10-4 稅務與再投資 API client。"""

from typing import Any
from urllib.parse import quote

from frontend.api.errors import APIResponseError
from frontend.api.transport import post_json


def validate_tax_reinvestment_result(payload: object) -> dict[str, Any]:
    """驗證稅務情境回應的必要公開欄位。"""

    if not isinstance(payload, dict):
        raise APIResponseError("稅務情境回應必須是 JSON 物件")
    if payload.get("status") not in {"AVAILABLE", "PARTIAL"}:
        raise APIResponseError("稅務情境 status 格式不正確")
    facts = payload.get("historical_facts")
    calculation = payload.get("calculation")
    if not isinstance(facts, dict) or not isinstance(calculation, dict):
        raise APIResponseError("稅務情境缺少歷史事實或計算結果")
    projection_years = calculation.get("projection_years")
    if (
        not isinstance(projection_years, int)
        or isinstance(projection_years, bool)
        or projection_years < 1
        or projection_years > 50
    ):
        raise APIResponseError("稅務情境 projection_years 格式不正確")
    scenarios = calculation.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) != 4:
        raise APIResponseError("稅務情境必須包含四種配息使用方式")
    return payload


def fetch_tax_reinvestment_scenarios(
    api_base_url: str,
    code: str,
    payload: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單一 ETF 的四種稅務與再投資情境。"""

    normalized_code = code.strip().upper()
    if not normalized_code:
        raise ValueError("ETF 代號不可為空白")
    result = post_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/etfs/{quote(normalized_code, safe='')}"
            "/tax-reinvestment-scenarios"
        ),
        operation_name=f"ETF {normalized_code} 稅務情境分析",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    return validate_tax_reinvestment_result(result)
