"""Per-session Streamlit owner unlock state."""

import streamlit as st

from frontend.api.decision_profile import fetch_decision_profile
from frontend.api.errors import APIClientError


OWNER_TOKEN_STATE = "owner_access_token"


def get_owner_token() -> str | None:
    value = st.session_state.get(OWNER_TOKEN_STATE)
    return value if isinstance(value, str) and value else None


@st.dialog(
    "喵窩",
    icon=":material/pets:",
)
def render_owner_dialog(api_base_url: str) -> None:
    """只在主人主動開啟時呈現私人入口。"""

    token = get_owner_token()
    if token:
        st.success("主人已進入喵窩。")
        if st.button(
            "離開喵窩",
            icon=":material/logout:",
            key="owner_lock",
        ):
            st.session_state.pop(OWNER_TOKEN_STATE, None)
            st.rerun()
        return

    with st.container(border=True):
        with st.form(
            "owner_unlock",
            border=False,
            enter_to_submit=False,
        ):
            entered = st.text_input(
                "喵窩通行碼",
                type="password",
                key="owner_token_input",
                autocomplete="off",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button(
                "進入",
                icon=":material/lock_open:",
            )

    if submitted:
        try:
            fetch_decision_profile(api_base_url, entered)
        except (APIClientError, ValueError):
            st.error("無法進入，請確認通行碼是否正確。")
        else:
            st.session_state[OWNER_TOKEN_STATE] = entered
            st.rerun()


def render_owner_access_trigger(api_base_url: str) -> None:
    """呈現可放入頁首水平列的喵窩入口。"""

    if st.button(
        "喵窩",
        icon=":material/pets:",
        key="owner_access_open",
    ):
        render_owner_dialog(api_base_url)


def render_owner_access(api_base_url: str) -> bool:
    """保留獨立入口介面，並回傳分頁存取狀態。"""

    with st.container(
        key="owner-access-trigger",
        horizontal=True,
        horizontal_alignment="right",
        gap=None,
    ):
        render_owner_access_trigger(api_base_url)

    return get_owner_token() is not None
