"""公開 ETF 歷史品質評等 API client 與安全驗證。"""

import json
from typing import Any

from frontend.api.errors import APIResponseError
from frontend.api.transport import get_json
from frontend.api.validators import validate_optional_iso_date


PUBLIC_GRADES = {"A+", "A", "B", "C", "D", "E", "F"}


def validate_historical_quality_grade(payload: object) -> dict[str, Any]:
    """驗證單檔公開評等，不接受內部分數、排名或可信度。"""

    if not isinstance(payload, dict):
        raise APIResponseError("ETF 歷史品質評等必須是 JSON 物件")
    status = str(payload.get("status", "")).strip().upper()
    grade = payload.get("grade")
    if status not in {"RATED", "UNRATED"}:
        raise APIResponseError("ETF 歷史品質評等狀態不正確")
    if status == "RATED" and grade not in PUBLIC_GRADES:
        raise APIResponseError("已評等 ETF 必須包含 A+ 至 F 字母評等")
    if status == "UNRATED" and grade is not None:
        raise APIResponseError("暫不評等 ETF 不可包含字母評等")
    if not isinstance(payload.get("explanation"), str):
        raise APIResponseError("ETF 歷史品質評等缺少說明")
    for field in ("strengths", "risks", "unavailable_evidence"):
        if not isinstance(payload.get(field), list):
            raise APIResponseError(f"ETF 歷史品質評等 {field} 格式不正確")
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    for forbidden in ("quality_score", "score_components", "rank", "confidence"):
        if forbidden in serialized:
            raise APIResponseError("ETF 歷史品質評等包含內部欄位")
    return payload


def validate_quality_grade_response(
    payload: object,
    expected_codes: list[str],
) -> dict[str, Any]:
    """驗證批次評等回應順序及版本。"""

    if not isinstance(payload, dict):
        raise APIResponseError("ETF 歷史品質評等回應必須是 JSON 物件")
    if payload.get("methodology") != "DETERMINISTIC_QUALITY_GRADE_V4_1":
        raise APIResponseError("ETF 歷史品質評等版本不正確")
    validate_optional_iso_date(payload.get("analysis_date"), "評等分析日期")
    years = payload.get("history_years")
    if not isinstance(years, int) or isinstance(years, bool) or not 1 <= years <= 10:
        raise APIResponseError("ETF 歷史品質評等觀察年數不正確")
    items = payload.get("items")
    if not isinstance(items, list) or len(items) != len(expected_codes):
        raise APIResponseError("ETF 歷史品質評等筆數不正確")
    normalized_items = []
    for index, (item, expected_code) in enumerate(
        zip(items, expected_codes, strict=True),
        start=1,
    ):
        if not isinstance(item, dict):
            raise APIResponseError(f"ETF 歷史品質評等第 {index} 筆格式不正確")
        code = str(item.get("etf_code", "")).strip().upper()
        if code != expected_code:
            raise APIResponseError("ETF 歷史品質評等順序不正確")
        normalized_items.append(
            {
                "etf_code": code,
                "historical_quality_grade": validate_historical_quality_grade(
                    item.get("historical_quality_grade")
                ),
            }
        )
    return {**payload, "items": normalized_items}


def fetch_historical_quality_grades(
    api_base_url: str,
    codes: list[str] | tuple[str, ...],
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    """批次取得 1 至 100 檔 ETF 的公開歷史品質評等。"""

    normalized_codes = list(
        dict.fromkeys(str(code).strip().upper() for code in codes if str(code).strip())
    )
    if not normalized_codes or len(normalized_codes) > 100:
        raise ValueError("ETF 評等查詢必須包含 1 至 100 個代號")
    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path="/api/v1/etfs/historical-quality-grades",
        operation_name="ETF 歷史品質評等",
        params={"codes": ",".join(normalized_codes)},
        timeout_seconds=timeout_seconds,
    )
    return validate_quality_grade_response(payload, normalized_codes)


def quality_grade_lookup(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """將已驗證回應轉為代號查詢表。"""

    return {
        item["etf_code"]: item["historical_quality_grade"]
        for item in payload.get("items", [])
    }
