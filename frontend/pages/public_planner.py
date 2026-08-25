"""V3-1 公開且不儲存資料的現金流配置試算頁。"""

from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import streamlit as st

from frontend.api_client import APIClientError, fetch_allocation_results
from frontend.config import get_api_base_url
from frontend.ui.formatters import format_number
from frontend.ui.states import loading_state, render_api_error


MONTH_PRESETS: dict[str, list[int] | None] = {
    "每月": list(range(1, 13)),
    "單數月": [1, 3, 5, 7, 9, 11],
    "雙數月": [2, 4, 6, 8, 10, 12],
    "季領（3、6、9、12 月）": [3, 6, 9, 12],
    "半年領（6、12 月）": [6, 12],
    "年領（12 月）": [12],
    "自訂": None,
}


def empty_holding_editor_rows() -> pd.DataFrame:
    """建立可接受 0 檔持股的明確型別空表。"""

    return pd.DataFrame(
        {
            "ETF 代號": pd.Series(dtype="string"),
            "持有股數": pd.Series(dtype="Int64"),
        }
    )


def build_holding_payload(
    rows: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[str]]:
    """將公開表格輸入正規化，並回傳可讀的列級錯誤。"""

    holdings: list[dict[str, Any]] = []
    errors: list[str] = []
    for row_number, row in enumerate(rows.to_dict(orient="records"), start=1):
        raw_code = row.get("ETF 代號")
        raw_units = row.get("持有股數")
        code = "" if pd.isna(raw_code) else str(raw_code).strip().upper()

        if not code and pd.isna(raw_units):
            continue
        if not code:
            errors.append(f"第 {row_number} 列缺少 ETF 代號。")
            continue
        try:
            units = Decimal(str(raw_units))
            units_is_valid = units.is_finite() and units > 0
        except (InvalidOperation, ValueError):
            units_is_valid = False
            units = Decimal("0")
        if not units_is_valid or units != units.to_integral_value():
            errors.append(f"第 {row_number} 列持有股數必須是正整數。")
            continue
        holdings.append({"etf_code": code, "held_units": int(units)})

    codes = [item["etf_code"] for item in holdings]
    duplicates = sorted({code for code in codes if codes.count(code) > 1})
    if duplicates:
        errors.append("ETF 代號不可重複：" + "、".join(duplicates))
    return holdings, errors


def build_monthly_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    """建立 12 個月份的透明現金流與缺口表格。"""

    rows = []
    for item in result["monthly_cash_flow"]:
        rows.append(
            {
                "月份": f"{int(item['month'])} 月",
                "目標月份": "是" if item["selected"] else "—",
                "歷史年均稅前現金": format_number(
                    item.get("gross_cash"),
                    decimal_places=2,
                    suffix=" TWD",
                    missing_text="無法計算",
                ),
                "扣除後可用現金": format_number(
                    item.get("after_tax_cash"),
                    decimal_places=2,
                    suffix=" TWD",
                    missing_text="無法計算",
                ),
                "現金流目標": format_number(
                    item.get("target_after_tax_cash"),
                    decimal_places=2,
                    suffix=" TWD",
                ),
                "尚缺金額": format_number(
                    item.get("shortfall"),
                    decimal_places=2,
                    suffix=" TWD",
                    missing_text="無法計算",
                ),
            }
        )
    return rows


def build_holding_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    """建立現有持股事實表，不將缺值誤顯示為零。"""

    return [
        {
            "ETF": f"{item['etf_code']} {item['name']}",
            "持有股數": f"{int(item['held_units']):,}",
            "官方收盤價": format_number(
                item.get("unit_price"),
                decimal_places=2,
                suffix=" TWD",
                missing_text="尚未取得",
            ),
            "目前部位價值": format_number(
                item.get("current_value"),
                decimal_places=2,
                suffix=" TWD",
                missing_text="無法計算",
            ),
            "價格日期": item.get("price_as_of_date") or "尚未取得",
            "歷史付款月份": (
                "、".join(f"{month} 月" for month in item["historical_payment_months"])
                or "尚無可用資料"
            ),
        }
        for item in result["holdings"]
    ]


