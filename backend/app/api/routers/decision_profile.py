"""M11-1 單一使用者條件與手動持有部位 API。"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.api.dependencies import get_database_path
from backend.app.models.decision_profile import (
    DecisionProfileResponse,
    ManualHoldingResponse,
    ManualHoldingUpsert,
    UserConditionsResponse,
    UserConditionsUpsert,
)
from backend.app.repositories.decision_profile_repository import (
    delete_manual_holding,
    get_user_conditions,
    list_manual_holdings,
    upsert_manual_holding,
    upsert_user_conditions,
)
from backend.app.repositories.etf_repository import get_etf_by_code


DatabasePath = Annotated[Path, Depends(get_database_path)]
router = APIRouter(
    prefix="/api/v1/decision-profile",
    tags=["Decision Profile"],
)


@router.get("", response_model=DecisionProfileResponse)
def read_decision_profile(
    database_path: DatabasePath,
) -> DecisionProfileResponse:
    return DecisionProfileResponse(
        conditions=get_user_conditions(database_path),
        holdings=list_manual_holdings(database_path),
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
