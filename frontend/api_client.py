"""Streamlit 前端使用的 FastAPI Client。"""

from typing import Any
from urllib.parse import quote

import httpx

from frontend.api.errors import (
    APIClientError,
    APIConnectionError,
    APIResourceNotFoundError,
    APIResponseError,
)
from frontend.api.etfs import (
    fetch_etf_by_code,
    fetch_etfs,
    validate_etf_item,
)
from frontend.api.normalizers import (
    COMPARISON_PERIODS,
    SUPPORTED_DIVIDEND_COMPONENT_BASES,
    SUPPORTED_DIVIDEND_REVIEW_ISSUE_TYPES,
    SUPPORTED_DIVIDEND_REVIEW_STATUSES,
    SUPPORTED_PERFORMANCE_METRICS,
    SUPPORTED_PERFORMANCE_PERIODS,
    normalize_component_basis,
    normalize_dividend_review_issue_type,
    normalize_dividend_review_status,
    normalize_etf_comparison_codes,
    normalize_performance_metric,
    normalize_performance_period,
)
from frontend.api.dividend_quality import (
    fetch_actual_dividend_coverage,
    fetch_dividend_review_queue,
    fetch_dividend_review_queue_item,
    fetch_etf_actual_76w,
    validate_actual_76w_item,
    validate_actual_dividend_coverage,
    validate_dividend_review_queue_item,
)
from frontend.api.dividends import (
    SUPPORTED_DIVIDEND_YIELD_BASES,
    fetch_dividend_components,
    fetch_dividend_detail,
    fetch_etf_dividends,
    fetch_etf_monthly_income,
    validate_dividend_component_item,
    validate_dividend_event_item,
    validate_monthly_income_distribution,
    validate_monthly_income_month_item,
)
from frontend.api.performance import (
    fetch_etf_performance,
    fetch_multi_period_performance_ranking,
    fetch_performance_ranking,
    validate_etf_performance_item,
    validate_multi_period_ranking_item,
    validate_performance_ranking_item,
    validate_return_pct,
)
from frontend.api.system_overview import (
    SYSTEM_OVERVIEW_BATCH_STATUSES,
    SYSTEM_OVERVIEW_PERIODS,
    fetch_system_overview,
    validate_overview_coverage_pct,
    validate_system_overview,
    validate_system_overview_batch,
    validate_system_overview_dividends,
    validate_system_overview_etfs,
    validate_system_overview_performance,
)
from frontend.api.transport import (
    extract_response_detail,
    get_json,
)

from frontend.api.validators import (
    validate_non_negative_integer,
    validate_optional_dividend_period,
    validate_optional_iso_date,
    validate_optional_iso_datetime,
    validate_optional_number,
    validate_performance_date,
    validate_positive_integer,
    validate_required_iso_datetime,
    validate_required_text,
)


def fetch_api_health(
    api_base_url: str,
    timeout_seconds: float = 5.0,
) -> dict[str, str]:
    """讀取 FastAPI 健康狀態。

    Args:
        api_base_url:
            FastAPI Base URL。
        timeout_seconds:
            HTTP 請求逾時秒數。

    Returns:
        dict[str, str]:
            FastAPI 健康狀態。

    Raises:
        APIConnectionError:
            無法連接 FastAPI。
        APIResponseError:
            FastAPI 回應格式不正確。
    """

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path="/health",
        operation_name="FastAPI 健康檢查",
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "FastAPI 健康檢查格式不正確"
        )

    status_value = payload.get("status")

    if status_value != "healthy":
        raise APIResponseError(
            "FastAPI 狀態不是 healthy"
        )

    return {
        "status": str(status_value),
    }


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


