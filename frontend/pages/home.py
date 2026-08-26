"""GoodCat 股利喵初學者首頁。"""

import streamlit as st

from frontend.branding import SITE_NAME
from frontend.navigation import (
    ETF_COMPARISON_ROUTE,
    ETF_SEARCH_ROUTE,
    PERFORMANCE_RANKING_ROUTE,
    PUBLIC_PLANNER_ROUTE,
    create_streamlit_page,
)
from frontend.ui.goodcat import (
    GoodCatState,
    render_goodcat_companion,
)


SITE_SLOGAN = (
    "股利喵幫你算，ETF規劃不踩雷！\n\n"
    "Your GoodCat, Easy ETF planning!"
)
PLANNER_INTRO = (
    "咪想知道主人要在哪些月份領股利 → 目標是多少，幫咪輸入目前持有的 "
    "ETF，或直接空白；\n\n"
    "咪會幫忙計算並推薦以及所需資金唷，喵~"
)
PLANNER_NOTICE = (
    "不需登入，所有資料皆來源自證交所及投信，計算結果僅供用戶參考，"
    "是否購買皆由用戶決定。"
)


def render_primary_action() -> None:
    """將核心配置流程放在首頁第一個可操作位置。"""

    with st.container(border=True, key="home-primary-action"):
        st.write(PLANNER_INTRO)
        st.page_link(
            create_streamlit_page(PUBLIC_PLANNER_ROUTE),
            label="開始配置",
            icon=":material/calculate:",
            width="stretch",
        )
        st.caption(PLANNER_NOTICE)


def render_exploration_links() -> None:
    """呈現核心配置以外的次要資料探索入口。"""

    st.subheader("也可以先了解 ETF")
    routes = (
        (ETF_SEARCH_ROUTE, "查 ETF 基本資料", ":material/search:"),
        (PERFORMANCE_RANKING_ROUTE, "看歷史績效", ":material/query_stats:"),
        (ETF_COMPARISON_ROUTE, "並排比較 ETF", ":material/compare_arrows:"),
    )
    columns = st.columns(3)
    for column, (route, label, icon) in zip(columns, routes, strict=True):
        with column:
            st.page_link(
                create_streamlit_page(route),
                label=label,
                icon=icon,
                width="stretch",
            )


def render_home() -> None:
    """顯示以初學者核心任務為主的首頁。"""

    st.title(SITE_NAME)
    st.caption(SITE_SLOGAN)
    render_goodcat_companion(
        GoodCatState.IDLE,
        key="home-goodcat",
    )
    render_primary_action()
    render_exploration_links()
