"""TW ETF AI Analyzer Streamlit 應用程式入口。"""

import streamlit as st

from frontend.pages.etf_search import (
    render_etf_search,
)
from frontend.pages.home import (
    render_home,
)
from frontend.pages.performance_ranking import (
    render_performance_ranking,
)


def main() -> None:
    """建立並執行 Streamlit 網站。"""

    st.set_page_config(
        page_title="TW ETF AI Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    home_page = st.Page(
        render_home,
        title="首頁",
        icon="🏠",
        default=True,
    )

    etf_search_page = st.Page(
        render_etf_search,
        title="ETF 查詢",
        icon="🔍",
        url_path="etf-search",
    )

    performance_ranking_page = st.Page(
        render_performance_ranking,
        title="績效排行榜",
        icon="📈",
        url_path="performance-ranking",
    )

    etf_detail_page = st.Page(
        "page_scripts/etf_detail_page.py",
        title="ETF 詳細資料",
        icon="📄",
        url_path="etf-detail",
        visibility="hidden",
    )

    navigation = st.navigation(
        {
            "TW ETF AI Analyzer": [
                home_page,
                etf_search_page,
                performance_ranking_page,
                etf_detail_page,
            ],
        }
    )

    navigation.run()


if __name__ == "__main__":
    main()
