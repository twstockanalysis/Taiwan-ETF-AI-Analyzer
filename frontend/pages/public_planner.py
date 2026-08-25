"""V3-1 公開且不儲存資料的現金流配置試算頁。"""

from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import streamlit as st

from frontend.api_client import APIClientError, fetch_portfolio_projections
from frontend.config import get_api_base_url
from frontend.ui.formatters import format_number
from frontend.ui.states import loading_state, render_api_error


MONTH_OPTIONS = list(range(1, 13))
MONTH_PRESETS = {
    "每月": MONTH_OPTIONS,
    "單數月": [1, 3, 5, 7, 9, 11],
    "雙數月": [2, 4, 6, 8, 10, 12],
}
TARGET_MONTHS_STATE_KEY = "public_planner_target_months"
REINVESTMENT_POLICY_STATE_KEY = "public_planner_reinvestment_policy"
HOLDING_ROWS_STATE_KEY = "public_planner_holding_rows"
HOLDING_EDITOR_VERSION_STATE_KEY = "public_planner_holding_editor_version"
HOLDING_SELECTION_COLUMN = "選取"
DEFAULT_HISTORY_YEARS = 10
DEFAULT_CASH_DEDUCTION_RATE_PCT = 0.0
DEFAULT_CUSTOM_REINVESTMENT_PCT = 50.0


def apply_month_preset(months: list[int]) -> None:
    """將月份快速選取同步到逐月選擇元件。"""

    st.session_state[TARGET_MONTHS_STATE_KEY] = list(months)


def empty_holding_editor_rows() -> pd.DataFrame:
    """建立可接受 0 檔持股的明確型別空表。"""

    return pd.DataFrame(
        {
            HOLDING_SELECTION_COLUMN: pd.Series(dtype="bool"),
            "ETF 代號": pd.Series(dtype="string"),
            "持有股數": pd.Series(dtype="Int64"),
        }
    )


def normalize_holding_editor_rows(rows: pd.DataFrame) -> pd.DataFrame:
    """維持庫存持股表欄位順序與明確型別。"""

    normalized = rows.reindex(
        columns=[HOLDING_SELECTION_COLUMN, "ETF 代號", "持有股數"]
    ).copy()
    normalized[HOLDING_SELECTION_COLUMN] = (
        normalized[HOLDING_SELECTION_COLUMN].fillna(False).astype("bool")
    )
    normalized["ETF 代號"] = normalized["ETF 代號"].astype("string")
    normalized["持有股數"] = pd.to_numeric(
        normalized["持有股數"], errors="coerce"
    ).astype("Int64")
    return normalized.reset_index(drop=True)


def add_empty_holding_row(rows: pd.DataFrame) -> pd.DataFrame:
    """在庫存持股表加入一列空白輸入。"""

    new_row = pd.DataFrame(
        {
            HOLDING_SELECTION_COLUMN: pd.Series([False], dtype="bool"),
            "ETF 代號": pd.Series([pd.NA], dtype="string"),
            "持有股數": pd.Series([pd.NA], dtype="Int64"),
        }
    )
    return normalize_holding_editor_rows(
        pd.concat([normalize_holding_editor_rows(rows), new_row], ignore_index=True)
    )


def remove_selected_holding_rows(rows: pd.DataFrame) -> pd.DataFrame:
    """只刪除已明確勾選的庫存持股列。"""

    normalized = normalize_holding_editor_rows(rows)
    return normalize_holding_editor_rows(
        normalized.loc[~normalized[HOLDING_SELECTION_COLUMN]]
    )


def replace_holding_rows(rows: pd.DataFrame) -> None:
    """更新庫存持股資料並重建編輯器，避免殘留舊列狀態。"""

    st.session_state[HOLDING_ROWS_STATE_KEY] = normalize_holding_editor_rows(rows)
    st.session_state[HOLDING_EDITOR_VERSION_STATE_KEY] += 1


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


def render_allocation_results(payload: dict[str, Any]) -> str:
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
    return plan["strategy"]