def render_public_planner_result(result: dict[str, Any]) -> None:
    """呈現現有持股基線，並清楚標示尚未涵蓋的自動配置。"""

    st.subheader("現有持股現金流基線")
    status_text = "資料可計算" if result["status"] == "AVAILABLE" else "部分資料不足"
    with st.container(horizontal=True):
        st.metric(
            "目前持股總值",
            format_number(
                result.get("total_current_value"),
                decimal_places=2,
                suffix=" TWD",
                missing_text="無法計算",
            ),
            border=True,
        )
        st.metric("選定領息月份", f"{len(result['target_months'])} 個月", border=True)
        st.metric("基線狀態", status_text, border=True)

    if result["holdings"]:
        st.table(build_holding_rows(result))
    else:
        st.info("目前以 0 檔持股起算，因此所有目標月份的缺口等於現金流目標。")

    st.dataframe(build_monthly_rows(result), hide_index=True)
    st.caption(
        f"分析日期 {result['analysis_date']}；使用最近 {result['history_years']} 年、"
        "依付款日歸月的歷史配息年均值。無配息事件的正式月份視為 0；"
        "整檔缺少可用資料時顯示為無法計算。"
    )

    issue_messages = []
    for item in result.get("issues", []):
        prefix = f"{item['etf_code']}：" if item.get("etf_code") else ""
        issue_messages.append(prefix + item["message"])
    if issue_messages:
        st.warning("資料提醒：" + "、".join(dict.fromkeys(issue_messages)))

    st.info(
        "此階段先建立現有持股與月份缺口基線。全市場自動挑選 ETF、"
        "各買多少整股及所需資金，將由 V3-2 與 V3-3 接續完成。"
    )


def build_addition_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "ETF": f"{item['etf_code']} {item['name']}",
            "增加股數": f"{int(item['additional_shares']):,}",
            "參考價格": format_number(
                item.get("reference_price"),
                decimal_places=2,
                suffix=" TWD",
            ),
            "價格日期": item.get("reference_price_as_of") or "未提供",
            "預估所需資金": format_number(
                item.get("required_capital"),
                decimal_places=2,
                suffix=" TWD",
            ),
            "支援月份": "、".join(
                f"{month} 月" for month in item.get("supported_target_months", [])
            ) or "未直接支援目標月份",
        }
        for item in result.get("additions", [])
    ]


def build_allocation_month_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "月份": f"{int(item['month'])} 月",
            "目前可用現金": format_number(
                item.get("current_after_tax_cash"),
                decimal_places=2,
                suffix=" TWD",
            ),
            "新增現金": format_number(
                item.get("added_after_tax_cash"),
                decimal_places=2,
                suffix=" TWD",
            ),
            "配置後現金": format_number(
                item.get("modeled_after_tax_cash"),
                decimal_places=2,
                suffix=" TWD",
            ),
            "目標": format_number(
                item.get("target_after_tax_cash"),
                decimal_places=2,
                suffix=" TWD",
            ),
            "尚缺": format_number(
                item.get("shortfall"),
                decimal_places=2,
                suffix=" TWD",
            ),
        }
        for item in result.get("monthly_results", [])
    ]


def build_resulting_holding_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "ETF 代號": item["etf_code"],
            "原有股數": f"{int(item['existing_shares']):,}",
            "增加股數": f"{int(item['additional_shares']):,}",
            "配置後股數": f"{int(item['resulting_shares']):,}",
            "配置後市值": format_number(
                item.get("resulting_value"),
                decimal_places=2,
                suffix=" TWD",
            ),
            "市值占比": format_number(
                item.get("allocation_pct"),
                decimal_places=2,
                suffix="%",
            ),
        }
        for item in result.get("resulting_holdings", [])
    ]


def render_allocation_results(payload: dict[str, Any]) -> None:
    st.subheader("配置結果")
    plans = payload["plans"]
    labels = [plan["label"] for plan in plans]
    selected_label = labels[0]
    if len(labels) > 1:
        selected_label = st.segmented_control(
            "選擇配置",
            labels,
            default=labels[0],
            key="public_planner_strategy",
        ) or labels[0]
    plan = next(item for item in plans if item["label"] == selected_label)
    result = plan["result"]

    st.caption(plan["simple_explanation"])
    status_labels = {
        "TARGET_MET": "目標月份皆達標",
        "PARTIAL": "部分月份仍有缺口",
        "NO_ELIGIBLE_ALLOCATION": "目前沒有符合門檻的配置",
        "UNAVAILABLE": "必要資料不足",
    }
    with st.container(horizontal=True):
        st.metric(
            "新增所需資金",
            format_number(
                result.get("total_required_additional_capital"),
                decimal_places=2,
                suffix=" TWD",
            ),
            border=True,
        )
        st.metric("新增 ETF", f"{len(result.get('additions', []))} 檔", border=True)
        st.metric(
            "配置狀態",
            status_labels.get(result["status"], result["status"]),
            border=True,
        )

    if result.get("additions"):
        st.markdown("#### 建議增加的 ETF 與股數")
        st.table(build_addition_rows(result))
    else:
        st.info("此配置目前沒有可新增的 ETF；請查看下方原因。")

    st.markdown("#### 目標月份現金流")
    st.dataframe(build_allocation_month_rows(result), hide_index=True)

    issues = [item["message"] for item in result.get("issues", [])]
    if issues:
        st.warning("配置提醒：" + "、".join(dict.fromkeys(issues)))
    if result.get("optimality") == "BOUNDED_BEST_EFFORT":
        st.caption("這是有界配置結果，不代表唯一或已證明的最低資金方案。")

    risks = list(
        dict.fromkeys(
            risk
            for addition in result.get("additions", [])
            for risk in addition.get("risks", [])
        )
    )
    if risks:
        with st.expander("資料限制與風險"):
            for risk in risks:
                st.write(f"- {risk}")

    holdings = build_resulting_holding_rows(result)
    if holdings:
        with st.expander("查看配置後持股"):
            st.dataframe(holdings, hide_index=True)

    assumptions = result.get("assumptions", {})
    st.caption(
        f"參考資料快照：{result.get('snapshot_id', '未提供')}。"
        f"現金扣除率 {assumptions.get('cash_deduction_rate_pct', 0)}%；"
        f"{assumptions.get('transaction_cost_note', '交易成本假設未提供')}"
    )

    strategy_messages = [
        item["message"] for item in payload.get("strategy_issues", [])
    ]
    if strategy_messages:
        st.info("其他配置：" + "、".join(dict.fromkeys(strategy_messages)))

    excluded = payload.get("excluded_candidates", [])
    if excluded:
        with st.expander(f"查看未納入的 ETF（{len(excluded)} 檔）"):
            st.caption("只顯示資料或風險門檻的排除理由，不代表買賣建議。")
            st.dataframe(
                [
                    {
                        "ETF": f"{item['etf_code']} {item['name']}",
                        "未納入原因": "、".join(
                            reason["message"] for reason in item.get("reasons", [])
                        ) or "未提供原因",
                    }
                    for item in excluded
                ],
                hide_index=True,
            )

    st.caption(payload["estimate_label"])


