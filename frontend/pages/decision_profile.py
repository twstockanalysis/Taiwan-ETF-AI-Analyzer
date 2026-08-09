"""M11-1 單一使用者條件與手動持有部位頁面。"""

from decimal import Decimal, InvalidOperation
from typing import Any

import streamlit as st

from frontend.api_client import (
    APIClientError,
    delete_manual_holding,
    fetch_decision_profile,
    save_manual_holding,
    save_user_conditions,
)
from frontend.config import get_api_base_url
from frontend.ui.formatters import (
    asset_type_label,
    format_iso_date,
    format_number,
    management_type_label,
)
from frontend.ui.states import loading_state, render_api_error


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def build_holding_rows(profile: dict[str, Any]) -> list[dict[str, str]]:
    """建立小型持有部位靜態表格，保留價格缺值語意。"""

    rows = []
    for item in profile["holdings"]:
        units = int(item["held_units"])
        unit_price = _decimal(item.get("unit_price"))
        reference_value = (
            unit_price * units if unit_price is not None else None
        )
        rows.append(
            {
                "ETF": f"{item['etf_code']} {item['name']}",
                "管理方式": management_type_label(item["is_active"]),
                "資產類型": asset_type_label(item["is_bond"]),
                "持有單位": f"{units:,}",
                "參考單價": (
                    f"{format_number(unit_price, decimal_places=2)} TWD"
                    if unit_price is not None
                    else "尚未取得"
                ),
                "參考部位價值": (
                    f"{format_number(reference_value, decimal_places=2)} TWD"
                    if reference_value is not None
                    else "無法計算"
                ),
                "價格日期": format_iso_date(
                    item.get("price_as_of_date"),
                    missing_text="未提供",
                ),
            }
        )
    return rows


@st.cache_data(ttl=30, max_entries=5, show_spinner=False)
def load_decision_profile(api_base_url: str) -> dict[str, Any]:
    return fetch_decision_profile(api_base_url)


@st.dialog("確認刪除持有部位")
def confirm_holding_delete(api_base_url: str, etf_code: str) -> None:
    st.write(f"確定刪除 **{etf_code}** 的手動持有部位嗎？")
    st.caption("這只會刪除本網站的手動紀錄，不會連接券商或送出交易。")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button(
            "確認刪除",
            type="primary",
            icon=":material/delete:",
            key=f"confirm_delete_{etf_code}",
        ):
            try:
                delete_manual_holding(api_base_url, etf_code)
            except APIClientError as error:
                render_api_error("無法刪除手動持有部位。", error)
                return
            load_decision_profile.clear()
            st.rerun()


def render_decision_profile() -> None:
    """顯示單一使用者條件與無券商連線的手動持有部位。"""

    st.title("我的條件與持有部位")
    st.caption(
        "M11-1 為單一使用者、手動輸入模式；"
        "不連接券商、不讀取帳戶，也不會送出交易。"
    )
    st.warning(
        "此頁目前只適用受控的單一使用者環境；"
        "公開部署前必須限制寫入存取，避免不同訪客共用或覆寫資料。"
    )
    try:
        api_base_url = get_api_base_url()
        with loading_state("正在讀取已儲存的條件與持有部位..."):
            profile = load_decision_profile(api_base_url)
    except (APIClientError, ValueError) as error:
        render_api_error("無法取得決策條件。", error)
        return

    conditions = profile.get("conditions") or {}
    st.subheader("固定分析條件")
    st.caption("這些條件會在後續切片重用 M10 計算；儲存本身不會產生推薦。")
    with st.form("decision_profile_conditions"):
        condition_columns = st.columns(3)
        with condition_columns[0]:
            monthly_target = st.number_input(
                "每月稅後現金目標（TWD）",
                min_value=0.0,
                value=float(conditions.get("monthly_after_tax_target", 3000)),
                step=500.0,
            )
        with condition_columns[1]:
            analysis_years = st.number_input(
                "分析年數",
                min_value=1,
                max_value=50,
                value=int(conditions.get("analysis_years", 10)),
            )
            history_years = st.number_input(
                "歷史資料年數",
                min_value=1,
                max_value=10,
                value=int(conditions.get("history_years", 3)),
            )
        with condition_columns[2]:
            saved_deduction = conditions.get("cash_deduction_rate_pct")
            has_deduction = st.checkbox(
                "提供現金扣除率假設",
                value=saved_deduction is not None,
            )
            deduction_rate = st.number_input(
                "現金扣除率（%）",
                min_value=0.0,
                max_value=100.0,
                value=float(saved_deduction or 0),
            )
        condition_submitted = st.form_submit_button(
            "儲存固定條件",
            type="primary",
            icon=":material/save:",
        )

    if condition_submitted:
        try:
            save_user_conditions(
                api_base_url,
                {
                    "monthly_after_tax_target": monthly_target,
                    "analysis_years": int(analysis_years),
                    "history_years": int(history_years),
                    "cash_deduction_rate_pct": (
                        deduction_rate if has_deduction else None
                    ),
                    "currency": "TWD",
                },
            )
        except APIClientError as error:
            render_api_error("無法儲存固定分析條件。", error)
        else:
            load_decision_profile.clear()
            st.rerun()

    st.divider()
    st.subheader("手動持有部位")
    st.caption(
        "參考價格是使用者輸入的情境值，不是即時報價；"
        "相同 ETF 代號再次儲存會更新既有紀錄。"
    )
    with st.form("manual_holding_upsert"):
        holding_columns = st.columns(3)
        with holding_columns[0]:
            etf_code = st.text_input(
                "ETF 代號",
                placeholder="例如 0056",
                max_chars=10,
            )
            held_units = st.number_input(
                "持有單位數",
                min_value=1,
                value=1000,
                step=1,
            )
        with holding_columns[1]:
            unit_price = st.number_input(
                "參考單價（TWD）",
                min_value=0.01,
                value=30.0,
                step=0.1,
            )
        with holding_columns[2]:
            has_price_date = st.checkbox("提供參考價格日期", value=False)
            price_date = st.date_input("參考價格日期")
        holding_submitted = st.form_submit_button(
            "新增或更新持有部位",
            type="primary",
            icon=":material/add_chart:",
        )

    if holding_submitted:
        normalized_code = etf_code.strip().upper()
        if not normalized_code:
            st.warning("請輸入 ETF 代號。")
        else:
            try:
                save_manual_holding(
                    api_base_url,
                    normalized_code,
                    {
                        "held_units": int(held_units),
                        "unit_price": unit_price,
                        "price_as_of_date": (
                            price_date.isoformat() if has_price_date else None
                        ),
                        "currency": "TWD",
                    },
                )
            except APIClientError as error:
                render_api_error("無法儲存手動持有部位。", error)
            else:
                load_decision_profile.clear()
                st.rerun()

    if not profile["holdings"]:
        st.info("目前尚未建立手動持有部位。")
        return

    st.table(build_holding_rows(profile))
    with st.container(horizontal=True):
        for item in profile["holdings"]:
            code = item["etf_code"]
            if st.button(
                f"刪除 {code}",
                icon=":material/delete:",
                key=f"delete_holding_{code}",
            ):
                confirm_holding_delete(api_base_url, code)
