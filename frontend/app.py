"""TW ETF AI Analyzer Streamlit 應用程式入口。"""

import streamlit as st

from frontend.pages.home import (
    render_home,
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

    navigation = st.navigation(
        {
            "TW ETF AI Analyzer": [
                home_page,
            ],
        }
    )

    navigation.run()


if __name__ == "__main__":
    main()