def render_public_planner() -> None:
    """Render the public, stateless V3-1 planning flow."""

    st.title("現金流配置試算")
    st.caption(
        "從每月可用現金目標、想領息的月份與 0～N 檔現有持股開始。"
        "輸入與結果不會寫入資料庫，也不連接券商或送出交易。"
    )

    preset_name = st.selectbox("領息月份方式", options=list(MONTH_PRESETS))
    custom_months: list[int] = []
    if MONTH_PRESETS[preset_name] is None:
        custom_months = st.multiselect(
            "選擇領息月份",
            options=list(range(1, 13)),
            format_func=lambda month: f"{month} 月",
            placeholder="至少選擇一個月份",
        )

    with st.form("public_cash_flow_planner"):
        input_columns = st.columns(3)
        with input_columns[0]:
            target_cash = st.number_input(
                "每個目標月的可用現金目標（TWD）",
                min_value=0.0,
                value=3000.0,
                step=500.0,
            )
        with input_columns[1]:
            history_years = st.number_input(
                "歷史配息年數",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
            )
        with input_columns[2]:
            deduction_rate = st.number_input(
                "現金扣除率假設（%）",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=1.0,
                help="可自行納入稅負、補充保費或其他現金扣除；0% 代表不扣除。",
            )

        st.markdown("#### 現有持股（可留空）")
        st.caption(
            "每列輸入一檔 ETF 與目前股數；使用表格下方新增或刪除列。"
            "價格採系統已保存的最新官方收盤價，不是即時報價。"
        )
        edited_holdings = st.data_editor(
            empty_holding_editor_rows(),
            num_rows="dynamic",
            hide_index=True,
            key="public_planner_holding_editor",
            column_config={
                "ETF 代號": st.column_config.TextColumn(
                    "ETF 代號",
                    help="限本網站收錄的台灣 ETF 代號",
                    max_chars=10,
                ),
                "持有股數": st.column_config.NumberColumn(
                    "持有股數",
                    min_value=1,
                    step=1,
                    format="%d",
                ),
            },
        )
        submitted = st.form_submit_button(
            "產生配置結果",
            type="primary",
            icon=":material/calculate:",
        )

    if submitted:
        selected_months = MONTH_PRESETS[preset_name]
        if selected_months is None:
            selected_months = custom_months
        holdings, errors = build_holding_payload(edited_holdings)
        if not selected_months:
            errors.append("請至少選擇一個領息月份。")
        if errors:
            for message in errors:
                st.warning(message)
        else:
            try:
                api_base_url = get_api_base_url()
                with loading_state("正在檢查全市場資料並計算整數股數..."):
                    result = fetch_allocation_results(
                        api_base_url,
                        {
                            "target_after_tax_cash_twd": target_cash,
                            "target_months": selected_months,
                            "existing_holdings": holdings,
                            "history_years": int(history_years),
                            "cash_deduction_rate_pct": deduction_rate,
                            "currency": "TWD",
                        },
                    )
            except (APIClientError, ValueError) as error:
                render_api_error("無法完成公開現金流試算。", error)
            else:
                st.session_state["public_allocation_results"] = result

    result = st.session_state.get("public_allocation_results")
    if isinstance(result, dict):
        render_allocation_results(result)
