"""前端 ETF 基礎查詢與回應驗證。"""

from typing import Any
from urllib.parse import quote

from frontend.api.errors import APIResponseError
from frontend.api.transport import get_json


def validate_etf_item(
    item: object,
    index: int,
) -> dict[str, Any]:
    """驗證單筆 ETF API 回應。

    Args:
        item:
            ETF API 回應項目。
        index:
            項目所在位置。

    Returns:
        dict[str, Any]:
            驗證後的 ETF 資料。

    Raises:
        APIResponseError:
            ETF 項目格式不正確。
    """

    if not isinstance(item, dict):
        raise APIResponseError(
            f"ETF 列表第 {index} 筆不是 JSON 物件"
        )

    required_fields = {
        "code",
        "name",
        "is_active",
        "is_bond",
        "listing_date",
        "fund_size",
        "expense_ratio",
    }

    missing_fields = (
        required_fields - item.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            f"ETF 列表第 {index} 筆缺少欄位："
            f"{missing_text}"
        )

    return item


def fetch_etfs(
    api_base_url: str,
    keyword: str | None = None,
    is_active: bool | None = None,
    is_bond: bool | None = None,
    limit: int = 20,
    offset: int = 0,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """讀取 ETF 篩選及分頁列表。

    Args:
        api_base_url:
            FastAPI Base URL。
        keyword:
            ETF 代號或名稱關鍵字。
        is_active:
            主動式或被動式篩選。
        is_bond:
            債券或非債券篩選。
        limit:
            每頁筆數，範圍為 1 到 100。
        offset:
            略過筆數。
        timeout_seconds:
            HTTP 逾時秒數。

    Returns:
        dict[str, Any]:
            ETF 列表、總筆數與分頁資訊。

    Raises:
        ValueError:
            分頁參數超出允許範圍。
        APIClientError:
            FastAPI 連線或回應錯誤。
    """

    if limit < 1 or limit > 100:
        raise ValueError(
            "limit 必須介於 1 到 100"
        )

    if offset < 0:
        raise ValueError(
            "offset 不得小於 0"
        )

    params: dict[str, str | int] = {
        "limit": limit,
        "offset": offset,
    }

    if keyword is not None:
        normalized_keyword = keyword.strip()

        if normalized_keyword:
            params["keyword"] = normalized_keyword

    if is_active is not None:
        params["is_active"] = (
            "true"
            if is_active
            else "false"
        )

    if is_bond is not None:
        params["is_bond"] = (
            "true"
            if is_bond
            else "false"
        )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path="/api/v1/etfs",
        operation_name="ETF 列表查詢",
        params=params,
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "ETF 列表回應必須是 JSON 物件"
        )

    items = payload.get("items")
    total = payload.get("total")
    response_limit = payload.get("limit")
    response_offset = payload.get("offset")

    if not isinstance(items, list):
        raise APIResponseError(
            "ETF 列表 items 格式不正確"
        )

    integer_values = {
        "total": total,
        "limit": response_limit,
        "offset": response_offset,
    }

    for field_name, value in integer_values.items():
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
        ):
            raise APIResponseError(
                f"ETF 列表 {field_name} "
                "必須是整數"
            )

    validated_items = [
        validate_etf_item(
            item,
            index,
        )
        for index, item in enumerate(
            items,
            start=1,
        )
    ]

    return {
        "items": validated_items,
        "total": total,
        "limit": response_limit,
        "offset": response_offset,
    }


def fetch_etf_by_code(
    api_base_url: str,
    code: str,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """依代號取得單筆 ETF 資料。

    Args:
        api_base_url:
            FastAPI Base URL。
        code:
            ETF 證券代號。
        timeout_seconds:
            HTTP 逾時秒數。

    Returns:
        dict[str, Any]:
            ETF 主資料。

    Raises:
        ValueError:
            ETF 代號為空白。
        APIClientError:
            FastAPI 連線或回應錯誤。
    """

    normalized_code = (
        code.strip().upper()
    )

    if not normalized_code:
        raise ValueError(
            "ETF 代號不可為空白"
        )

    encoded_code = quote(
        normalized_code,
        safe="",
    )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/etfs/"
            f"{encoded_code}"
        ),
        operation_name=(
            f"ETF {normalized_code} 查詢"
        ),
        timeout_seconds=timeout_seconds,
    )

    item = validate_etf_item(
        payload,
        index=1,
    )

    response_code = str(
        item["code"]
    ).strip().upper()

    if response_code != normalized_code:
        raise APIResponseError(
            "ETF 詳細資料代號與查詢代號不一致"
        )

    return item
