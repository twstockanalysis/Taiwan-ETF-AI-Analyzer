"""單一 ETF 目標現金流分析 API client。"""

from typing import Any
from urllib.parse import quote

from frontend.api.errors import APIResponseError
from frontend.api.transport import get_json, post_json
from frontend.api.validators import (
    validate_optional_iso_date,
    validate_optional_number,
    validate_required_text,
)


def validate_latest_close(payload: object) -> dict[str, Any]:
    """驗證官方最新收盤價回應並保留缺值語意。"""

    if not isinstance(payload, dict):
        raise APIResponseError("最新收盤價回應必須是物件")
    result = dict(payload)
    result["etf_code"] = validate_required_text(
        result.get("etf_code"), "etf_code"
    )
    result["name"] = validate_required_text(result.get("name"), "name")
    result["close_price"] = validate_optional_number(
        result.get("close_price"), "close_price", minimum=0.000001
    )
    result["trade_date"] = validate_optional_iso_date(
        result.get("trade_date"), "trade_date"
    )
    source_id = result.get("source_id")
    result["source_id"] = (
        None
        if source_id is None
        else validate_required_text(source_id, "source_id")
    )
    price_fields = (
        result["close_price"], result["trade_date"], result["source_id"]
    )
    if any(value is None for value in price_fields) and not all(
        value is None for value in price_fields
    ):
        raise APIResponseError("最新收盤價的價格、日期與來源必須同時存在")
    return result


def validate_price_history(payload: object) -> dict[str, Any]:
    """驗證依交易日排序的官方收盤價歷史。"""

    if not isinstance(payload, dict):
        raise APIResponseError("歷史收盤價回應必須是物件")

    result = dict(payload)
    result["etf_code"] = validate_required_text(
        result.get("etf_code"),
        "etf_code",
    )
    result["name"] = validate_required_text(
        result.get("name"),
        "name",
    )
    items = result.get("items")
    if not isinstance(items, list):
        raise APIResponseError("歷史收盤價 items 必須是陣列")

    validated_items: list[dict[str, Any]] = []
    previous_date: str | None = None
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise APIResponseError(
                f"歷史收盤價第 {index} 筆必須是物件"
            )
        trade_date = validate_optional_iso_date(
            item.get("trade_date"),
            f"items[{index}].trade_date",
        )
        if trade_date is None:
            raise APIResponseError(
                f"items[{index}].trade_date 不得缺少"
            )
        if previous_date is not None and trade_date <= previous_date:
            raise APIResponseError(
                "歷史收盤價必須依交易日遞增且不可重複"
            )
        previous_date = trade_date
        validated_items.append(
            {
                "trade_date": trade_date,
                "close_price": validate_optional_number(
                    item.get("close_price"),
                    f"items[{index}].close_price",
                    minimum=0.000001,
                ),
                "source_id": validate_required_text(
                    item.get("source_id"),
                    f"items[{index}].source_id",
                ),
            }
        )
        if validated_items[-1]["close_price"] is None:
            raise APIResponseError(
                f"items[{index}].close_price 不得缺少"
            )

    result["items"] = validated_items
    return result


def validate_target_analysis_result(payload: object) -> dict[str, Any]:
    """驗證前端會呈現的目標分析必要結構。"""

    if not isinstance(payload, dict):
        raise APIResponseError("目標分析回應必須是物件")
    result = dict(payload)
    if not isinstance(result.get("cash_flow"), dict):
        raise APIResponseError("cash_flow 必須是物件")
    if not isinstance(result.get("scenario_estimate"), dict):
        raise APIResponseError("scenario_estimate 必須是物件")
    for field in ("warnings", "unavailable_fields"):
        if not isinstance(result.get(field), list):
            raise APIResponseError(f"{field} 必須是陣列")
    for index, warning in enumerate(result["warnings"]):
        if not isinstance(warning, dict):
            raise APIResponseError(f"warnings[{index}] 必須是物件")
        validate_required_text(warning.get("code"), f"warnings[{index}].code")
        validate_required_text(
            warning.get("message"), f"warnings[{index}].message"
        )
        validate_optional_iso_date(
            warning.get("as_of_date"), f"warnings[{index}].as_of_date"
        )
        source_id = warning.get("source_id")
        if source_id is not None:
            validate_required_text(source_id, f"warnings[{index}].source_id")
        if not isinstance(warning.get("evidence", {}), dict):
            raise APIResponseError(f"warnings[{index}].evidence 必須是物件")
    monthly = result.get("monthly_cash_flow")
    if not isinstance(monthly, list) or len(monthly) != 12:
        raise APIResponseError("monthly_cash_flow 必須包含 12 個月份")
    months = [item.get("month") for item in monthly if isinstance(item, dict)]
    if months != list(range(1, 13)):
        raise APIResponseError("monthly_cash_flow 必須依 1 至 12 月排序")
    return result


def fetch_etf_latest_close(
    api_base_url: str, code: str, timeout_seconds: float = 5.0
) -> dict[str, Any]:
    """取得單一 ETF 的官方最新收盤價。"""

    normalized_code = code.strip().upper()
    if not normalized_code:
        raise ValueError("ETF 代號不可為空白")
    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/etfs/{quote(normalized_code, safe='')}/latest-close"
        ),
        operation_name=f"ETF {normalized_code} 最新收盤價",
        timeout_seconds=timeout_seconds,
    )
    return validate_latest_close(payload)


def fetch_etf_price_history(
    api_base_url: str,
    code: str,
    limit: int = 260,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單一 ETF 最近的官方收盤價歷史。"""

    normalized_code = code.strip().upper()
    if not normalized_code:
        raise ValueError("ETF 代號不可為空白")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 2 <= limit <= 1250:
        raise ValueError("歷史收盤價筆數必須介於 2 與 1250")

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/etfs/{quote(normalized_code, safe='')}/price-history"
        ),
        operation_name=f"ETF {normalized_code} 歷史收盤價",
        params={"limit": limit},
        timeout_seconds=timeout_seconds,
    )
    return validate_price_history(payload)


def fetch_etf_target_analysis(
    api_base_url: str,
    code: str,
    payload: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """依官方收盤價取得單一 ETF 目標現金流分析。"""

    normalized_code = code.strip().upper()
    if not normalized_code:
        raise ValueError("ETF 代號不可為空白")
    result = post_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/etfs/{quote(normalized_code, safe='')}/target-analysis"
        ),
        operation_name=f"ETF {normalized_code} 目標現金流分析",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    return validate_target_analysis_result(result)
