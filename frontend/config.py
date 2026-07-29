"""Streamlit 前端系統設定。"""

import os


DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"


def get_api_base_url() -> str:
    """取得 FastAPI 後端網址。

    優先讀取環境變數 TW_ETF_API_URL。
    未設定時使用本機 FastAPI 網址。

    Returns:
        str: FastAPI Base URL。

    Raises:
        ValueError: API URL 格式不正確。
    """

    api_base_url = os.getenv(
        "TW_ETF_API_URL",
        DEFAULT_API_BASE_URL,
    ).strip()

    if not api_base_url:
        api_base_url = DEFAULT_API_BASE_URL

    api_base_url = api_base_url.rstrip("/")

    if not api_base_url.startswith(
        (
            "http://",
            "https://",
        )
    ):
        raise ValueError(
            "TW_ETF_API_URL 必須以 "
            "http:// 或 https:// 開頭"
        )

    return api_base_url