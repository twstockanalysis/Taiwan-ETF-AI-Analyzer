"""TW ETF AI Analyzer FastAPI 應用程式入口。"""

from fastapi import FastAPI


# 建立 FastAPI 應用程式物件。
#
# title：
# 顯示在自動產生的 API 文件中。
#
# description：
# 說明這個後端 API 的用途。
#
# version：
# 目前 API 的版本。
app = FastAPI(
    title="TW ETF AI Analyzer API",
    description="台灣 ETF 分析網站後端 API",
    version="0.1.0",
)


@app.get(
    "/",
    tags=["System"],
    summary="API 首頁",
)
async def read_root() -> dict[str, str]:
    """回傳 API 基本資訊。

    Returns:
        dict[str, str]: API 名稱及目前執行狀態。
    """

    return {
        "message": "TW ETF AI Analyzer API",
        "status": "running",
    }


@app.get(
    "/health",
    tags=["System"],
    summary="健康檢查",
)
async def health_check() -> dict[str, str]:
    """檢查後端 API 是否正常運作。

    Returns:
        dict[str, str]: API 健康狀態。
    """

    return {
        "status": "healthy",
    }