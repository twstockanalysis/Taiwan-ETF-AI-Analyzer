"""GoodCat 股利喵 Streamlit 應用程式入口。"""

import streamlit as st

from frontend.branding import SITE_NAME
from frontend.navigation import (
    create_navigation,
)
from frontend.owner_access import get_owner_token


def main() -> None:
    """建立並執行 Streamlit 網站。"""

    st.set_page_config(
        page_title=SITE_NAME,
        page_icon=":material/finance_mode:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    owner_unlocked = get_owner_token() is not None
    navigation = create_navigation(owner_unlocked=owner_unlocked)
    navigation.run()


if __name__ == "__main__":
    main()
