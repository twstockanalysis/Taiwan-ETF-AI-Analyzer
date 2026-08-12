"""M11-1 單一使用者條件與手動持有部位 API。"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.api.dependencies import get_database_path
from backend.app.api.owner_access import require_owner_access
from backend.app.models.decision_profile import (
    CandidateHoldingAnalysisRequest,
    CandidateHoldingAnalysisResponse,
    CurrentHoldingAnalysisResponse,
    DecisionProfileResponse,
    DecisionRecordResponse,
    DecisionRecordSummary,
    ManualHoldingBatchUpsert,
    ManualHoldingResponse,
    ManualHoldingUpsert,
    UserConditionsResponse,
    UserConditionsUpsert,
)
from backend.app.repositories.decision_profile_repository import (
    delete_manual_holding,
    get_user_conditions,
    list_manual_holdings,
    replace_manual_holdings,
    upsert_manual_holding,
    upsert_user_conditions,
)
from backend.app.repositories.etf_repository import get_etf_by_code
from backend.app.repositories.daily_close_repository import (
    get_latest_daily_close,
)
from backend.app.repositories.decision_record_repository import (
    get_decision_record,
    list_decision_records,
)
from backend.app.services.current_holding_analysis import analyze_current_holdings
from backend.app.services.candidate_holding_analysis import (
    analyze_candidate_holding,
)
from backend.app.services.decision_record import (
    create_candidate_decision_record,
)
from backend.app.services.decision_record_export import (
    export_decision_record_xlsx,
)


DatabasePath = Annotated[Path, Depends(get_database_path)]
router = APIRouter(
    prefix="/api/v1/decision-profile",
    tags=["Decision Profile"],
    dependencies=[Depends(require_owner_access)],
)


@router.get("", response_model=DecisionProfileResponse)
def read_decision_profile(
    database_path: DatabasePath,
) -> DecisionProfileResponse:
    return DecisionProfileResponse(
        conditions=get_user_conditions(database_path),
        holdings=list_manual_holdings(database_path),
    )


@router.get(
    "/current-holding-analysis",
    response_model=CurrentHoldingAnalysisResponse,
    summary="以已儲存條件分析目前手動持倉",
)
def read_current_holding_analysis(
    database_path: DatabasePath,
) -> CurrentHoldingAnalysisResponse:
    return analyze_current_holdings(database_path)


@router.post(
    "/candidate-analysis/{etf_code}",
    response_model=CandidateHoldingAnalysisResponse,
    summary="比較候選 ETF 加入目前持倉前後的情境",
)
def read_candidate_holding_analysis(
    etf_code: str,
    value: CandidateHoldingAnalysisRequest,
    database_path: DatabasePath,
) -> CandidateHoldingAnalysisResponse:
    normalized_code = etf_code.strip().upper()
    result = analyze_candidate_holding(
        normalized_code,
        value,
        database_path,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到 ETF：{normalized_code}",
        )
    return result


@router.post(
    "/candidate-analysis/{etf_code}/decision-records",
    response_model=DecisionRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="重新分析候選 ETF 並保存不可變決策快照",
)
def save_candidate_decision_record(
    etf_code: str,
    value: CandidateHoldingAnalysisRequest,
    database_path: DatabasePath,
) -> DecisionRecordResponse:
    normalized_code = etf_code.strip().upper()
    result = create_candidate_decision_record(
        normalized_code,
        value,
        database_path,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到 ETF：{normalized_code}",
        )
    return result


@router.get(
    "/decision-records",
    response_model=list[DecisionRecordSummary],
    summary="列出不可變決策快照",
)
def read_decision_records(
    database_path: DatabasePath,
) -> list[DecisionRecordSummary]:
    return [
        DecisionRecordSummary.model_validate(item)
        for item in list_decision_records(database_path)
    ]


def _read_record_or_404(
    record_id: int,
    database_path: Path,
) -> DecisionRecordResponse:
    record = get_decision_record(record_id, database_path)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到決策紀錄：{record_id}",
        )
    return DecisionRecordResponse.model_validate(record)


@router.get(
    "/decision-records/{record_id}",
    response_model=DecisionRecordResponse,
    summary="讀取單一不可變決策快照",
)
def read_decision_record(
    record_id: int,
    database_path: DatabasePath,
) -> DecisionRecordResponse:
    return _read_record_or_404(record_id, database_path)


@router.get(
    "/decision-records/{record_id}/export.xlsx",
    summary="匯出單一決策快照 Excel",
)
def export_decision_record(
    record_id: int,
    database_path: DatabasePath,
) -> Response:
    record = _read_record_or_404(record_id, database_path)
    return Response(
        content=export_decision_record_xlsx(record),
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                "attachment; filename="
                f'"decision-record-{record.id}-{record.candidate_etf_code}.xlsx"'
            )
        },
    )


@router.put(
    "/conditions",
    response_model=UserConditionsResponse,
)
def save_user_conditions(
    value: UserConditionsUpsert,
    database_path: DatabasePath,
) -> UserConditionsResponse:
    return UserConditionsResponse(
        **upsert_user_conditions(value, database_path)
    )


@router.put(
    "/holdings",
    response_model=list[ManualHoldingResponse],
    summary="以官方最新收盤價取代目前全部手動持股",
)
def save_manual_holding_batch(
    value: ManualHoldingBatchUpsert,
    database_path: DatabasePath,
) -> list[ManualHoldingResponse]:
    resolved: list[dict] = []
    for item in value.holdings:
        if get_etf_by_code(item.etf_code, database_path) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到 ETF：{item.etf_code}",
            )
        latest_close = get_latest_daily_close(item.etf_code, database_path)
        resolved.append(
            {
                "etf_code": item.etf_code,
                "held_units": item.held_units,
                "unit_price": (
                    latest_close["close_price"] if latest_close else None
                ),
                "price_as_of_date": (
                    latest_close["trade_date"] if latest_close else None
                ),
                "price_source_id": (
                    latest_close["source_id"] if latest_close else None
                ),
            }
        )

    return [
        ManualHoldingResponse(**item)
        for item in replace_manual_holdings(resolved, database_path)
    ]


@router.put(
    "/holdings/{etf_code}",
    response_model=ManualHoldingResponse,
)
def save_manual_holding(
    etf_code: str,
    value: ManualHoldingUpsert,
    database_path: DatabasePath,
) -> ManualHoldingResponse:
    normalized_code = etf_code.strip().upper()
    if get_etf_by_code(normalized_code, database_path) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到 ETF：{normalized_code}",
        )
    return ManualHoldingResponse(
        **upsert_manual_holding(normalized_code, value, database_path)
    )


@router.delete(
    "/holdings/{etf_code}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_manual_holding(
    etf_code: str,
    database_path: DatabasePath,
) -> Response:
    normalized_code = etf_code.strip().upper()
    if not delete_manual_holding(normalized_code, database_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到手動持有部位：{normalized_code}",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
