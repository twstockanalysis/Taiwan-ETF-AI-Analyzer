"""GoodCat 股利喵初學者首頁。"""

import streamlit as st

from frontend.branding import SITE_NAME
from frontend.config import get_api_base_url
from frontend.navigation import (
    ETF_COMPARISON_ROUTE,
    ETF_SEARCH_ROUTE,
    PERFORMANCE_RANKING_ROUTE,
    PUBLIC_PLANNER_ROUTE,
    create_streamlit_page,
)
from frontend.ui.goodcat import (
    GoodCatState,
    get_goodcat_presentation,
)
from frontend.ui.theme_toggle import render_theme_toggle
from frontend.owner_access import render_owner_access_trigger


SITE_SLOGAN = (
    "股利喵幫你算，規劃不踩雷！\n\n"
    "Your GoodCat, Easy planning!"
)
PLANNER_INTRO = (
    "咪想幫主人能固定賺到罐頭錢，這樣才能買很多好吃的罐頭  \n"
    "咪會幫主人規劃&計算所需資金吧，喵嗚~"
)
HOME_GOODCAT_HERO_PATH = get_goodcat_presentation(
    GoodCatState.IDLE
).asset_path.with_name("goodcat-sleeping-hero.png")


def render_primary_action() -> None:
    """將核心配置流程放在首頁第一個可操作位置。"""

    with st.container(border=True, key="home-primary-action"):
        cat_column, copy_column = st.columns(
            [2, 3],
            vertical_alignment="center",
            gap="medium",
        )
        with cat_column:
            st.image(
                HOME_GOODCAT_HERO_PATH,
                caption=None,
                width=260,
                output_format="PNG",
            )
        with copy_column:
            st.write(PLANNER_INTRO)
            st.page_link(
                create_streamlit_page(PUBLIC_PLANNER_ROUTE),
                label="開始!",
                icon=":material/calculate:",
                width="stretch",
            )


def render_exploration_links() -> None:
    """呈現核心配置以外的次要資料探索入口。"""

    st.subheader("也可以")
    routes = (
        (ETF_SEARCH_ROUTE, "查查基本資料", ":material/search:"),
        (PERFORMANCE_RANKING_ROUTE, "看看績效", ":material/query_stats:"),
        (ETF_COMPARISON_ROUTE, "比較比較", ":material/compare_arrows:"),
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

    with st.container(
        key="home-top-actions",
        horizontal=True,
        horizontal_alignment="distribute",
        vertical_alignment="center",
        gap="small",
    ):
        st.title(SITE_NAME, width="content")
        render_owner_access_trigger(
            get_api_base_url()
        )
    slogan_zh, slogan_en = SITE_SLOGAN.split("\n\n", maxsplit=1)
    with st.container(
        key="home-slogan-actions",
        horizontal=True,
        horizontal_alignment="distribute",
        vertical_alignment="center",
        gap="small",
    ):
        with st.container(key="home-slogan", gap=None):
            st.markdown(f"#### {slogan_zh}")
            st.caption(slogan_en)
        render_theme_toggle()
    render_primary_action()
    render_exploration_links()
