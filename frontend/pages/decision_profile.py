"""M11-1 單一使用者條件與手動持有部位頁面。"""

from decimal import Decimal, InvalidOperation
from typing import Any

import streamlit as st

from frontend.api_client import (
    APIClientError,
    delete_manual_holding,
    fetch_candidate_holding_analysis,
    fetch_current_holding_analysis,
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


def build_analysis_holding_rows(
    analysis: dict[str, Any],
) -> list[dict[str, str]]:
    """建立目前持倉分析的可閱讀歷史事實表格。"""

    rows = []
    for item in analysis["holdings"]:
        annual_cash = _decimal(item.get("annual_gross_distribution_cash"))
        annual_return = _decimal(item.get("annualized_price_return_pct"))
        rows.append(
            {
                "ETF": f"{item['etf_code']} {item['name']}",
                "目前部位價值": (
                    f"{format_number(item['current_value'], decimal_places=2)} TWD"
                ),
                "年均稅前配息現金": (
                    f"{format_number(annual_cash, decimal_places=2)} TWD"
                    if annual_cash is not None
                    else "無法計算"
                ),
                "價格報酬期間": item.get("price_return_period_code") or "無資料",
                "年化價格報酬": (
                    f"{format_number(annual_return, decimal_places=2)}%"
                    if annual_return is not None
                    else "無法計算"
                ),
            }
        )
    return rows


@st.cache_data(ttl=30, max_entries=5, show_spinner=False)
def load_decision_profile(api_base_url: str) -> dict[str, Any]:
    return fetch_decision_profile(api_base_url)


@st.cache_data(ttl=30, max_entries=5, show_spinner=False)
def load_current_holding_analysis(api_base_url: str) -> dict[str, Any]:
    return fetch_current_holding_analysis(api_base_url)


def _metric_value(value: Any, *, suffix: str = "") -> str:
    parsed = _decimal(value)
    if parsed is None:
        return "無法計算"
    return f"{format_number(parsed, decimal_places=2)}{suffix}"


def render_current_holding_analysis_result(
    analysis: dict[str, Any],
) -> None:
    """以原生 Streamlit 元件呈現整體持倉情境結果。"""

    if analysis["status"] == "UNAVAILABLE":
        reasons = "、".join(
            item["reason"] for item in analysis["unavailable_fields"]
        )
        st.info(f"目前無法分析：{reasons}")
        return

    portfolio = analysis["portfolio_analysis"]
    cash_flow = portfolio["cash_flow"]
    scenario = portfolio["scenario_estimate"]
    with st.container(horizontal=True):
        st.metric(
            "目前部位總值",
            _metric_value(analysis.get("total_current_value"), suffix=" TWD"),
            border=True,
        )
        st.metric(
            "年均稅前配息現金",
            _metric_value(cash_flow.get("gross_distribution_cash"), suffix=" TWD"),
            border=True,
        )
        st.metric(
            "年均稅後可用現金",
            _metric_value(cash_flow.get("after_tax_usable_cash"), suffix=" TWD"),
            border=True,
        )
        st.metric(
            "年度目標覆蓋率",
            _metric_value(cash_flow.get("target_coverage_pct"), suffix="%"),
            border=True,
        )

    st.table(build_analysis_holding_rows(analysis))
    st.caption(
        f"分析日期 {analysis['analysis_date']}；情境期間 "
        f"{scenario.get('projection_years') or '無法計算'} 年。"
        "價格報酬會先年化後依目前部位價值加權；配息不再投入。"
    )
    data_warnings = [
        f"{item['etf_code']}：{warning['message']}"
        for item in analysis["holdings"]
        for warning in item.get("warnings", [])
    ]
    if data_warnings:
        st.warning("資料提醒：" + "、".join(data_warnings))
    if analysis["status"] == "PARTIAL":
        reasons = "、".join(
            f"{item['field']}：{item['reason']}"
            for item in analysis["unavailable_fields"]
        )
        st.warning(f"部分結果無法計算：{reasons}")


def build_candidate_comparison_rows(
    comparison: dict[str, Any],
) -> list[dict[str, str]]:
    """建立候選加入前後的小型靜態比較表。"""

    fields = [
        ("目前部位總值", "total_value_before", "total_value_after", " TWD"),
        (
            "年均稅後可用現金",
            "annual_after_tax_cash_before",
            "annual_after_tax_cash_after",
            " TWD",
        ),
        (
            "年度目標覆蓋率",
            "target_coverage_pct_before",
            "target_coverage_pct_after",
            "%",
        ),
        (
            "資金缺口",
            "funding_shortfall_before",
            "funding_shortfall_after",
            " TWD",
        ),
        (
            "情境稅後總報酬率",
            "after_tax_total_return_pct_before",
            "after_tax_total_return_pct_after",
            "%",
        ),
    ]
    return [
        {
            "比較項目": label,
            "目前持倉": _metric_value(comparison.get(before), suffix=suffix),
            "加入候選後": _metric_value(comparison.get(after), suffix=suffix),
        }
        for label, before, after, suffix in fields
    ]


def render_candidate_holding_analysis_result(
    analysis: dict[str, Any],
) -> None:
    """呈現候選 ETF 前後差異與 M10-5 納入／排除理由。"""

    if analysis["status"] == "UNAVAILABLE":
        reasons = "、".join(
            item["reason"] for item in analysis["unavailable_fields"]
        )
        st.info(f"目前無法比較候選 ETF：{reasons}")
        return

    comparison = analysis["comparison"]
    with st.container(horizontal=True):
        st.metric(
            "候選投入金額",
            _metric_value(comparison.get("additional_capital"), suffix=" TWD"),
            border=True,
        )
        st.metric(
            "目標覆蓋率變化",
            _metric_value(
                comparison.get("target_coverage_pct_delta"), suffix="%"
            ),
            border=True,
        )
        st.metric(
            "稅後現金變化",
            _metric_value(
                comparison.get("annual_after_tax_cash_delta"), suffix=" TWD"
            ),
            border=True,
        )
        st.metric(
            "資金缺口減少",
            _metric_value(
                comparison.get("funding_shortfall_reduction"), suffix=" TWD"
            ),
            border=True,
        )
    st.table(build_candidate_comparison_rows(comparison))

    eligibility = analysis["eligibility"]
    selected = eligibility["selected_candidates"]
    rejected = eligibility["rejected_candidates"]
    candidate = selected[0] if selected else rejected[0]
    reason_text = "；".join(
        item["message"] for item in candidate.get("reasons", [])
    )
    reason_codes = {
        item["code"] for item in candidate.get("reasons", [])
    }
    if "MONTHLY_COVERAGE_DISABLED" in reason_codes:
        st.info(f"本次未進行月配候選判定：{reason_text}")
    elif selected:
        st.success(f"候選通過目前門檻：{reason_text}")
    else:
        st.warning(f"候選未通過目前門檻：{reason_text}")
    st.caption(
        "判定順序固定為：總報酬與本金風險 → 稅後現金流可行性 → "
        "稅務效率 → 選配月月領息。持股重疊缺值不等於零。"
    )
    st.caption(analysis["estimate_label"] + "；分析不會寫入手動持倉。")


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
            load_current_holding_analysis.clear()
            st.session_state.pop("candidate_holding_analysis_result", None)
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
            load_current_holding_analysis.clear()
            st.session_state.pop("candidate_holding_analysis_result", None)
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
                load_current_holding_analysis.clear()
                st.session_state.pop("candidate_holding_analysis_result", None)
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

    st.divider()
    st.subheader("目前持倉分析")
    st.caption(
        "使用上方已儲存條件與所有手動持倉，重用 M10 公式進行整體情境估算；"
        "結果不是個別 ETF 推薦，也不保證未來收益。"
    )
    if st.button(
        "分析目前持倉",
        type="primary",
        icon=":material/analytics:",
    ):
        st.session_state["show_current_holding_analysis"] = True
    if st.session_state.get("show_current_holding_analysis", False):
        try:
            with loading_state("正在彙總目前持倉分析..."):
                analysis = load_current_holding_analysis(api_base_url)
        except APIClientError as error:
            render_api_error("無法取得目前持倉分析。", error)
        else:
            render_current_holding_analysis_result(analysis)

    st.divider()
    st.subheader("候選 ETF 加碼比較")
    st.caption(
        "輸入一個候選加碼情境，比較加入前後的整體持倉；"
        "此分析不會新增或更新手動持倉。"
    )
    with st.form("candidate_holding_analysis"):
        candidate_columns = st.columns(3)
        with candidate_columns[0]:
            candidate_code = st.text_input(
                "候選 ETF 代號",
                placeholder="例如 00878",
                max_chars=10,
            )
            proposed_units = st.number_input(
                "預計增加單位數",
                min_value=1,
                value=1000,
                step=1,
            )
        with candidate_columns[1]:
            candidate_price = st.number_input(
                "候選參考單價（TWD）",
                min_value=0.01,
                value=20.0,
                step=0.1,
            )
            analysis_goal = st.segmented_control(
                "候選分析目標",
                options=["補足月配缺口", "不進行月配候選判定"],
                default="補足月配缺口",
            )
        with candidate_columns[2]:
            has_overlap = st.checkbox("提供持股重疊估計", value=False)
            overlap = st.number_input(
                "與目前持倉重疊（%）",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                disabled=not has_overlap,
            )
        candidate_submitted = st.form_submit_button(
            "比較候選加入前後",
            type="primary",
            icon=":material/compare_arrows:",
        )

    if candidate_submitted:
        normalized_candidate = candidate_code.strip().upper()
        if not normalized_candidate:
            st.warning("請輸入候選 ETF 代號。")
        else:
            try:
                with loading_state("正在比較候選 ETF 加入前後..."):
                    st.session_state[
                        "candidate_holding_analysis_result"
                    ] = fetch_candidate_holding_analysis(
                        api_base_url,
                        normalized_candidate,
                        {
                            "proposed_units": int(proposed_units),
                            "unit_price": candidate_price,
                            "holding_overlap_pct": (
                                overlap if has_overlap else None
                            ),
                            "monthly_coverage_enabled": (
                                analysis_goal == "補足月配缺口"
                            ),
                        },
                    )
            except APIClientError as error:
                render_api_error("無法完成候選持倉分析。", error)
    if "candidate_holding_analysis_result" in st.session_state:
        render_candidate_holding_analysis_result(
            st.session_state["candidate_holding_analysis_result"]
        )
