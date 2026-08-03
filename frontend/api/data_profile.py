"""前端 ETF 資料概況查詢與回應驗證。"""

from typing import Any
from urllib.parse import quote

from frontend.api.errors import APIResponseError
from frontend.api.normalizers import SUPPORTED_PERFORMANCE_PERIODS
from frontend.api.transport import get_json
from frontend.api.validators import (
    validate_non_negative_integer,
    validate_optional_iso_date,
    validate_optional_iso_datetime,
    validate_required_text,
)


def validate_etf_data_profile_sources(
    payload: object,
    field_name: str,
) -> list[dict[str, str]]:
    """驗證 ETF 資料概況來源清單。"""

    if not isinstance(payload, list):
        raise APIResponseError(
            f"{field_name} 必須是陣列"
        )

    sources: list[
        dict[str, str]
    ] = []

    seen_source_ids: set[str] = set()

    for index, item in enumerate(
        payload,
        start=1,
    ):
        if not isinstance(item, dict):
            raise APIResponseError(
                f"{field_name} 第 {index} 筆"
                "必須是 JSON 物件"
            )

        source_id = (
            validate_required_text(
                item.get("source_id"),
                (
                    f"{field_name} 第 {index} 筆 "
                    "source_id"
                ),
            ).lower()
        )

        display_name = (
            validate_required_text(
                item.get("display_name"),
                (
                    f"{field_name} 第 {index} 筆 "
                    "display_name"
                ),
            )
        )

        if source_id in seen_source_ids:
            raise APIResponseError(
                f"{field_name} 包含重複來源："
                f"{source_id}"
            )

        seen_source_ids.add(
            source_id
        )

        sources.append(
            {
                "source_id": source_id,
                "display_name": (
                    display_name
                ),
            }
        )

    return sources


