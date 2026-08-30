"""前端 ETF 配息查詢與回應驗證。"""

from typing import Any
from urllib.parse import quote

from frontend.api.errors import APIResponseError
from frontend.api.normalizers import (
    SUPPORTED_DIVIDEND_COMPONENT_BASES,
    normalize_component_basis,
)
from frontend.api.transport import get_json
from frontend.api.validators import (
    validate_non_negative_integer,
    validate_optional_dividend_period,
    validate_optional_iso_date,
    validate_optional_number,
    validate_positive_integer,
    validate_required_text,
)


SUPPORTED_DIVIDEND_YIELD_BASES = (
    "OFFICIAL",
    "CALCULATED",
)


def validate_dividend_event_item(
    item: object,
    index: int,
    require_summary_fields: bool = True,
) -> dict[str, Any]:
    """驗證單筆 ETF 配息事件。"""

    if not isinstance(item, dict):
        raise APIResponseError(
            f"配息歷史第 {index} 筆"
            "不是 JSON 物件"
        )

    required_fields = {
        "dividend_id",
        "source_event_id",
        "announcement_date",
        "ex_dividend_date",
        "record_date",
        "payment_date",
        "amount_per_unit",
        "currency",
        "source_id",
    }

    if require_summary_fields:
        required_fields.update(
            {
                "distribution_period",
                "distribution_period_source_id",
                "yield_pct",
                "yield_basis",
                "yield_source_id",
                "reference_trade_date",
                "reference_close_price",
            }
        )

    missing_fields = (
        required_fields - item.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            f"配息歷史第 {index} 筆"
            f"缺少欄位：{missing_text}"
        )

    currency = validate_required_text(
        item["currency"],
        (
            f"配息歷史第 {index} 筆 "
            "currency"
        ),
    ).upper()

    if len(currency) != 3:
        raise APIResponseError(
            f"配息歷史第 {index} 筆 "
            "currency 必須是 3 個字元"
        )

    amount_per_unit = (
        validate_optional_number(
            item["amount_per_unit"],
            (
                f"配息歷史第 {index} 筆 "
                "amount_per_unit"
            ),
            minimum=0,
        )
    )

    if amount_per_unit is None:
        raise APIResponseError(
            f"配息歷史第 {index} 筆 "
            "amount_per_unit 不可為空值"
        )

    distribution_period = (
        validate_optional_dividend_period(
            item.get("distribution_period"),
            (
                f"配息歷史第 {index} 筆 "
                "distribution_period"
            ),
        )
    )

    raw_period_source = item.get(
        "distribution_period_source_id"
    )

    period_source = (
        validate_required_text(
            raw_period_source,
            (
                f"配息歷史第 {index} 筆 "
                "distribution_period_source_id"
            ),
        ).lower()
        if raw_period_source is not None
        else None
    )

    if (
        distribution_period is None
    ) != (
        period_source is None
    ):
        raise APIResponseError(
            f"配息歷史第 {index} 筆年季與來源不一致"
        )

    yield_pct = validate_optional_number(
        item.get("yield_pct"),
        f"配息歷史第 {index} 筆 yield_pct",
        minimum=0,
    )

    raw_yield_basis = item.get(
        "yield_basis"
    )
    yield_basis = (
        validate_required_text(
            raw_yield_basis,
            f"配息歷史第 {index} 筆 yield_basis",
        ).upper()
        if raw_yield_basis is not None
        else None
    )

    if (
        yield_basis is not None
        and yield_basis
        not in SUPPORTED_DIVIDEND_YIELD_BASES
    ):
        raise APIResponseError(
            f"配息歷史第 {index} 筆 yield_basis 不支援"
        )

    raw_yield_source = item.get(
        "yield_source_id"
    )
    yield_source = (
        validate_required_text(
            raw_yield_source,
            f"配息歷史第 {index} 筆 yield_source_id",
        ).lower()
        if raw_yield_source is not None
        else None
    )

    reference_trade_date = (
        validate_optional_iso_date(
            item.get("reference_trade_date"),
            (
                f"配息歷史第 {index} 筆 "
                "reference_trade_date"
            ),
        )
    )

    reference_close_price = (
        validate_optional_number(
            item.get("reference_close_price"),
            (
                f"配息歷史第 {index} 筆 "
                "reference_close_price"
            ),
            minimum=0.000000001,
        )
    )

    if yield_pct is None:
        if any(
            value is not None
            for value in (
                yield_basis,
                yield_source,
                reference_trade_date,
                reference_close_price,
            )
        ):
            raise APIResponseError(
                f"配息歷史第 {index} 筆殖利率來源不完整"
            )

    elif (
        yield_basis is None
        or yield_source is None
    ):
        raise APIResponseError(
            f"配息歷史第 {index} 筆殖利率缺少基礎或來源"
        )

    elif yield_basis == "CALCULATED" and (
        reference_trade_date is None
        or reference_close_price is None
    ):
        raise APIResponseError(
            f"配息歷史第 {index} 筆回退殖利率缺少價格基準"
        )

    elif yield_basis == "OFFICIAL" and (
        reference_trade_date is not None
        or reference_close_price is not None
    ):
        raise APIResponseError(
            f"配息歷史第 {index} 筆官方殖利率混入價格基準"
        )

    return {
        "dividend_id": (
            validate_positive_integer(
                item["dividend_id"],
                (
                    f"配息歷史第 {index} 筆 "
                    "dividend_id"
                ),
            )
        ),
        "source_event_id": (
            validate_required_text(
                item["source_event_id"],
                (
                    f"配息歷史第 {index} 筆 "
                    "source_event_id"
                ),
            )
        ),
        "announcement_date": (
            validate_optional_iso_date(
                item["announcement_date"],
                (
                    f"配息歷史第 {index} 筆 "
                    "announcement_date"
                ),
            )
        ),
        "ex_dividend_date": (
            validate_optional_iso_date(
                item["ex_dividend_date"],
                (
                    f"配息歷史第 {index} 筆 "
                    "ex_dividend_date"
                ),
            )
        ),
        "record_date": (
            validate_optional_iso_date(
                item["record_date"],
                (
                    f"配息歷史第 {index} 筆 "
                    "record_date"
                ),
            )
        ),
        "payment_date": (
            validate_optional_iso_date(
                item["payment_date"],
                (
                    f"配息歷史第 {index} 筆 "
                    "payment_date"
                ),
            )
        ),
        "amount_per_unit": amount_per_unit,
        "currency": currency,
        "source_id": (
            validate_required_text(
                item["source_id"],
                (
                    f"配息歷史第 {index} 筆 "
                    "source_id"
                ),
            ).lower()
        ),
        "distribution_period": (
            distribution_period
        ),
        "distribution_period_source_id": (
            period_source
        ),
        "yield_pct": yield_pct,
        "yield_basis": yield_basis,
        "yield_source_id": yield_source,
        "reference_trade_date": (
            reference_trade_date
        ),
        "reference_close_price": (
            reference_close_price
        ),
    }


