"""前端 ETF 比較查詢與回應驗證。"""

from typing import Any

from frontend.api.data_profile import validate_etf_data_profile
from frontend.api.errors import APIResponseError
from frontend.api.etfs import validate_etf_item
from frontend.api.normalizers import (
    COMPARISON_PERIODS,
    normalize_etf_comparison_codes,
)
from frontend.api.performance import validate_etf_performance_item
from frontend.api.transport import get_json
from frontend.api.validators import (
    validate_non_negative_integer,
    validate_optional_iso_date,
    validate_optional_number,
    validate_positive_integer,
    validate_required_text,
)


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