def build_historical_evidence_rows(evidence: dict[str, Any]) -> list[dict[str, str]]:
    labels = {
        "AVAILABLE_HISTORY": "最長可用歷史",
        "3Y": "近 3 年",
        "5Y": "近 5 年",
        "10Y": "近 10 年",
    }
    rows = []
    for item in evidence.get("historical_periods", []):
        available = item.get("status") == "AVAILABLE"
        period_start = item.get("period_start")
        period_end = item.get("period_end")
        issue_messages = [
            issue["message"] for issue in item.get("issues", [])
        ]
        rows.append(
            {
                "期間": labels.get(item.get("period"), item.get("period", "")),
                "實際資料範圍": (
                    f"{period_start} 至 {period_end}"
                    if available and period_start and period_end
                    else "歷史資料不足"
                ),
                "含息總報酬估算": format_number(
                    item.get("total_return_pct") if available else None,
                    decimal_places=2,
                    suffix="%",
                    missing_text="無法計算",
                ),
                "年化含息報酬估算": format_number(
                    item.get("annualized_total_return_pct") if available else None,
                    decimal_places=2,
                    suffix="%",
                    missing_text="無法計算",
                ),
                "說明": "、".join(issue_messages) if issue_messages else "可用",
            }
        )
    return rows


def build_scenario_chart_rows(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    rows_by_year: dict[int, dict[str, Any]] = {}
    for scenario in evidence.get("scenarios", []):
        label = scenario["label"]
        for point in scenario.get("index_points", []):
            year = int(point["year"])
            rows_by_year.setdefault(year, {"年數": year})[label] = float(
                point["total_value_index"]
            )
    return [rows_by_year[year] for year in sorted(rows_by_year)]


def render_long_term_evidence(payload: dict[str, Any], strategy: str) -> None:
    evidence = next(
        item for item in payload["plan_evidence"] if item["strategy"] == strategy
    )
    st.subheader("長期歷史與十年情境")
    st.caption(
        "以上方配置後的整數股數回算；歷史配息不再投入。"
    )
    st.dataframe(build_historical_evidence_rows(evidence), hide_index=True)
    has_available_history = any(
        item.get("status") == "AVAILABLE"
        for item in evidence.get("historical_periods", [])
    )
    if has_available_history:
        st.warning(
            "歷史價格目前是官方原始收盤價，尚未調整 ETF 分割或反分割；"
            "如果期間發生股數變動，報酬估算可能失真。"
        )

    scenarios = evidence.get("scenarios", [])
    if not scenarios:
        st.info("完整一年期觀察少於 2 筆，因此不產生十年情境。")
    else:
        with st.container(horizontal=True):
            for scenario in scenarios:
                st.metric(
                    scenario["label"],
                    format_number(
                        scenario["annual_total_return_assumption_pct"],
                        decimal_places=2,
                        suffix="% / 年",
                    ),
                    border=True,
                )
        chart_rows = build_scenario_chart_rows(evidence)
        st.line_chart(
            pd.DataFrame(chart_rows),
            x="年數",
            y=[scenario["label"] for scenario in scenarios],
            x_label="配置後年數",
            y_label="含息總價值指數",
        )
        st.caption(
            f"指數從 100 起算，不是實際金額。三種情境來自 "
            f"{int(evidence.get('annual_observation_count', 0))} 筆完整一年期歷史觀察的"
            "25／50／75 百分位，再以每年複利延伸。"
        )

    issue_messages = [item["message"] for item in evidence.get("issues", [])]
    extra_messages = [
        message
        for message in dict.fromkeys(issue_messages)
        if "分割或反分割" not in message
        and "少於兩個完整一年期" not in message
    ]
    if extra_messages:
        st.info("長期資料提醒：" + "、".join(extra_messages))
    st.caption(payload["estimate_label"])


def _portfolio_projection_chart_rows(
    market: dict[str, Any],
    selected_policy: str | None = None,
) -> list[dict[str, Any]]:
    policy_labels = {
        "NO_REINVESTMENT": "領出使用",
        "EXCESS_ONLY": "只投入超過目標部分",
        "CUSTOM_PERCENTAGE": "按比例投入",
        "FULL_REINVESTMENT": "全部投入",
    }
    rows_by_year: dict[int, dict[str, Any]] = {}
    for result in market.get("reinvestment_results", []):
        if selected_policy is not None and result["policy"] != selected_policy:
            continue
        label = policy_labels[result["policy"]]
        for point in result.get("year_points", []):
            year = int(point["year"])
            rows_by_year.setdefault(year, {"年數": year})[label] = float(
                point["ending_value"]
            ) + float(point["usable_cash"])
    return [rows_by_year[year] for year in sorted(rows_by_year)]


def render_portfolio_projection(
    payload: dict[str, Any],
    strategy: str,
    selected_reinvestment_policy: str,
) -> None:
    projection = next(
        item for item in payload["plan_projections"] if item["strategy"] == strategy
    )
    st.subheader(f"整體組合 {payload['projection_years']} 年試算")
    st.caption(
        "以配置後全部持股一起估算，只顯示可能產生的個人所得稅與二代健保金額；"
        "不同人的實際結果可能不同。"
    )
    with st.container(horizontal=True):
        st.metric(
            "組合起始價值",
            format_number(
                projection.get("initial_value"), decimal_places=2, suffix=" TWD"
            ),
            border=True,
        )
        st.metric(
            "年現金目標",
            format_number(
                projection.get("annual_cash_target"), decimal_places=2, suffix=" TWD"
            ),
            border=True,
        )
        st.metric(
            "歷史年均配息率",
            format_number(
                projection.get("weighted_annual_gross_distribution_rate_pct"),
                decimal_places=2,
                suffix="%",
                missing_text="無法計算",
            ),
            border=True,
        )

    if projection.get("status") != "AVAILABLE":
        messages = [item["message"] for item in projection.get("issues", [])]
        st.info(
            "目前無法建立整體組合試算。"
            + ((" " + "、".join(dict.fromkeys(messages))) if messages else "")
        )
        return

    markets = projection["market_projections"]
    labels = [item["label"] for item in markets]
    selected = st.segmented_control(
        "市場情境",
        labels,
        default=labels[1] if len(labels) > 1 else labels[0],
        key=f"portfolio_market_{strategy}",
    ) or labels[0]
    market = next(item for item in markets if item["label"] == selected)
    st.caption(
        "這個市場情境假設每年含息報酬約 "
        + format_number(
            market["gross_annual_total_return_assumption_pct"],
            decimal_places=2,
            suffix="%",
        )
        + "；不是未來預測。"
    )

    policy_labels = {
        "NO_REINVESTMENT": "領出使用",
        "EXCESS_ONLY": "只投入超過目標部分",
        "CUSTOM_PERCENTAGE": "按比例投入",
        "FULL_REINVESTMENT": "全部投入",
    }
    selected_policy_label = policy_labels[selected_reinvestment_policy]
    st.caption(f"本次選擇的股息使用方式：{selected_policy_label}。")
    rows = []
    for result in market["reinvestment_results"]:
        if result["policy"] != selected_reinvestment_policy:
            continue
        rows.append(
            {
                "配息使用方式": policy_labels[result["policy"]],
                "期末持股價值": format_number(
                    result["ending_value"], decimal_places=2, suffix=" TWD"
                ),
                "期間可用現金": format_number(
                    result["usable_cash"], decimal_places=2, suffix=" TWD"
                ),
                "投入金額": format_number(
                    result["reinvested_cash"], decimal_places=2, suffix=" TWD"
                ),
                "可能的所得稅": format_number(
                    result["modeled_income_tax"], decimal_places=2, suffix=" TWD"
                ),
                "可能的二代健保": format_number(
                    result["modeled_supplementary_premium"],
                    decimal_places=2,
                    suffix=" TWD",
                ),
                "稅後總報酬": format_number(
                    result["after_tax_total_return_pct"],
                    decimal_places=2,
                    suffix="%",
                ),
            }
        )
    st.dataframe(rows, hide_index=True)
    st.line_chart(
        pd.DataFrame(
            _portfolio_projection_chart_rows(
                market,
                selected_reinvestment_policy,
            )
        ),
        x="年數",
        y=[selected_policy_label],
        x_label="配置後年數",
        y_label="持股價值加已領可用現金（TWD）",
    )

    actual_count = int(projection.get("actual_component_holding_count", 0))
    estimated_count = int(projection.get("estimated_component_holding_count", 0))
    unavailable_count = int(projection.get("unavailable_component_holding_count", 0))
    st.caption(
        f"配息組成來源：正式資料 {actual_count} 檔、估算資料 {estimated_count} 檔、"
        f"缺少資料 {unavailable_count} 檔。估算資本利得不會標示為正式 76W。"
    )
    st.caption(payload["estimate_label"])


def render_public_planner() -> None:
    """Render the public, stateless V3-1 planning flow."""

    st.title("股利試算")
    st.caption("請依序選擇輸入")

    st.session_state.setdefault(TARGET_MONTHS_STATE_KEY, MONTH_OPTIONS)
    st.session_state.setdefault(
        HOLDING_ROWS_STATE_KEY,
        add_empty_holding_row(empty_holding_editor_rows()),
    )
    st.session_state.setdefault(HOLDING_EDITOR_VERSION_STATE_KEY, 0)

    st.subheader("1. 每個目標月想領多少股利（TWD）")
    target_cash = st.number_input(
        "每個目標月想領多少股利（TWD）",
        min_value=0,
        value=3000,
        step=500,
        label_visibility="collapsed",
    )

    st.subheader("2. 領息月份")
    with st.container(horizontal=True):
        for preset_label, preset_months in MONTH_PRESETS.items():
            st.button(
                preset_label,
                type="secondary",
                on_click=apply_month_preset,
                args=(preset_months,),
                key=f"public_planner_month_preset_{preset_label}",
            )
    selected_months = st.pills(
        "領息月份",
        options=MONTH_OPTIONS,
        selection_mode="multi",
        format_func=lambda month: f"{month} 月",
        key=TARGET_MONTHS_STATE_KEY,
        label_visibility="collapsed",
        width="stretch",
    )

    st.subheader("3. 想持有年限")
    projection_years = st.number_input(
        "想持有年限",
        min_value=1,
        max_value=20,
        value=10,
        step=1,
        label_visibility="collapsed",
    )

    st.subheader("4. 庫存ETF持股 (可留空)")
    st.caption(
        "請輸入代號＋股數，價格自動擷取最新收盤價，非即時報價；"
        "若在盤中，則為前一日收盤價。"
    )
    holding_actions = st.container(horizontal=True)
    editor_version = st.session_state[HOLDING_EDITOR_VERSION_STATE_KEY]
    with st.container(key="public-planner-holdings"):
        edited_holdings = st.data_editor(
            st.session_state[HOLDING_ROWS_STATE_KEY],
            num_rows="fixed",
            hide_index=True,
            key=f"public_planner_holding_editor_{editor_version}",
            column_order=[HOLDING_SELECTION_COLUMN, "ETF 代號", "持有股數"],
            column_config={
                HOLDING_SELECTION_COLUMN: st.column_config.CheckboxColumn(
                    "選取",
                    help="先勾選要刪除的持股",
                    default=False,
                    width="small",
                ),
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

    selected_holding_count = int(
        edited_holdings[HOLDING_SELECTION_COLUMN].fillna(False).sum()
    )
    with holding_actions:
        add_holding_clicked = st.button(
            "新增持股",
            icon=":material/add:",
            key="public_planner_add_holding",
        )
        delete_holdings_clicked = False
        if selected_holding_count:
            delete_holdings_clicked = st.button(
                f"刪除已選取（{selected_holding_count}）",
                icon=":material/delete:",
                type="secondary",
                key="public_planner_delete_holdings",
            )

    if add_holding_clicked:
        replace_holding_rows(add_empty_holding_row(edited_holdings))
        st.rerun()
    if delete_holdings_clicked:
        replace_holding_rows(remove_selected_holding_rows(edited_holdings))
        st.rerun()

    st.subheader("5. 股息再投入與否")
    reinvestment_policy_label = st.segmented_control(
        "股息再投入與否",
        ["不再投入", "全部再投入"],
        default="不再投入",
        selection_mode="single",
        label_visibility="collapsed",
        key="public_planner_reinvestment_choice",
    ) or "不再投入"

    with st.expander("稅務與再投入假設（可調整）"):
        st.caption(
            "若不調整，系統會依合併計稅、5% 所得稅率及需要估算二代健保，"
            "直接算出可能的所得稅與二代健保金額。"
        )
        tax_method_label = st.segmented_control(
            "股利計稅方式",
            ["合併計稅並試算抵減", "股利 28% 分開計稅"],
            default="合併計稅並試算抵減",
        ) or "合併計稅並試算抵減"
        advanced_columns = st.columns(3)
        with advanced_columns[0]:
            marginal_tax_rate = st.number_input(
                "預估個人所得稅率（%）",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=1.0,
                disabled=tax_method_label == "股利 28% 分開計稅",
            )
        with advanced_columns[1]:
            remaining_credit_cap = st.number_input(
                "今年剩餘股利抵減上限（TWD）",
                min_value=0.0,
                max_value=80000.0,
                value=80000.0,
                step=1000.0,
                disabled=tax_method_label == "股利 28% 分開計稅",
            )
            other_income_tax_rate = st.number_input(
                "其他配息組成稅率（%）",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=1.0,
            )
        with advanced_columns[2]:
            premium_exempt = st.checkbox("不估算二代健保", value=False)
    submitted = st.button(
        "產生配置結果",
        type="primary",
        icon=":material/calculate:",
        key="public_planner_submit",
    )

    if submitted:
        selected_reinvestment_policy = (
            "FULL_REINVESTMENT"
            if reinvestment_policy_label == "全部再投入"
            else "NO_REINVESTMENT"
        )
        st.session_state[REINVESTMENT_POLICY_STATE_KEY] = (
            selected_reinvestment_policy
        )
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
                    result = fetch_portfolio_projections(
                        api_base_url,
                        {
                            "target_after_tax_cash_twd": target_cash,
                            "target_months": selected_months,
                            "existing_holdings": holdings,
                            "history_years": DEFAULT_HISTORY_YEARS,
                            "cash_deduction_rate_pct": (
                                DEFAULT_CASH_DEDUCTION_RATE_PCT
                            ),
                            "currency": "TWD",
                            "projection_years": int(projection_years),
                            "custom_reinvestment_pct": (
                                DEFAULT_CUSTOM_REINVESTMENT_PCT
                            ),
                            "dividend_tax_method": (
                                "SEPARATE_28"
                                if tax_method_label == "股利 28% 分開計稅"
                                else "COMBINED_WITH_CREDIT"
                            ),
                            "marginal_income_tax_rate_pct": marginal_tax_rate,
                            "other_income_tax_rate_pct": other_income_tax_rate,
                            "remaining_annual_dividend_credit_cap_twd": (
                                remaining_credit_cap
                            ),
                            "supplementary_premium_exempt": premium_exempt,
                        },
                    )
            except (APIClientError, ValueError) as error:
                render_api_error("無法完成股利試算。", error)
            else:
                st.session_state["public_portfolio_projections"] = result

    result = st.session_state.get("public_portfolio_projections")
    if isinstance(result, dict):
        long_term = result["long_term_scenarios"]
        selected_strategy = render_allocation_results(long_term["allocation_results"])
        render_long_term_evidence(long_term, selected_strategy)
        render_portfolio_projection(
            result,
            selected_strategy,
            st.session_state.get(
                REINVESTMENT_POLICY_STATE_KEY,
                "NO_REINVESTMENT",
            ),
        )