def fetch_etf_dividends(
    api_base_url: str,
    code: str,
    limit: int = 20,
    offset: int = 0,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單一 ETF 的配息歷史。"""

    normalized_code = (
        code.strip().upper()
    )

    if not normalized_code:
        raise ValueError(
            "ETF 代號不可為空白"
        )

    if limit < 1 or limit > 100:
        raise ValueError(
            "limit 必須介於 1 到 100"
        )

    if offset < 0:
        raise ValueError(
            "offset 不得小於 0"
        )

    encoded_code = quote(
        normalized_code,
        safe="",
    )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/etfs/"
            f"{encoded_code}/dividends"
        ),
        operation_name=(
            f"ETF {normalized_code} "
            "配息歷史查詢"
        ),
        params={
            "limit": limit,
            "offset": offset,
        },
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "ETF 配息歷史回應必須是 JSON 物件"
        )

    response_code = validate_required_text(
        payload.get("etf_code"),
        "ETF 配息歷史 etf_code",
    ).upper()

    if response_code != normalized_code:
        raise APIResponseError(
            "ETF 配息歷史代號與查詢代號不一致"
        )

    items = payload.get("items")

    if not isinstance(items, list):
        raise APIResponseError(
            "ETF 配息歷史 items 格式不正確"
        )

    total = validate_non_negative_integer(
        payload.get("total"),
        "ETF 配息歷史 total",
    )

    response_limit = (
        validate_positive_integer(
            payload.get("limit"),
            "ETF 配息歷史 limit",
        )
    )

    response_offset = (
        validate_non_negative_integer(
            payload.get("offset"),
            "ETF 配息歷史 offset",
        )
    )

    if response_limit != limit:
        raise APIResponseError(
            "ETF 配息歷史回傳 limit "
            "與查詢條件不一致"
        )

    if response_offset != offset:
        raise APIResponseError(
            "ETF 配息歷史回傳 offset "
            "與查詢條件不一致"
        )

    validated_items = [
        validate_dividend_event_item(
            item,
            index,
        )
        for index, item in enumerate(
            items,
            start=1,
        )
    ]

    return {
        "etf_code": response_code,
        "total": total,
        "limit": response_limit,
        "offset": response_offset,
        "items": validated_items,
    }


def validate_monthly_income_month_item(
    item: object,
    index: int,
) -> dict[str, Any]:
    """驗證單一曆月的入帳分布。"""

    if not isinstance(item, dict):
        raise APIResponseError(
            f"每月領息第 {index} 筆不是 JSON 物件"
        )

    required_fields = {
        "month",
        "event_count",
        "observed_year_count",
        "total_amount_per_unit",
        "average_amount_per_event",
        "latest_payment_date",
    }

    missing_fields = (
        required_fields - item.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            f"每月領息第 {index} 筆缺少欄位："
            f"{missing_text}"
        )

    month = validate_positive_integer(
        item["month"],
        f"每月領息第 {index} 筆 month",
    )

    if month > 12:
        raise APIResponseError(
            f"每月領息第 {index} 筆 month "
            "不得大於 12"
        )

    event_count = validate_non_negative_integer(
        item["event_count"],
        f"每月領息第 {index} 筆 event_count",
    )

    observed_year_count = (
        validate_non_negative_integer(
            item["observed_year_count"],
            (
                f"每月領息第 {index} 筆 "
                "observed_year_count"
            ),
        )
    )

    if observed_year_count > event_count:
        raise APIResponseError(
            f"每月領息第 {index} 筆出現年度"
            "不得多於配息事件"
        )

    total_amount = validate_optional_number(
        item["total_amount_per_unit"],
        (
            f"每月領息第 {index} 筆 "
            "total_amount_per_unit"
        ),
        minimum=0,
    )

    average_amount = validate_optional_number(
        item["average_amount_per_event"],
        (
            f"每月領息第 {index} 筆 "
            "average_amount_per_event"
        ),
        minimum=0,
    )

    latest_payment_date = (
        validate_optional_iso_date(
            item["latest_payment_date"],
            (
                f"每月領息第 {index} 筆 "
                "latest_payment_date"
            ),
        )
    )

    if event_count == 0 and any(
        value is not None
        for value in (
            total_amount,
            average_amount,
            latest_payment_date,
        )
    ):
        raise APIResponseError(
            f"每月領息第 {index} 筆沒有事件時"
            "不得帶入金額或日期"
        )

    if event_count == 0 and observed_year_count != 0:
        raise APIResponseError(
            f"每月領息第 {index} 筆沒有事件時"
            "出現年度必須為 0"
        )

    if event_count > 0 and (
        observed_year_count == 0
        or latest_payment_date is None
    ):
        raise APIResponseError(
            f"每月領息第 {index} 筆有事件時"
            "必須帶入出現年度與最近入帳日"
        )

    return {
        "month": month,
        "event_count": event_count,
        "observed_year_count": (
            observed_year_count
        ),
        "total_amount_per_unit": total_amount,
        "average_amount_per_event": (
            average_amount
        ),
        "latest_payment_date": (
            latest_payment_date
        ),
    }


def validate_monthly_income_distribution(
    payload: object,
    *,
    expected_code: str,
    expected_lookback_years: int,
) -> dict[str, Any]:
    """驗證 ETF 每月領息分布回應。"""

    if not isinstance(payload, dict):
        raise APIResponseError(
            "ETF 每月領息回應必須是 JSON 物件"
        )

    required_fields = {
        "etf_code",
        "name",
        "date_basis",
        "lookback_years",
        "as_of_date",
        "window_start_date",
        "total_dividend_event_count",
        "dated_dividend_event_count",
        "missing_payment_date_count",
        "analysis_event_count",
        "covered_month_count",
        "covered_month_occurrence_count",
        "analysis_currency",
        "has_mixed_currencies",
        "total_amount_per_unit",
        "months",
    }

    missing_fields = (
        required_fields - payload.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            "ETF 每月領息回應缺少欄位："
            f"{missing_text}"
        )

    response_code = validate_required_text(
        payload["etf_code"],
        "ETF 每月領息 etf_code",
    ).upper()

    if response_code != expected_code:
        raise APIResponseError(
            "ETF 每月領息代號與查詢代號不一致"
        )

    date_basis = validate_required_text(
        payload["date_basis"],
        "ETF 每月領息 date_basis",
    ).upper()

    if date_basis != "PAYMENT_DATE":
        raise APIResponseError(
            "ETF 每月領息必須以 PAYMENT_DATE 為準"
        )

    lookback_years = validate_positive_integer(
        payload["lookback_years"],
        "ETF 每月領息 lookback_years",
    )

    if lookback_years != expected_lookback_years:
        raise APIResponseError(
            "ETF 每月領息回傳年數與查詢條件不一致"
        )

    total_event_count = (
        validate_non_negative_integer(
            payload[
                "total_dividend_event_count"
            ],
            (
                "ETF 每月領息 "
                "total_dividend_event_count"
            ),
        )
    )

    dated_event_count = (
        validate_non_negative_integer(
            payload[
                "dated_dividend_event_count"
            ],
            (
                "ETF 每月領息 "
                "dated_dividend_event_count"
            ),
        )
    )

    missing_payment_date_count = (
        validate_non_negative_integer(
            payload[
                "missing_payment_date_count"
            ],
            (
                "ETF 每月領息 "
                "missing_payment_date_count"
            ),
        )
    )

    analysis_event_count = (
        validate_non_negative_integer(
            payload["analysis_event_count"],
            "ETF 每月領息 analysis_event_count",
        )
    )

    covered_month_count = (
        validate_non_negative_integer(
            payload["covered_month_count"],
            "ETF 每月領息 covered_month_count",
        )
    )

    covered_occurrence_count = (
        validate_non_negative_integer(
            payload[
                "covered_month_occurrence_count"
            ],
            (
                "ETF 每月領息 "
                "covered_month_occurrence_count"
            ),
        )
    )

    if (
        dated_event_count
        + missing_payment_date_count
        != total_event_count
    ):
        raise APIResponseError(
            "ETF 每月領息事件總數不一致"
        )

    if analysis_event_count > dated_event_count:
        raise APIResponseError(
            "ETF 每月領息分析事件不可多於"
            "已有入帳日事件"
        )

    months_value = payload["months"]

    if not isinstance(months_value, list):
        raise APIResponseError(
            "ETF 每月領息 months 格式不正確"
        )

    if len(months_value) != 12:
        raise APIResponseError(
            "ETF 每月領息必須固定回傳 12 個月"
        )

    months = [
        validate_monthly_income_month_item(
            item,
            index,
        )
        for index, item in enumerate(
            months_value,
            start=1,
        )
    ]

    if [
        item["month"]
        for item in months
    ] != list(range(1, 13)):
        raise APIResponseError(
            "ETF 每月領息月份必須依 1 到 12 排列"
        )

    if analysis_event_count != sum(
        item["event_count"]
        for item in months
    ):
        raise APIResponseError(
            "ETF 每月領息分析事件與月份明細不一致"
        )

    if covered_month_count != sum(
        item["event_count"] > 0
        for item in months
    ):
        raise APIResponseError(
            "ETF 每月領息涵蓋月份與月份明細不一致"
        )

    if covered_occurrence_count != sum(
        item["observed_year_count"]
        for item in months
    ):
        raise APIResponseError(
            "ETF 每月領息涵蓋年月與月份明細不一致"
        )

    mixed_currencies = payload[
        "has_mixed_currencies"
    ]

    if not isinstance(
        mixed_currencies,
        bool,
    ):
        raise APIResponseError(
            "ETF 每月領息 has_mixed_currencies "
            "必須是布林值"
        )

    currency_value = payload[
        "analysis_currency"
    ]

    if currency_value is None:
        analysis_currency = None

    else:
        analysis_currency = (
            validate_required_text(
                currency_value,
                "ETF 每月領息 analysis_currency",
            ).upper()
        )

        if len(analysis_currency) != 3:
            raise APIResponseError(
                "ETF 每月領息 analysis_currency "
                "必須是 3 個字元"
            )

    total_amount = validate_optional_number(
        payload["total_amount_per_unit"],
        "ETF 每月領息 total_amount_per_unit",
        minimum=0,
    )

    if mixed_currencies and (
        analysis_currency is not None
        or total_amount is not None
        or any(
            item["total_amount_per_unit"]
            is not None
            or item[
                "average_amount_per_event"
            ] is not None
            for item in months
        )
    ):
        raise APIResponseError(
            "ETF 每月領息混合幣別不得加總金額"
        )

    if not mixed_currencies:
        if analysis_event_count == 0 and (
            analysis_currency is not None
            or total_amount is not None
        ):
            raise APIResponseError(
                "ETF 每月領息沒有分析事件時"
                "不得帶入幣別或總金額"
            )

        if analysis_event_count > 0 and (
            analysis_currency is None
            or total_amount is None
            or any(
                item["event_count"] > 0
                and (
                    item[
                        "total_amount_per_unit"
                    ] is None
                    or item[
                        "average_amount_per_event"
                    ] is None
                )
                for item in months
            )
        ):
            raise APIResponseError(
                "ETF 每月領息單一幣別事件"
                "必須帶入金額"
            )

    return {
        "etf_code": response_code,
        "name": validate_required_text(
            payload["name"],
            "ETF 每月領息 name",
        ),
        "date_basis": date_basis,
        "lookback_years": lookback_years,
        "as_of_date": (
            validate_optional_iso_date(
                payload["as_of_date"],
                "ETF 每月領息 as_of_date",
            )
        ),
        "window_start_date": (
            validate_optional_iso_date(
                payload["window_start_date"],
                "ETF 每月領息 window_start_date",
            )
        ),
        "total_dividend_event_count": (
            total_event_count
        ),
        "dated_dividend_event_count": (
            dated_event_count
        ),
        "missing_payment_date_count": (
            missing_payment_date_count
        ),
        "analysis_event_count": (
            analysis_event_count
        ),
        "covered_month_count": (
            covered_month_count
        ),
        "covered_month_occurrence_count": (
            covered_occurrence_count
        ),
        "analysis_currency": (
            analysis_currency
        ),
        "has_mixed_currencies": (
            mixed_currencies
        ),
        "total_amount_per_unit": (
            total_amount
        ),
        "months": months,
    }


def fetch_etf_monthly_income(
    api_base_url: str,
    code: str,
    lookback_years: int = 3,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單一 ETF 的實際入帳月份分布。"""

    normalized_code = code.strip().upper()

    if not normalized_code:
        raise ValueError(
            "ETF 代號不可為空白"
        )

    if (
        not isinstance(lookback_years, int)
        or isinstance(lookback_years, bool)
        or lookback_years < 1
        or lookback_years > 10
    ):
        raise ValueError(
            "lookback_years 必須介於 1 到 10"
        )

    encoded_code = quote(
        normalized_code,
        safe="",
    )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/etfs/{encoded_code}/"
            "monthly-income"
        ),
        operation_name=(
            f"ETF {normalized_code} "
            "每月領息查詢"
        ),
        params={
            "lookback_years": lookback_years,
        },
        timeout_seconds=timeout_seconds,
    )

    return validate_monthly_income_distribution(
        payload,
        expected_code=normalized_code,
        expected_lookback_years=(
            lookback_years
        ),
    )


