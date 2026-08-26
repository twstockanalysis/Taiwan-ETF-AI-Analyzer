"""Per-session Streamlit owner unlock state."""

import streamlit as st

from frontend.api.decision_profile import fetch_decision_profile
from frontend.api.errors import APIClientError


OWNER_TOKEN_STATE = "owner_access_token"


def get_owner_token() -> str | None:
    value = st.session_state.get(OWNER_TOKEN_STATE)
    return value if isinstance(value, str) and value else None


def render_owner_access(api_base_url: str) -> bool:
    """Render the owner unlock control and return current session access."""

    token = get_owner_token()
    with st.sidebar:
        st.divider()
        st.subheader("Owner-only 功能")
        if token:
            st.success("此分頁已解鎖私人持股功能。")
            if st.button("鎖定私人功能", icon=":material/lock:", key="owner_lock"):
                st.session_state.pop(OWNER_TOKEN_STATE, None)
                st.rerun()
            return True
        with st.form(
            "owner_unlock",
            border=False,
            enter_to_submit=False,
        ):
            entered = st.text_input(
                "Owner token",
                type="password",
                key="owner_token_input",
                autocomplete="off",
            )
            submitted = st.form_submit_button(
                "解鎖私人功能",
                icon=":material/lock_open:",
            )
        if submitted:
            try:
                fetch_decision_profile(api_base_url, entered)
            except (APIClientError, ValueError):
                st.error("無法解鎖，請確認 token 與後端設定。")
            else:
                st.session_state[OWNER_TOKEN_STATE] = entered
                st.rerun()
        st.caption("公開 ETF 查詢不需解鎖；token 僅保留在此瀏覽器分頁的 session。")
    return False
