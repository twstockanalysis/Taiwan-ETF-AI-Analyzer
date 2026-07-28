"""ETF 主資料 API 路由。"""

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies import get_database_path
from backend.app.models.etf import ETFResponse
from backend.app.repositories.etf_repository import (
    get_etf_by_code,
    list_etfs,
)


DatabasePath = Annotated[
    Path,
    Depends(get_database_path),
]


router = APIRouter(
    prefix="/api/v1/etfs",
    tags=["ETFs"],
)


@router.get(
    "",
    response_model=list[ETFResponse],
    summary="取得 ETF 列表",
)
def read_etfs(
    database_path: DatabasePath,
) -> list[dict[str, Any]]:
    """取得所有 ETF 主資料。

    Args:
        database_path: FastAPI 注入的資料庫路徑。

    Returns:
        list[dict[str, Any]]: ETF 資料列表。
    """

    return list_etfs(database_path)


@router.get(
    "/{code}",
    response_model=ETFResponse,
    summary="依代號查詢 ETF",
)
def read_etf(
    code: str,
    database_path: DatabasePath,
) -> dict[str, Any]:
    """依 ETF 代號取得單筆資料。

    Args:
        code: ETF 證券代號。
        database_path: FastAPI 注入的資料庫路徑。

    Returns:
        dict[str, Any]: ETF 主資料。

    Raises:
        HTTPException:
            找不到指定 ETF 時回傳 HTTP 404。
    """

    normalized_code = code.strip().upper()

    etf = get_etf_by_code(
        normalized_code,
        database_path,
    )

    if etf is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到 ETF：{normalized_code}",
        )

    return etf