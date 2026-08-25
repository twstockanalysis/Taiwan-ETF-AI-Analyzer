"""ETF奈米戶 Streamlit 應用程式入口。"""

import streamlit as st

from frontend.navigation import (
    create_navigation,
)
from frontend.config import get_api_base_url
from frontend.owner_access import render_owner_access


def main() -> None:
    """建立並執行 Streamlit 網站。"""

    st.set_page_config(
        page_title="ETF奈米戶",
        page_icon=":material/finance_mode:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    owner_unlocked = render_owner_access(get_api_base_url())
    navigation = create_navigation(owner_unlocked=owner_unlocked)
    navigation.run()


if __name__ == "__main__":
    main()
