"""前端 API 回應的共用驗證函式。"""

from frontend.api.errors import APIResponseError


def validate_non_negative_integer(
    value: object,
    field_name: str,
) -> int:
    """驗證非負整數。"""

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        raise APIResponseError(
            f"{field_name} 必須是非負整數"
        )

    return value


def validate_positive_integer(
    value: object,
    field_name: str,
) -> int:
    """驗證正整數。"""

    normalized_value = (
        validate_non_negative_integer(
            value,
            field_name,
        )
    )

    if normalized_value < 1:
        raise APIResponseError(
            f"{field_name} 必須大於 0"
        )

    return normalized_value


def validate_optional_number(
    value: object,
    field_name: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float | None:
    """驗證可能為空值的數值。"""

    if value is None:
        return None

    if (
        not isinstance(
            value,
            (
                int,
                float,
            ),
        )
        or isinstance(value, bool)
    ):
        raise APIResponseError(
            f"{field_name} 必須是數值"
        )

    normalized_value = float(value)

    if (
        minimum is not None
        and normalized_value < minimum
    ):
        raise APIResponseError(
            f"{field_name} 不得小於 "
            f"{minimum}"
        )

    if (
        maximum is not None
        and normalized_value > maximum
    ):
        raise APIResponseError(
            f"{field_name} 不得大於 "
            f"{maximum}"
        )

    return normalized_value


def validate_required_text(
    value: object,
    field_name: str,
) -> str:
    """驗證必要文字欄位。"""

    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise APIResponseError(
            f"{field_name} 必須是非空白文字"
        )

    return value.strip()


def validate_optional_dividend_period(
    value: object,
    field_name: str,
) -> str | None:
    """驗證官方收益所屬年季 YYYYQn。"""

    if value is None:
        return None

    normalized_value = validate_required_text(
        value,
        field_name,
    ).upper()

    if not (
        len(normalized_value) == 6
        and normalized_value[:4].isdigit()
        and normalized_value[4] == "Q"
        and normalized_value[5] in "1234"
    ):
        raise APIResponseError(
            f"{field_name} 必須是 YYYYQ1–Q4"
        )

    return normalized_value