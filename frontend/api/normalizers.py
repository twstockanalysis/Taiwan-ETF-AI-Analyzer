"""前端 API 請求參數的共用正規化函式。"""


SUPPORTED_PERFORMANCE_PERIODS = (
    "1M",
    "3M",
    "6M",
    "1Y",
)

SUPPORTED_PERFORMANCE_METRICS = (
    "PRICE_RETURN",
    "TOTAL_RETURN",
    "NAV_RETURN",
)

SUPPORTED_DIVIDEND_COMPONENT_BASES = (
    "ESTIMATED",
    "ACTUAL",
)

SUPPORTED_DIVIDEND_REVIEW_STATUSES = (
    "PENDING",
    "IN_REVIEW",
    "RESOLVED",
    "SKIPPED",
)

SUPPORTED_DIVIDEND_REVIEW_ISSUE_TYPES = (
    "MISSING_ACTUAL_COMPONENTS",
    "MISSING_SOURCE_DOCUMENT",
)

COMPARISON_PERIODS = (
    "1M",
    "3M",
    "6M",
    "1Y",
)


def normalize_performance_period(
    value: str,
) -> str:
    """正規化前端使用的績效期間。"""

    normalized_value = value.strip().upper()

    if (
        normalized_value
        not in SUPPORTED_PERFORMANCE_PERIODS
    ):
        raise ValueError(
            "period 必須是 "
            "1M、3M、6M 或 1Y"
        )

    return normalized_value


def normalize_performance_metric(
    value: str,
) -> str:
    """正規化前端使用的績效類型。"""

    normalized_value = value.strip().upper()

    if (
        normalized_value
        not in SUPPORTED_PERFORMANCE_METRICS
    ):
        raise ValueError(
            "metric 必須是 "
            "PRICE_RETURN、TOTAL_RETURN "
            "或 NAV_RETURN"
        )

    return normalized_value


def normalize_component_basis(
    value: str | None,
) -> str | None:
    """正規化配息組成資訊基礎。"""

    if value is None:
        return None

    normalized_value = (
        value.strip().upper()
    )

    if (
        normalized_value
        not in SUPPORTED_DIVIDEND_COMPONENT_BASES
    ):
        raise ValueError(
            "component_basis 必須是 "
            "ESTIMATED 或 ACTUAL"
        )

    return normalized_value


def normalize_dividend_review_status(
    value: str | None,
) -> str | None:
    """正規化正式配息審核狀態。"""

    if value is None:
        return None

    normalized_value = value.strip().upper()

    if (
        normalized_value
        not in SUPPORTED_DIVIDEND_REVIEW_STATUSES
    ):
        raise ValueError(
            "status 必須是 PENDING、IN_REVIEW、"
            "RESOLVED 或 SKIPPED"
        )

    return normalized_value


def normalize_dividend_review_issue_type(
    value: str | None,
) -> str | None:
    """正規化正式配息缺失類型。"""

    if value is None:
        return None

    normalized_value = value.strip().upper()

    if (
        normalized_value
        not in SUPPORTED_DIVIDEND_REVIEW_ISSUE_TYPES
    ):
        raise ValueError(
            "issue_type 必須是 "
            "MISSING_ACTUAL_COMPONENTS 或 "
            "MISSING_SOURCE_DOCUMENT"
        )

    return normalized_value


def normalize_etf_comparison_codes(
    codes: list[str] | tuple[str, ...],
) -> tuple[str, ...]:
    """正規化並驗證 2 至 4 個 ETF 代號。"""

    normalized: list[str] = []
    seen: set[str] = set()

    for value in codes:
        code = str(value).strip().upper()

        if not code or code in seen:
            continue

        if (
            len(code) < 4
            or len(code) > 10
            or not code.isalnum()
        ):
            raise ValueError(
                f"ETF 代號格式不正確：{code}"
            )

        normalized.append(code)
        seen.add(code)

    if len(normalized) < 2:
        raise ValueError(
            "ETF 比較至少需要 2 個不同代號"
        )

    if len(normalized) > 4:
        raise ValueError(
            "ETF 比較最多支援 4 個不同代號"
        )

    return tuple(normalized)