def validate_dividend_component_item(
    item: object,
    index: int,
    expected_dividend_id: int,
) -> dict[str, Any]:
    """驗證單筆配息組成。"""

    if not isinstance(item, dict):
        raise APIResponseError(
            f"配息組成第 {index} 筆"
            "不是 JSON 物件"
        )

    required_fields = {
        "component_id",
        "dividend_id",
        "component_code",
        "component_basis",
        "component_name",
        "amount_per_unit",
        "ratio_pct",
        "source_id",
    }

    missing_fields = (
        required_fields - item.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            f"配息組成第 {index} 筆"
            f"缺少欄位：{missing_text}"
        )

    dividend_id = validate_positive_integer(
        item["dividend_id"],
        (
            f"配息組成第 {index} 筆 "
            "dividend_id"
        ),
    )

    if dividend_id != expected_dividend_id:
        raise APIResponseError(
            "配息組成包含其他配息事件資料"
        )

    component_basis = (
        validate_required_text(
            item["component_basis"],
            (
                f"配息組成第 {index} 筆 "
                "component_basis"
            ),
        ).upper()
    )

    if (
        component_basis
        not in SUPPORTED_DIVIDEND_COMPONENT_BASES
    ):
        raise APIResponseError(
            f"配息組成第 {index} 筆 "
            "component_basis 格式不正確"
        )

    component_name = (
        item["component_name"]
    )

    if component_name is not None:
        component_name = (
            validate_required_text(
                component_name,
                (
                    f"配息組成第 {index} 筆 "
                    "component_name"
                ),
            )
        )

    return {
        "component_id": (
            validate_positive_integer(
                item["component_id"],
                (
                    f"配息組成第 {index} 筆 "
                    "component_id"
                ),
            )
        ),
        "dividend_id": dividend_id,
        "component_code": (
            validate_required_text(
                item["component_code"],
                (
                    f"配息組成第 {index} 筆 "
                    "component_code"
                ),
            ).upper()
        ),
        "component_basis": (
            component_basis
        ),
        "component_name": (
            component_name
        ),
        "amount_per_unit": (
            validate_optional_number(
                item["amount_per_unit"],
                (
                    f"配息組成第 {index} 筆 "
                    "amount_per_unit"
                ),
                minimum=0,
            )
        ),
        "ratio_pct": (
            validate_optional_number(
                item["ratio_pct"],
                (
                    f"配息組成第 {index} 筆 "
                    "ratio_pct"
                ),
                minimum=0,
                maximum=100,
            )
        ),
        "source_id": (
            validate_required_text(
                item["source_id"],
                (
                    f"配息組成第 {index} 筆 "
                    "source_id"
                ),
            ).lower()
        ),
    }


