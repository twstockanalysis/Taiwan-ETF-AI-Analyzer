"""前端 FastAPI 健康狀態查詢與回應驗證。"""

from frontend.api.errors import APIResponseError
from frontend.api.transport import get_json


def fetch_api_health(
    api_base_url: str,
    timeout_seconds: float = 5.0,
) -> dict[str, str]:
    """讀取 FastAPI 健康狀態。

    Args:
        api_base_url:
            FastAPI Base URL。
        timeout_seconds:
            HTTP 請求逾時秒數。

    Returns:
        dict[str, str]:
            FastAPI 健康狀態。

    Raises:
        APIConnectionError:
            無法連接 FastAPI。
        APIResponseError:
            FastAPI 回應格式不正確。
    """

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path="/health",
        operation_name="FastAPI 健康檢查",
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "FastAPI 健康檢查格式不正確"
        )

    status_value = payload.get("status")

    if status_value != "healthy":
        raise APIResponseError(
            "FastAPI 狀態不是 healthy"
        )

    return {
        "status": str(status_value),
    }
