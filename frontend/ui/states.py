"""Streamlit 共用載入、空白與錯誤狀態。"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import streamlit as st


@contextmanager
def loading_state(
    message: str,
) -> Iterator[None]:
    """顯示一致的資料載入狀態。"""

    with st.spinner(message):
        yield


def render_empty_state(
    message: str,
    *,
    hint: str | None = None,
) -> None:
    """顯示查無資料或尚無資料狀態。"""

    st.info(message)

    if hint:
        st.caption(hint)


def render_not_found_state(
    message: str,
    *,
    hint: str | None = None,
) -> None:
    """顯示指定資源不存在狀態。"""

    st.warning(message)

    if hint:
        st.caption(hint)


def render_api_error(
    title: str,
    error: Exception | str,
    *,
    hint: str | None = None,
) -> None:
    """顯示一致的 API 或設定錯誤。"""

    st.error(title)

    error_text = str(error).strip()

    if error_text:
        st.code(
            error_text,
            language=None,
        )

    if hint:
        st.info(hint)
