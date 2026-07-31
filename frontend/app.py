"""TW ETF AI Analyzer Streamlit 應用程式入口。"""

import streamlit as st

from frontend.navigation import (
    create_navigation,
)


def main() -> None:
    """建立並執行 Streamlit 網站。"""

    st.set_page_config(
        page_title="TW ETF AI Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    navigation = create_navigation()
    navigation.run()


if __name__ == "__main__":
    main()