def validate_etf_data_profile(
    payload: object,
) -> dict[str, Any]:
    """驗證 ETF 詳細頁資料來源與新鮮度回應。"""

    if not isinstance(payload, dict):
        raise APIResponseError(
            "ETF 資料概況回應必須是 JSON 物件"
        )

    etf_code = (
        validate_required_text(
            payload.get("etf_code"),
            "ETF 資料概況 etf_code",
        ).upper()
    )

    master = payload.get("master")
    performance = payload.get(
        "performance"
    )
    dividends = payload.get(
        "dividends"
    )
    actual_dividend = payload.get(
        "actual_dividend"
    )

    sections = {
        "master": master,
        "performance": performance,
        "dividends": dividends,
        "actual_dividend": (
            actual_dividend
        ),
    }

    for section_name, section in (
        sections.items()
    ):
        if not isinstance(section, dict):
            raise APIResponseError(
                "ETF 資料概況 "
                f"{section_name} "
                "必須是 JSON 物件"
            )

    validated_master = {
        "sources": (
            validate_etf_data_profile_sources(
                master.get("sources"),
                "ETF 資料概況 master sources",
            )
        ),
        "latest_import_at": (
            validate_optional_iso_datetime(
                master.get(
                    "latest_import_at"
                ),
                (
                    "ETF 資料概況 master "
                    "latest_import_at"
                ),
            )
        ),
    }

    metric_code = (
        validate_required_text(
            performance.get(
                "metric_code"
            ),
            (
                "ETF 資料概況 performance "
                "metric_code"
            ),
        ).upper()
    )

    if metric_code != "PRICE_RETURN":
        raise APIResponseError(
            "ETF 資料概況目前只支援 "
            "PRICE_RETURN"
        )

    raw_periods = performance.get(
        "available_periods"
    )

    if not isinstance(raw_periods, list):
        raise APIResponseError(
            "ETF 資料概況 performance "
            "available_periods 必須是陣列"
        )

    available_periods: list[str] = []
    seen_periods: set[str] = set()

    for index, value in enumerate(
        raw_periods,
        start=1,
    ):
        period_code = (
            validate_required_text(
                value,
                (
                    "ETF 資料概況 performance "
                    "available_periods 第 "
                    f"{index} 筆"
                ),
            ).upper()
        )

        if (
            period_code
            not in SUPPORTED_PERFORMANCE_PERIODS
        ):
            raise APIResponseError(
                "ETF 資料概況包含不支援"
                f"的績效期間：{period_code}"
            )

        if period_code in seen_periods:
            raise APIResponseError(
                "ETF 資料概況包含重複"
                f"績效期間：{period_code}"
            )

        seen_periods.add(
            period_code
        )
        available_periods.append(
            period_code
        )

    performance_record_count = (
        validate_non_negative_integer(
            performance.get(
                "record_count"
            ),
            (
                "ETF 資料概況 performance "
                "record_count"
            ),
        )
    )

    latest_as_of_date = (
        validate_optional_iso_date(
            performance.get(
                "latest_as_of_date"
            ),
            (
                "ETF 資料概況 performance "
                "latest_as_of_date"
            ),
        )
    )

    if (
        performance_record_count == 0
        and (
            available_periods
            or latest_as_of_date is not None
        )
    ):
        raise APIResponseError(
            "ETF 資料概況沒有績效紀錄時"
            "不得提供期間或最新日期"
        )

    validated_performance = {
        "metric_code": metric_code,
        "sources": (
            validate_etf_data_profile_sources(
                performance.get(
                    "sources"
                ),
                (
                    "ETF 資料概況 "
                    "performance sources"
                ),
            )
        ),
        "record_count": (
            performance_record_count
        ),
        "available_periods": (
            available_periods
        ),
        "latest_as_of_date": (
            latest_as_of_date
        ),
        "latest_import_at": (
            validate_optional_iso_datetime(
                performance.get(
                    "latest_import_at"
                ),
                (
                    "ETF 資料概況 "
                    "performance "
                    "latest_import_at"
                ),
            )
        ),
    }

    dividend_event_count = (
        validate_non_negative_integer(
            dividends.get(
                "event_count"
            ),
            (
                "ETF 資料概況 dividends "
                "event_count"
            ),
        )
    )

    latest_event_date = (
        validate_optional_iso_date(
            dividends.get(
                "latest_event_date"
            ),
            (
                "ETF 資料概況 dividends "
                "latest_event_date"
            ),
        )
    )

    if (
        dividend_event_count == 0
        and latest_event_date is not None
    ):
        raise APIResponseError(
            "ETF 資料概況沒有配息事件時"
            "不得提供最新事件日期"
        )

    validated_dividends = {
        "sources": (
            validate_etf_data_profile_sources(
                dividends.get(
                    "sources"
                ),
                (
                    "ETF 資料概況 "
                    "dividends sources"
                ),
            )
        ),
        "event_count": (
            dividend_event_count
        ),
        "latest_event_date": (
            latest_event_date
        ),
        "latest_import_at": (
            validate_optional_iso_datetime(
                dividends.get(
                    "latest_import_at"
                ),
                (
                    "ETF 資料概況 "
                    "dividends "
                    "latest_import_at"
                ),
            )
        ),
    }

    actual_component_count = (
        validate_non_negative_integer(
            actual_dividend.get(
                "actual_component_event_count"
            ),
            (
                "ETF 資料概況 actual_dividend "
                "actual_component_event_count"
            ),
        )
    )

    actual_76w_count = (
        validate_non_negative_integer(
            actual_dividend.get(
                "actual_76w_event_count"
            ),
            (
                "ETF 資料概況 actual_dividend "
                "actual_76w_event_count"
            ),
        )
    )

    source_document_count = (
        validate_non_negative_integer(
            actual_dividend.get(
                "source_document_event_count"
            ),
            (
                "ETF 資料概況 actual_dividend "
                "source_document_event_count"
            ),
        )
    )

    if actual_76w_count > actual_component_count:
        raise APIResponseError(
            "ETF 資料概況正式 76W 事件數"
            "不可大於 ACTUAL 事件數"
        )

    if source_document_count > actual_component_count:
        raise APIResponseError(
            "ETF 資料概況正式來源文件事件數"
            "不可大於 ACTUAL 事件數"
        )

    validated_actual_dividend = {
        "sources": (
            validate_etf_data_profile_sources(
                actual_dividend.get(
                    "sources"
                ),
                (
                    "ETF 資料概況 "
                    "actual_dividend sources"
                ),
            )
        ),
        "actual_component_event_count": (
            actual_component_count
        ),
        "actual_76w_event_count": (
            actual_76w_count
        ),
        "source_document_event_count": (
            source_document_count
        ),
        "latest_source_document_date": (
            validate_optional_iso_date(
                actual_dividend.get(
                    "latest_source_document_date"
                ),
                (
                    "ETF 資料概況 "
                    "actual_dividend "
                    "latest_source_document_date"
                ),
            )
        ),
        "latest_import_at": (
            validate_optional_iso_datetime(
                actual_dividend.get(
                    "latest_import_at"
                ),
                (
                    "ETF 資料概況 "
                    "actual_dividend "
                    "latest_import_at"
                ),
            )
        ),
    }

    return {
        "etf_code": etf_code,
        "master": validated_master,
        "performance": (
            validated_performance
        ),
        "dividends": (
            validated_dividends
        ),
        "actual_dividend": (
            validated_actual_dividend
        ),
    }


def fetch_etf_data_profile(
    api_base_url: str,
    code: str,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單一 ETF 的資料來源與新鮮度。"""

    normalized_code = (
        code.strip().upper()
    )

    if not normalized_code:
        raise ValueError(
            "ETF 代號不可為空白"
        )

    encoded_code = quote(
        normalized_code,
        safe="",
    )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            "/api/v1/etfs/"
            f"{encoded_code}/data-profile"
        ),
        operation_name="ETF 資料概況查詢",
        timeout_seconds=timeout_seconds,
    )

    profile = validate_etf_data_profile(
        payload
    )

    if (
        profile["etf_code"]
        != normalized_code
    ):
        raise APIResponseError(
            "ETF 資料概況回傳代號"
            "與查詢條件不一致"
        )

    return profile
