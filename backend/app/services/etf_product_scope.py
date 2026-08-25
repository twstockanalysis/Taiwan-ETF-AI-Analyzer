"""V3 共用的 ETF 產品類型支援範圍判定。"""


def unsupported_allocation_product_reason(
    code: str,
    name: str,
    is_bond: bool,
) -> str | None:
    """排除尚未有可比較配置規則的非一般股票型 ETF。"""

    normalized_code = code.strip().upper()
    normalized_name = name.strip().upper()
    if is_bond or normalized_code.endswith(("B", "D")) or "債" in normalized_name:
        return "BOND_OR_FIXED_INCOME"
    if normalized_code.endswith(("L", "R", "U")):
        return "LEVERAGED_INVERSE_OR_FUTURES"
    if any(value in normalized_name for value in ("正2", "反1", "反一")):
        return "LEVERAGED_INVERSE_OR_FUTURES"
    if normalized_name.startswith("期") or any(
        value in normalized_name for value in ("原油", "黃金", "美元指", "布蘭特")
    ):
        return "LEVERAGED_INVERSE_OR_FUTURES"
    if normalized_code.endswith("T") or "平衡" in normalized_name:
        return "MULTI_ASSET"
    return None