def validate_etf_comparison(
    payload: object,
) -> dict[str, Any]:
    """驗證 ETF 比較 API 回應。"""

    if not isinstance(payload, dict):
        raise APIResponseError(
            "ETF 比較回應必須是 JSON 物件"
        )

    raw_codes = payload.get("codes")
    periods = payload.get("periods")
    items = payload.get("items")

    if not isinstance(raw_codes, list):
        raise APIResponseError(
            "ETF 比較 codes 格式不正確"
        )

    try:
        codes = normalize_etf_comparison_codes(
            [str(value) for value in raw_codes]
        )

    except ValueError as error:
        raise APIResponseError(
            str(error)
        ) from error

    metric_code = str(
        payload.get("metric_code", "")
    ).strip().upper()

    if metric_code != "PRICE_RETURN":
        raise APIResponseError(
            "ETF 比較目前只接受 PRICE_RETURN"
        )

    if (
        not isinstance(periods, list)
        or [
            str(value).strip().upper()
            for value in periods
        ]
        != list(COMPARISON_PERIODS)
    ):
        raise APIResponseError(
            "ETF 比較期間必須依序為 1M、3M、6M、1Y"
        )

    if (
        not isinstance(items, list)
        or len(items) != len(codes)
    ):
        raise APIResponseError(
            "ETF 比較 items 數量與 codes 不一致"
        )

    validated_items: list[
        dict[str, Any]
    ] = []

    for index, item in enumerate(
        items,
        start=1,
    ):
        if not isinstance(item, dict):
            raise APIResponseError(
                f"ETF 比較第 {index} 筆格式不正確"
            )

        etf = validate_etf_item(
            item.get("etf"),
            index,
        )

        expected_code = codes[index - 1]

        if etf["code"] != expected_code:
            raise APIResponseError(
                "ETF 比較項目順序與 codes 不一致"
            )

        performance_items = item.get(
            "performance_items"
        )

        if not isinstance(
            performance_items,
            list,
        ):
            raise APIResponseError(
                "ETF 比較 performance_items 格式不正確"
            )

        validated_performance = [
            validate_etf_performance_item(
                performance_item,
                performance_index,
                metric_code,
            )
            for performance_index, performance_item in enumerate(
                performance_items,
                start=1,
            )
        ]

        period_codes = [
            performance_item[
                "period_code"
            ]
            for performance_item in (
                validated_performance
            )
        ]

        if len(period_codes) != len(
            set(period_codes)
        ):
            raise APIResponseError(
                "ETF 比較績效包含重複期間"
            )

        validated_performance.sort(
            key=lambda value: (
                COMPARISON_PERIODS.index(
                    value["period_code"]
                )
            )
        )

        dividend = item.get("dividend")
        actual_76w = item.get(
            "actual_76w"
        )
        completeness = item.get(
            "completeness"
        )

        if not isinstance(dividend, dict):
            raise APIResponseError(
                "ETF 比較 dividend 格式不正確"
            )

        event_count = (
            validate_non_negative_integer(
                dividend.get("event_count"),
                "ETF 比較 event_count",
            )
        )

        latest_event_date = (
            validate_optional_iso_date(
                dividend.get(
                    "latest_event_date"
                ),
                "ETF 比較 latest_event_date",
            )
        )

        latest_amount = (
            validate_optional_number(
                dividend.get(
                    "latest_amount_per_unit"
                ),
                "ETF 比較 latest_amount_per_unit",
                minimum=0,
            )
        )

        currency = dividend.get(
            "currency"
        )

        if currency is not None:
            currency = validate_required_text(
                currency,
                "ETF 比較 currency",
            ).upper()

            if len(currency) != 3:
                raise APIResponseError(
                    "ETF 比較 currency 必須是 3 個字元"
                )

        if event_count == 0 and any(
            value is not None
            for value in (
                latest_event_date,
                latest_amount,
                currency,
            )
        ):
            raise APIResponseError(
                "沒有配息事件時不得提供最新配息資料"
            )

        if not isinstance(actual_76w, dict):
            raise APIResponseError(
                "ETF 比較 actual_76w 格式不正確"
            )

        record_count = (
            validate_non_negative_integer(
                actual_76w.get(
                    "record_count"
                ),
                "ETF 比較 76W record_count",
            )
        )
        full_count = (
            validate_non_negative_integer(
                actual_76w.get(
                    "full_76w_count"
                ),
                "ETF 比較 76W full_76w_count",
            )
        )

        if full_count > record_count:
            raise APIResponseError(
                "100% 76W 次數不可大於 76W 紀錄數"
            )

        latest_ratio = validate_optional_number(
            actual_76w.get(
                "latest_ratio_pct"
            ),
            "ETF 比較 latest_ratio_pct",
            minimum=0,
            maximum=100,
        )
        average_ratio = validate_optional_number(
            actual_76w.get(
                "average_ratio_pct"
            ),
            "ETF 比較 average_ratio_pct",
            minimum=0,
            maximum=100,
        )

        if record_count == 0 and any(
            value is not None
            for value in (
                latest_ratio,
                average_ratio,
            )
        ):
            raise APIResponseError(
                "沒有 76W 紀錄時比例必須為空值"
            )

        profile = validate_etf_data_profile(
            item.get("data_profile")
        )

        if profile["etf_code"] != expected_code:
            raise APIResponseError(
                "ETF 比較資料概況代號不一致"
            )

        if not isinstance(
            completeness,
            dict,
        ):
            raise APIResponseError(
                "ETF 比較 completeness 格式不正確"
            )

        available_count = (
            validate_non_negative_integer(
                completeness.get(
                    "available_section_count"
                ),
                "ETF 比較 available_section_count",
            )
        )
        total_count = validate_positive_integer(
            completeness.get(
                "total_section_count"
            ),
            "ETF 比較 total_section_count",
        )
        score_pct = validate_optional_number(
            completeness.get("score_pct"),
            "ETF 比較 score_pct",
            minimum=0,
            maximum=100,
        )

        available_sections = completeness.get(
            "available_sections"
        )
        missing_sections = completeness.get(
            "missing_sections"
        )

        if (
            not isinstance(
                available_sections,
                list,
            )
            or not isinstance(
                missing_sections,
                list,
            )
        ):
            raise APIResponseError(
                "ETF 比較完整度區塊格式不正確"
            )

        available_sections = [
            validate_required_text(
                value,
                "ETF 比較 available_sections",
            )
            for value in available_sections
        ]
        missing_sections = [
            validate_required_text(
                value,
                "ETF 比較 missing_sections",
            )
            for value in missing_sections
        ]

        if (
            available_count
            != len(available_sections)
            or total_count
            != (
                len(available_sections)
                + len(missing_sections)
            )
        ):
            raise APIResponseError(
                "ETF 比較完整度計數不一致"
            )

        expected_score = round(
            available_count
            / total_count
            * 100,
            6,
        )

        if (
            score_pct is None
            or abs(
                score_pct - expected_score
            )
            > 0.000001
        ):
            raise APIResponseError(
                "ETF 比較完整度百分比不一致"
            )

        validated_items.append(
            {
                "etf": etf,
                "performance_items": (
                    validated_performance
                ),
                "dividend": {
                    "event_count": event_count,
                    "latest_event_date": (
                        latest_event_date
                    ),
                    "latest_amount_per_unit": (
                        latest_amount
                    ),
                    "currency": currency,
                },
                "actual_76w": {
                    "record_count": record_count,
                    "full_76w_count": (
                        full_count
                    ),
                    "latest_ratio_pct": (
                        latest_ratio
                    ),
                    "average_ratio_pct": (
                        average_ratio
                    ),
                },
                "data_profile": profile,
                "completeness": {
                    "available_section_count": (
                        available_count
                    ),
                    "total_section_count": (
                        total_count
                    ),
                    "score_pct": score_pct,
                    "available_sections": (
                        available_sections
                    ),
                    "missing_sections": (
                        missing_sections
                    ),
                },
            }
        )

    return {
        "codes": list(codes),
        "metric_code": metric_code,
        "periods": list(
            COMPARISON_PERIODS
        ),
        "items": validated_items,
    }


def fetch_etf_comparison(
    api_base_url: str,
    codes: list[str] | tuple[str, ...],
    timeout_seconds: float = 15.0,
) -> dict[str, Any]:
    """取得 2 至 4 檔 ETF 的聚合比較資料。"""

    normalized_codes = (
        normalize_etf_comparison_codes(
            codes
        )
    )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            "/api/v1/etfs/comparison"
        ),
        operation_name="ETF 比較查詢",
        params={
            "codes": ",".join(
                normalized_codes
            ),
        },
        timeout_seconds=timeout_seconds,
    )

    result = validate_etf_comparison(
        payload
    )

    if tuple(result["codes"]) != (
        normalized_codes
    ):
        raise APIResponseError(
            "ETF 比較回傳代號與查詢條件不一致"
        )

    return result