def fetch_dividend_detail(
    api_base_url: str,
    dividend_id: int,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單次配息事件及全部組成。"""

    if dividend_id < 1:
        raise ValueError(
            "dividend_id 必須大於 0"
        )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/dividends/"
            f"{dividend_id}"
        ),
        operation_name=(
            f"配息事件 {dividend_id} 查詢"
        ),
        timeout_seconds=timeout_seconds,
    )

    event = validate_dividend_event_item(
        payload,
        index=1,
    )

    if (
        event["dividend_id"]
        != dividend_id
    ):
        raise APIResponseError(
            "配息事件 ID 與查詢 ID 不一致"
        )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "配息事件回應必須是 JSON 物件"
        )

    etf_code = validate_required_text(
        payload.get("etf_code"),
        "配息事件 etf_code",
    ).upper()

    components = payload.get(
        "components"
    )

    if not isinstance(components, list):
        raise APIResponseError(
            "配息事件 components 格式不正確"
        )

    validated_components = [
        validate_dividend_component_item(
            item=item,
            index=index,
            expected_dividend_id=(
                dividend_id
            ),
        )
        for index, item in enumerate(
            components,
            start=1,
        )
    ]

    selected_basis = payload.get(
        "selected_component_basis"
    )
    if selected_basis is not None:
        selected_basis = validate_required_text(
            selected_basis,
            "配息事件 selected_component_basis",
        ).upper()
        if selected_basis not in {
            "ACTUAL",
            "ESTIMATED_FALLBACK",
        }:
            raise APIResponseError(
                "配息事件 selected_component_basis 不支援"
            )

    selected_components_value = payload.get(
        "selected_components"
    )
    if not isinstance(
        selected_components_value,
        list,
    ):
        raise APIResponseError(
            "配息事件 selected_components 格式不正確"
        )
    selected_components = [
        validate_dividend_component_item(
            item=item,
            index=index,
            expected_dividend_id=dividend_id,
        )
        for index, item in enumerate(
            selected_components_value,
            start=1,
        )
    ]
    expected_source_basis = (
        "ACTUAL"
        if selected_basis == "ACTUAL"
        else "ESTIMATED"
        if selected_basis == "ESTIMATED_FALLBACK"
        else None
    )
    if expected_source_basis is None:
        if selected_components:
            raise APIResponseError(
                "配息事件缺少選定組成基礎"
            )
    elif (
        not selected_components
        or any(
            item["component_basis"]
            != expected_source_basis
            for item in selected_components
        )
    ):
        raise APIResponseError(
            "配息事件選定組成與資料基礎不一致"
        )

    return {
        **event,
        "etf_code": etf_code,
        "components": validated_components,
        "selected_component_basis": selected_basis,
        "selected_components": selected_components,
    }


def fetch_dividend_components(
    api_base_url: str,
    dividend_id: int,
    component_basis: str | None = None,
    component_code: str | None = None,
    source_id: str | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單次配息的篩選後組成。"""

    if dividend_id < 1:
        raise ValueError(
            "dividend_id 必須大於 0"
        )

    normalized_basis = (
        normalize_component_basis(
            component_basis
        )
    )

    params: dict[str, str | int] = {}

    if normalized_basis is not None:
        params["component_basis"] = (
            normalized_basis
        )

    if component_code is not None:
        normalized_component_code = (
            component_code.strip().upper()
        )

        if not normalized_component_code:
            raise ValueError(
                "component_code 不可為空白"
            )

        params["component_code"] = (
            normalized_component_code
        )

    if source_id is not None:
        normalized_source_id = (
            source_id.strip().lower()
        )

        if not normalized_source_id:
            raise ValueError(
                "source_id 不可為空白"
            )

        params["source_id"] = (
            normalized_source_id
        )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/dividends/"
            f"{dividend_id}/components"
        ),
        operation_name=(
            f"配息事件 {dividend_id} "
            "組成查詢"
        ),
        params=params,
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "配息組成回應必須是 JSON 物件"
        )

    response_dividend_id = (
        validate_positive_integer(
            payload.get("dividend_id"),
            "配息組成 dividend_id",
        )
    )

    if response_dividend_id != dividend_id:
        raise APIResponseError(
            "配息組成回傳事件 ID "
            "與查詢 ID 不一致"
        )

    items = payload.get("items")

    if not isinstance(items, list):
        raise APIResponseError(
            "配息組成 items 格式不正確"
        )

    total = validate_non_negative_integer(
        payload.get("total"),
        "配息組成 total",
    )

    validated_items = [
        validate_dividend_component_item(
            item=item,
            index=index,
            expected_dividend_id=(
                dividend_id
            ),
        )
        for index, item in enumerate(
            items,
            start=1,
        )
    ]

    if total != len(
        validated_items
    ):
        raise APIResponseError(
            "配息組成 total 與 items "
            "筆數不一致"
        )

    return {
        "dividend_id": (
            response_dividend_id
        ),
        "total": total,
        "items": validated_items,
    }
