"""前端 API Client 的錯誤類別。"""


class APIClientError(RuntimeError):
    """FastAPI Client 的共用錯誤。"""


class APIConnectionError(APIClientError):
    """無法連接 FastAPI 時的錯誤。"""


class APIResponseError(APIClientError):
    """FastAPI 回應內容不正確時的錯誤。"""


class APIResourceNotFoundError(
    APIResponseError
):
    """FastAPI 找不到指定資源。"""