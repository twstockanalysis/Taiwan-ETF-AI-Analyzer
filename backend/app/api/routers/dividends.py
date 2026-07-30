"""ETF 配息歷史、組成與 76W 查詢 API。"""

from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path as PathParameter,
    Query,
    status,
)

from backend.app.api.dependencies import (
    get_database_path,
)
from backend.app.models.dividend_api import (
    Actual76WSummaryResponse,
    DividendComponentListResponse,
    DividendDetailResponse,
    ETFDividendHistoryResponse,
)
from backend.app.models.etf_analysis import (
    DividendComponentBasis,
)
from backend.app.repositories.dividend_repository import (
    build_actual_76w_summary,
    count_etf_dividends,
    get_dividend_by_id,
    list_etf_dividends,
    list_filtered_dividend_components,
)
from backend.app.repositories.etf_repository import (
    get_etf_by_code,
)


DatabasePath = Annotated[
    Path,
    Depends(get_database_path),
]


router = APIRouter(
    tags=["Dividends"],
)


def require_etf(
    code: str,
    database_path: Path,
) -> str:
    """Normalize an ETF code and raise 404 when absent."""

    normalized_code = (
        code.strip().upper()
    )

    etf = get_etf_by_code(
        normalized_code,
        database_path,
    )

    if etf is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                f"找不到 ETF："
                f"{normalized_code}"
            ),
        )

    return normalized_code


def require_dividend(
    dividend_id: int,
    database_path: Path,
) -> dict[str, Any]:
    """Return one dividend or raise HTTP 404."""

    dividend = get_dividend_by_id(
        dividend_id=dividend_id,
        database_path=database_path,
    )

    if dividend is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                f"找不到配息事件："
                f"{dividend_id}"
            ),
        )

    return dividend


def map_dividend_item(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Map Repository event keys to API keys."""

    return {
        "dividend_id": row["id"],
        "source_event_id": (
            row["source_event_id"]
        ),
        "announcement_date": (
            row["announcement_date"]
        ),
        "ex_dividend_date": (
            row["ex_dividend_date"]
        ),
        "record_date": row["record_date"],
        "payment_date": (
            row["payment_date"]
        ),
        "amount_per_unit": (
            row["amount_per_unit"]
        ),
        "currency": row["currency"],
        "source_id": row["source_id"],
    }


def map_component_item(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Map Repository component keys to API keys."""

    return {
        "component_id": row["id"],
        "dividend_id": row["dividend_id"],
        "component_code": (
            row["component_code"]
        ),
        "component_basis": (
            row["component_basis"]
        ),
        "component_name": (
            row["component_name"]
        ),
        "amount_per_unit": (
            row["amount_per_unit"]
        ),
        "ratio_pct": row["ratio_pct"],
        "source_id": row["source_id"],
    }


@router.get(
    "/api/v1/etfs/{code}/dividends",
    response_model=ETFDividendHistoryResponse,
    summary="取得 ETF 配息歷史",
)
def read_etf_dividends(
    code: str,
    database_path: DatabasePath,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="單次回傳筆數",
        ),
    ] = 20,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="略過筆數",
        ),
    ] = 0,
) -> dict[str, Any]:
    """Return one ETF's paginated dividend history."""

    normalized_code = require_etf(
        code,
        database_path,
    )

    rows = list_etf_dividends(
        etf_code=normalized_code,
        database_path=database_path,
        limit=limit,
        offset=offset,
    )

    total = count_etf_dividends(
        etf_code=normalized_code,
        database_path=database_path,
    )

    return {
        "etf_code": normalized_code,
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            map_dividend_item(row)
            for row in rows
        ],
    }


@router.get(
    "/api/v1/etfs/{code}/dividends/76w",
    response_model=Actual76WSummaryResponse,
    summary="取得 ETF 實際 76W 歷史",
)
def read_etf_actual_76w(
    code: str,
    database_path: DatabasePath,
) -> dict[str, Any]:
    """Return ACTUAL 76W records only."""

    normalized_code = require_etf(
        code,
        database_path,
    )

    return build_actual_76w_summary(
        etf_code=normalized_code,
        database_path=database_path,
    )


@router.get(
    "/api/v1/dividends/{dividend_id}",
    response_model=DividendDetailResponse,
    summary="取得單次配息事件與組成",
)
def read_dividend(
    dividend_id: Annotated[
        int,
        PathParameter(
            ge=1,
            description="配息事件資料庫 ID",
        ),
    ],
    database_path: DatabasePath,
) -> dict[str, Any]:
    """Return one dividend event with all components."""

    dividend = require_dividend(
        dividend_id,
        database_path,
    )

    components = (
        list_filtered_dividend_components(
            dividend_id=dividend_id,
            database_path=database_path,
        )
    )

    return {
        **map_dividend_item(
            dividend
        ),
        "etf_code": dividend["etf_code"],
        "components": [
            map_component_item(row)
            for row in components
        ],
    }


@router.get(
    "/api/v1/dividends/{dividend_id}/components",
    response_model=DividendComponentListResponse,
    summary="查詢單次配息組成",
)
def read_dividend_components(
    dividend_id: Annotated[
        int,
        PathParameter(
            ge=1,
            description="配息事件資料庫 ID",
        ),
    ],
    database_path: DatabasePath,
    component_basis: Annotated[
        DividendComponentBasis | None,
        Query(
            description=(
                "篩選 ESTIMATED 或 ACTUAL"
            ),
        ),
    ] = None,
    component_code: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=40,
            description="篩選配息組成代碼",
        ),
    ] = None,
    source_id: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=50,
            description="篩選資料來源",
        ),
    ] = None,
) -> dict[str, Any]:
    """Return filtered components for one dividend."""

    require_dividend(
        dividend_id,
        database_path,
    )

    rows = list_filtered_dividend_components(
        dividend_id=dividend_id,
        database_path=database_path,
        component_basis=component_basis,
        component_code=component_code,
        source_id=source_id,
    )

    return {
        "dividend_id": dividend_id,
        "total": len(rows),
        "items": [
            map_component_item(row)
            for row in rows
        ],
    }
