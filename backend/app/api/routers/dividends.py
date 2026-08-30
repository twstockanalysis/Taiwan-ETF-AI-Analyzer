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
    list_etf_component_history,
    list_filtered_dividend_components,
)
from backend.app.repositories.etf_repository import (
    get_etf_by_code,
)
from backend.app.services.dividend_component_data import (
    select_composite_component_mix,
    select_composite_realized_gain_history,
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
        "distribution_period": (
            row["distribution_period"]
        ),
        "distribution_period_source_id": (
            row[
                "distribution_period_source_id"
            ]
        ),
        "yield_pct": row["yield_pct"],
        "yield_basis": row["yield_basis"],
        "yield_source_id": (
            row["yield_source_id"]
        ),
        "reference_trade_date": (
            row["reference_trade_date"]
        ),
        "reference_close_price": (
            row["reference_close_price"]
        ),
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
    summary="取得 ETF 正式 76W 與綜合資本利得分析",
)
def read_etf_actual_76w(
    code: str,
    database_path: DatabasePath,
) -> dict[str, Any]:
    """Return formal 76W history plus clearly separated fallback analysis."""

    normalized_code = require_etf(
        code,
        database_path,
    )

    actual_summary = build_actual_76w_summary(
        etf_code=normalized_code,
        database_path=database_path,
    )
    analysis_records = select_composite_realized_gain_history(
        list_etf_component_history(
            normalized_code,
            database_path,
        )
    )
    ratios = [float(item.ratio_pct) for item in analysis_records]

    return {
        **actual_summary,
        "analysis_record_count": len(analysis_records),
        "analysis_actual_count": sum(
            item.basis == "ACTUAL" for item in analysis_records
        ),
        "analysis_estimated_fallback_count": sum(
            item.basis == "ESTIMATED_FALLBACK"
            for item in analysis_records
        ),
        "full_realized_gain_count": sum(
            ratio == 100.0 for ratio in ratios
        ),
        "latest_realized_gain_ratio_pct": (
            ratios[0] if ratios else None
        ),
        "average_realized_gain_ratio_pct": (
            round(sum(ratios) / len(ratios), 6)
            if ratios
            else None
        ),
        "latest_analysis_basis": (
            analysis_records[0].basis
            if analysis_records
            else None
        ),
    }


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
    selection = select_composite_component_mix(
        [
            {
                **row,
                "source_event_id": dividend[
                    "source_event_id"
                ],
                "announcement_date": dividend[
                    "announcement_date"
                ],
                "ex_dividend_date": dividend[
                    "ex_dividend_date"
                ],
                "record_date": dividend[
                    "record_date"
                ],
                "payment_date": dividend[
                    "payment_date"
                ],
            }
            for row in components
        ]
    )
    selected_source_basis = (
        "ACTUAL"
        if selection is not None
        and selection.basis == "ACTUAL"
        else "ESTIMATED"
        if selection is not None
        else None
    )
    selected_components = [
        row
        for row in components
        if selected_source_basis is not None
        and str(row["component_basis"]).upper()
        == selected_source_basis
    ]

    return {
        **map_dividend_item(
            dividend
        ),
        "etf_code": dividend["etf_code"],
        "components": [
            map_component_item(row)
            for row in components
        ],
        "selected_component_basis": (
            selection.basis
            if selection is not None
            else None
        ),
        "selected_components": [
            map_component_item(row)
            for row in selected_components
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
